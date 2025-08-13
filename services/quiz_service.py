import random
from data.quiz_data import quiz

def get_random_quiz_by_state(state: str):
    filtered = [q for q in quiz if q["state"] == state]
    if not filtered:
        return None
    return random.sample(filtered, min(10, len(filtered)))