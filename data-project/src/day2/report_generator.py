"""
프로그램명: Day2 분석 결과 자동 보고서 생성기
작성자: 1조
파일명: report_generator.py
작성일: 2026-08-07
프로그램 설명:
  - 정제된 뉴욕 택시 데이터를 로딩하여 기술통계, 상관계수, t-test와 카이제곱 검정을 수행합니다.
  - 머신러닝 Pipeline의 평가 지표를 산출하고 학습된 모델을 joblib 파일로 저장합니다.
  - Seaborn 정적 차트와 Plotly 인터랙티브 차트를 생성합니다.
  - Pandas 및 Polars 성능 비교를 포함한 전체 분석 결과를 report.md로 자동 저장합니다.
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))

from clean import run_performance_test
from ml_pipeline import run_ml_ablation_pipeline
from statistical_analyzer import analyze_dispute_zones, run_basic_statistics_and_ttest
from viz import create_and_save_plotly_chart, create_eda_subplots

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
OUTPUT_ROOT = BASE_DIR / "output" / "yellow_taxi_2026_05"

DEFAULT_DATA_PATH = str((DATA_ROOT / "processed" / "cleaned_tripdata.parquet").resolve())
DEFAULT_RAW_PATH = str((DATA_ROOT / "raw" / "yellow_tripdata_2026-05.parquet").resolve())
DEFAULT_ZONE_LOOKUP = str((PROJECT_ROOT / "taxi_zone_lookup.csv").resolve())
DEFAULT_REPORT_PATH = str((OUTPUT_ROOT / "report.md").resolve())
DEFAULT_MODEL_PATH = str((OUTPUT_ROOT / "ml_lr_credit_card.joblib").resolve())
DEFAULT_EDA_IMAGE = str((OUTPUT_ROOT / "eda_subplots.png").resolve())
DEFAULT_PLOTLY_HTML = str((OUTPUT_ROOT / "taxi_interactive_chart.html").resolve())

def run_report(
    data_path: str, raw_path: str, output_report: str,
    model_save_path: str, eda_image_path: str, plotly_html_path: str,
    iters: int = 3, include_performance: bool = True
):
    if not Path(data_path).exists():
        raise FileNotFoundError(f"분석용 파일이 없습니다: {data_path}")

    Path(output_report).parent.mkdir(parents=True, exist_ok=True)
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
    Path(eda_image_path).parent.mkdir(parents=True, exist_ok=True)
    Path(plotly_html_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(data_path)

    lines = []
    lines.append("# Day 2 자동 분석 리포트")
    lines.append(f"- 생성 일시: {datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 데이터 행/열: {len(df):,} x {len(df.columns)}\n")

    # 1) 통계 + t-test
    basic = run_basic_statistics_and_ttest(df)
    lines.append("## 1) 기본 통계 & t-test")
    lines.append(f"- t-statistic: {basic['t_stat']:.4f}, p-value: {basic['p_val']:.4e}")
    lines.append(f"- 해석: {basic['ttest_verdict']}\n")
    lines.append("### 기술통계\n" + basic["desc_stats"].to_string() + "\n")
    lines.append("### 상관계수\n" + basic["correlation"].round(3).to_string() + "\n")

    # 2) 카이제곱 검정 (PULocationID 기반)
    lines.append("## 2) 분쟁 다발 지역 카이제곱 검정")
    dispute = analyze_dispute_zones(df)
    if dispute is None:
        lines.append("- 실행 실패: 데이터 상태를 확인하세요.\n")
    else:
        lines.append(f"- chi2: {dispute['chi2']:.4f}, p-value: {dispute['p_value']:.4e}")
        lines.append(f"- 해석: {'유의미한 차이 존재' if dispute['significant'] else '유의미한 차이 미검출'}\n")

    # 3) ML (Pipeline)
    lines.append("## 3) ML Pipeline")
    ml_df = df.copy()
    pickup_dt = pd.to_datetime(ml_df["tpep_pickup_datetime"], errors="coerce")
    ml_df["pickup_hour"] = pickup_dt.dt.hour
    ml_df["pickup_weekday"] = pickup_dt.dt.day_name()

    ml_result = run_ml_ablation_pipeline(ml_df, model_save_path)
    if ml_result is not None:
        lines.append(f"- Model A Accuracy: {ml_result['acc_a']:.4f} | F1: {ml_result['f1_a']:.4f}")
        lines.append(f"- Model B Accuracy: {ml_result['acc_b']:.4f} | F1: {ml_result['f1_b']:.4f}\n")

    # 4) 시각화 및 기타
    lines.append("## 4) 시각화 및 모델 산출물")
    create_eda_subplots(df, eda_image_path)
    create_and_save_plotly_chart(df, plotly_html_path)
    lines.append(f"- Seaborn: {eda_image_path}\n- Plotly: {plotly_html_path}\n- 모델: {model_save_path}")

    # 5) Pandas·Polars 성능 비교
    if include_performance:
        lines.append("\n## 5) Pandas·Polars 성능 비교")
        if Path(raw_path).exists():
            performance = run_performance_test(raw_path, iters=iters, return_metrics=True)
            if performance is not None:
                lines.append(f"- Pandas: {performance['pandas_time_sec']:.4f}초")
                lines.append(f"- Polars Eager: {performance['polars_eager_time_sec']:.4f}초")
                lines.append(f"- Polars Lazy: {performance['polars_lazy_time_sec']:.4f}초")
        else:
            lines.append(f"- 원본 파일이 없어 성능 비교를 생략했습니다: {raw_path}")

    report_text = "\n".join(lines) + "\n"
    Path(output_report).write_text(report_text, encoding="utf-8")
    logger.info("✅ report.md 생성 완료: %s", output_report)

def parse_args():
    p = argparse.ArgumentParser(description="뉴욕 택시 Day2 분석 자동 보고서 생성")
    p.add_argument("--data", default=DEFAULT_DATA_PATH)
    p.add_argument("--raw", default=DEFAULT_RAW_PATH)
    p.add_argument("--output", default=DEFAULT_REPORT_PATH)
    p.add_argument("--model-out", default=DEFAULT_MODEL_PATH)
    p.add_argument("--eda-image", default=DEFAULT_EDA_IMAGE)
    p.add_argument("--plotly-html", default=DEFAULT_PLOTLY_HTML)
    p.add_argument("--iters", type=int, default=3)
    p.add_argument("--skip-performance", action="store_true")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    run_report(
        data_path=args.data, raw_path=args.raw, output_report=args.output,
        model_save_path=args.model_out, eda_image_path=args.eda_image,
        plotly_html_path=args.plotly_html, iters=args.iters,
        include_performance=not args.skip_performance,
    )
