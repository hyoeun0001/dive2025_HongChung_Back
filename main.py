from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.quiz_api import router as quiz_router
from api.average_price_api import router as average_price_router
from api.risk_prediction_api import router as risk_prediction_router
from api.better_risk_api import router as better_risk_router
from api.audio_api import router as audio_router
from api.text_search_api import router as text_search_router

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:5173",  # Vite 개발 서버
    "http://127.0.0.1:5173", # 혹시 127.0.0.1로 접근할 때도 허용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True,
    allow_methods=["*"],    # 모든 HTTP 메소드 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

app.include_router(quiz_router)
app.include_router(average_price_router)
app.include_router(risk_prediction_router)
app.include_router(better_risk_router)
app.include_router(audio_router)
app.include_router(text_search_router)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}