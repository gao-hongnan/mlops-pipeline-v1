from hydra import compose, initialize
from omegaconf import DictConfig
from rich.pretty import pprint

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
