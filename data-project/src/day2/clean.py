"""
프로그램명: Pandas vs Polars Parquet 데이터 전처리 및 성능 비교 파이프라인
작성자: 1조
작성일: 2026-08-07
프로그램 설명: 
  - 뉴욕 택시 데이터(Parquet)를 다운로드하여 Pandas와 Polars로 각각 로딩합니다.
  - 기본 EDA(데이터 확인, 결측치 조회)를 수행하고 결측치 및 중복 데이터를 제거합니다.
  - 두 라이브러리의 정제 결과를 검증 및 비교한 뒤, 최종 데이터를 Parquet 파일로 저장합니다.
  - timeit을 통해 두 도구의 데이터 전처리(I/O + 정제) 성능을 공정하게 비교합니다.
"""

import sys
import timeit
import logging
import urllib.request
from pathlib import Path

import pandas as pd
import polars as pl

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 파일 경로 설정
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-05.parquet"
LOCAL_FILE = PROJECT_ROOT / "data" / "raw" / "yellow_tripdata_2026-05.parquet"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_tripdata.parquet"

# 가설 기반 정제 임계값
MAX_PASSENGER_COUNT = 8
MAX_TRIP_DURATION_SEC = 12 * 60 * 60  # 12시간
OUTLIER_QUANTILE = 0.999
OUTLIER_IQR_MULTIPLIER = 1.5
USE_IQR_OUTLIER_RULE = False  # True로 변경하면 이상치 판정 기준을 IQR로 변경


# 0) 데이터 다운로드 (공정한 성능 평가를 위한 로컬 캐싱)
# --------------------------------------------------------------------
def download_data():
    LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOCAL_FILE.exists():
        print("Parquet 파일을 다운로드합니다.")
        try:
            urllib.request.urlretrieve(SOURCE_URL, LOCAL_FILE)
            logger.info("다운로드 완료.")
        except (OSError, urllib.error.URLError) as e:
            logger.error(f"❌ 다운로드 중 오류 발생: {e}")
            sys.exit(1)
# --------------------------------------------------------------------

# 가설 기반 비정상 레코드 제거
def _clean_with_hypothesis_rules_pandas(df, verbose=True, use_iqr=USE_IQR_OUTLIER_RULE):
    total_before = len(df)
    clean = df.copy()

    required_numeric_cols = ["trip_distance", "fare_amount", "total_amount"]
    required_cols = required_numeric_cols + [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "PULocationID",
        "DOLocationID",
    ]

    # 핵심 분석 컬럼만 기준으로 결측 제거
    clean = clean.dropna(subset=required_cols)

    # 이상치/무효 규칙
    mask = pd.Series(True, index=clean.index)

    # 1) 이동거리, 요금: 0 이하 제거 + 극단치 제거
    for col in ["trip_distance", "fare_amount", "total_amount"]:
        mask &= clean[col] > 0
        if len(clean) == 0:
            continue

        if use_iqr:
            q1 = clean[col].quantile(0.25)
            q3 = clean[col].quantile(0.75)
            iqr = q3 - q1
            if pd.notna(iqr) and iqr > 0:
                lower = q1 - OUTLIER_IQR_MULTIPLIER * iqr
                upper = q3 + OUTLIER_IQR_MULTIPLIER * iqr
                mask &= clean[col].between(lower, upper)
        else:
            q = clean[col].quantile(OUTLIER_QUANTILE)
            if pd.notna(q):
                mask &= clean[col] <= q

    # 2) 승객 수/지역 ID 유효성
    mask &= clean["passenger_count"].between(1, MAX_PASSENGER_COUNT)
    mask &= clean["PULocationID"].between(1, 265)
    mask &= clean["DOLocationID"].between(1, 265)

    # 3) 시각 순서 및 여행시간 상한(물리적으로 불가능한 기록 제거)
    pickup_ts = pd.to_datetime(clean["tpep_pickup_datetime"], errors="coerce")
    dropoff_ts = pd.to_datetime(clean["tpep_dropoff_datetime"], errors="coerce")
    trip_seconds = (dropoff_ts - pickup_ts).dt.total_seconds()
    mask &= pickup_ts.notna() & dropoff_ts.notna()
    mask &= trip_seconds.between(1, MAX_TRIP_DURATION_SEC)

    clean = clean.loc[mask]

    removed = total_before - len(clean)
    removed_ratio = (removed / total_before * 100) if total_before else 0.0
    if verbose:
        print(
            f"[Pandas 가설 정제] 원본: {total_before}행 -> 정제 후: {len(clean)}행 "
            f"| 제거: {removed}행 ({removed_ratio:.2f}%)"
        )
    return clean


