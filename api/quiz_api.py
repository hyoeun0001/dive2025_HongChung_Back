from fastapi import APIRouter, Query
from controllers.quiz_controller import fetch_quiz

router = APIRouter()

@router.get("/quiz")
def get_quiz(state: str = Query(..., description="퀴즈 상태 (계약전, 계약중, 계약후)")):
    result = fetch_quiz(state)
    return result