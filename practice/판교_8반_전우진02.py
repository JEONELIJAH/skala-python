"""
프로그램명: 파일 I/O, 예외 처리, Pydantic 검증 파이프라인 실습 스크립트
작성자: 전우진 P267
작성일: 2026-08-06
프로그램 설명: 
  - 본 파일은 JSON 데이터를 로드하고 Pydantic v2를 통해 데이터를 검증한 후, 
  - 정상 데이터와 오류 데이터를 분리하여 각각 CSV와 JSON으로 저장하는 실습입니다.
"""

import os
import sys
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field, ValidationError
import csv

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'data', 'Python_Practice2_Data.json')


# 1) 예외 처리 + 파일 읽기
# --------------------------------------------------------------------
def safe_load_csv(file_path: str):
    """
    지정된 경로의 데이터 파일을 읽어옵니다.
    """
    try:
        # json 파일을 읽기 모드('r')로 엽니다.
        # with문을 써서 파일을 자동으로 닫게 합니다.
        with open(file_path, 'r', encoding='utf-8') as file:
            # json.load()를 사용해 파이썬 객체로 변환합니다.
            data = json.load(file)
        logger.info(f"데이터 로딩 성공: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return None
    except json.JSONDecodeError:
        logger.error("❌ 올바른 JSON 형식이 아닙니다.")
        return None
    except Exception as e:
        logger.error(f"❌ 오류가 발생했습니다: {e}")
        return None
    finally:
        print("로딩 종료")

# print(f"1) safe_load_csv 실행 결과: \n {safe_load_csv(file_path)}")
print()
# --------------------------------------------------------------------

# 2) Pydantic v2 스키마 정의
# --------------------------------------------------------------------
class SalesRecord(BaseModel):
    # 빈 문자열을 허용하지 않기 위해 min_length=1 적용합니다.
    month: str = Field(min_length=1, description="한 글자 이상")
    region: str = Field(min_length=1, description="한 글자 이상")
    # 0 초과 조건 적용
    amount: int = Field(gt=0, description="양수")
    # category는 없어도 되므로 Optional로 처리했습니다.
    category: Optional[str] = None

# --------------------------------------------------------------------

# 3) 검증 파이프라인 + 파일 저장 함수화
# --------------------------------------------------------------------
def process_and_save_data(data_list, csv_path, json_path):
    valid_records = []
    error_records = []

    if data_list:
        print("\n--- Pydantic 검증 시작 ---")
        # raw_data를 하나씩 꺼내서 row에 담아줍니다. 1 index로 순번을 i에 담습니다.
        for i, row in enumerate(data_list, 1):
            # ValidationError 처리
            try:
                # 딕셔너리 언패킹으로 row를 푼 값을 Pydantic 스키마 SalesRecord에서 검증합니다.
                record = SalesRecord(**row)
                valid_records.append(record)
                # print(f"✅ [행 {i} 검증 통과] 데이터 정상 저장")
            except ValidationError as e:
                print(f"⚠️ [행 {i} 검증 오류]")
                print(e)
                # 에러 내역을 딕셔너리로 저장
                error_records.append({"row": row, "error": str(e)})

    # 정상 데이터 CSV 저장
    if valid_records:
        with open(csv_path, 'w', encoding='utf-8', newline='') as file:
            fieldnames = list(valid_records[0].model_dump().keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for record in valid_records:
                writer.writerow(record.model_dump())

    # 오류 데이터 JSON 저장
    if error_records:
        with open(json_path, 'w', encoding='utf-8') as file:
            # ensure_ascii=False 설정으로 한글 깨짐을 방지합니다.
            json.dump(error_records, file, ensure_ascii=False, indent=4)

    return valid_records, error_records


def reload_csv(csv_path):
    # CSV 재로딩
    reloaded = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                reloaded.append(row)
    return reloaded

# --------------------------------------------------------------------

# 4) 실행 및 결과 테스트
# --------------------------------------------------------------------
csv_output_path = os.path.join(current_dir, 'valid_records.csv')
json_output_path = os.path.join(current_dir, 'error_records.json')

raw_data = safe_load_csv(file_path)
valid_records, error_records = process_and_save_data(raw_data, csv_output_path, json_output_path)
reloaded = reload_csv(csv_output_path)


print("\n--- Checkpoint 테스트 시작 ---")

# 1. safe_load_csv 동작 + assert None 통과
none_test = safe_load_csv(os.path.join(current_dir, 'fake_file.json'))
assert none_test is None, "존재하지 않는 파일 로드 시 None이 반환되어야 합니다."
print("✅ 1. safe_load_csv 동작 및 assert None 통과")

print("✅ 2. ValidationError 오류 내용 정상 출력 완료")

# 3. valid 4건 / errors 3건 assert 통과

# 의도한 결과가 나올 수 있도록 mock data를 구성합니다.
mock_data = [
    {"month": "2024-01", "region": "서울", "amount": 1500, "category": "전자"},
    {"month": "2024-01", "region": "부산", "amount": 800},
    {"month": "2024-02", "region": "서울", "amount": 1200, "category": "의류"},
    {"month": "2024-02", "region": "제주", "amount": 650, "category": "전자"},
    {"month": "", "region": "대구", "amount": 950, "category": "전자"},
    {"month": "2024-01", "region": "", "amount": 950, "category": "전자"},
    {"month": "2024-01", "region": "광주", "amount": 0, "category": "전자"}
]

valid_mock, error_mock = process_and_save_data(mock_data, csv_output_path, json_output_path)
reloaded = reload_csv(csv_output_path)

assert len(valid_mock) == 4, f"valid 건수 오류: {len(valid_mock)}"
assert len(error_mock) == 3, f"errors 건수 오류: {len(error_mock)}"
print("✅ 3. valid 4건 / errors 3건 분리 완벽 (assert 통과)")

# 4. 재로딩 후 len(reloaded)==4 통과
assert len(reloaded) == 4, f"재로딩 건수 오류: {len(reloaded)}"
print(f"✅ 4. 재로딩 데이터 검증 완료 (총 {len(reloaded)}건 통과)")

print("--- 모든 Checkpoint 통과 ---")