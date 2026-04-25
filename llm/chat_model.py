from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from system_prompt import SYSTEM_PROMPT

load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

def chat_with_context(user_input: str, user_profile: dict) -> str:
    # Build system prompt with user context
    system_with_context = SYSTEM_PROMPT.format(
        life_stage=user_profile.get('lifeStage', 'unknown'),
        monthly_income=user_profile.get('monthlyIncome', 0),
        total_expenses=sum(user_profile.get('expenses', {}).values()),
        approx_savings=user_profile.get('approxSavings', 0),
        investments=', '.join(user_profile.get('investments', [])),
        health_insurance=user_profile.get('healthInsurance', 'unknown'),
        life_insurance=user_profile.get('lifeInsurance', 'unknown'),
        files_tax=user_profile.get('filesTax', 'unknown')
    )
    
    messages = [SystemMessage(content=system_with_context)]
    messages.append(HumanMessage(content=user_input))
    
    response = model.invoke(messages)
    messages.append(AIMessage(content=response.content))
    
    return response.content

def chat(user_input: str) -> str:
    # Fallback without profile
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.append(HumanMessage(content=user_input))
    response = model.invoke(messages)
    messages.append(AIMessage(content=response.content))
    return response.content

def main():
    print("=== Financial Planning Assistant ===\n")
    
    # Example profile
    user_profile = {
        'lifeStage': 'working',
        'monthlyIncome': 50000,
        'expenses': {'rent': 15000, 'food': 8000, 'utilities': 2000, 'internet': 500, 'transport': 3000, 'homeLoan': 0},
        'approxSavings': 10000,
        'investments': ['SIP', 'FD'],
        'healthInsurance': True,
        'lifeInsurance': False,
        'filesTax': True
    }
    
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        response = chat_with_context(user_input, user_profile)
        print(f"\nAI: {response}\n")

if __name__ == "__main__":
    main()