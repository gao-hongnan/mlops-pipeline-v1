import os
import time
from datetime import datetime
from pathlib import Path

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
from dotenv import load_dotenv

# TODO: add logger to my common_utils
# TODO: add transforms to elt like dbt and great expectations
# TODO: add tests
# TODO: split to multiple files
# Set environment variables.

DOCKER = True

ROOT_DIR = get_root_dir(env_var="ROOT_DIR", root_dir=".")
pprint(ROOT_DIR)
os.environ["ROOT_DIR"] = str(ROOT_DIR)
if DOCKER:
    # Load environment variables from .env file
    load_dotenv("/gaohn/.env.docker")
else:
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
    log_dir=f"{OUTPUTS_DIR}/logs",
    # log_dir=None,
).logger

DEBUG = False

if DEBUG:
    time.sleep(600)


def load_configs() -> DictConfig:
    initialize(config_path="../conf", version_base=None)
    cfg: DictConfig = compose(
        config_name="base",
        overrides=["extract.start_time=1685620800000"],
        return_hydra_config=True,
    )
    pprint(cfg)
    pprint(cfg.extract)
    pprint(cfg.general.start_time)

    # print(OmegaConf.to_yaml(cfg, resolve=True))
    return cfg


def pipeline(
    symbol: str,
    start_time: int,
    interval: str = "1m",
    limit: int = 1000,
    base_url: str = "https://api.binance.com",
    endpoint: str = "/api/v3/klines",
    project_id: str = PROJECT_ID,
    google_application_credentials: str = GOOGLE_APPLICATION_CREDENTIALS,
    bucket_name: str = None,
    dataset: str = None,  # for example bigquery dataset
    raw_table_name: str = None,  # for example bigquery table id
    processed_table_name: str = None,  # for example bigquery table id
):
    gcs = GCS(
        project_id=project_id,
        google_application_credentials=google_application_credentials,
        bucket_name=bucket_name,
    )
    bucket_exists = gcs.check_if_bucket_exists()
    if not bucket_exists:
        gcs.create_bucket()

    bq = BigQuery(
        project_id=project_id,
        google_application_credentials=google_application_credentials,
        dataset=dataset,
        table_name=raw_table_name,
    )

    # flag to check if dataset exists
    dataset_exists = bq.check_if_dataset_exists()

    # flag to check if table exists
    table_exists = bq.check_if_table_exists()

    metadata = load.Metadata()
    updated_at = metadata.updated_at

    # if dataset or table does not exist, create them
    if not dataset_exists or not table_exists:
        logger.warning("Dataset or table does not exist. Creating them now...")
        assert (
            start_time is not None
        ), "start_time must be provided to create dataset and table"

        sgt = pytz.timezone("Asia/Singapore")
        time_now = int(datetime.now(sgt).timestamp() * 1000)

        df, _ = extract.from_api(
            symbol=symbol,
            start_time=start_time,
            end_time=time_now,
            interval=interval,
            limit=limit,
            base_url=base_url,
            endpoint=endpoint,
        )

        df = load.update_metadata(df, metadata)

        blob = load.to_google_cloud_storage(
            df,
            gcs=gcs,
            dataset=dataset,
            table_name=raw_table_name,
            updated_at=updated_at,
        )
        logger.info(f"File {blob.name} uploaded to {bucket_name}.")

        schema = load.generate_bq_schema_from_pandas(df)
        pprint(schema)

        if not dataset_exists:
            bq.create_dataset()

        if not table_exists:
            bq.create_table(schema=schema)

        load.to_bigquery(df, bq=bq, write_disposition="WRITE_APPEND", schema=schema)
    else:
        logger.info("Dataset and table already exist. Fetching the latest date now...")

        # Query to find the maximum open_date
        query = f"""
        SELECT MAX(open_time) as max_open_time
        FROM `{bq.table_id}`
        """
        max_date_result: pd.DataFrame = bq.query(query, as_dataframe=True)
        max_open_time = max(max_date_result["max_open_time"])

        # now max_open_time is your new start_time
        start_time = max_open_time + interval_to_milliseconds(interval)

        # Get the timezone for Singapore
        sgt = pytz.timezone("Asia/Singapore")
        time_now = int(datetime.now(sgt).timestamp() * 1000)

        # only pull data from start_time onwards, which is the latest date in the table
        df, _ = extract.from_api(
            symbol=symbol,
            start_time=start_time,
            end_time=time_now,
            interval=interval,
            limit=limit,
            base_url=base_url,
            endpoint=endpoint,
        )

        df = load.update_metadata(df, metadata)
        blob = load.to_google_cloud_storage(
            df,
            gcs=gcs,
            dataset=dataset,
            table_name=raw_table_name,
            updated_at=updated_at,
        )
        logger.info(f"File {blob.name} uploaded to {bucket_name}.")

        # Append the new data to the existing table
        load.to_bigquery(df, bq=bq, write_disposition="WRITE_APPEND")

    transformed_df = transform.cast_columns(df)
    blob = load.to_google_cloud_storage(
        transformed_df,
        gcs=gcs,
        dataset=dataset,
        table_name=processed_table_name,
        updated_at=updated_at,
    )
    logger.info(f"File {blob.name} uploaded to {bucket_name}.")
    schema = load.generate_bq_schema_from_pandas(transformed_df)
    pprint(schema)
    bq.table_name = processed_table_name

    if not bq.check_if_table_exists():
        bq.create_table(schema=schema)
    load.to_bigquery(transformed_df, bq=bq, write_disposition="WRITE_APPEND")


def run():
    # eg: int(datetime(2023, 6, 1, 8, 0, 0).timestamp() * 1000)
    start_time = int(datetime(2023, 6, 1, 20, 0, 0).timestamp() * 1000)

    pipeline(
        symbol="BTCUSDT",  # "ETHUSDT
        start_time=start_time,
        interval="1m",
        limit=1000,
        base_url="https://api.binance.com",
        endpoint="/api/v3/klines",
        project_id=PROJECT_ID,
        google_application_credentials=GOOGLE_APPLICATION_CREDENTIALS,
        bucket_name=BUCKET_NAME,
        dataset="mlops_pipeline_v1_staging",
        raw_table_name="raw_binance_btcusdt_spot",
        processed_table_name="processed_binance_btcusdt_spot",
    )


if __name__ == "__main__":
    run()
