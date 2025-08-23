from fastapi import FastAPI, HTTPException
from catboost import CatBoostClassifier
from pathlib import Path
import pandas as pd
import math
from catboost import Pool
import itertools
from utils.util import get_jeonse_rate, get_unsold_value, get_base_rate, map_housing_type, calculate_guarantee_period

# 모델 로드
MODEL_PATH = Path(__file__).parent.parent / "models" / "catboost_0822.cbm"
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

def better_risk(
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

    # ⚡ feature_order에 맞게 데이터 구성
    features_dict = {
        "초기LTV": initialLTV,
        "주택가액": housePrice,
        "임대보증금액": depositAmount,
        "선순위": seniority,
        "시도": region,  # 범주형
        "주택구분": map_housing_type(houseType),  # 범주형
        "보증기간_개월": guaranteePeriodMonths,
        "보증시작월_전세가율": jeonseRateStartMonth,
        "기준금리": baseRate,
        "미분양주택수": unsoldValue,
        "보증시작월_dt_연": int(str(guaranteeStartMonth)[:4]),
        "보증시작월_dt_월": int(str(guaranteeStartMonth)[4:]),
        "보증완료월_dt_연": int(str(guaranteeEndMonth)[:4]),
        "보증완료월_dt_월": int(str(guaranteeEndMonth)[4:]),
        "대출액": loanAmount,
    }

    # DataFrame으로 변환 (순서 보장)
    feature_order = [
        "초기LTV", "주택가액", "임대보증금액", "선순위",
        "시도", "주택구분", "보증기간_개월", "보증시작월_전세가율",
        "기준금리", "미분양주택수", "보증시작월_dt_연", "보증시작월_dt_월",
        "보증완료월_dt_연", "보증완료월_dt_월", "대출액"
    ]
    features_df = pd.DataFrame([[features_dict[col] for col in feature_order]], columns=feature_order)

    # Pool 객체 생성 (categorical_features 지정)
    categorical_features = ["시도", "주택구분"]
    pool = Pool(features_df, cat_features=categorical_features)

    try:
        prediction = model.predict(pool)
        probability = model.predict_proba(pool)[:, 1] * 100
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    
    if prediction == 1.0:
        adjustments = [0.8, 0.9, 1.0, 1.1, 1.2]  # 탐색 범위 확장
        combinations = list(itertools.product(adjustments, repeat=3))
        rows = []
        for hp_factor, deposit_factor, seniority_factor in combinations:
            new_housePrice = housePrice * hp_factor
            new_depositAmount = depositAmount * deposit_factor
            new_seniority = seniority * seniority_factor

            if new_housePrice == 0:
                continue  # division by zero 방지
            new_initialLTV = (new_seniority + new_depositAmount) / new_housePrice
            new_loanAmount = new_initialLTV * new_housePrice

            new_features = features_dict.copy()
            new_features.update({
                "주택가액": new_housePrice,
                "임대보증금액": new_depositAmount,
                "선순위": new_seniority,
                "초기LTV": new_initialLTV,
                "대출액": new_loanAmount
            })
            rows.append([new_features[col] for col in feature_order])

        new_df = pd.DataFrame(rows, columns=feature_order)
        new_pool = Pool(new_df, cat_features=categorical_features)

        # 27개 케이스 확률 한 번에 계산
        probs = model.predict_proba(new_pool)[:, 1] * 100

        # 최소 확률 찾기
        best_idx = probs.argmin()
        best_prob = probs[best_idx]

        best_result = {
            "주택가액": {
                "isUseful": round(new_df.iloc[best_idx]["주택가액"]) - housePrice != 0,
                "result": (round(new_df.iloc[best_idx]["주택가액"]) - housePrice) / housePrice * 100
            },
            "임대보증금액": {
                "isUseful": round(new_df.iloc[best_idx]["임대보증금액"]) - depositAmount != 0,
                "result": (round(new_df.iloc[best_idx]["임대보증금액"]) - depositAmount) / depositAmount * 100
            },
            "선순위": {
                "isUseful": round(new_df.iloc[best_idx]["선순위"]) - seniority != 0,
                "result": (round(new_df.iloc[best_idx]["선순위"]) - seniority) / seniority * 100
            },
            "probability": round(float(best_prob), 2) *100,
            "isFound": False if best_prob >= probability else True
        }

        return {
            "prediction": float(prediction[0]),
            "probability": round(float(probability[0]), 2),
            "recommendation": best_result
        }
    else:
        return {
            "prediction": float(prediction[0]),
            "probability": round(float(probability[0]), 2)
        }