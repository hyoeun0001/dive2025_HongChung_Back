from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from catboost import CatBoostClassifier  # 또는 CatBoostRegressor
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from schemas.risk_prediction_schema import RiskRequest

MODEL_PATH = Path(__file__).parent.parent / "models" / "catboost_0817.cbm"

# 모델 한 번만 로드
model = CatBoostClassifier()
model.load_model(MODEL_PATH)

# 데이터 로드 (전세가율 CSV)
JEONSE_PATH = Path(__file__).parent.parent / "data" / "jeonse_rate.csv"
try:
    jeonse_df = pd.read_csv(JEONSE_PATH)
except FileNotFoundError:
    raise RuntimeError(f"전세가율 데이터 파일을 찾을 수 없습니다: {JEONSE_PATH}")

# 유틸 함수들
def map_housing_type(x: str) -> str:
    # """주택 유형 표준화"""
    x = str(x).strip()
    if x in ["아파트", "주상복합", "오피스텔"]:
        return "아파트"
    elif x in ["연립주택", "다세대주택", "다가구주택", "다중주택"]:
        return "연립다세대"
    elif x == "단독주택":
        return "단독주택"
    else:
        return "종합"


def calculate_guarantee_period(start_month: int, end_month: int) -> int:
    """보증기간 개월 수 계산"""
    start_dt = datetime.strptime(str(start_month), "%Y%m")
    end_dt = datetime.strptime(str(end_month), "%Y%m")
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    if months < 0:
        raise HTTPException(status_code=400, detail="보증 완료월이 시작월보다 빠릅니다.")
    return months


# 전세 비율 가져오기
def get_jeonse_rate(region: str, house_type: str):
    house_type_map = {
        "아파트": "아파트",
        "연립다세대": "연립다세대",
        "단독주택": "단독주택",
    }

    mapped_house_type = house_type_map.get(house_type, house_type)

    row = jeonse_df[
        (jeonse_df["지역별(1)"] == region)
        & (jeonse_df["주택유형별(1)"] == mapped_house_type)
    ]

    if row.empty:
        return None

    # 최신 월 데이터 (마지막 컬럼) 사용
    latest_col = jeonse_df.columns[-1]
    return row[latest_col].values[0]
    
def predict_risk(data: RiskRequest):
    houseType = map_housing_type(data.houseType)

    # 파생 변수 생성
    loanAmount = data.initialLTV * data.housePrice
    guaranteePeriodMonths = calculate_guarantee_period(
        data.guaranteeStartMonth, data.guaranteeEndMonth
    )
    jeonseRateStartMonth = get_jeonse_rate(data.region, houseType, data.guaranteeStartMonth)

    # 피처 순서 맞추기
    features = [
        data.initialLTV,         # 0
        data.housePrice,         # 1
        data.depositAmount,      # 2
        data.seniority,          # 3
        data.region,             # 4 (카테고리형)
        houseType,               # 5 (카테고리형)
        data.guaranteeStartMonth,# 6
        data.guaranteeEndMonth,  # 7
        guaranteePeriodMonths,   # 8
        jeonseRateStartMonth,    # 9
        loanAmount               # 10
    ]

    features_array = np.array([features], dtype=object)

    # 예측 수행
    try:
        prediction = model.predict(features_array)
        probability = model.predict_proba(features_array)[:, 1]  # 위험 확률 (1 클래스)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return {
        "prediction": float(prediction[0]),
        "probability": float(probability[0])
    }