from fastapi import APIRouter
from pydantic import BaseModel
from llm.chat_model import chat_with_context

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    user_profile: dict

@router.post("/message")
async def send_message(request: ChatRequest):
    try:
        response = chat_with_context(request.message, request.user_profile)
        return {
            "user_id": request.user_id,
            "message": request.message,
            "response": response
        }
    except Exception as e:
        return {
            "error": str(e),
            "response": "I'm here to help with your personal finance in India. Could you rephrase your question?"
        }

@router.get("/{user_id}")
async def get_user_chat(user_id: str):
    return {"user_id": user_id, "status": "ready"}