import os
import time
from datetime import datetime
from pathlib import Path
import joblib
import pandas as pd
import pytz
import rich
from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from common_utils.core.common import get_root_dir, load_env_vars
from common_utils.core.logger import Logger
from hydra import compose, initialize
from mlops_pipeline_feature_v1 import extract, load, transform
from mlops_pipeline_feature_v1.utils import interval_to_milliseconds
from omegaconf import DictConfig
from rich.pretty import pprint

ROOT_DIR = get_root_dir(env_var="ROOT_DIR", root_dir=".")
pprint(ROOT_DIR)
os.environ["ROOT_DIR"] = str(ROOT_DIR)
load_env_vars(root_dir=ROOT_DIR)

PROJECT_ID = os.getenv("PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")
rich.print(PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, BUCKET_NAME)

OUTPUTS_DIR = f"{ROOT_DIR}/outputs/mlops_pipeline_feature_v1"
Path(OUTPUTS_DIR).mkdir(parents=True, exist_ok=True)

LOGS_DIR = f"{OUTPUTS_DIR}/logs"
STORES_DIR = f"{OUTPUTS_DIR}/stores"

Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
Path(STORES_DIR).mkdir(parents=True, exist_ok=True)

# Setup logging
# so if you are in docker, then ROOT_DIR = opt/airflow
# but i overwrite to become     ROOT_DIR: ${ROOT_DIR:-/opt/airflow/dags}
logger = Logger(
    log_file="mlops_pipeline_feature_v1.log",
    log_dir=LOGS_DIR,
    # log_dir=None,
).logger


def preprocess(
    project_id: str,
    google_application_credentials: str,
    dataset: str,
    table_name: str,
):
    bq = BigQuery(
        project_id=project_id,
        google_application_credentials=google_application_credentials,
        dataset=dataset,
        table_name=table_name,
    )

    query = """
    SELECT *
    FROM `gao-hongnan.mlops_pipeline_v1_staging.processed_binance_btcusdt_spot` t
    WHERE t.utc_datetime > DATETIME(TIMESTAMP "2023-06-09 00:00:00 UTC")
    ORDER BY t.utc_datetime DESC
    LIMIT 1000;
    """

    df = bq.query(query=query, as_dataframe=True)

    df["price_increase"] = (df["close"] > df["open"]).astype(int)

    pprint(df.head())

    features = [
        "open",
        "high",
        "low",
        "volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
    ]
    X = df[features]
    y = df["price_increase"]
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pprint(X_train.shape)
    pprint(X_test.shape)
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    from sklearn.metrics import accuracy_score

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"Accuracy: {accuracy}")

    # save model to outputs folder
    joblib.dump(model, f"{STORES_DIR}/model.joblib")


if __name__ == "__main__":
    preprocess(
        project_id=PROJECT_ID,
        google_application_credentials=GOOGLE_APPLICATION_CREDENTIALS,
        dataset="mlops_pipeline_v1",
        table_name="processed_binance_btcusdt_spot",
    )
