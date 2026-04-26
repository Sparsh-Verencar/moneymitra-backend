from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

LEARNING_CHAT_SYSTEM_PROMPT = """You are a financial education assistant for India. A user is currently studying a specific financial topic and has questions about it.

## YOUR SCOPE
You ONLY answer questions related to the topic and concepts provided below. If the user asks anything outside this material, politely redirect them:
"I'm here to help you understand {subtopic} under {topic}. Got a question about that?"

## LEARNING MATERIAL
Topic: {topic}
Subtopic: {subtopic}

Concepts covered:
{concepts_block}

## TONE
- Simple, clear language — no jargon without explanation.
- Encouraging and patient.
- Use Indian examples (₹, Indian banks, SEBI, RBI, etc.) where relevant.
- Keep answers concise but complete. If a concept needs depth, break it into steps.
- Never answer questions outside the material above.
"""

def chat_with_learning_context(
    message: str,
    history: list,
    topic: str,
    subtopic: str,
    concepts: list,
) -> str:
    # Build concepts block
    concepts_block = "\n\n".join([
        f"### {c['title']}\n{c['content']}\nKey Points: {', '.join(c.get('keyPoints', []))}"
        for c in concepts
    ])

    system_prompt = LEARNING_CHAT_SYSTEM_PROMPT.format(
        topic=topic,
        subtopic=subtopic,
        concepts_block=concepts_block,
    )

    messages = [SystemMessage(content=system_prompt)]

    # Inject conversation history
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=message))

    response = model.invoke(messages)
    return response.content