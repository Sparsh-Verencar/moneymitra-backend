from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from system_prompt import SYSTEM_PROMPT

load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

messages = [SystemMessage(content=SYSTEM_PROMPT)]

def chat(user_input: str) -> str:
    messages.append(HumanMessage(content=user_input))
    response = model.invoke(messages)
    messages.append(AIMessage(content=response.content))
    return response.content

def main():
    print("=== Financial Planning Assistant ===\n")
    
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        
        response = chat(user_input)
        print(f"\nAI: {response}\n")

if __name__ == "__main__":
    main()