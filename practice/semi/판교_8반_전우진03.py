"""
프로그램명: Pandas EDA · Polars Lazy · DuckDB SQL 성능 비교 파이프라인
작성자: 전우진 P267
작성일: 2026-08-07
프로그램 설명: 
  - 본 파일은 대용량 데이터(sales_100k.csv)를 로드하여 기초 탐색 및 이상치를 제거하고,
  - Pandas, Polars Lazy API, DuckDB 세 가지 도구를 활용하여 동일한 그룹 집계(Named Aggregation)를 수행하며,
  - timeit을 통해 세 도구의 실행 성능을 공정하게 비교하는 실습입니다.
"""

import os
import sys
import timeit
import logging
import pandas as pd
import polars as pl
import duckdb

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'data', 'sales_100k.csv')

# 1) Pandas EDA 기초 탐색 + 이상치 처리
# --------------------------------------------------------------------
def process_pandas_eda(csv_path):
    """
    Pandas를 이용해 데이터를 탐색하고 IQR 방식으로 이상치를 제거합니다.
    """
    try:
        # csv 파일을 읽어옵니다.
        df = pd.read_csv(csv_path)
        logger.info(f"데이터 로딩 성공: {csv_path}")

        print("\n--- 1. Pandas 기초 탐색(EDA) ---")
        print("[info 확인]")
        df.info()
        
        print("\n[결측치 확인 - isnull().sum()]")
        print(df.isnull().sum())

        # 제거하기 전 df의 크기
        before_cnt = len(df)

        # IQR 이상치 탐지
        Q1 = df['amount'].quantile(0.25)
        Q3 = df['amount'].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # between 메서드를 사용하여 정상 범위 데이터만 필터링합니다.
        # (CoW) read 목적의 뷰이기 때문에 copy()를 사용하지 않았습니다.
        df_clean = df[df['amount'].between(lower_bound, upper_bound)]
        after_cnt = len(df_clean)
        
        print(f"\n[이상치 제거 결과] 제거 전: {before_cnt}행 -> 제거 후: {after_cnt}행")
        
        return df_clean, lower_bound, upper_bound
    
    except FileNotFoundError:
        logger.error(f"❌ 파일을 찾을 수 없습니다: {csv_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 오류가 발생했습니다: {e}")
        sys.exit(1)
# --------------------------------------------------------------------

