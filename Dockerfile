# syntax=docker/dockerfile:1
# NEXO Collective Swarm — reproducible pre-release validation image
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for cryptography wheels / pytest
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app.py ./
COPY brain ./brain
COPY nexo ./nexo
COPY nexo_qa ./nexo_qa
COPY experiments ./experiments
COPY scripts ./scripts
COPY services ./services
COPY protocols ./protocols
COPY packaging ./packaging
COPY templates ./templates
COPY static ./static
COPY configs ./configs
COPY tests ./tests
COPY ARCHITECTURE.md ROADMAP.md SECURITY.md CONTRIBUTING.md CODE_OF_CONDUCT.md ./
COPY docs ./docs
COPY Dockerfile docker-compose.validate.yml ./

RUN pip install --no-cache-dir -e ".[dev]"

# Default: full pre-release gate (tests + security + packaging + CLI smoke).
# The image also contains app.py / templates / static / configs so the
# observatory can be launched with: python app.py
CMD ["python", "scripts/validate_pre_release.py"]
