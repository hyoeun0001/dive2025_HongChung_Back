import os
import subprocess
from pathlib import Path
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
FFMPEG = os.getenv("FFMPEG_PATH")
if not FFMPEG:
    raise RuntimeError("FFMPEG_PATH 환경 변수가 설정되지 않았습니다.")

def run_ffmpeg(in_path: Path, out_path: Path, to_flac: bool = False):
    if to_flac:
        cmd = [FFMPEG, "-y", "-i", str(in_path), "-ac", "1", "-ar", "16000", "-c:a", "flac", str(out_path)]
    else:
        cmd = [FFMPEG, "-y", "-i", str(in_path), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out_path)]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise HTTPException(status_code=400, detail=f"ffmpeg 변환 실패: {p.stderr.decode(errors='ignore')[:400]}")
