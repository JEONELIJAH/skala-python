"""
프로그램명: 머신러닝 파이프라인 및 모델 저장 모듈
파일명: ml_pipeline.py
작성자: 1조
작성일: 2026-08-07
프로그램 설명: 
  - sklearn.pipeline.Pipeline을 이용해 ColumnTransformer 전처리와 
    LogisticRegression 모델 학습을 수행합니다.
  - 평가 지표(Accuracy, F1-score)를 출력하고 joblib으로 모델을 저장합니다.
"""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_tripdata.parquet"
DEFAULT_MODEL_PATH = BASE_DIR / "output" / "yellow_taxi_2026_05" / "ml_lr_credit_card.joblib"

ML_SAMPLE_SIZE = 300000
BASE_NUMERIC = ["trip_distance"]
BASE_CATEGORICAL = ["pickup_hour", "pickup_weekday"]
LOCATION_CATEGORICAL = ["PULocationID", "DOLocationID"]
TARGET_COLUMN = "is_credit_card"


def build_pipeline(categorical_features):
    """Scikit-Learn Pipeline 및 ColumnTransformer 구성"""
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]
    )
    preprocessor = ColumnTransformer(
        [("num", numeric_pipeline, BASE_NUMERIC), ("cat", categorical_pipeline, categorical_features)]
    )
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def train_and_score(df_sample, categorical_features):
    """모델 학습 및 평가 지표(Accuracy, F1) 산출"""
    X = df_sample[BASE_NUMERIC + categorical_features]
    y = df_sample[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    pipeline = build_pipeline(categorical_features)
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    return accuracy, f1, pipeline


def run_ml_ablation_pipeline(df, model_save_path):
    """
    [ML Pipeline] 지역 정보 포함 유무에 따른 대조실험(Ablation) 수행, 
    평가 지표 출력 및 joblib 모델 저장
    """
    print("\n--- [3] 머신러닝 파이프라인 (Ablation 실험 및 저장) ---")
    try:
        eligible = df.loc[df["payment_type"].isin([1, 2])].copy()
        eligible[TARGET_COLUMN] = (eligible["payment_type"] == 1).astype(int)

        sample_size = min(ML_SAMPLE_SIZE, len(eligible))
        if sample_size < len(eligible):
            sample, _ = train_test_split(
                eligible, train_size=sample_size, stratify=eligible[TARGET_COLUMN], random_state=42
            )
        else:
            sample = eligible

        # Model A: 지역 정보 미포함
        acc_a, f1_a, _ = train_and_score(sample, BASE_CATEGORICAL)
        print(f"   - [Model A (기본 피처)] Accuracy: {acc_a:.4f} | F1-Score: {f1_a:.4f}")

        # Model B: 지역 정보 포함
        acc_b, f1_b, pipeline_b = train_and_score(sample, BASE_CATEGORICAL + LOCATION_CATEGORICAL)
        print(f"   - [Model B (지역 피처 추가)] Accuracy: {acc_b:.4f} | F1-Score: {f1_b:.4f}")

        # joblib을 통한 최적 모델 저장
        model_save_path = Path(model_save_path)
        model_save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline_b, model_save_path)
        print(f"✅ [joblib] 모델 저장 완료: {model_save_path}")

        return {
            "acc_a": acc_a, "f1_a": f1_a,
            "acc_b": acc_b, "f1_b": f1_b,
        }
    except (OSError, ImportError, ValueError, KeyError, TypeError) as e:
        logger.error(f"머신러닝 파이프라인 실행 중 오류 발생: {e}")
        return None


if __name__ == "__main__":
    # 1) 데이터 경로
    data_path = DEFAULT_DATA_PATH
    model_save_path = DEFAULT_MODEL_PATH
    model_save_path.parent.mkdir(parents=True, exist_ok=True)

    # 2) 데이터 로드
    df = pd.read_parquet(data_path)

    # 3) 피처 생성: BASE_CATEGORICAL에서 요구하는 시간 파생변수
    pickup_dt = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    df["pickup_hour"] = pickup_dt.dt.hour
    df["pickup_weekday"] = pickup_dt.dt.day_name()

    # 4) 파이프라인 실행
    result = run_ml_ablation_pipeline(df, model_save_path)
    if result is not None:
        print(f"[요약] Model A(F1): {result['f1_a']:.4f}, Model B(F1): {result['f1_b']:.4f}")
