from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_users():
    return {"message": "All users"}

@router.get("/{chat_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
