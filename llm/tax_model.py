from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

TAX_SYSTEM_PROMPT = """You are a tax analysis expert for India. Analyze tax situations and provide recommendations in JSON format only. Be precise with calculations and recommendations."""

messages = [SystemMessage(content=TAX_SYSTEM_PROMPT)]

def analyze_tax(user_input: str) -> str:
    messages.append(HumanMessage(content=user_input))
    response = model.invoke(messages)
    messages.append(AIMessage(content=response.content))
    return response.content