"""NYC Yellow Taxi Day 2 End-to-End 분석 파이프라인입니다."""

from pathlib import Path

__all__ = ["run_pipeline"]


def run_pipeline(
    *,
    clean_data: bool = True,
    include_performance: bool = True,
    iters: int = 3,
) -> dict:
    """데이터 전처리부터 리포트 생성까지 전체 Day 2 분석을 실행합니다.

    모듈 로딩 시 대용량 분석 패키지를 즉시 불러오지 않도록 필요한 시점에
    내부 모듈을 로딩합니다.
    """
    if iters < 1:
        raise ValueError("성능 비교 반복 횟수는 1 이상이어야 합니다.")

    from .clean import OUTPUT_FILE, run_cleaning_pipeline
    from .report_generator import (
        DEFAULT_EDA_IMAGE,
        DEFAULT_MODEL_PATH,
        DEFAULT_PLOTLY_HTML,
        DEFAULT_RAW_PATH,
        DEFAULT_REPORT_PATH,
        run_report,
    )

    cleaning_result = None
    if clean_data:
        # 성능 비교는 report.md에 기록하기 위해 리포트 단계에서 한 번만 수행합니다.
        cleaning_result = run_cleaning_pipeline(run_performance=False, iters=iters)

    report_path = run_report(
        data_path=str(OUTPUT_FILE),
        raw_path=DEFAULT_RAW_PATH,
        output_report=DEFAULT_REPORT_PATH,
        model_save_path=DEFAULT_MODEL_PATH,
        eda_image_path=DEFAULT_EDA_IMAGE,
        plotly_html_path=DEFAULT_PLOTLY_HTML,
        iters=iters,
        include_performance=include_performance,
    )

    artifacts = {
        "processed_data": Path(OUTPUT_FILE),
        "report": report_path,
        "model": Path(DEFAULT_MODEL_PATH),
        "seaborn_chart": Path(DEFAULT_EDA_IMAGE),
        "plotly_chart": Path(DEFAULT_PLOTLY_HTML),
    }
    missing_artifacts = [name for name, path in artifacts.items() if not path.exists()]
    if missing_artifacts:
        raise RuntimeError(f"생성되지 않은 산출물이 있습니다: {missing_artifacts}")

    return {"cleaning": cleaning_result, "artifacts": artifacts}
