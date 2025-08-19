from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from catboost import CatBoostClassifier
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import math

# 모델 로드
MODEL_PATH = Path(__file__).parent.parent / "models" / "catboost_0817.cbm"
model = CatBoostClassifier()
model.load_model(MODEL_PATH)

# 데이터 로드 (전세가율 CSV)
JEONSE_PATH = Path(__file__).parent.parent / "data" / "dataset_Jeonse_rate.xlsx"
try:
    jeonse_df = pd.read_excel(JEONSE_PATH, engine="openpyxl", header=1)  # header=1 추가: row2를 헤더로
    new_columns = []
    for col in jeonse_df.columns:
        if isinstance(col, (float, int)):
            year = math.floor(col)
            month_str = str(round((col - year) * 100))
            if len(month_str) == 1:
                month_str = '0' + month_str
            new_columns.append(f"{year:d}.{month_str}")
        else:
            new_columns.append(str(col))
    jeonse_df.columns = new_columns
except FileNotFoundError:
    raise RuntimeError(f"전세가율 데이터 파일을 찾을 수 없습니다: {JEONSE_PATH}")

# 유틸 함수들
def map_housing_type(x: str) -> str:
    x = str(x).strip()
    if x in ["아파트", "주상복합", "오피스텔"]:
        return "아파트"
    elif x in ["연립주택", "다세대주택", "다가구주택", "다중주택", "연립다세대"]:
        return "연립다세대"
    elif x == "단독주택":
        return "단독주택"
    else:
        return "종합"

def calculate_guarantee_period(start_month: int, end_month: int) -> int:
    start_dt = datetime.strptime(str(start_month), "%Y%m")
    end_dt = datetime.strptime(str(end_month), "%Y%m")
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    if months < 0:
        raise HTTPException(status_code=400, detail="보증 완료월이 시작월보다 빠릅니다.")
    return months

# 현재 날짜를 YYYY.MM 형식으로 반환
def get_current_month() -> str:
    current_date = datetime.now()
    return f"{current_date.year}.{current_date.month:02d}"

# 전세 비율 가져오기
def get_jeonse_rate(region: str, house_type: str, start_month: str = None):
    house_type_mapped = map_housing_type(house_type)
    if start_month is None:
        start_month = get_current_month()
    else:
        start_month = str(start_month)
        if len(start_month) == 6:  # YYYYMM
            start_month = f"{start_month[:4]}.{start_month[4:]}"
    
    if start_month not in jeonse_df.columns:
        available_columns = [col for col in jeonse_df.columns if col not in ["지역별(1)", "주택유형별(1)"]]
        available_columns.sort(reverse=True)
        for col in available_columns:
            if col < start_month:
                start_month = col
                break
        else:
            raise ValueError(f"No suitable column found for {start_month}")

    row = jeonse_df[(jeonse_df["지역별(1)"] == region) & (jeonse_df["주택유형별(1)"] == house_type_mapped)]
    if row.empty:
        return None
    return row[start_month].values[0]

def predict_risk(
    initialLTV,
    housePrice,
    depositAmount,
    seniority,
    region,
    houseType,
    guaranteeStartMonth,
    guaranteeEndMonth
):
    loanAmount = initialLTV * housePrice
    guaranteePeriodMonths = calculate_guarantee_period(guaranteeStartMonth, guaranteeEndMonth)
    jeonseRateStartMonth = get_jeonse_rate(region, houseType, guaranteeStartMonth)
    if jeonseRateStartMonth is None:
        raise HTTPException(status_code=400, detail="전세가율 데이터를 찾을 수 없습니다.")

    features = [
        initialLTV,
        housePrice,
        depositAmount,
        seniority,
        region,
        map_housing_type(houseType),
        guaranteeStartMonth,
        guaranteeEndMonth,
        guaranteePeriodMonths,
        jeonseRateStartMonth,
        loanAmount
    ]
    features_array = np.array([features], dtype=object)
    
    try:
        prediction = model.predict(features_array)
        probability = model.predict_proba(features_array)[:, 1]
        print(jeonse_df["지역별(1)"].unique())
        print(jeonse_df["주택유형별(1)"].unique())
        print(jeonse_df.columns.tolist())
        print(jeonseRateStartMonth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return {"prediction": float(prediction[0]), "probability": float(probability[0])}
        