import os
import uuid
import json
import re
from typing import Dict, Any, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
sessions: Dict[str, Dict[str, Any]] = {}

QUESTION_FLOW = [
    "income_frequency",
    "income_amount",
    "fixed_expenses",
    "variable_expenses",
    "current_savings_exact",
    "lifestyle_preferences",
    "goal_confirmation",
]


class PersonalInfo(BaseModel):
    name: str = ""
    age: str = ""
    gender: str = ""
    cast: str = ""


class LifeStageInfo(BaseModel):
    stage: str = ""


class DynamicInfo(BaseModel):
    monthly_allowance_range: str = ""
    monthly_income_range: str = ""
    income_type: str = ""
    dependents: str = ""
    monthly_pension_range: str = ""


class HousingExpense(BaseModel):
    rent: str = ""
    home_loan_emi: str = ""
    utilities: str = ""
    internet_cable: str = ""


class ExpenseSnapshot(BaseModel):
    housing: HousingExpense
    food: str = ""
    transport: str = ""


class SavingsStatus(BaseModel):
    currently_save_money: str = ""
    approx_savings_range: str = ""


class Investments(BaseModel):
    invested_before: str = ""
    fd: str = ""
    sip_mutual_funds: str = ""
    stocks: str = ""
    ppf: str = ""


class InsuranceCheck(BaseModel):
    health_insurance: str = ""
    life_insurance: str = ""


class TaxAwareness(BaseModel):
    file_income_tax: str = ""
    want_to_save_tax: str = ""


class GoalPlan(BaseModel):
    item_to_buy: str = ""
    time_limit: str = ""
    target_amount: str = ""


class IntakeData(BaseModel):
    personal_info: PersonalInfo
    life_stage: LifeStageInfo
    dynamic_info: DynamicInfo
    expense_snapshot: ExpenseSnapshot
    savings_status: SavingsStatus
    investments: Investments
    insurance_check: InsuranceCheck
    tax_awareness: TaxAwareness
    goal_plan: GoalPlan


class StartSessionRequest(BaseModel):
    intake_data: IntakeData


class AnswerRequest(BaseModel):
    session_id: str
    field_key: str
    answer: Any


def normalize_monthly_income(frequency: str, amount: float) -> float:
    if frequency == "monthly":
        return round(amount, 2)
    if frequency == "weekly":
        return round((amount * 52) / 12, 2)
    if frequency == "hourly":
        return round(amount * 8 * 26, 2)
    return round(amount, 2)


