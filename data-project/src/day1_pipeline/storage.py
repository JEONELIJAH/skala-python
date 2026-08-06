import logging
import os
import time

import pandas as pd

logger = logging.getLogger(__name__)

# 검증된 날씨 데이터를 CSV와 Parquet로 저장하고 입출력 성능을 비교합니다.
def save_and_compare_performance(validated_data, output_dir="output"): # default "output"
    
    # 시간대별 날씨 데이터를 추출합니다.
    weather_records = validated_data.get("weather", [])
    if not weather_records:
        logger.warning("저장할 날씨 데이터가 없습니다.")
        return

    # 1. Pydantic 객체 리스트를 Pandas DataFrame으로 변환
    # record.model_dump()를 통해 객체를 순수 딕셔너리로 풀어줍니다.
    df = pd.DataFrame([record.model_dump() for record in weather_records])
    
    # 출력물을 저장할 폴더 생성 (없으면 자동 생성)
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "weather.csv")
    parquet_path = os.path.join(output_dir, "weather.parquet")

    print("\n--- 💾 데이터 저장 및 성능 측정 시작 ---")
    
    # 1. CSV 성능 측정
    start_time = time.perf_counter()
    df.to_csv(csv_path, index=False, encoding='utf-8')
    csv_write_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    pd.read_csv(csv_path)
    csv_read_time = time.perf_counter() - start_time

    # 2. Parquet 성능 측정
    start_time = time.perf_counter()
    df.to_parquet(parquet_path, engine='pyarrow')
    parquet_write_time = time.perf_counter() - start_time

    start_time = time.perf_counter()
    pd.read_parquet(parquet_path, engine='pyarrow')
    parquet_read_time = time.perf_counter() - start_time

    # 3. 결과 출력
    print(f"[CSV]     쓰기: {csv_write_time:.5f}초 | 읽기: {csv_read_time:.5f}초")
    print(f"[Parquet] 쓰기: {parquet_write_time:.5f}초 | 읽기: {parquet_read_time:.5f}초")
    
    print("--- 🏁 측정 종료 ---\n")