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