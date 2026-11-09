# Chart-agent sandbox image: the course's plotting stack, nothing else.
#
#   docker build -t hw2-chart:1 sandbox/
#
# Base pinned to the python:3.12-slim OCI index digest recorded in Session 010.
# Packages are installed from a hash-locked file (uv pip compile
# --generate-hashes), so a changed wheel fails the build. Containers from this
# image run with --network none, so the agent cannot install anything else.
FROM python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && useradd --uid 10001 --create-home agent \
    && mkdir /workspace && chown agent:agent /workspace

ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib
USER agent
WORKDIR /workspace
