from fastapi import APIRouter

chat_router = APIRouter()

@chat_router.get("/")
def get_users():
    return {"message": "All users"}

@chat_router.get("/{chat_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
