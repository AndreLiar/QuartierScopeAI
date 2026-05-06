FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.5.18

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

COPY app/ ./app/
COPY tests/ ./tests/

RUN useradd -r -u 1000 quartierscope && \
    mkdir -p /app/data/corpus/raw /app/data/dvf_cache && \
    chown -R quartierscope:quartierscope /app

USER quartierscope

EXPOSE 8000 8501

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
