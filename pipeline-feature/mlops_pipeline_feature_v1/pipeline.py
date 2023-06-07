import logging
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import pytz
import requests
import rich
from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from dotenv import load_dotenv
from google.cloud import bigquery
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from rich.logging import RichHandler
from rich.pretty import pprint

# TODO: add logger to my common_utils
# TODO: add transforms to elt like dbt and great expectations
# TODO: add tests
# TODO: split to multiple files

# Setup logging
logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger("rich")

# Set environment variables.
if os.getenv("ROOT_DIR") is None:
    ROOT_DIR = str(Path.cwd().parent.parent)
    os.environ["ROOT_DIR"] = ROOT_DIR
    print(f"ROOT_DIR: {ROOT_DIR}")
else:
    print(
        "ROOT_DIR is already set. Likely in Docker since Environment is set in compose file."
    )
    ROOT_DIR = Path(os.getenv("ROOT_DIR"))
    print(f"ROOT_DIR: {ROOT_DIR}")

load_dotenv(dotenv_path=f"{ROOT_DIR}/.env")

PROJECT_ID = os.getenv("PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")
rich.print(PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, BUCKET_NAME)

# gcs = GCS(PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS, bucket_name=BUCKET_NAME)
# files = gcs.list_gcs_files()

# rich.print(files)


def interval_to_milliseconds(interval: str) -> int:
    if interval.endswith("m"):
        return int(interval[:-1]) * 60 * 1000
    elif interval.endswith("h"):
        return int(interval[:-1]) * 60 * 60 * 1000
    elif interval.endswith("d"):
        return int(interval[:-1]) * 24 * 60 * 60 * 1000
    else:
        raise ValueError(f"Invalid interval format: {interval}")


def get_binance_data(
    symbol: str,
    start_time: int,
    end_time: Optional[int] = None,
    interval: str = "1m",
    limit: int = 1000,
) -> pd.DataFrame:
    base_url = "https://api.binance.com"
    endpoint = "/api/v3/klines"
    url = base_url + endpoint
    # Convert interval to milliseconds
    interval_in_milliseconds = interval_to_milliseconds(interval)

    time_range = end_time - start_time  # total time range
    pprint(f"time_range: {time_range}")
    request_max = limit * interval_in_milliseconds
    pprint(f"request_max: {request_max}")

    start_iteration = start_time
    end_iteration = start_time + request_max

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": start_time,
    }

    if end_time is not None:
        params["endTime"] = end_time

    response_columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]

    if time_range <= request_max:  # time range selected within 1000 rows limit
        resp = requests.get(url=url, params=params, timeout=30)
        data = resp.json()
        df = pd.DataFrame(data, columns=response_columns)

        time.sleep(1)

    elif (
        time_range > request_max
    ):  # start_time and end_time selected > limit rows of data
        df = pd.DataFrame()  # empty dataframe to append to
        num_iterations = math.ceil(time_range / request_max)  # number of loops required
        pprint(f"num_iterations: {num_iterations}")

        for _ in range(num_iterations):
            # make request with updated params
            resp = requests.get(url=url, params=params, timeout=30)
            data = resp.json()
            _df = pd.DataFrame(data, columns=response_columns)

            df = pd.concat([df, _df])

            start_iteration = end_iteration
            end_iteration = min(
                end_iteration + request_max, end_time
            )  # don't go beyond the actual end time
            # adjust params

            params["startTime"], params["endTime"] = (
                start_iteration,
                end_iteration,
            )  # adjust params
            time.sleep(1)

    df.insert(0, "utc_datetime", pd.to_datetime(df["open_time"], unit="ms"))
    return df


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

        df = get_binance_data(
            symbol=symbol,
            start_time=start_time,
            end_time=time_now,
            interval=interval,
            limit=1000,
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
        df = get_binance_data(
            symbol="BTCUSDT",
            start_time=start_time,
            end_time=time_now,
            interval="1m",
            limit=1000,
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
