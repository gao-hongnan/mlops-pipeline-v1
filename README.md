# MLOps Pipeline v1


> Have major problems setting default google ssh keys, so create your own and
> link to gcp vm.

```bash
# Define the paths and secret names
ENV_FILE_PATH=".env"
GOOGLE_APPLICATION_CREDENTIALS_JSON="GOOGLE_APPLICATION_CREDENTIALS_JSON"
GOOGLE_COMPUTE_ENGINE_SSH_KEY_PATH="~/.ssh/google_compute_engine"
GOOGLE_COMPUTE_ENGINE_SSH_KEY_VALUE="GCP_SSH_PRIVATE_KEY"

# Load the environment variables from the .env file
export $(grep -v '^#' $ENV_FILE_PATH | xargs)

# Use jq to format the JSON file pointed to by the environment variable, and pipe this into gh secret set
jq -c . "${GOOGLE_APPLICATION_CREDENTIALS}" | gh secret set $GOOGLE_APPLICATION_CREDENTIALS_JSON -b-

# Read the file content and pipe it into gh secret set
cat $GOOGLE_COMPUTE_ENGINE_SSH_KEY_PATH | gh secret set $GOOGLE_COMPUTE_ENGINE_SSH_KEY_VALUE -b-
```

## Problem Statement

Dummy prediction: use some features to predict `num_of_trades`.

## Docker

```bash
docker compose --env-file .env.docker down && \
# docker rmi $(docker images -q) && \
docker compose --env-file .env.docker up --build -d
```

```bash
docker exec -it mlops-pipeline-v1 /bin/bash
```

```bash
cat /var/log/cron.log
```

## DevOps (Continuous Integration (CI) Workflow in Machine Learning)

Find time to implement CI pipeline for this project. Reference
`pre-merge-checks`.

In a typical Machine Learning (ML) CI workflow, several stages are included.