# 2) Pandas groupby 및 named aggregation
# --------------------------------------------------------------------
def process_pandas_agg(df):
    """
    정제된 데이터를 그룹화하고 Named aggregation을 적용합니다.
    """
    try:
        print("\n--- 2. Pandas Named Aggregation ---")
        
        # region, category별로 묶은 뒤, 집계 결과의 컬럼명을 직접 지정합니다.
        # 총매출 내림차순으로 정렬하고, reset_index()를 사용하여 0-base 인덱싱을 합니다.
        pd_result = df.groupby(['region', 'category']).agg(
            total=('amount', 'sum'),
            mean=('amount', 'mean'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False).reset_index()
        
        print(pd_result.head())
        return pd_result
    
    except Exception as e:
        logger.error(f"❌ Pandas 집계 중 오류 발생: {e}")
        return None
# --------------------------------------------------------------------

# 3) Polars Lazy API로 동일 집계 작성
# --------------------------------------------------------------------
def process_polars_lazy(csv_path, lower, upper):
    """
    Polars의 Lazy API를 활용하여 데이터를 처리합니다.
    """
    try:
        print("\n--- 3. Polars Lazy API 집계 ---")
        
        # read_csv 대신 scan_csv를 사용하여 실행 계획 수립 후 collect()하도록 했습니다.
        pl_result = (
            pl.scan_csv(csv_path)
            .filter(pl.col('amount').is_between(lower, upper))
            .group_by(['region', 'category'])
            .agg(
                pl.col('amount').sum().alias('total'),
                pl.col('amount').mean().alias('mean'),
                pl.col('amount').count().alias('count')
            )
            .sort('total', descending=True)
            .collect() # collect()를 호출해 실행합니다.
        )
        
        print(pl_result.head())
        return pl_result
    
    except Exception as e:
        logger.error(f"❌ Polars 처리 중 오류 발생: {e}")
        return None
# --------------------------------------------------------------------

# 4) DuckDB SQL로 동일 집계 작성
# --------------------------------------------------------------------
def process_duckdb_sql(csv_path, lower, upper):
    """
    DuckDB를 활용하여 표준 SQL 구문으로 동일한 집계를 수행합니다.
    """
    try:
        print("\n--- 4. DuckDB SQL 집계 ---")
        
        # SQL 구문으로 그룹화 및 정렬 조건을 작성했습니다.
        # 쿼리를 실행한 뒤 결과를 Pandas DataFrame으로 변환하여 출력합니다.
        ddb_result = duckdb.sql(f"""
            SELECT region, 
                category, 
                SUM(amount) AS total, 
                AVG(amount) AS mean, 
                COUNT(amount) AS count
            FROM read_csv_auto('{csv_path}')
            WHERE amount BETWEEN {lower} AND {upper}
            GROUP BY region, category
            ORDER BY total DESC""").df()
        print(ddb_result.head())
        return ddb_result
    
    except Exception as e:
        logger.error(f"❌ DuckDB 처리 중 오류 발생: {e}")
        return None
# --------------------------------------------------------------------


# 5) timeit 사용 세 도구 성능 비교
# --------------------------------------------------------------------
def run_performance_test(csv_path, lower, upper, iters=5):
    """
    timeit을 통해 세 가지 도구의 실행 시간을 측정합니다.
    """
    print(f"\n--- 5. 세 도구 성능 비교 측정 시작 (반복 횟수: {iters}회) ---")
    
    def time_pandas():
        df = pd.read_csv(csv_path)
        df_clean = df[df['amount'].between(lower, upper)]
        df_clean.groupby(['region', 'category']).agg(
            total=('amount', 'sum'),
            mean=('amount', 'mean'),
            count=('amount', 'count')
        ).sort_values(by='total', ascending=False).reset_index()

    def time_polars():
        (
            pl.scan_csv(csv_path)
            .filter(pl.col('amount').is_between(lower, upper))
            .group_by(['region', 'category'])
            .agg(
                pl.col('amount').sum().alias('total'),
                pl.col('amount').mean().alias('mean'),
                pl.col('amount').count().alias('count')
            )
            .sort('total', descending=True)
            .collect() # collect()를 호출해 실행합니다.
        )

    def time_duckdb():
        duckdb.sql(f"""
            SELECT region, 
                category, 
                SUM(amount) AS total, 
                AVG(amount) AS mean, 
                COUNT(amount) AS count
            FROM read_csv_auto('{csv_path}')
            WHERE amount BETWEEN {lower} AND {upper}
            GROUP BY region, category
            ORDER BY total DESC""").df()

    try:
        # 공정한 비교를 위해 세 도구 모두 number 값을 동일하게 맞춥니다.
        pd_time = timeit.timeit(time_pandas, number=iters)
        pl_time = timeit.timeit(time_polars, number=iters)
        ddb_time = timeit.timeit(time_duckdb, number=iters)

        print(f"🐼 Pandas 실행 시간 : {pd_time:.5f}초")
        print(f"🐻‍❄️ Polars 실행 시간 : {pl_time:.5f}초")
        print(f"🦆 DuckDB 실행 시간 : {ddb_time:.5f}초")
        
    except Exception as e:
        logger.error(f"❌ 성능 측정 중 오류 발생: {e}")
# --------------------------------------------------------------------


# 6) 메인 실행 및 결과 테스트
# --------------------------------------------------------------------
if __name__ == "__main__":
    # 파이프라인 실행
    df_cleaned, low_b, up_b = process_pandas_eda(file_path)
    process_pandas_agg(df_cleaned)
    process_polars_lazy(file_path, low_b, up_b)
    process_duckdb_sql(file_path, low_b, up_b)
    run_performance_test(file_path, low_b, up_b)