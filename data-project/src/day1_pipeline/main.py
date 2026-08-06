"""
파일명: main.py
작성자: 전우진 P267
작성일: 2026-08-06
설명: 비동기 API 수집, Pydantic 스키마 검증, 파일 저장 및 성능 측정까지
      전체 데이터 파이프라인의 흐름을 제어하는 메인 모듈입니다.
"""

import asyncio

from collector import collect_all_data
from schemas import validate_data
from storage import save_and_compare_performance


# 데이터 수집, 검증, 저장을 통합 실행하는 파이프라인 메인 함수입니다.
def run_data_pipeline():
    
    # 1. 외부 API 데이터 비동기 수집
    raw_data = asyncio.run(collect_all_data())
    
    # 2. Pydantic 스키마 검증 및 데이터 정제
    validated_data = validate_data(raw_data)
    
    # 3. CSV/Parquet 저장 및 성능 비교
    save_and_compare_performance(validated_data)

if __name__ == "__main__":
    # 메인 파이프라인 실행
    run_data_pipeline()