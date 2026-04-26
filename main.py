from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, tax, quiz
from routes.learning_chat import router as learning_chat_router
from routes.budget_router import router as budget_router
from routes.section_router import router as section_router

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["Chats"])
app.include_router(tax.router, prefix="/analyze-tax", tags=["Tax"])
app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])
app.include_router(learning_chat_router, prefix="/learning/chat")
app.include_router(budget_router)
app.include_router(section_router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
