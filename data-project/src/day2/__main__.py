"""`python -m src.day2`로 Day 2 전체 파이프라인을 실행합니다."""

import argparse
import sys
from pathlib import Path

if __package__:
    from . import run_pipeline
else:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    from src.day2 import run_pipeline


def parse_args() -> argparse.Namespace:
    """전체 파이프라인 실행 옵션을 파싱합니다."""
    parser = argparse.ArgumentParser(description="NYC Yellow Taxi Day 2 End-to-End 분석")
    parser.add_argument(
        "--skip-cleaning",
        action="store_true",
        help="기존 cleaned_tripdata.parquet을 재사용합니다.",
    )
    parser.add_argument(
        "--skip-performance",
        action="store_true",
        help="Pandas·Polars 성능 비교를 생략합니다.",
    )
    parser.add_argument("--iters", type=int, default=3, help="성능 비교 반복 횟수")
    return parser.parse_args()


def main() -> None:
    """명령행 옵션으로 Day 2 파이프라인을 실행합니다."""
    args = parse_args()
    result = run_pipeline(
        clean_data=not args.skip_cleaning,
        include_performance=not args.skip_performance,
        iters=args.iters,
    )

    print("\n--- 🏁 Day 2 End-to-End 파이프라인 정상 종료 ---")
    for name, path in result["artifacts"].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
