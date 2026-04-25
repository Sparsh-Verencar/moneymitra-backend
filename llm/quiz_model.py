from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
import json

load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

QUIZ_SYSTEM_PROMPT = """You are a financial education expert for India. Generate MCQ quizzes based on the learning material provided. Return ONLY valid JSON, no markdown, no backticks."""

def generate_quiz(topic: str, subtopic: str, concepts: list, num_questions: int) -> list:
    context = "\n\n".join([
        f"Concept: {c['title']}\nContent: {c['content']}\nKey Points: {', '.join(c.get('keyPoints', []))}"
        for c in concepts
    ])

    prompt = f"""Based on this learning material on "{subtopic}" under "{topic}":

{context}

Generate {num_questions} MCQs to test understanding. Return ONLY this JSON format:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct": "A",
      "explanation": "..."
    }}
  ]
}}"""

    response = model.invoke([
        SystemMessage(content=QUIZ_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])

    try:
        clean = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean)
        return data.get("questions", [])
    except:
        return []