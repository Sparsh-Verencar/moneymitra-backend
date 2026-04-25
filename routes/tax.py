from fastapi import APIRouter
from pydantic import BaseModel
from llm.tax_model import analyze_tax
import json

router = APIRouter()

class TaxInput(BaseModel):
    salary: float
    interest: float
    freelance: float
    rent: float
    capitalGains: float
    section80C: float
    section80D: float
    section80E: float
    section80G: float
    tdsPaid: float

@router.post("")
async def tax_analyze(data: TaxInput):
    total_income = data.salary + data.interest + data.freelance + data.rent + data.capitalGains
    total_deductions = data.section80C + data.section80D + data.section80E + data.section80G
    taxable_income = max(0, total_income - total_deductions)
    
    # Calculate estimated tax (India FY 2024-25 New Regime)
    if taxable_income <= 300000:
        estimated_tax = 0
    elif taxable_income <= 700000:
        estimated_tax = (taxable_income - 300000) * 0.05
    elif taxable_income <= 1000000:
        estimated_tax = 20000 + (taxable_income - 700000) * 0.10
    elif taxable_income <= 1200000:
        estimated_tax = 50000 + (taxable_income - 1000000) * 0.15
    else:
        estimated_tax = 80000 + (taxable_income - 1200000) * 0.20
    
    # Add cess (4% on tax)
    estimated_tax = estimated_tax * 1.04
    
    refund_or_payable = data.tdsPaid - estimated_tax
    
    prompt = f"""You are a tax expert. Analyze and provide personalized recommendations in JSON format.

Income Details:
- Salary: ₹{data.salary}
- Interest: ₹{data.interest}
- Freelance: ₹{data.freelance}
- Rent: ₹{data.rent}
- Capital Gains: ₹{data.capitalGains}
Total Income: ₹{total_income}

Deductions Applied:
- 80C: ₹{data.section80C}
- 80D: ₹{data.section80D}
- 80E: ₹{data.section80E}
- 80G: ₹{data.section80G}
Total Deductions: ₹{total_deductions}

Taxable Income: ₹{taxable_income}
Estimated Tax: ₹{estimated_tax:.0f}
TDS Paid: ₹{data.tdsPaid}
Refund/Payable: ₹{refund_or_payable:.0f}

Provide JSON with: regime (New or Old), itrForm, estimatedTax, recommendations (4-5 specific actionable tips based on their income), refundOrPayable.

Be specific to their situation. Example: "You have freelance income of ₹{data.freelance} - consider filing quarterly estimated tax to avoid penalties."

Return ONLY valid JSON."""

    response = analyze_tax(prompt)
    
    try:
        ai_data = json.loads(response)
    except Exception as e:
        ai_data = {
            "regime": "New",
            "itrForm": "ITR-1",
            "estimatedTax": int(estimated_tax),
            "recommendations": [
                f"Your taxable income is ₹{taxable_income:,.0f}. File ITR-1 form.",
                f"You have tax liability of ₹{estimated_tax:,.0f}.",
                f"TDS paid: ₹{data.tdsPaid:,.0f}.",
                f"Increase 80C deductions (currently ₹{data.section80C:,.0f}) to reduce tax."
            ],
            "refundOrPayable": int(refund_or_payable)
        }
    
    return {
        "totalIncome": total_income,
        "taxableIncome": taxable_income,
        "estimatedTax": int(ai_data.get("estimatedTax", estimated_tax)),
        "regime": ai_data.get("regime", "New"),
        "recommendations": ai_data.get("recommendations", []),
        "itrForm": ai_data.get("itrForm", "ITR-1"),
        "refundOrPayable": int(ai_data.get("refundOrPayable", refund_or_payable))
    }