from pydantic import BaseModel

class RateRequest(BaseModel):
    city: str
    district: str
    type: str
    price: float