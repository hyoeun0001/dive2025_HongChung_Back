# controllers/audio_controller.py
from fastapi import HTTPException, UploadFile
from services.audio_service import stt_from_webm_ser
from services.intent_service import route_intent

async def stt_and_route_con(file: UploadFile, use_flac: bool = False):
    try:
        stt_result = await stt_from_webm_ser(file, use_flac)
        text = stt_result.get("text", "")
        if not text:
            return {"error": "음성에서 텍스트를 추출하지 못했습니다."}
        intent_result = route_intent(text)
        return {
            "stt": stt_result,
            "intent": intent_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류: {str(e)}")