"""
프로그램명: 뉴욕 택시 데이터 시각화 모듈 (EDA 및 인터랙티브 차트)
파일명: visualizer.py
작성자: 1조
작성일: 2026-08-07
프로그램 설명: 
  - 정제된 뉴욕 택시 데이터(cleaned_tripdata.parquet)를 활용합니다.
  - Seaborn을 활용한 정적 시각화 4종(거리 분포, 요금 vs 거리 상관관계 등)과 
    Plotly를 활용한 인터랙티브 차트를 생성합니다.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

# 시각화 패키지
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import plotly.express as px

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cleaned_file_path = '/Users/jeon/skala/projects/skala-python/data-project/cleaned_tripdata.parquet'
current_dir = os.path.dirname(os.path.abspath(__file__))

# 폰트 설정 (Mac 환경 맞춤 설정)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


# 1) 정제된 Parquet 데이터 로딩
# --------------------------------------------------------------------
def load_cleaned_data(parquet_path):
    print("\n--- [0] 정제된 택시 데이터 로딩 중 ---")
    try:
        df = pd.read_parquet(parquet_path)
        logger.info(f"데이터 로딩 완료: 총 {len(df):,}행")
        return df
    except Exception as e:
        logger.error(f"❌ 데이터 로딩 실패: {e}")
        sys.exit(1)
# --------------------------------------------------------------------


# 2) EDA 시각화 4종 (Seaborn 정적 차트 - 뉴욕 택시 맞춤)
# --------------------------------------------------------------------
def create_eda_subplots(df, output_image_path):
    try:
        print("\n--- [1] EDA 시각화 4종 (Seaborn 2x2 Subplots) 생성 ---")
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Yellow Taxi Data EDA Summary (2x2 Subplots)', fontsize=16)

        # [1] 이동 거리(trip_distance) 분포 (히스토그램 + KDE) -> 상위 1% 이상치 제외하고 시각화 가독성 확보
        dist_filtered = df[df['trip_distance'] < df['trip_distance'].quantile(0.99)]
        sns.histplot(dist_filtered['trip_distance'], kde=True, ax=axes[0, 0], color='skyblue')
        axes[0, 0].set_title('1) 운행 거리 분포 (분포)')
        axes[0, 0].set_xlabel('이동 거리 (Miles)')

        # [2] 결제 방식(payment_type)별 총 요금(total_amount) 분포 (박스플롯 - 그룹 비교)
        # 1. TLC 공식 데이터 사전을 참조하여 숫자 코드를 텍스트로 변환
        payment_dict = {1: '신용카드', 2: '현금', 3: '무료', 4: '분쟁'}
        
        # 2. 1~4번 데이터만 필터링 후 이름 맵핑
        pay_filtered = df[df['payment_type'].isin([1, 2, 3, 4])].copy()
        pay_filtered['payment_name'] = pay_filtered['payment_type'].map(payment_dict)
        
        # 3. showfliers=False를 통해 이상치 점을 숨겨서 박스 자체의 비교를 극대화
        sns.boxplot(
            x='payment_name', y='total_amount', data=pay_filtered, 
            ax=axes[0, 1], palette='Set2', hue='payment_name', legend=False,
            showfliers=False  # 핵심: 까만 점 제거
        )
        axes[0, 1].set_title('2) 결제 수단별 총 요금 분포 (이상치 제외)')
        axes[0, 1].set_xlabel('결제 타입')
        axes[0, 1].set_ylabel('총 요금 (USD)')
        # [3] 일별(Daily) 총 승차 건수 시계열 라인 차트
        # 1. 날짜만 추출
        df['pickup_date'] = pd.to_datetime(df['tpep_pickup_datetime']).dt.date
        
        # 2. 2026년 5월 정상 데이터만 필터링 (미터기 시간 오류 이상치 제거)
        target_start = pd.to_datetime('2026-05-01').date()
        target_end = pd.to_datetime('2026-05-31').date()
        df_filtered_date = df[(df['pickup_date'] >= target_start) & (df['pickup_date'] <= target_end)]
        
        # 3. 일별 승차 건수 집계
        daily_counts = df_filtered_date.groupby('pickup_date').size().reset_index(name='trip_count')
        
        # 4. 차트 생성
        sns.lineplot(x='pickup_date', y='trip_count', data=daily_counts, ax=axes[1, 0], marker='o', color='coral', linewidth=2)
        axes[1, 0].set_title('3) 일별 총 승차 건수 추이 (2026년 5월)')
        axes[1, 0].set_xlabel('날짜 (Date)')
        axes[1, 0].set_ylabel('승차 건수')
        axes[1, 0].tick_params(axis='x', rotation=45)

        # [4] 수치형 주요 변수 간 상관관계 히트맵 (상관관계)
        # 1. 모든 수치형 데이터 선택 (필터링 없음)
        numeric_df = df.select_dtypes(include=[np.number])
        
        # 2. 대용량 렌더링 속도 개선을 위한 샘플링
        sub_df = numeric_df.sample(n=10000, random_state=42)
        
        # 3. 15개가 넘는 컬럼을 한 화면에 담기 위해 폰트 크기 대폭 축소
        sns.heatmap(
            sub_df.corr(), annot=True, fmt='.2f', cmap='coolwarm', ax=axes[1, 1], 
            annot_kws={"size": 5}, cbar_kws={'shrink': 0.8}
        )
        
        axes[1, 1].set_title('4) 전체 수치형 변수 상관관계 (Heatmap)')
        
        # 축 라벨이 길어서 겹치지 않도록 폰트 크기 조절 및 회전
        axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor', fontsize=7)
        axes[1, 1].tick_params(axis='y', labelsize=7)

        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300)
        print(f"✅ 2x2 서브플롯 시각화 저장 완료: {output_image_path}")
        plt.close()

    except Exception as e:
        logger.error(f"❌ 시각화 생성 중 오류 발생: {e}")
# --------------------------------------------------------------------


# 3) Plotly 인터랙티브 차트 생성 & HTML 저장
# --------------------------------------------------------------------
def create_and_save_plotly_chart(df, html_output_path):
    try:
        print("\n--- [2] Plotly 인터랙티브 차트 작성 및 HTML 저장 ---")

        # 분석 편의를 위해 샘플링 및 요약 (결제 타입별 평균 거리와 요금)
        sample_df = df.sample(n=10000, random_state=42)
        
        fig = px.scatter(
            sample_df, x='trip_distance', y='total_amount', color='payment_type',
            title='운행 거리에 따른 총 요금 분포 (인터랙티브 산점도)',
            labels={'trip_distance': '이동 거리 (Miles)', 'total_amount': '총 요금 (USD)', 'payment_type': '결제 타입'},
            template='plotly_white', opacity=0.6
        )

        fig.write_html(html_output_path)
        print(f"✅ Plotly 인터랙티브 차트 저장 완료 (.html): {html_output_path}")

    except Exception as e:
        logger.error(f"❌ Plotly 차트 생성 중 오류 발생: {e}")
# --------------------------------------------------------------------


if __name__ == "__main__":
    
    image_file = os.path.join(current_dir, 'eda_subplots.png')
    html_file = os.path.join(current_dir, 'taxi_interactive_chart.html')

    # 1. 정제된 Parquet 데이터 로드
    df_clean = load_cleaned_data(cleaned_file_path)
    
    # 2. Seaborn 정적 차트 (2x2 서브플롯) 생성
    create_eda_subplots(df_clean, image_file)
    
    # 3. Plotly 인터랙티브 차트 생성
    create_and_save_plotly_chart(df_clean, html_file)

    print("\n--- 🏁 뉴욕 택시 시각화 모듈 정상 종료 ---")