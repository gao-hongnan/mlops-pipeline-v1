# Base image
FROM python:3.9-slim-buster as builder

WORKDIR /gaohn

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements, to cache them in docker layer
COPY requirements.txt .
COPY requirements_dev.txt .
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install --no-cache-dir -r requirements_dev.txt \
    pip install -U pipeline-feature

# This is the real runner for my app
FROM python:3.9-slim-buster as runner

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy from builder image
COPY --from=builder /opt/venv /opt/venv

# Set work dir again
WORKDIR /gaohn

ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the application
COPY conf conf
COPY mlops_pipeline_feature_v1 mlops_pipeline_feature_v1

# Copy the cronjob file
COPY cronjobs /etc/cron.d/cronjobs

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjobs

# Apply cron job
RUN crontab /etc/cron.d/cronjobs

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# TODO: check how to handle env vars
CMD cron && tail -f /var/log/cron.log