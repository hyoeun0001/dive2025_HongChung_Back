from fastapi import FastAPI
from api.quiz_api import router as quiz_router
from api.average_price_api import router as average_price_router
from api.risk_prediction_api import router as risk_prediction_router

app = FastAPI()

app.include_router(quiz_router)
app.include_router(average_price_router)
app.include_router(risk_prediction_router)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}