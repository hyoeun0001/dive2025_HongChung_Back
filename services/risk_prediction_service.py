from fastapi import FastAPI, HTTPException
from catboost import CatBoostClassifier
from pathlib import Path
import numpy as np
import pandas as pd
import math
from utils.util import get_jeonse_rate, get_unsold_value, get_base_rate, map_housing_type, calculate_guarantee_period

# 모델 로드
MODEL_PATH = Path(__file__).parent.parent / "models" / "catboost_0819.cbm"
model = CatBoostClassifier()
model.load_model(MODEL_PATH)

# 데이터 로드 (전세가율 xlsx)
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

# 데이터 로드 (미분양현황 xlsx)
UNSOLD_PATH = Path(__file__).parent.parent / "data" / "dataset_unsold.xlsx"
try:
    unsold_df = pd.read_excel(UNSOLD_PATH, engine="openpyxl", header=0)  # 첫 줄이 header
except FileNotFoundError:
    raise RuntimeError(f"지역별 미판매 데이터 파일을 찾을 수 없습니다: {UNSOLD_PATH}")

# 데이터 로드 (기준금리 xlsx)
BASE_RATE_PATH = Path(__file__).parent.parent / "data" / "dataset_base_interest_rate.xlsx"
try:
    base_rate_df = pd.read_excel(BASE_RATE_PATH, engine="openpyxl", header=0)
except FileNotFoundError:
    raise RuntimeError(f"기준금리 파일을 찾을 수 없습니다: {BASE_RATE_PATH}")

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
    jeonseRateStartMonth = get_jeonse_rate(jeonse_df, region, houseType, guaranteeStartMonth)
    if jeonseRateStartMonth is None:
        raise HTTPException(status_code=400, detail="전세가율 데이터를 찾을 수 없습니다.")
    
    unsoldValue = get_unsold_value(unsold_df, region, guaranteeStartMonth)
    if unsoldValue is None:
        raise HTTPException(status_code=400, detail="지역별 미판매 데이터를 찾을 수 없습니다.")
    
    baseRate = get_base_rate(base_rate_df, guaranteeStartMonth)

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
        baseRate,
        unsoldValue,
        loanAmount,
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

    return {"prediction": float(prediction[0]), "probability": round(float(probability[0]), 2)}
        