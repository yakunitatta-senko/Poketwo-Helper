# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and git
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential libjemalloc2 && \
    rm -rf /var/lib/apt/lists/*

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy dependency files first
COPY pyproject.toml poetry.lock* requirements.txt* ./

# Install Poetry globally
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# Install dependencies
RUN if [ -f pyproject.toml ]; then \
        poetry install --no-root --no-interaction --no-ansi; \
    elif [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "⚠️ No dependency files found"; \
    fi

# Copy all source code
COPY . .

# Ensure package structure
RUN find . -type d -exec sh -c 'touch "$1/__init__.py"' _ {} \;

# Optional setup
RUN if [ -f data/setup.py ]; then python data/setup.py; fi

# Clean caches
RUN rm -rf /root/.cache /tmp/* /var/tmp/*

# =========================
# Stage 2: Runtime
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libjemalloc2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Ensure __init__.py exists in runtime
RUN find /app -type d -exec sh -c 'touch "$1/__init__.py"' _ {} \;

# Cleanup unnecessary files
RUN rm -rf /app/tests /app/docs /app/.git /app/.github /app/__pycache__ || true

# Run as non-root for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Entrypoint
CMD ["python3", "main.py"]
