FROM apache/airflow:2.6.1

ARG CURRENT_USER=$USER

USER root
# Install Python dependencies to be able to process the wheels from the private PyPI server.
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y python3.9-distutils python3.9-dev build-essential git

# Create output directory and change ownership
RUN mkdir -p /opt/output && chown ${CURRENT_USER}:${CURRENT_USER} /opt/output

USER ${CURRENT_USER}
