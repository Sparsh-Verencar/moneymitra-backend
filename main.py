from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, tax

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

@app.get("/")
def read_root():
    return {"message": "Hello World"}