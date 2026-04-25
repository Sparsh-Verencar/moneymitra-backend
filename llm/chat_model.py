from dotenv import load_dotenv
import os
from langchain.chat_models import init_chat_model
from system_prompt import financial_prompt
load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

user_profile = {
    "first_name": "Rahul",
    "age": 28,
    "caste_category": "General",
    "employment_type": "Salaried",
    "income_range": "30,000-50,000",
    "dependents": 2,
    "state": "Maharashtra"
}

chain = financial_prompt | model

response = chain.invoke({
    "first_name": user_profile["first_name"],
    "age": user_profile["age"],
    "caste_category": user_profile["caste_category"],
    "employment_type": user_profile["employment_type"],
    "income_range": user_profile["income_range"],
    "dependents": user_profile["dependents"],
    "state": user_profile["state"],
    "user_query": "What's the best way to save for retirement?"
})

print("RESPONSE:", response.content)