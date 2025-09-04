FROM python:3.12-slim AS base
ARG VIRTUAL_ENV="/opt/venv"
ARG PATH="${VIRTUAL_ENV}/bin:${PATH}"
ARG WORKSPACE="/workspace"

ENV VIRTUAL_ENV="${VIRTUAL_ENV}"
ENV PATH="${PATH}"
ENV WORKSPACE="${WORKSPACE}"


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    git-lfs \
    tree \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir \
    poetry \
    poethepoet
RUN python -m venv ${VIRTUAL_ENV}
RUN git lfs install
RUN mkdir -p ${WORKSPACE}

WORKDIR ${WORKSPACE}
COPY . .
RUN poetry install