def get_answer_map(session: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for item in session["answers"]:
        result[item["field_key"]] = item["answer"]
    return result


def get_next_unanswered_step(session: Dict[str, Any]) -> Optional[str]:
    answer_map = get_answer_map(session)
    for step in QUESTION_FLOW:
        if step not in answer_map:
            return step
    return None


def build_question(step: str, session: Dict[str, Any]) -> Dict[str, Any]:
    intake = session["intake_data"]
    goal = intake.get("goal_plan", {})
    item = goal.get("item_to_buy", "").strip()

    question_bank = {
        "income_frequency": {
            "reply_type": "question",
            "question": "How do you receive your income?",
            "field_key": "income_frequency",
            "input_type": "select",
            "options": ["monthly", "weekly", "hourly"],
        },
        "income_amount": {
            "reply_type": "question",
            "question": "What is your income amount in rupees?",
            "field_key": "income_amount",
            "input_type": "number",
        },
        "fixed_expenses": {
            "reply_type": "question",
            "question": "Enter your fixed monthly expenses like rent, EMI, internet, school fees or subscriptions.",
            "field_key": "fixed_expenses",
            "input_type": "multi_expense",
        },
        "variable_expenses": {
            "reply_type": "question",
            "question": "Enter your variable monthly expenses like food, travel, shopping or eating out.",
            "field_key": "variable_expenses",
            "input_type": "multi_expense",
        },
        "current_savings_exact": {
            "reply_type": "question",
            "question": "How much money do you currently have saved in rupees?",
            "field_key": "current_savings_exact",
            "input_type": "number",
        },
        "lifestyle_preferences": {
            "reply_type": "question",
            "question": "What lifestyle spending do you want to keep even while budgeting?",
            "field_key": "lifestyle_preferences",
            "input_type": "text",
        },
        "goal_confirmation": {
            "reply_type": "question",
            "question": f"Do you want me to create a savings plan for your goal{f' to buy {item}' if item else ''}?",
            "field_key": "goal_confirmation",
            "input_type": "yes_no",
        },
    }
    return question_bank[step]


def generate_budget_advice(session: Dict[str, Any]) -> Dict[str, Any]:
    intake = session["intake_data"]
    answers = get_answer_map(session)

    income_frequency = answers.get("income_frequency", "monthly")
    raw_income_amount = float(answers.get("income_amount", 0) or 0)
    normalized_income = normalize_monthly_income(income_frequency, raw_income_amount)

    fixed_expenses = answers.get("fixed_expenses", [])
    variable_expenses = answers.get("variable_expenses", [])

    fixed_total = sum(float(item.get("amount", 0) or 0) for item in fixed_expenses)
    variable_total = sum(
        float(item.get("amount", 0) or 0) for item in variable_expenses
    )
    current_savings = float(answers.get("current_savings_exact", 0) or 0)

    goal = intake.get("goal_plan", {})
    target_amount = float(goal.get("target_amount", 0) or 0)
    time_limit_text = goal.get("time_limit", "").strip()
    goal_item = goal.get("item_to_buy", "").strip()
    goal_confirmation = str(answers.get("goal_confirmation", "no")).lower()

    months = 0
    if time_limit_text:
        match = re.search(r"(\d+)", time_limit_text)
        if match:
            months = int(match.group(1))

    disposable = normalized_income - fixed_total - variable_total
    gap = max(target_amount - current_savings, 0)

    prompt = f"""
You are a budgeting coach. Return only valid JSON.

User intake:
{json.dumps(intake, indent=2)}

Collected answers:
{json.dumps(answers, indent=2)}

Calculated facts:
- normalized_monthly_income: {normalized_income}
- fixed_total: {fixed_total}
- variable_total: {variable_total}
- disposable_income: {disposable}
- current_savings: {current_savings}
- goal_item: {goal_item}
- goal_target_amount: {target_amount}
- goal_months: {months}
- goal_confirmed: {goal_confirmation}
- savings_gap: {gap}

Return JSON in this exact shape:
{{
  "reply_type": "advice",
  "question": "",
  "field_key": "done",
  "advice": {{
    "monthly_target": "",
    "suggested_cuts": ["", ""],
    "plan": ["", "", ""],
    "summary": {{
      "monthly_income_estimate": "",
      "fixed_expenses_total": "",
      "variable_expenses_total": "",
      "disposable_income": ""
    }}
  }}
}}
"""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a precise budgeting assistant that returns JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    parsed = json.loads(content)
    return parsed


@app.get("/")
def root():
    return {"message": "Budget AI backend running"}


@app.post("/start-session")
def start_session(payload: StartSessionRequest):
    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "intake_data": payload.intake_data.model_dump(),
        "answers": [],
    }

    first_step = get_next_unanswered_step(sessions[session_id])

    return {
        "session_id": session_id,
        "saved_data": sessions[session_id]["intake_data"],
        "saved_answers": sessions[session_id]["answers"],
        "ai": build_question(first_step, sessions[session_id]),
    }


@app.post("/answer")
def answer_question(payload: AnswerRequest):
    if payload.session_id not in sessions:
        return {"error": "Invalid session_id"}

    session = sessions[payload.session_id]

    session["answers"] = [
        item for item in session["answers"] if item["field_key"] != payload.field_key
    ]

    session["answers"].append(
        {"field_key": payload.field_key, "answer": payload.answer}
    )

    next_step = get_next_unanswered_step(session)

    if next_step:
        return {
            "saved_answers": session["answers"],
            "ai": build_question(next_step, session),
        }

    advice = generate_budget_advice(session)

    return {"saved_answers": session["answers"], "ai": advice}


@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        return {"error": "Invalid session_id"}
    return sessions[session_id]
