import os
import time
from datetime import datetime
from typing import List

import pandas as pd
import pytz
import rich
from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from common_utils.core.common import get_root_dir, load_env_vars
from common_utils.core.logger import Logger
from google.cloud import bigquery
from hydra import compose, initialize
from pathlib import Path
from omegaconf import DictConfig
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from rich.pretty import pprint

from mlops_pipeline_feature_v1 import extract
from mlops_pipeline_feature_v1.utils import interval_to_milliseconds

# TODO: add logger to my common_utils
# TODO: add transforms to elt like dbt and great expectations
# TODO: add tests
# TODO: split to multiple files
# Set environment variables.

ROOT_DIR = get_root_dir(env_var="ROOT_DIR", root_dir=".")
pprint(ROOT_DIR)
os.environ["ROOT_DIR"] = str(ROOT_DIR)
load_env_vars(root_dir=ROOT_DIR)
PROJECT_ID = os.getenv("PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")
rich.print(PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, BUCKET_NAME)

Path(f"{ROOT_DIR}/outputs/mlops_pipeline_feature_v1").mkdir(parents=True, exist_ok=True)


# Setup logging
# so if you are in docker, then ROOT_DIR = opt/airflow
# but i overwrite to become     ROOT_DIR: ${ROOT_DIR:-/opt/airflow/dags}
logger = Logger(
    log_file="mlops_pipeline_feature_v1.log",
    log_dir=f"{ROOT_DIR}/outputs/mlops_pipeline_feature_v1",
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


def generate_bq_schema_from_pandas(df: pd.DataFrame) -> List[bigquery.SchemaField]:
    """
    Convert pandas dtypes to BigQuery dtypes.

    Parameters
    ----------
    dtypes : pandas Series
        The pandas dtypes to convert.

    Returns
    -------
    List[google.cloud.bigquery.SchemaField]
        The corresponding BigQuery dtypes.
    """
    dtype_mapping = {
        "int64": bigquery.enums.SqlTypeNames.INT64,
        "float64": bigquery.enums.SqlTypeNames.FLOAT64,
        "object": bigquery.enums.SqlTypeNames.STRING,
        "bool": bigquery.enums.SqlTypeNames.BOOL,
        "datetime64[ns]": bigquery.enums.SqlTypeNames.DATETIME,
    }

    schema = []

    for column, dtype in df.dtypes.items():
        if str(dtype) not in dtype_mapping:
            raise ValueError(f"Cannot convert {dtype} to a BigQuery data type.")

        bq_dtype = dtype_mapping[str(dtype)]
        field = bigquery.SchemaField(name=column, field_type=bq_dtype, mode="NULLABLE")
        schema.append(field)

    return schema


class Metadata(BaseModel):
    updated_at: datetime = datetime.now(pytz.timezone("Asia/Singapore"))
    source: str = "binance"
    source_type: str = "spot"


def update_metadata(df, metadata: Metadata):
    """Updates the DataFrame with metadata information."""
    for key, value in metadata.dict().items():
        df[key] = value
    return df


def upload_latest_data(
    symbol: str,
    interval: str,
    project_id: str,
    google_application_credentials: str,
    bucket_name: str = None,
    table_name: str = None,  # for example bigquery table id
    dataset: str = None,  # for example bigquery dataset
    start_time: int = None,
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
        table_name=table_name,
    )

    # flag to check if dataset exists
    dataset_exists = bq.check_if_dataset_exists()

    # flag to check if table exists
    table_exists = bq.check_if_table_exists()

    # if dataset or table does not exist, create them
    if not dataset_exists or not table_exists:
        logger.warning("Dataset or table does not exist. Creating them now...")
        assert (
            start_time is not None
        ), "start_time must be provided to create dataset and table"

        sgt = pytz.timezone("Asia/Singapore")
        time_now = int(datetime.now(sgt).timestamp() * 1000)

        df, metadata = extract.from_api(
            symbol=symbol,
            start_time=start_time,
            end_time=time_now,
            interval=interval,
            limit=1000,
            base_url="https://api.binance.com",
            endpoint="/api/v3/klines",
        )
        metadata = Metadata()
        df = update_metadata(df, metadata)
        pprint(df)

        updated_at = df["updated_at"].iloc[0]
        blob = gcs.create_blob(f"{dataset}/{table_name}/{updated_at}.csv")

        blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
        logger.info(f"File {blob.name} uploaded to {bucket_name}.")

        schema = generate_bq_schema_from_pandas(df)
        pprint(schema)

        bq.create_dataset()
        bq.create_table(schema=schema)  # empty table with schema
        job_config = bq.load_job_config(schema=schema, write_disposition="WRITE_APPEND")
        bq.load_table_from_dataframe(df=df, job_config=job_config)
    else:
        logger.info("Dataset and table already exist. Fetching the latest date now...")

        # Query to find the maximum open_date
        query = f"""
        SELECT MAX(open_time) as max_open_time
        FROM `{bq.table_id}`
        """
        max_date_result: pd.DataFrame = bq.query(query, as_dataframe=True)
        pprint(max_date_result)
        max_open_time = max(max_date_result["max_open_time"])
        pprint(max_open_time)

        # now max_open_time is your new start_time
        start_time = max_open_time + interval_to_milliseconds(interval)
        print(f"start_time={start_time}")

        # Get the timezone for Singapore
        sgt = pytz.timezone("Asia/Singapore")
        time_now = int(datetime.now(sgt).timestamp() * 1000)
        print(f"time_now={time_now}")

        # only pull data from start_time onwards, which is the latest date in the table
        df, metadata = extract.from_api(
            symbol="BTCUSDT",
            start_time=start_time,
            end_time=time_now,
            interval="1m",
            limit=1000,
            base_url="https://api.binance.com",
            endpoint="/api/v3/klines",
        )
        print("df.head()", df.head())

        metadata = Metadata()
        df = update_metadata(df, metadata)
        updated_at = df["updated_at"].iloc[0]
        blob = gcs.create_blob(f"{dataset}/{table_name}/{updated_at}.csv")
        blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
        logger.info(f"File {blob.name} uploaded to {bucket_name}.")

        # Append the new data to the existing table
        job_config = bq.load_job_config(write_disposition="WRITE_APPEND")
        bq.load_table_from_dataframe(df=df, job_config=job_config)


def run():
    start_time = int(datetime(2023, 6, 1, 20, 0, 0).timestamp() * 1000)

    upload_latest_data(
        "BTCUSDT",  # "ETHUSDT
        "1m",
        PROJECT_ID,
        GOOGLE_APPLICATION_CREDENTIALS,
        BUCKET_NAME,
        dataset="mlops_pipeline_v1_staging",
        table_name="binance_btcusdt_spot",
        start_time=start_time,
    )


if __name__ == "__main__":
    # eg: int(datetime(2023, 6, 1, 8, 0, 0).timestamp() * 1000)
    run()
