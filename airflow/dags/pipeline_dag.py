from datetime import datetime

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.edgemodifier import Label

# Variable.set("ml_pipeline_feature_group_version", "5")
# Variable.set("ml_pipeline_days_export", "30")
# Variable.set("ml_pipeline_should_run_hyperparameter_tuning", False)


@dag(
    dag_id="mlops_pipeline_v1",
    schedule="@hourly",
    start_date=datetime(2023, 6, 1),  # year, month, day
    catchup=False,  # catchup=False, # set to False to disable backfill
    tags=["pipeline-feature", "pipeline-training", "pipeline-serving"],
    max_active_runs=1,
)
def ml_pipeline():
    @task.virtualenv(
        task_id="run_feature_pipeline",
        requirements=["pipeline-feature==0.0.2"],
        python_version="3.9",
        multiple_outputs=True,
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

        from datetime import datetime

        from mlops_pipeline_feature_v1 import pipeline

        pipeline.run()
