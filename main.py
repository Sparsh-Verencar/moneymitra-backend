from fastapi import FastAPI
from routes import chat


app = FastAPI()

app.include_router(chat.router, prefix="/chat", tags=["Chats"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}
