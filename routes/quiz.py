from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from llm.quiz_model import generate_quiz

router = APIRouter()

class Concept(BaseModel):
    title: str
    content: str
    keyPoints: List[str] = []

class QuizRequest(BaseModel):
    topic: str
    subtopic: str
    concepts: List[Concept]
    num_questions: int = 6

@router.post("/generate")
async def generate_quiz_route(request: QuizRequest):
    try:
        questions = generate_quiz(
            topic=request.topic,
            subtopic=request.subtopic,
            concepts=[c.model_dump() for c in request.concepts],
            num_questions=request.num_questions
        )
        return { "questions": questions }
    except Exception as e:
        return { "error": str(e), "questions": [] }