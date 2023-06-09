"""Technically, this is a load and transform module.
In airbyte lingo, it is tweak and load where you add some metadata to the data
before loading it to the destination."""
from datetime import datetime
from typing import List, Optional

import pandas as pd
import pytz
from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from google.cloud import bigquery, storage
from pydantic import BaseModel  # pylint: disable=no-name-in-module


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
        "datetime64[ns, Asia/Singapore]": bigquery.enums.SqlTypeNames.DATETIME,
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


def to_google_cloud_storage(
    df: pd.DataFrame, gcs: GCS, dataset: str, table_name: str, updated_at: str
) -> storage.Blob:
    blob = gcs.create_blob(f"{dataset}/{table_name}/{updated_at}.csv")
    blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
    return blob


def to_bigquery(
    df: pd.DataFrame,
    bq: BigQuery,
    write_disposition: str = "WRITE_APPEND",
    schema: Optional[List[bigquery.SchemaField]] = None,
) -> None:
    job_config = bq.load_job_config(schema=schema, write_disposition=write_disposition)
    bq.load_table_from_dataframe(df=df, job_config=job_config)
