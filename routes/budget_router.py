import os
import uuid
import json
import re
from typing import Dict, Any, Optional, List

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
router = APIRouter()

sessions: Dict[str, Dict[str, Any]] = {}

QUESTION_FLOW: List[str] = [
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
    result: Dict[str, Any] = {}
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
    item = (goal.get("item_to_buy") or "").strip()

    question_bank: Dict[str, Dict[str, Any]] = {
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
            "question": "Enter your fixed monthly expenses (rent, EMI, internet, subscriptions, school fees, etc.).",
            "field_key": "fixed_expenses",
            "input_type": "multi_expense",
        },
        "variable_expenses": {
            "reply_type": "question",
            "question": "Enter your variable monthly expenses (food, travel, shopping, eating out, etc.).",
            "field_key": "variable_expenses",
            "input_type": "multi_expense",
        },
        "current_savings_exact": {
            "reply_type": "question",
            "question": "How much money do you currently have saved (₹)?",
            "field_key": "current_savings_exact",
            "input_type": "number",
        },
        "lifestyle_preferences": {
            "reply_type": "question",
            "question": "What lifestyle spending do you want to keep even while budgeting? (e.g. gym, weekend trips, coffee)",
            "field_key": "lifestyle_preferences",
            "input_type": "text",
        },
        "goal_confirmation": {
            "reply_type": "question",
            "question": f"Ready to generate your full savings plan{f' for {item}' if item else ''}? Type 'yes' to proceed.",
            "field_key": "goal_confirmation",
            "input_type": "yes_no",
        },
    }
    return question_bank[step]


def parse_int_from_text(text: str) -> int:
    if not text:
        return 0
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0


def safe_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        amt = value.get("amount", 0)
        try:
            return float(amt or 0)
        except Exception:
            return 0.0
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_float_from_list(items: Any) -> float:
    if not isinstance(items, list):
        return 0.0
    total = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        total += safe_float(item.get("amount", 0))
    return total


def generate_budget_advice(session: Dict[str, Any]) -> Dict[str, Any]:
    intake = session["intake_data"]
    answers = get_answer_map(session)

    income_frequency = answers.get("income_frequency", "monthly")
    raw_income_amount = safe_float(answers.get("income_amount", 0))
    normalized_income = normalize_monthly_income(
        str(income_frequency), raw_income_amount
    )

    fixed_expenses = answers.get("fixed_expenses", [])
    variable_expenses = answers.get("variable_expenses", [])

    fixed_total = safe_float_from_list(fixed_expenses)
    variable_total = safe_float_from_list(variable_expenses)
    current_savings = safe_float(answers.get("current_savings_exact", 0))

    goal = intake.get("goal_plan", {})
    target_amount = safe_float(goal.get("target_amount", 0))
    time_limit_text = (goal.get("time_limit") or "").strip()
    goal_item = (goal.get("item_to_buy") or "").strip()

    months = parse_int_from_text(time_limit_text)
    disposable = normalized_income - fixed_total - variable_total
    gap = max(target_amount - current_savings, 0)
    required_monthly = round(gap / months, 2) if months > 0 else 0
    realistic_months = round(gap / max(disposable, 1), 1) if disposable > 0 else None

    prompt = f"""
You are a personal finance coach for an Indian user. Return ONLY valid JSON — no markdown, no explanation.

User profile:
{json.dumps(intake, indent=2)}

Session answers:
{json.dumps(answers, indent=2)}

Pre-computed numbers:
- normalized_monthly_income: ₹{normalized_income}
- fixed_expenses_total: ₹{fixed_total}
- variable_expenses_total: ₹{variable_total}
- disposable_income (income - all expenses): ₹{disposable}
- current_savings: ₹{current_savings}
- goal_item: "{goal_item}"
- goal_target_amount: ₹{target_amount}
- goal_timeline_months: {months}
- savings_gap (target - current savings): ₹{gap}
- required_monthly_saving_to_hit_goal_in_time: ₹{required_monthly}
- realistic_months_at_current_disposable_pace: {realistic_months}

Instructions:
1. Assess whether the goal is REALISTIC in {months} months given the disposable income and required monthly saving.
2. If not realistic, state clearly what is achievable and when — give specific month counts and amounts.
3. List specific expense cuts (with ₹ amounts) that would help close the gap. Be concrete, not generic.
4. Build a month-by-month savings plan showing cumulative savings toward the goal.
5. If the user has lifestyle preferences they want to keep, respect those and find cuts elsewhere.
6. Give an honest, encouraging tone — like a smart friend who is a CA.

Return this exact JSON shape (all string values, arrays of strings):
{{
  "reply_type": "advice",
  "question": "",
  "field_key": "done",
  "advice": {{
    "goal_feasibility": "Realistic | Tight | Not Realistic",
    "goal_verdict": "One clear sentence: can they hit the goal in time or not, and why.",
    "required_monthly_saving": "₹X per month needed to hit goal in Y months",
    "current_monthly_surplus": "₹X disposable after all expenses",
    "shortfall_per_month": "₹X gap between what they need to save vs what they have",
    "suggested_cuts": [
      "Cut [specific expense] by ₹X/month — saves ₹Y over Z months",
      "..."
    ],
    "realistic_timeline": "At current pace, you can reach your goal in X months (Month YYYY)",
    "accelerated_timeline": "With suggested cuts, you can reach it in X months instead",
    "monthly_plan": [
      "Month 1: Save ₹X → Total: ₹Y",
      "Month 3: Total: ₹Y",
      "Month 6: Total: ₹Y"
    ],
    "income_boost_tip": "Optional: one specific way to earn more (freelance, overtime, selling old items)",
    "summary": {{
      "monthly_income": "₹{normalized_income}",
      "fixed_expenses": "₹{fixed_total}",
      "variable_expenses": "₹{variable_total}",
      "disposable_income": "₹{disposable}",
      "current_savings": "₹{current_savings}",
      "goal": "{goal_item} — ₹{target_amount} in {months} months"
    }}
  }}
}}
"""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a precise budgeting assistant. Return JSON only. No markdown fences.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    parsed = json.loads(content)
    return parsed


@router.get("/")
def root():
    return {"message": "Budget AI backend running"}


@router.post("/start-session")
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
        "ai": build_question(first_step, sessions[session_id]) if first_step else None,
    }


@router.post("/answer")
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


@router.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        return {"error": "Invalid session_id"}
    return sessions[session_id]
