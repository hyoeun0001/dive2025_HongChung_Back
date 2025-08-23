from fastapi import APIRouter, Body
from controllers.text_search_controller import fetch_text_search

router = APIRouter()

@router.post("/text-search")
def get_text_search(data: dict = Body(...)):
    text = data.get("text", "")
    return fetch_text_search(text)