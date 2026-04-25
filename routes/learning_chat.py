from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from llm.learning_chat_model import chat_with_learning_context

router = APIRouter()

class Message(BaseModel):
    role: str      # "user" | "assistant"
    content: str

class Concept(BaseModel):
    title: str
    content: str
    keyPoints: List[str] = []

class LearningChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    topic: str
    subtopic: str
    concepts: List[Concept]

@router.post("/message")
async def learning_chat(request: LearningChatRequest):
    try:
        reply = chat_with_learning_context(
            message=request.message,
            history=[m.model_dump() for m in request.history],
            topic=request.topic,
            subtopic=request.subtopic,
            concepts=[c.model_dump() for c in request.concepts],
        )
        return { "reply": reply }
    except Exception as e:
        return {
            "error": str(e),
            "reply": "Sorry, something went wrong. Please try again."
        }