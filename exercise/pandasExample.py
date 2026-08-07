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