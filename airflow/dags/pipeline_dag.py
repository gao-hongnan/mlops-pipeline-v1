# pylint: disable=unused-import,no-name-in-module
from datetime import datetime

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.edgemodifier import Label
from airflow.utils.trigger_rule import TriggerRule

# Variable.set("ml_pipeline_feature_group_version", "5")
# Variable.set("ml_pipeline_days_export", "30")
# Variable.set("ml_pipeline_should_run_hyperparameter_tuning", False)
# pylint: disable=import-outside-toplevel


@dag(
    dag_id="mlops_pipeline_v1",
    # every 10 minutes = "*/10 * * * *", hourly = "@hourly", daily = "@daily"
    schedule="*/10 * * * *",
    start_date=datetime(2023, 6, 1),  # year, month, day
    catchup=False,  # catchup=False, # set to False to disable backfill
    tags=["pipeline-feature", "pipeline-training", "pipeline-serving"],
    max_active_runs=1,
)
def ml_pipeline():
    @task.virtualenv(
        task_id="run_feature_pipeline",
        requirements=["pipeline-feature"],
        python_version="3.9",
        multiple_outputs=True,  # FIXME: multiple_outputs=True means must return a dict.
        system_site_packages=True,
    )
    def run_feature_pipeline() -> dict:
        """
        Run the feature pipeline.

        Args:
            export_end_reference_datetime: The end reference datetime of the export window. If None, the current time is used.
                Because the data is always delayed with "days_delay" days, this date is used only as a reference point.
                The real extracted window will be computed as [export_end_reference_datetime - days_delay - days_export, export_end_reference_datetime - days_delay].

            days_delay : int
                Data has a delay of N days. Thus, we have to shift our window with N days.

            days_export : int
                The number of days to export.

            url : str
                URL to the raw data.

            feature_group_version : int
                Version of the feature store feature group to use.

        Returns:
            Metadata of the feature pipeline run.
        """
        from mlops_pipeline_feature_v1 import pipeline

        cfg = pipeline.load_configs()

        pipeline.run()
        return {"feature_pipeline_run_id": "123"}

    dummy_task = DummyOperator(task_id="dummy_task")

    # define DAG, empty operator is a dummy operator
    run_feature_pipeline() >> dummy_task


ml_pipeline_dag = ml_pipeline()
