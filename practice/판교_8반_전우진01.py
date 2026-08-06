"""
프로그램명: 파이썬 자료구조 집계 및 고급 문법 실습 스크립트
작성자: 전우진 P267
작성일: 2026-08-06
프로그램 설명: 
  - 본 파일은 Python의 자료구조 집계 · 컴프리헨션 · 제너레이터를 이해하기 위한 실습 과정을 담은 결과입니다.
  - JSON 데이터를 불러와 파이썬의 핵심 자료구조(List, Dict, set)와 
  - 고급 문법(Comprehension, Generator, collections 모듈)을 활용해 데이터를 집계하고, 
  - 제너레이터의 메모리 효율성을 검증하는 실습 프로그램입니다.
"""

import os
import sys
import json
from collections import defaultdict, Counter

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'data', 'Python_Practice2_Data.json')

try:
    # json 파일을 읽기 모드('r')로 엽니다.
    # with문을 써서 파일을 자동으로 닫게 합니다.
    with open(file_path, 'r', encoding='utf-8') as file:
        # json.load()를 사용해 파이썬 객체로 변환합니다.
        sales = json.load(file)
except FileNotFoundError:
    print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
    sys.exit(1)
except json.JSONDecodeError:
    print("❌ 올바른 JSON 형식이 아닙니다.")
    sys.exit(1)
except Exception as e:
    print(f"❌ 오류가 발생했습니다: {e}")
    sys.exit(1)


# 1) 리스트/딕셔너리 컴프리헨션
# --------------------------------------------------------------------
# amount가 1000 이상인 거래를 필터링하고, 지역별 총매출 dict를 컴프리헨션으로 계산합니다.
region_total = {
    # 2. 만들어진 set을 순회하며 amount가 1000 이상인 target_region의 amount를 sum()으로 더해주고, target_region value에 할당합니다.
    target_region: sum(sale["amount"] for sale in sales if sale["region"] == target_region and sale["amount"] >= 1000)
    # 1. amount가 1000 이상인 지역을 필터링하고, set을 사용해 중복을 제거한 target_region을 만듭니다.
    for target_region in set(sale["region"] for sale in sales if sale["amount"] >= 1000)
}

print(f"1) 리스트/딕셔너리 컴프리헨션 결과: \n {region_total}")
print()
# --------------------------------------------------------------------

# 2) Counter + defaultdict
# --------------------------------------------------------------------
# Counter를 사용하여 지역별 거래 건수를 계산합니다.
region_transaction_count = Counter(sale["region"] for sale in sales)
print(f"2-1) Counter 사용한 지역별 거래 건수 결과: \n {region_transaction_count}")

# defaultdict를 사용해 카테고리별 amount 리스트를 계산합니다.
amount_by_category = defaultdict(list)

for sale in sales:
    # defaultdict는 딕셔너리에 해당 카테고리 키가 없으면 알아서 []를 만든 뒤 추가해 줍니다.
    amount_by_category[sale["category"]].append(sale["amount"])
print(f"2-2) defaultdict를 사용한 카테고리별 amount 리스트 결과: \n {amount_by_category}")
print()
# --------------------------------------------------------------------

# 3) 제너레이터 - 메모리 비교
# --------------------------------------------------------------------
# 제너레이터 함수를 만들어서 amount가 1000을 초과하는 행만 yield합니다.
def generator_version(sales):
    for sale in sales:
        if sale["amount"] > 1000:
            yield sale

# list()를 사용해 결과를 확인합니다.
filtered_over_thousand = list(generator_version(sales))
# print(filtered_over_thousand)

# list 버전
list_version = [sale for sale in sales if sale["amount"] > 1000]

# list vs 제너레이터 메모리 비교를 합니다.
print("3-1) 리스트 메모리:", sys.getsizeof(list_version), "bytes")
print("3-2) 제너레이터 메모리:", sys.getsizeof(generator_version(sales)), "bytes")
print()
# --------------------------------------------------------------------

# 4) 종합 - 월별 카테고리 매출 집계
# --------------------------------------------------------------------
# sales 데이터를 month, category 기준으로 그룹핑해 총매출 dict를 만듭니다. (컴프리헨션 + defaultdict)

# 1. month, category 기준으로 그룹핑하여 리스트에 모으기 defaultdict
total_by_month_and_category = defaultdict(list)
for sale in sales:
    # month와 category를 묶어서 하나의 튜플 키로 만듭니다.
    key = (sale["month"], sale["category"])
    total_by_month_and_category[key].append(sale["amount"])

# 2. 각 그룹의 리스트를 총매출 변환하기 컴프리헨션
total_monthly = {k: sum(v) for k, v in total_by_month_and_category.items()}
print(f"4) 월별 카테고리 매출 집계 결과: \n {total_monthly}")

# defaultdict(int)로 선언하고, total_by_month_and_category[key] += sale["amount"]로 동일한 결과를 얻을 수 있습니다.
# --------------------------------------------------------------------


# --------------------------------------------------------------------
# 결과 테스트
print("\n--- Checkpoint 테스트 시작 ---\n")

# 1. region_total 값 정확 (assert 통과)
assert region_total == {'광주': 4830, '대전': 6300, '부산': 4550, '세종': 5750, '울산': 7270, '인천': 11950, '대구': 8320, '서울': 17670}, f"region_total 값이 틀립니다: {region_total}"
print("✅ 1. region_total 값 정확 (assert 통과)")

# 2. Counter.most_common() 순서 정확
# 가장 많이 거래된 지역부터 내림차순으로 튜플 형태로 정렬되어 나오는지 확인합니다.
print(f"✅ 2. Counter.most_common() 순서 정확: {region_transaction_count.most_common()}")

# 3. generator sys.getsizeof < list 확인
list_version = [sale for sale in sales if sale["amount"] > 1000]

# [수정] 함수명과 동일했던 변수명을 gen_obj로 변경하여 함수 덮어쓰기를 방지했습니다.
gen_obj = generator_version(sales)

gen_size = sys.getsizeof(gen_obj)
list_size = sys.getsizeof(list_version)

# 제너레이터 용량이 리스트보다 작은지 assert로 확인
assert gen_size < list_size, "제너레이터 메모리가 리스트보다 큽니다."
print(f"✅ 3. generator sys.getsizeof < list 확인 (Gen: {gen_size} bytes < List: {list_size} bytes)")

# 4. top3 금액 내림차순 정렬 정확
top3_sales = sorted(sales, key=lambda x: x["amount"], reverse=True)[:3]
print("✅ 4. top3 금액 내림차순 정렬 정확:")
for i, sale in enumerate(top3_sales, 1):
    print(f"   {i}위: {sale}")

print("\n--- 모든 Checkpoint 통과 ---")