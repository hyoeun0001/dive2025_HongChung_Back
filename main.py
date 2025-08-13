from fastapi import FastAPI
from api.quiz_api import router as quiz_router

app = FastAPI()

app.include_router(quiz_router)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}