from services.intent_service import route_intent
from fastapi import HTTPException

def fetch_text_search(text: str):
    try:
        intent_result = route_intent(text)
        return {
            "text": text,
            "intent": intent_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {str(e)}")