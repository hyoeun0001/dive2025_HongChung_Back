from fastapi import APIRouter, UploadFile, File
from controllers.audio_controller import stt_and_route_con

router = APIRouter(prefix="/audio", tags=["audio"])

@router.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...), use_flac: bool = False):
    return await stt_and_route_con(file, use_flac)