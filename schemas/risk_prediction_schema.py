from pydantic import BaseModel

class RiskRequest(BaseModel):
    initialLTV: float        # 초기LTV
    housePrice: int          # 주택가액
    depositAmount: int       # 임대보증금액
    seniority: int           # 선순위
    region: str              # 시도
    houseType: str           # 주택구분
    guaranteeStartMonth: int # 보증시작월_dt (예: 202210)
    guaranteeEndMonth: int   # 보증완료월_dt (예: 202401)
