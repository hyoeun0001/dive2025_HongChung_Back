from fastapi import APIRouter
from schemas.risk_prediction_schema import RiskRequest
from controllers.risk_prediction_controller import fetch_risk_prediction

router = APIRouter()

@router.post("/risk-prediction")
def get_risk_prediction(data: RiskRequest):
    return fetch_risk_prediction(data)