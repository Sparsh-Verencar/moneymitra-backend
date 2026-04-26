import os
import json
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

router = APIRouter()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set in environment or .env file")

client = Groq(api_key=api_key)


class OnboardingFormData(BaseModel):
    name: str
    age: str
    gender: str
    caste: str
    lifeStage: str
    monthlyAllowance: str
    monthlyIncome: str
    incomeType: str
    dependents: str
    monthlyPension: str
    rent: str
    homeLoan: str
    utilities: str
    internet: str
    food: str
    transport: str
    savesMoney: bool | None
    approxSavings: str
    investedBefore: bool | None
    investments: list[str]
    healthInsurance: bool | None
    lifeInsurance: bool | None
    filesTax: bool | None
    wantsTaxSave: bool | None


class TaxAdviceRequest(BaseModel):
    onboarding: OnboardingFormData
    question: str


class TaxAdviceResponse(BaseModel):
    summary: str
    regime_hint: str
    sections_used: list[dict]
    suggestions: list[str]
    warnings: list[str]


def build_tax_prompt(onboarding: dict, question: str) -> str:
    return f"""
You are an Indian personal tax assistant helping a non-expert user.

User profile (from app onboarding):
{json.dumps(onboarding, indent=2)}

User question or situation:
{question}

You must:
- Explain in SIMPLE plain language (no legal jargon).
- Use Indian Income Tax Act sections only where relevant: 80C, 80CCD (NPS), 80D, 80E, 24(b) (home loan interest), 80EE/80EEA, 80G, HRA under Section 10, 87A, etc.
- Respect old vs new regime basics:
  - Old regime: many deductions allowed (80C, 80D, HRA, 24(b), etc.).
  - New regime: lower slab rates but very few deductions (80C, 80D generally not allowed). [Old vs new summary: many deductions only in old regime, limited in new.]

Output JSON ONLY in this exact structure:

{{
  "summary": "2–4 sentences in plain language summarising what they can do.",
  "regime_hint": "old / new / depends",
  "sections_used": [
    {{
      "section": "80C",
      "title": "Basic tax-saving investments",
      "approx_limit": "₹1.5L",
      "why_relevant": "e.g. they have salary income and want to save long term",
      "concrete_actions": [
        "Action 1",
        "Action 2"
      ]
    }}
  ],
  "suggestions": [
    "Short, concrete recommendations the user can apply.",
    "Mention typical combos like 80C + 80CCD(1B) + 80D + HRA where relevant."
  ],
  "warnings": [
    "Any caveats: e.g. 'Old regime needed for most deductions', 'Check updated slab rates', 'Consult CA for exact numbers'."
  ]
}}

Rules:
- If you are not sure of something (like exact slab), say 'approximate' and advise them to verify.
- Keep numbers generic and safe (no exact tax payable).
- Always mention if the advice mainly fits the OLD regime.
"""


@router.post("/tax-advice")
def tax_advice(payload: TaxAdviceRequest):
    onboarding_dict = payload.onboarding.model_dump()
    question = payload.question

    messages = [
        {
            "role": "system",
            "content": "You are a cautious, India-specific tax assistant.",
        },
        {"role": "user", "content": build_tax_prompt(onboarding_dict, question)},
    ]

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=(
            {"type": "array", "items": {"type": "object"}} if False else messages
        ),
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "summary": "I could not format a perfect JSON answer, but here is a plain summary.",
            "regime_hint": "depends",
            "sections_used": [],
            "suggestions": [content],
            "warnings": ["Output fell back to plain text JSON parsing."],
        }

    return data