# 가설 기반 비정상 레코드 제거 Polars 버전
def _clean_with_hypothesis_rules_polars(df, verbose=True, use_iqr=USE_IQR_OUTLIER_RULE):
    total_before = df.height
    clean = df

    required_cols = [
        "trip_distance",
        "fare_amount",
        "total_amount",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "PULocationID",
        "DOLocationID",
    ]

    clean = clean.drop_nulls(subset=required_cols)

    exprs = []
    for col in ["trip_distance", "fare_amount", "total_amount"]:
        exprs.append(pl.col(col) > 0)
        if clean.height > 0:
            if use_iqr:
                q1 = clean.select(pl.col(col).quantile(0.25, interpolation="linear")).to_series()[0]
                q3 = clean.select(pl.col(col).quantile(0.75, interpolation="linear")).to_series()[0]
                iqr = q3 - q1
                if q1 is not None and q3 is not None and iqr is not None and iqr > 0:
                    lower = q1 - OUTLIER_IQR_MULTIPLIER * iqr
                    upper = q3 + OUTLIER_IQR_MULTIPLIER * iqr
                    exprs.append(pl.col(col).is_between(lower, upper))
            else:
                q = clean.select(
                    pl.col(col).quantile(OUTLIER_QUANTILE, interpolation="linear")
                ).to_series()[0]
                if q is not None and q > 0:
                    exprs.append(pl.col(col) <= q)

    exprs.extend(
        [
            pl.col("passenger_count").is_between(1, MAX_PASSENGER_COUNT),
            pl.col("PULocationID").is_between(1, 265),
            pl.col("DOLocationID").is_between(1, 265),
        ]
    )

    exprs.append(pl.col("tpep_dropoff_datetime") >= pl.col("tpep_pickup_datetime"))
    clean = clean.with_columns(
        (pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime"))
        .dt.total_seconds()
        .alias("__trip_seconds")
    )
    exprs.append(pl.col("__trip_seconds").is_between(1, float(MAX_TRIP_DURATION_SEC)))

    clean = clean.filter(pl.all_horizontal(exprs)).drop("__trip_seconds")

    removed = total_before - clean.height
    removed_ratio = (removed / total_before * 100) if total_before else 0.0
    if verbose:
        print(
            f"[Polars 가설 정제] 원본: {total_before}행 -> 정제 후: {clean.height}행 "
            f"| 제거: {removed}행 ({removed_ratio:.2f}%)"
        )
    return clean


# 1) Pandas: 로딩, EDA, 결측치, 중복 처리
# --------------------------------------------------------------------
def process_pandas(file_path):
    print("\n--- 1. Pandas 로딩 및 전처리 ---")
    try:
        # 데이터 로딩
        df = pd.read_parquet(file_path)
        before_cnt = len(df)
        
        # 기본 EDA
        print("[Pandas Info]")
        df.info(memory_usage='deep')
        print("\n[Pandas 결측치 확인]")
        print(df.isnull().sum().head()) # 컬럼이 많아 상위 5개만 출력
        
        # 결측치 및 중복 데이터 제거
        df_clean = _clean_with_hypothesis_rules_pandas(df, verbose=True).drop_duplicates()
        after_cnt = len(df_clean)
        
        print(f"\n[Pandas 정제 결과] 제거 전: {before_cnt}행 -> 제거 후: {after_cnt}행")
        return df_clean
    
    except (OSError, ImportError, ValueError, KeyError, TypeError) as e:
        logger.error(f"❌ Pandas 처리 중 오류 발생: {e}")
        return None
# --------------------------------------------------------------------


# 2) Polars: 로딩, EDA, 결측치·중복 처리
# --------------------------------------------------------------------
def process_polars(file_path):
    print("\n--- 2. Polars 로딩 및 전처리 ---")
    try:
        # 데이터 로딩 (Lazy Execution을 적용하기 위해 scan_parquet 사용 후 collect)
        df = pl.scan_parquet(file_path).collect()
        before_cnt = df.height
        
        # 기본 EDA
        print("[Polars Schema]")
        print(df.schema)
        print("\n[Polars 결측치 확인]")
        print(df.null_count().select(df.columns[:5]))
        
        # 결측치 및 중복 데이터 제거
        df_clean = _clean_with_hypothesis_rules_polars(df, verbose=True).unique()
        after_cnt = df_clean.height
        
        print(f"\n[Polars 정제 결과] 제거 전: {before_cnt}행 -> 제거 후: {after_cnt}행")
        return df_clean
    
    except (OSError, ValueError, KeyError, TypeError, pl.exceptions.PolarsError) as e:
        logger.error(f"❌ Polars 처리 중 오류 발생: {e}")
        return None
# --------------------------------------------------------------------


# 3) 결과 비교 및 Parquet 파일 저장
# --------------------------------------------------------------------
def compare_and_save(pd_df, pl_df, output_path):
    print("\n--- 3. 처리 결과 비교 및 저장 ---")
    
    pd_rows = len(pd_df)
    pl_rows = pl_df.height
    
    print(f"Pandas 최종 행 수 : {pd_rows:,}")
    print(f"Polars 최종 행 수 : {pl_rows:,}")
    
    if pd_rows == pl_rows:
        print("✅ 양쪽 라이브러리의 정제 결과(행 수)가 일치합니다.")
    else:
        print("⚠️ 주의: 두 라이브러리의 처리 결과가 다릅니다.")

    # 저장 (여기서는 Polars의 DataFrame을 기준으로 저장)
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pl_df.write_parquet(output_path)
        print(f"💾 정제된 데이터를 저장했습니다: {output_path}")
    except (OSError, ValueError, pl.exceptions.PolarsError) as e:
        logger.error(f"❌ 파일 저장 중 오류 발생: {e}")
# --------------------------------------------------------------------


# 4) timeit 사용 세 도구 성능 비교
# --------------------------------------------------------------------
def run_performance_test(file_path, iters=5, return_metrics=False):
    print(f"\n--- 4. Pandas vs Polars 성능 비교 측정 시작 (반복 횟수: {iters}회) ---")
    
    def time_pandas():
        # 로딩 -> 가설 기반 정제 -> 중복 제거
        _clean_with_hypothesis_rules_pandas(pd.read_parquet(file_path), verbose=False).drop_duplicates()

    def time_polars_eager():
        # Eager 방식
        _clean_with_hypothesis_rules_polars(pl.read_parquet(file_path), verbose=False).unique()

    def time_polars_lazy():
        # Lazy 방식 (실행 계획 최적화 후 동작)
        _clean_with_hypothesis_rules_polars(pl.scan_parquet(file_path).collect(), verbose=False).unique()

    try:
        pd_time = timeit.timeit(time_pandas, number=iters)
        pl_eager_time = timeit.timeit(time_polars_eager, number=iters)
        pl_lazy_time = timeit.timeit(time_polars_lazy, number=iters)

        print(f"🐼 Pandas 실행 시간        : {pd_time:.4f}초")
        print(f"🐻‍❄️ Polars (Eager) 실행 시간 : {pl_eager_time:.4f}초")
        print(f"🐻‍❄️ Polars (Lazy) 실행 시간  : {pl_lazy_time:.4f}초")

        if return_metrics:
            return {
                "pandas_time_sec": pd_time,
                "polars_eager_time_sec": pl_eager_time,
                "polars_lazy_time_sec": pl_lazy_time,
            }
        
    except (
        OSError,
        ImportError,
        ValueError,
        KeyError,
        TypeError,
        pl.exceptions.PolarsError,
    ) as e:
        logger.error(f"❌ 성능 측정 중 오류 발생: {e}")
        if return_metrics:
            return None
# --------------------------------------------------------------------


# 5) 메인 실행
# --------------------------------------------------------------------
if __name__ == "__main__":
    download_data()
    
    pd_cleaned = process_pandas(LOCAL_FILE)
    pl_cleaned = process_polars(LOCAL_FILE)
    
    if pd_cleaned is not None and pl_cleaned is not None:
        compare_and_save(pd_cleaned, pl_cleaned, OUTPUT_FILE)
        run_performance_test(LOCAL_FILE, iters=3)
