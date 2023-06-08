# Airflow Pipeline

See article, the `.env` file in `airflow/` contains `AIRFLOW_UID` and `ROOT_DIR` for airflow.
The `.env` file in `airflow/dags/` will contain credentials.

For now no Dockerfile needed and if need is for mount output folder?

- bash pypi.sh # to change name so that it is pushed and airflow can directly install it in the vm.
- This step is impt, see deploy/.. in paul.
- Think the `output` folder paul created is to solve the airflow transfer of data problem.
- Find out how to redeploy pypi package and airflow pipeline in CICD.

    ```bash
    docker compose down && \
    docker compose up airflow-init && \
    docker compose --env-file .env up --build -d
    ```

    This automates build and push?

In Airflow, Dags are triggered according to their schedule by default. If you have set a schedule in your Dag definition like "*/10 * * * *", then Airflow scheduler should automatically trigger your Dag every 10 minutes. You do not need to manually trigger it each time you update your Dag.

However, if you want to trigger a Dag run immediately after updating your Dag, there are a few ways to do this:

Airflow CLI: You can use Airflow's command line interface (CLI) to trigger a Dag. After updating your Dag and restarting your Airflow services, you can run a command like airflow dags trigger mlops_pipeline_v1 to trigger your Dag. This can be part of your automation script that runs after your CI/CD pipeline.

Airflow REST API: Airflow also provides a REST API that you can use to trigger a Dag run. You can make a POST request to the /api/v1/dags/{dag_id}/dagRuns endpoint to trigger a Dag. This can also be part of your automation script.

Airflow Python Client: If you have a Python script running in your environment that can communicate with your Airflow instance, you can use the Airflow Python client to trigger a Dag. The airflow-client-python package provides a simple way to interact with Airflow using Python.

Remember, all these methods require your Airflow instance to be up and running. When you make changes to your Dag, you need to ensure that your Airflow services (specifically the webserver and scheduler) are restarted to pick up the changes.

Please note that the approach you choose depends on your specific setup and requirements. If your Dags are scheduled to run frequently (e.g., every 10 minutes), you may not need to manually trigger them after each update. The scheduler will automatically trigger the Dag runs according to the schedule.

## Commands

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.6.1/docker-compose.yaml'
mkdir -p ./dags ./logs ./plugins ./config
mkdir -p ./dags/credentials
cp GCP-credentials.json ./dags/credentials/
touch ./dags/.gitingore
echo "# Ignore everything in this directory
*
# Except this file
!.gitignore" > ./dags/.gitignore

touch ./dags/__init__.py ./dags/pipeline_dag.py
cat python code to ./dags/pipeline_dag.py


echo -e "AIRFLOW_UID=$(id -u)" > .env # if linux else macos is 50000 default
# FOR MACOS AIRFLOW_UID=50000 # FOR LINUX AIRFLOW_UID=$(id -u)
echo "ROOT_DIR=/opt/airflow/dags" >> .env
# UPDATE .env with my local .env
echo "credentials" >> ./dags/.env # TO REPLACE
sudo chmod 777 ./logs ./plugins
echo env ROOT_DIR: ${ROOT_DIR:-/opt/airflow/dags} to docker-compose.yaml # TODO: check if AIRFLOW_PROJ_DIR is the same as ROOT_DIR if yes then remove ROOT_DIR

# TODO: AIRFLOW__CORE__LOAD_EXAMPLES: 'false' # to remove example dags
# Initialize the Airflow database
docker compose up airflow-init

# Start Airflow
airflow/ $ docker compose --env-file .env up --build -d
```

```
docker compose down && \
docker compose up airflow-init && \
docker compose --env-file .env up --build -d
```

# GCP STEPS

gcloud compute firewall-rules create mlops-pipeline-v1-expose-ports \
    --allow tcp:8501,tcp:8502,tcp:8001,tcp:8000,tcp:8080,tcp:5000 \
    --target-tags=mlops-pipeline-v1-expose-ports \
    --description="Firewall rule to expose ports for energy forecasting" \
    --project=gao-hongnan

gcloud compute firewall-rules create iap-tcp-tunneling \
    --allow tcp:22 \
    --target-service-accounts=gcp-storage-service-account@gao-hongnan.iam.gserviceaccount.com \
    --source-ranges=35.235.240.0/20 \
    --description="Firewall rule to allow IAP TCP tunneling" \
    --project=gao-hongnan

source /Users/gaohn/gaohn/common-utils/scripts/cloud/gcp/gcloud_functions.sh

vm_create --instance-name mlops-pipeline-v1 \
    --machine-type e2-standard-4 \
    --zone asia-southeast1-a \
    --boot-disk-size 30GB \
    --image ubuntu-1804-bionic-v20230510 \
    --image-project ubuntu-os-cloud \
    --project gao-hongnan \
    --service-account gcp-storage-service-account@gao-hongnan.iam.gserviceaccount.com \
    --scopes https://www.googleapis.com/auth/cloud-platform \
    --description "MLOps Pipeline V1 VM instance" \
    --additional-flags --tags=http-server,https-server,iap-tcp-tunneling,mlops-pipeline-v1-expose-ports

- SSH into VM

```bash
gcloud compute ssh \
    mlops-pipeline-v1 \
    --project=gao-hongnan \
    --zone=asia-southeast1-a \
    --tunnel-through-iap \
    --quiet
