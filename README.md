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
````

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

## SSH

We create a new ssh key for this project to interact with GCP VM. We will make
it passwordless for convenience.

```bash
ssh-keygen -t rsa -f ~/.ssh/<SSH-FILE-NAME> -C "<USERNAME>"
```

A concrete implementation is as follows:

```bash
ssh-keygen -t rsa -f ~/.ssh/mlops-pipeline-v1 -C "gaohn"
```

And then in to ssh into the VM, we need to add the ssh key to the VM.

```bash
ssh <USERNAME>@<EXTERNAL-IP-ADDRESS>
```

and once in the VM, we need to add the ssh key to the VM.

```bash
cd ~/.ssh
```

Open the `authorized_keys` file and paste the public key in.

```bash
nano authorized_keys
```

Back on your local machine, open the `gcp_vm_no_passphrase.pub` file in a text
editor and copy its content.

Paste the content into the `authorized_keys` file on the VM.

Now one can ssh into the VM without password.

```bash
ssh -i ~/.ssh/<SSH-FILE-NAME> <USERNAME>@<EXTERNAL-IP-ADDRESS>
```

And to use the private ssh keys in github actions, we need to add the private
key to github secrets.

```bash
cat ~/.ssh/<SSH-FILE-NAME> | gh secret set <SSH-FILE-NAME> -b-
```


## DevOps (Continuous Integration (CI) Workflow in Machine Learning)

Find time to implement CI pipeline for this project. Reference
`pre-merge-checks`.

In a typical Machine Learning (ML) CI workflow, several stages are included.

### Code Formatting

For code formatting, you can use tools like
[black](https://black.readthedocs.io/). Black enforces a consistent code style
to make the codebase easier to read and understand.

### Linting

Linting tools like [pylint](https://www.pylint.org/) can be used to check your
code for potential errors and enforce a coding standard.

### Unit Testing

Unit testing frameworks like [pytest](https://docs.pytest.org/) can be used to
write tests that check the functionality of individual pieces of your code.

### Static Type Checking

Static type checkers like [mypy](http://mypy-lang.org/) can be used to perform
static type analysis on your code. This helps catch certain kinds of errors
before runtime.

### Integration Testing

Integration tests look at how different parts of your system work together.
These might be particularly important for ML workflows, where data pipelines,
training scripts, and evaluation scripts all need to interact smoothly.

### System Testing

System testing falls within the scope of black-box testing, and as such, should
require no knowledge of the inner design of the code or logic.

In a machine learning context, system testing might involve running the entire
machine learning pipeline with a predefined dataset and checking if the output
is as expected. You would typically look to see if the entire system, when run
end-to-end, produces the expected results, given a specific input. This could
involve evaluating overall system performance, checking the quality of the
predictions, and validating that the system meets all the specified
requirements.

## Performance Testing/Benchmarking

Track the performance of your models or certain parts of your code over time.
This could involve running certain benchmarks as part of your CI pipeline and
tracking the results.

### Model Validation

Depending on your workflow, you might want to have a stage that validates your
models, checking things like model performance metrics (accuracy, AUC-ROC, etc.)
to ensure they meet a certain threshold.

### Security Checks

Tools like [bandit](https://bandit.readthedocs.io/) can be used to find common
security issues in your Python code.

### Code Complexity Measurement

Tools like [radon](https://radon.readthedocs.io/) can give you metrics about how
complex your codebase is. This can help keep complexity down as the project
grows.

### Documentation Building and Testing

If you have auto-generated documentation, you might have a CI step to build and
test this documentation. Tools like [sphinx](https://www.sphinx-doc.org/) can
help with this.


