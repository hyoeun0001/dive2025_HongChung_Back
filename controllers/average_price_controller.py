from schemas.average_price_schema import RateRequest
from services.average_price_service import calculate_average_price

def fetch_average_price(data: RateRequest):
    result = calculate_average_price(
        city=data.city,
        district=data.district,
        type_=data.type,
        price=data.price
    )
    if not result:
        return {"error": "해당 조건에 맞는 데이터가 없습니다."}
    return result