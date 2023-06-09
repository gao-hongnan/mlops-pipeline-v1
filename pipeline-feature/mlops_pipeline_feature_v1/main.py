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
from omegaconf import OmegaConf

from common_utils.cloud.gcp.storage.bigquery import BigQuery
from common_utils.cloud.gcp.storage.gcs import GCS
from common_utils.core.logger import Logger
from dotenv import load_dotenv
from hydra import compose, initialize

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
# logger = Logger(
#     log_file="mlops_pipeline_feature_v1.log",
#     log_dir="../outputs/mlops_pipeline_feature_v1",
# ).logger


def run() -> DictConfig:
    initialize(config_path="../conf", version_base=None)
    cfg: DictConfig = compose(
        config_name="base",
        overrides=["extract.start_time=1685620800000"],
        return_hydra_config=True,
    )

    pprint(cfg.extract)
    pprint(cfg.general.start_time)

    # print(OmegaConf.to_yaml(cfg, resolve=True))
    return cfg


if __name__ == "__main__":
    run()
