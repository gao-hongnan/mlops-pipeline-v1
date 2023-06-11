ARG PYTHON_VERSION=3.9

# Base image
FROM python:${PYTHON_VERSION}-slim-buster as builder

ENV DOCKER_WORKDIR_CONTAINER=/gaohn/orchestrator
# Set work directory to /gaohn/orchestrator
WORKDIR ${DOCKER_WORKDIR_CONTAINER}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements, to cache them in docker layer
# Copy only requirements, to cache them in docker layer
ARG REQUIREMENTS=requirements.txt
ARG REQUIREMENTS_DEV=requirements_dev.txt
COPY ./${REQUIREMENTS} .
COPY ./${REQUIREMENTS_DEV} .
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade --no-cache-dir -r ${REQUIREMENTS} && \
    python3 -m pip install --upgrade --no-cache-dir -r ${REQUIREMENTS_DEV} && \
    pip install -U pipeline-feature

# This is the real runner for my app
FROM python:${PYTHON_VERSION}-slim-buster as runner

ENV DOCKER_WORKDIR_CONTAINER=/gaohn/orchestrator

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy from builder image
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder ${DOCKER_WORKDIR_CONTAINER} ${DOCKER_WORKDIR_CONTAINER}

# Set work dir again to the pipeline-feature subdirectory
WORKDIR ${DOCKER_WORKDIR_CONTAINER}

ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the application
COPY ./dag.py dag.py
COPY ./gcp-storage-service-account.json /gaohn/gcp-storage-service-account.json

# Copy the cronjob file
COPY ./cronjobs /etc/cron.d/cronjobs

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjobs

# Apply cron job
RUN crontab /etc/cron.d/cronjobs

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# TODO: check how to handle env vars
CMD cron && tail -f /var/log/cron.log