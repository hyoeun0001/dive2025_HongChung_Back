# services/audio_service.py
import aiofiles
import tempfile
import shutil
from pathlib import Path
from fastapi import HTTPException, UploadFile
from utils.ffmpeg_util import run_ffmpeg
from google.cloud import speech

async def stt_from_webm_ser(file: UploadFile, use_flac: bool = False):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src_name = Path(file.filename or "audio.webm").name
        src = td / src_name
        async with aiofiles.open(src, "wb") as f:
            await f.write(await file.read())

        out = td / ("audio.flac" if use_flac else "audio.wav")
        try:
            run_ffmpeg(src, out, to_flac=use_flac)
        except HTTPException as e:
            raise

        async with aiofiles.open(out, "rb") as f:
            audio_bytes = await f.read()
        encoding = "FLAC" if use_flac else "LINEAR16"
        try:
            return google_stt_bytes(audio_bytes, encoding=encoding)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"STT 실패: {e}")

def google_stt_bytes(audio_bytes: bytes, encoding: str = "LINEAR16", rate: int = 16000, lang="ko-KR"):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=getattr(speech.RecognitionConfig.AudioEncoding, encoding),
        sample_rate_hertz=rate,
        language_code=lang,
        enable_automatic_punctuation=True,
        model="latest_short"
    )
    resp = client.recognize(config=config, audio=audio)
    if resp.results:
        text = " ".join(alt.transcript for r in resp.results for alt in r.alternatives[:1])
        confidence = resp.results[0].alternatives[0].confidence
    else:
        text, confidence = "", None
    return {"text": text, "confidence": confidence}