from fastapi import APIRouter
from schemas.risk_prediction_schema import RiskRequest
from controllers.better_risk_controller import fetch_better_risk

router = APIRouter()

@router.post("/better-risk")
def get_better_risk(data: RiskRequest):
    return fetch_better_risk(data)