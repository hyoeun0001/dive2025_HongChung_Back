from schemas.risk_prediction_schema import RiskRequest
from services.risk_prediction_service import predict_risk

def fetch_risk_prediction(data: RiskRequest):
    result = predict_risk(
        initialLTV = data.initialLTV,
        housePrice = data.housePrice,
        depositAmount = data.depositAmount,
        seniority = data.seniority,
        region = data.region,
        houseType = data.houseType,
        guaranteeStartMonth = data.guaranteeStartMonth,
        guaranteeEndMonth = data.guaranteeEndMonth
    )
    if not result:
        return {"error": "해당 조건에 맞는 데이터가 없습니다."}
    return result