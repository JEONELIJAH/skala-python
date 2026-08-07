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
        print("\n[결측치 확인 - isna().sum()]")
        print(df.isna().sum())

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

df_cleaned, low_b, up_b = process_pandas_eda(file_path)
process_pandas_agg(df_cleaned)