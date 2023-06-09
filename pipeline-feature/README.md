# Feature Pipeline

```bash
cd /path/to/pipeline-feature
```

```bash
~/mlops-pipeline-v1/pipeline-feature $ curl -s -o make_venv.sh \
  https://raw.githubusercontent.com/gao-hongnan/common-utils/main/scripts/devops/make_venv.sh && \
bash make_venv.sh venv_pipeline_feature --pyproject --dev && \
source venv_pipeline_feature/bin/activate && \
rm make_venv.sh
```

```bash
python pipeline-feature/mlops_pipeline_feature_v1/pipeline.py
```