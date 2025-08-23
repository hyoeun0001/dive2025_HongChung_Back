from fastapi import APIRouter, Query
from controllers.text_search_controller import fetch_text_search

router = APIRouter()

@router.get("/text-search")
def get_text_search(text: str = Query(...)):
    return fetch_text_search(text)