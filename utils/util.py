from datetime import datetime
import pandas as pd
from fastapi import HTTPException

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

def get_jeonse_rate(jeonse_df: pd.DataFrame, region: str, house_type: str, start_month: str = None):
    house_type_mapped = map_housing_type(house_type)
    
    # start_month가 None이면 현재 달로 설정
    if start_month is None:
        start_month = get_current_month()
    else:
        start_month = str(start_month)
        if len(start_month) == 6:  # YYYYMM 형식
            start_month = f"{start_month[:4]}.{start_month[4:]}"
    
    # start_month가 DataFrame 열에 있는지 확인
    if start_month not in jeonse_df.columns:
        available_columns = [col for col in jeonse_df.columns if col not in ["지역별(1)", "주택유형별(1)"]]
        if not available_columns:
            raise ValueError("jeonse_df에 유효한 날짜 열이 없습니다")
        
        # start_month를 datetime으로 변환하여 비교
        try:
            target_date = datetime.strptime(start_month, "%Y.%m")
        except ValueError:
            raise ValueError(f"start_month의 날짜 형식이 잘못되었습니다: {start_month}")
        
        # 가장 가까운 달 찾기
        closest_month = None
        min_diff = float('inf')
        
        for col in available_columns:
            try:
                col_date = datetime.strptime(col, "%Y.%m")
                time_diff = abs((target_date - col_date).days)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_month = col
            except ValueError:
                continue  # 잘못된 날짜 형식의 열은 무시
        
        if closest_month is None:
            raise ValueError(f"{start_month}에 적합한 열을 찾을 수 없습니다")
        
        start_month = closest_month
    
    # 지역과 주택 유형에 맞는 행 조회
    row = jeonse_df[(jeonse_df["지역별(1)"] == region) & (jeonse_df["주택유형별(1)"] == house_type_mapped)]
    if row.empty:
        return None
    
    return row[start_month].values[0]

def get_unsold_value(unsold_df: pd.DataFrame, region: str, month):
    # int이면 str로 변환
    if isinstance(month, int):
        month = str(month)
        if len(month) == 6:  # YYYYMM -> YYYY.MM
            month = f"{month[:4]}.{month[4:]}"
    
    available_cols = [col for col in unsold_df.columns if col != "구분(1)"]

    # 요청한 월이 없으면 가장 가까운 컬럼 찾기
    if month not in available_cols:
        try:
            target_date = datetime.strptime(month, "%Y.%m")
        except ValueError:
            raise ValueError(f"month의 날짜 형식이 잘못되었습니다: {month}")
        
        closest_month = None
        min_diff = float('inf')
        
        for col in available_cols:
            try:
                col_date = datetime.strptime(col, "%Y.%m")
                time_diff = abs((target_date - col_date).days)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_month = col
            except ValueError:
                continue  # 잘못된 날짜 형식의 열은 무시
        
        if closest_month is None:
            raise ValueError(f"{month}에 적합한 열을 찾을 수 없습니다")
        
        month = closest_month

    row = unsold_df[unsold_df["구분(1)"] == region]
    if row.empty:
        return None
    return row[month].values[0]

def get_base_rate(base_rate_df: pd.DataFrame, month):
    # int이면 str로 변환
    if isinstance(month, int):
        month = str(month)
        if len(month) == 6:  # YYYYMM -> YYYY.MM
            month = f"{month[:4]}.{month[4:]}"
    
    # available_months를 str로 변환
    available_months = [str(m) for m in base_rate_df["yyyymm_str"].tolist()]
    
    if month not in available_months:
        try:
            target_date = datetime.strptime(month, "%Y.%m")
        except ValueError:
            raise ValueError(f"month의 날짜 형식이 잘못되었습니다: {month}")
        
        closest_month = None
        min_diff = float('inf')
        
        for col in available_months:
            try:
                col_date = datetime.strptime(col, "%Y.%m")
                time_diff = abs((target_date - col_date).days)
                if time_diff < min_diff:
                    min_diff = time_diff
                    closest_month = col
            except ValueError:
                continue  # 잘못된 날짜 형식은 무시
        
        if closest_month is None:
            raise ValueError(f"{month}에 적합한 기준금리 데이터를 찾을 수 없습니다")
        
        month = closest_month

    rate = base_rate_df.loc[base_rate_df["yyyymm_str"].astype(str) == month, "기준금리"].values[0]
    return rate