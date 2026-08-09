"""
프로그램명: 뉴욕 택시 데이터 통계 분석 및 가설 검증 모듈
파일명: statistical_analyzer.py
작성자: 1조
작성일: 2026-08-07
프로그램 설명: 
  - 기술통계(평균, 표준편차, 분위수) 산출
  - 수치형 변수 간 상관계수 계산
  - scipy.stats.ttest_ind를 이용한 독립표본 t-test 수행 및 p-value 해석
  - 카이제곱 독립성 검정 및 대조실험 결과 집계
"""

import logging
from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

# 로그 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_tripdata.parquet"

ALPHA = 0.05
MIN_ZONE_VOLUME = 200
TOP_N_DISPUTE_ZONES = 10


def run_basic_statistics_and_ttest(df):
    """
    [필수 통계 분석] 기술통계, 상관계수 산출 및 t-test 수행
    """
    print("\n--- [1] 기본 통계 분석 (기술통계, 상관계수, t-test) ---")
    
    # 1. 수치형 변수 지정
    numeric_cols = ['trip_distance', 'fare_amount', 'tip_amount', 'total_amount']
    
    # 2. 기술통계 산출 (평균, 표준편차, 분위수)
    desc_stats = df[numeric_cols].describe()
    print("\n[기술통계 (평균, 표준편차, 분위수)]")
    print(desc_stats.round(2))
    
    # 3. 변수 간 상관계수 계산
    correlation = df[numeric_cols].corr()
    print("\n[수치형 변수 간 상관계수]")
    print(correlation.round(3))
    
    # 4. 독립표본 t-test (카드 결제 vs 현금 결제 승객의 '운행 거리' 차이)
    print("\n[독립표본 t-test: 카드 vs 현금 결제건의 이동 거리 차이]")
    card_dist = df[df['payment_type'] == 1]['trip_distance'].dropna()
    cash_dist = df[df['payment_type'] == 2]['trip_distance'].dropna()

    if card_dist.empty or cash_dist.empty:
        logger.error("표본이 비어 있어 t-test를 수행할 수 없습니다.")
        return {"desc_stats": desc_stats, "correlation": correlation, "t_stat": None, "p_val": None, "ttest_verdict": "검정 불가"}

    t_stat, p_val = ttest_ind(card_dist, cash_dist, equal_var=False)
    print(f"   - t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

    if p_val < ALPHA:
        print("해석: p-value < 0.05 이므로, 카드와 현금 결제 간 평균 이동 거리에 유의미한 차이가 있습니다. (귀무가설 기각)")
        ttest_verdict = "유의미한 차이 있음 (귀무가설 기각)"
    else:
        print("해석: p-value >= 0.05 이므로, 귀무가설을 기각할 근거가 부족합니다. (차이가 없다고 단정할 수는 없음)")
        ttest_verdict = "유의미한 차이를 발견하지 못함 (귀무가설 기각 실패)"
        
    return {
        "desc_stats": desc_stats,
        "correlation": correlation,
        "t_stat": t_stat,
        "p_val": p_val,
        "ttest_verdict": ttest_verdict
    }


def analyze_dispute_zones(df):
    """[가설 검증] 분쟁 다발 지역 카이제곱 독립성 검정"""
    print("\n--- [2] 분쟁 다발 지역 카이제곱 검정 ---")
    try:
        # PULocationID 기준으로 집계
        zone_stats = df.groupby("PULocationID").agg(
            total_count=("payment_type", "size"),
            dispute_count=("payment_type", lambda s: (s == 4).sum()),
        )
        zone_stats["dispute_rate"] = zone_stats["dispute_count"] / zone_stats["total_count"]
        zone_stats = zone_stats.loc[zone_stats["total_count"] >= MIN_ZONE_VOLUME]

        top_zones = zone_stats.sort_values("dispute_rate", ascending=False).head(TOP_N_DISPUTE_ZONES)

        eligible = df.loc[df["payment_type"].isin([1, 2])].copy()
        eligible["is_top_dispute_zone"] = eligible["PULocationID"].isin(top_zones.index)
        eligible["결제수단"] = eligible["payment_type"].map({1: "카드", 2: "현금"})

        contingency = pd.crosstab(eligible["is_top_dispute_zone"], eligible["결제수단"])
        chi2, p_value, _dof, _ = chi2_contingency(contingency)
        is_significant = p_value < ALPHA

        print(f"   - chi2: {chi2:.4f}, p-value: {p_value:.6f}")
        return {
            "top_zones": top_zones,
            "chi2": chi2,
            "p_value": p_value,
            "significant": is_significant,
        }
    except KeyError as e:
        logger.error(f"필요한 컬럼이 데이터에 없습니다: {e}")
        return None

if __name__ == "__main__":
    # 데이터 경로
    DATA_PATH = DEFAULT_DATA_PATH

    # 데이터 로드
    df = pd.read_parquet(DATA_PATH)

    # [1] 기본 통계 + t-test
    basic_result = run_basic_statistics_and_ttest(df)

    # [2] 분쟁 지역 가설 검증
    dispute_result = analyze_dispute_zones(df)

    # 결과 요약 출력
    print("✅ 기본 통계/ttest 완료:", basic_result["ttest_verdict"])
    if dispute_result is not None:
        print(f"✅ 카이제곱 검정 p-value: {dispute_result['p_value']:.6f}")
