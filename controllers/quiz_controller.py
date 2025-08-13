from services.quiz_service import get_random_quiz_by_state

def fetch_quiz(state: str):
    quiz_items = get_random_quiz_by_state(state)
    if quiz_items is None:
        return {"error": "해당 state에 맞는 퀴즈가 없습니다."}
    return quiz_items