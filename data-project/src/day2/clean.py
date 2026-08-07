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

import os
import sys
import timeit
import logging
import urllib.request
import pandas as pd
import polars as pl

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 파일 경로 설정
SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-05.parquet"
LOCAL_FILE = "yellow_tripdata_2026-05.parquet"
OUTPUT_FILE = "cleaned_tripdata.parquet"


# 0) 데이터 다운로드 (공정한 성능 평가를 위한 로컬 캐싱)
# --------------------------------------------------------------------
def download_data():
    if not os.path.exists(LOCAL_FILE):
        print(f"Parquet 파일을 다운로드합니다.")
        try:
            urllib.request.urlretrieve(SOURCE_URL, LOCAL_FILE)
            logger.info("다운로드 완료.")
        except Exception as e:
            logger.error(f"❌ 다운로드 중 오류 발생: {e}")
            sys.exit(1)
# --------------------------------------------------------------------


# 1) Pandas: 로딩, EDA, 결측치·중복 처리
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
        df_clean = df.dropna().drop_duplicates()
        after_cnt = len(df_clean)
        
        print(f"\n[Pandas 정제 결과] 제거 전: {before_cnt}행 -> 제거 후: {after_cnt}행")
        return df_clean
    
    except Exception as e:
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
        print(df.null_count().select(pl.all().head(5))) 
        
        # 결측치 및 중복 데이터 제거
        df_clean = df.drop_nulls().unique()
        after_cnt = df_clean.height
        
        print(f"\n[Polars 정제 결과] 제거 전: {before_cnt}행 -> 제거 후: {after_cnt}행")
        return df_clean
    
    except Exception as e:
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
        pl_df.write_parquet(output_path)
        print(f"💾 정제된 데이터를 저장했습니다: {output_path}")
    except Exception as e:
        logger.error(f"❌ 파일 저장 중 오류 발생: {e}")
# --------------------------------------------------------------------


# 4) timeit 사용 세 도구 성능 비교
# --------------------------------------------------------------------
def run_performance_test(file_path, iters=5):
    print(f"\n--- 4. Pandas vs Polars 성능 비교 측정 시작 (반복 횟수: {iters}회) ---")
    
    def time_pandas():
        # 로딩 -> 결측치 제거 -> 중복 제거 체이닝
        pd.read_parquet(file_path).dropna().drop_duplicates()

    def time_polars_eager():
        # Eager 방식
        pl.read_parquet(file_path).drop_nulls().unique()

    def time_polars_lazy():
        # Lazy 방식 (실행 계획 최적화 후 동작)
        pl.scan_parquet(file_path).drop_nulls().unique().collect()

    try:
        pd_time = timeit.timeit(time_pandas, number=iters)
        pl_eager_time = timeit.timeit(time_polars_eager, number=iters)
        pl_lazy_time = timeit.timeit(time_polars_lazy, number=iters)

        print(f"🐼 Pandas 실행 시간        : {pd_time:.4f}초")
        print(f"🐻‍❄️ Polars (Eager) 실행 시간 : {pl_eager_time:.4f}초")
        print(f"🐻‍❄️ Polars (Lazy) 실행 시간  : {pl_lazy_time:.4f}초")
        
    except Exception as e:
        logger.error(f"❌ 성능 측정 중 오류 발생: {e}")
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