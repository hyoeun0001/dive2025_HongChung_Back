from data.rate_data import rate

def calculate_average_price(city: str, district: str, type_: str, price: float):
# 해당 조건에 맞는 rate 검색
    matched = next(
        (
            r for r in rate
            if r["city"] == city and r["type"] == type_ and (r["district"] == district or r["district"] is None)
        ),
        None
    )
    if not matched:
        return None
    
    average_price = price * matched["rate"] / 100
    return {
        "rate": matched["rate"],
        "averagePrice": int(average_price)
    }