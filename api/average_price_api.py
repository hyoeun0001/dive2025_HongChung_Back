from fastapi import APIRouter, Query
from schemas.average_price_schema import RateRequest
from controllers.average_price_controller import fetch_average_price

router = APIRouter()

@router.post("/calculate-price")
def get_average_price(data: RateRequest):
    return fetch_average_price(data)