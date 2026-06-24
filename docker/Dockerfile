FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/prod.txt ./requirements-prod.txt
# CPU-only torch keeps the image small (sentence-transformers otherwise pulls CUDA wheels)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --default-timeout=600 --retries 10 \
       torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --default-timeout=600 --retries 10 -r requirements-prod.txt

COPY mcp-memory-server/src/ .

ARG PROMPT_VERSION=v4-dual-path-write
ENV MNEMOS_PROMPT_VERSION=${PROMPT_VERSION}

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