```

- Setup docker in VM
- SUDO DOCKER

```bash
sudo usermod -aG docker $USER && \
logout
```
if dont logout then run `newgrp docker` to apply changes?

```bash
git clone https://github.com/gao-hongnan/common-utils.git && \
cd common-utils/scripts/containerization/docker && \
bash docker_setup.sh && \
sudo usermod -aG docker $USER && \
newgrp docker

```

- Git clone repo

    ```bash
    cd ~ && \
    git clone https://github.com/gao-hongnan/mlops-pipeline-v1.git && \
    cd mlops-pipeline-v1
    # git checkout dev
    ```

- mkdir credentials if not exist

    ```bash
    mkdir -p airflow/dags/credentials
    ```

- send gcp json to vm

    ```bash
    $ local terminal
    gcloud compute scp --recurse \
        --zone asia-southeast1-a \
        --quiet \
        --tunnel-through-iap \
        --project gao-hongnan \
        /Users/gaohn/gcp-storage-service-account.json \
        mlops-pipeline-v1:~/mlops-pipeline-v1/airflow/dags/credentials/
    ```

    ```bash
    # from airflow/
    gcloud compute scp --recurse \
        --zone asia-southeast1-a \
        --quiet \
        --tunnel-through-iap \
        --project gao-hongnan \
        .env \
        mlops-pipeline-v1:~/mlops-pipeline-v1/airflow/.env

    gcloud compute scp --recurse \
        --zone asia-southeast1-a \
        --quiet \
        --tunnel-through-iap \
        --project gao-hongnan \
        ./dags/.env \
        mlops-pipeline-v1:~/mlops-pipeline-v1/airflow/dags/.env
    ```


- run Airflow Pipeline above

```bash
airflow $
cd ~/mlops-pipeline-v1/airflow && \
docker compose up airflow-init && \
docker compose --env-file .env up --build -d
```

the steps above is explained below:

```
# Initialize the Airflow database
docker compose up airflow-init

# Start up all services
# Note: You should set up the private PyPi server credentials before running this command.
docker compose --env-file .env up --build -d
```

- This means Airflow UI is accessible at http://34.143.176.217:8080

## Flow

> You need to setup the docker steps above manually for the first time. Can we automate the above as well
    by pushing a docker image to GCP and then run it in the VM?

> For now I will ssh in and update packages and dags from github actions cicd.

I deployed my airflow server to a GCP VM instance in detached mode so it is running there under an external IP Address.
The airflow pipeline orchestrates the following steps:

- Feature Pipeline
    - Extract
    - Load
    - Transform
- Model Pipeline
    - Train
    - Evaluate
    - Validate
- Deploy Pipeline
    - Deploy
    - Predict
    - Monitor

So intuitively, airflow is in itself a CICD pipeline that orchestrates the above steps because
i fetch data daily for retraining and comparing with previous model performance. If the new model is better, then i deploy it to production.

What I need help is the "correct" and industry way of deploying my airflow pipeline to production.
Currently, I am referring to a similar repo doing:

```yaml
jobs:
  ci_cd:
    runs-on: ubuntu-latest
    steps:
      - uses: 'actions/checkout@v3'

      - id: 'auth'
        uses: 'google-github-actions/auth@v0'
        with:
          credentials_json: '${{ secrets.GCP_CREDENTIALS }}'
      - id: 'compute-ssh'
        uses: 'google-github-actions/ssh-compute@v0'
        with:
          project_id: '${{ env.CLOUDSDK_CORE_PROJECT }}'
          user: '${{ env.USER }}'
          instance_name: '${{ env.INSTANCE_NAME }}'
          zone: '${{ env.ZONE }}'
          ssh_private_key: '${{ secrets.GCP_SSH_PRIVATE_KEY }}'
          command: >
            cd ~/energy-forecasting &&
            git pull &&
            sh deploy/ml-pipeline.sh
```

where `ml-pipeline.sh` is

```bash
#!/bin/bash

# Build and publish the feature-pipeline, training-pipeline, and batch-prediction-pipeline packages.
# This is done so that the pipelines can be run from the CLI.
# The pipelines are executed in the feature-pipeline, training-pipeline, and batch-prediction-pipeline
# directories, so we must change directories before building and publishing the packages.
# The my-pypi repository must be defined in the project's poetry.toml file.

cd feature-pipeline
poetry build
poetry publish -r my-pypi

cd ../training-pipeline
poetry build
poetry publish -r my-pypi

cd ../batch-prediction-pipeline
poetry build
poetry publish -r my-pypi
```

What these steps do is to build and publish the feature-pipeline, training-pipeline, and batch-prediction-pipeline packages to my private pypi server.
But I do not understand what he is trying to do. I do know that his airflow dags needs to
install the packages from the private pypi server. But I do not understand why he needs to build and publish the packages to the private pypi server.