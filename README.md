# MLOps Pipeline v1

## Problem Statement

Dummy prediction: use some features to predict `num_of_trades`.

## DataOPs

- Extract data from source
- Load to staging GCS
    - The format is `dataset/table_name/created_at=YYYY-MM-DD:HH:MM:SS:MS` so that we
    can always find out which csv corresponds to which date in bigquery.
- Load to staging BigQuery
    - Write and Append mode! Incremental refresh
    - Added metadata such as `created_at` and `updated_at`
    - Bigquery has not so good primary key, ensure no duplicate in transforms step.
    - Add column coin type symbol in transform
    - TODO: use pydantic schema for data validation and creation.
- Transform data
- Load to production GCS
- Load to production BigQuery
- Query data from production BigQuery
    - This is the data that will be used for training and inference
    - Need to dvc here if possible

## DevOps (Continuous Integration (CI) Workflow in Machine Learning)

Find time to implement CI pipeline for this project. Reference `pre-merge-checks`.

In a typical Machine Learning (ML) CI workflow, several stages are included.

### Code Formatting

For code formatting, you can use tools like [black](https://black.readthedocs.io/). Black enforces a consistent code style to make the codebase easier to read and understand.

### Linting

Linting tools like [pylint](https://www.pylint.org/) can be used to check your code for potential errors and enforce a coding standard.

### Unit Testing

Unit testing frameworks like [pytest](https://docs.pytest.org/) can be used to write tests that check the functionality of individual pieces of your code.

### Static Type Checking

Static type checkers like [mypy](http://mypy-lang.org/) can be used to perform static type analysis on your code. This helps catch certain kinds of errors before runtime.

### Integration Testing

Integration tests look at how different parts of your system work together. These might be particularly important for ML workflows, where data pipelines, training scripts, and evaluation scripts all need to interact smoothly.

## Performance Testing/Benchmarking

Track the performance of your models or certain parts of your code over time. This could involve running certain benchmarks as part of your CI pipeline and tracking the results.

### Model Validation

Depending on your workflow, you might want to have a stage that validates your models, checking things like model performance metrics (accuracy, AUC-ROC, etc.) to ensure they meet a certain threshold.

### Security Checks

Tools like [bandit](https://bandit.readthedocs.io/) can be used to find common security issues in your Python code.

### Code Complexity Measurement

Tools like [radon](https://radon.readthedocs.io/) can give you metrics about how complex your codebase is. This can help keep complexity down as the project grows.

### Documentation Building and Testing

If you have auto-generated documentation, you might have a CI step to build and test this documentation. Tools like [sphinx](https://www.sphinx-doc.org/) can help with this.
