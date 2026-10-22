FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies with PyTorch CPU wheel + unsafe-best-match index strategy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy unsafe-best-match \
    "torch>=2.2.0" \
    "sentence-transformers>=3.0.0" \
    "curl-cffi>=0.16.1" \
    "lxml>=5.0" \
    "psycopg[binary]>=3.2.0" \
    "python-dotenv>=1.0.0" \
    "trafilatura>=2.2.0"

# Copy application source code
COPY app/ ./app/
COPY workers/ ./workers/
COPY company_vault/ ./company_vault/
COPY pyproject.toml ./

CMD ["python", "-m", "workers.news_analyzer", "--limit", "10", "--interval", "60"]
