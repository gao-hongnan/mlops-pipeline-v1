# Airflow Pipeline

See article, the `.env` file in `airflow/` contains `AIRFLOW_UID` and `ROOT_DIR` for airflow.
The `.env` file in `airflow/dags/` will contain credentials.

For now no Dockerfile needed and if need is for mount output folder?

- bash pypi.sh # to change name so that it is pushed and airflow can directly install it in the vm.
- This step is impt, see deploy/.. in paul.
- Think the `output` folder paul created is to solve the airflow transfer of data problem.

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