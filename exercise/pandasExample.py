# 기초 EDA 패턴
import pandas as pd
df = pd.read_json('./practice/data/Python_Practice2_Data.json')

# 기초 확인
df.shape # (행수, 열수)
df.info() # 타입·결측·메모리
df.describe() # 수치 기술통계
df.describe(include='all') # 범주형 포함

# 타입 변환
df['month'] = pd.to_datetime(df['month'])
df['region'] = df['region'].astype('category')

# 컬럼 선택
df['amount'] # Series
df[['region','amount']] # DataFrame
df.loc[df['amount']>1000] # 조건 필터

'''
Data columns (total 5 columns):
 #   Column    Non-Null Count  Dtype
---  ------    --------------  -----
 0   region    100 non-null    str  
 1   category  98 non-null     str  
 2   amount    100 non-null    int64
 3   month     99 non-null     str  
 4   Category  1 non-null      str  
dtypes: int64(1), str(4)
'''

# 결측치·이상치 처리
# 결측치 파악
df.isna().sum()
df.isna().sum() / len(df) * 100 # 비율

# 처리 전략
df['amount'].fillna(df['amount'].median())
df['category'].fillna(df['category'].mode()[0])
df.dropna(subset=['month','amount'])

# IQR 이상치 탐지
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
lo, hi = Q1 - 1.5*IQR, Q3 + 1.5*IQR
df_clean = df[df['amount'].between(lo, hi)]
print(f'이상치 {(~df["amount"].between(lo,hi)).sum()}건 제거')

'''
이상치 1건 제거
'''

# 집계·결합 실전
# 다중 집계 + 컬럼명 지정 (monthly)
monthly = df.groupby('month').agg(
    revenue=('amount','sum'),
    cnt=('amount','count'),
    avg=('amount','mean')
).reset_index()

print(f"\n{monthly}\n")

"""
       month  revenue  cnt          avg
0 2024-01-01    22690   23   986.521739
1 2024-02-01    26870   27   995.185185
2 2024-03-01    23500   22  1068.181818
3 2024-04-01    27190   26  1045.769231
"""

# pivot_table
pivot = df.pivot_table(
    values='amount', index='region',
    columns='category', aggfunc='sum',
    fill_value=0)

print(f"\n{pivot}\n")

"""
category    식품    의류     전자
region                     
             0   680      0
광주        1620  2450   4830
대구        1620  5170   5870
대전        1270  3740   4810
부산        1330  4800   4800
서울        2390  5570  12100
세종        1920  2470   5750
울산        1360  3070   7270
인천        1630  4550   8350
"""

# merge (LEFT JOIN)
# result = pd.merge(df_sales, df_cust, on='customer_id', how='left')
# merge vs join 차이
# merge: 컬럼 기준 | join: 인덱스 기준

# 1) 복사본에서 실습
df_work = df.copy()

# 2) 서울 행 필터
mask_seoul = df_work['region'].eq('서울')

# 방법 A: 실수형으로 바꾼 뒤 계산 (가장 깔끔)
df_work['amount'] = df_work['amount'].astype('float64')      # int64 -> float64로 미리 변경
df_work.loc[mask_seoul, 'amount'] = df_work.loc[mask_seoul, 'amount'] * 1.1

# 확인
print(df_work.dtypes)

# 방법 B: amount를 int로 유지해야 한다면 반올림 후 int 캐스팅
df_work2 = df.copy()
df_work2.loc[mask_seoul, 'amount'] = (
    (df_work2.loc[mask_seoul, 'amount'].astype('float64') * 1.1)
    .round(0)
    .astype('Int64')   # pandas nullable int
)

# 체인 할당 쓰고 싶을 때(원본 수정 X)도 .copy()를 꼭 붙이고, 계산 끝에 타입 맞추기
df_seoul = df.loc[df['region'] == '서울'].copy()
df_seoul['amount'] = (df_seoul['amount'].astype('float64') * 1.1)