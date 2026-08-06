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