import hydra
from omegaconf import DictConfig
import os
from datetime import datetime
from pathlib import Path
from typing import List

import hydra
import pandas as pd
import pytz
import rich
from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from common_utils.core.logger import Logger
from dotenv import load_dotenv

from google.cloud import bigquery
from omegaconf import DictConfig
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from rich.pretty import pprint

from extract import extract_from_api
from utils import interval_to_milliseconds
from hydra.core.hydra_config import HydraConfig

# TODO: add logger to my common_utils
# TODO: add transforms to elt like dbt and great expectations
# TODO: add tests
# TODO: split to multiple files

# Setup logging
logger = Logger(
    log_file="mlops_pipeline_feature_v1.log",
    log_dir="../outputs/mlops_pipeline_feature_v1",
).logger


@hydra.main(config_path="../conf", config_name="base", version_base=None)
def my_app(cfg: DictConfig) -> None:
    output_dir = HydraConfig.get().runtime.output_dir

    logger.info(f"Output dir: {output_dir}")
    pprint(cfg.extract)
    pprint(cfg.general)


if __name__ == "__main__":
    my_app()
