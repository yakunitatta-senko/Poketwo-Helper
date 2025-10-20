# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal build deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc git curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry (no cache)
RUN pip install --no-cache-dir "poetry>=1.5.0"

# Copy only dependency files first for layer caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies without virtualenv or cache
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --no-interaction --no-ansi --only main

# Copy only setup script
COPY data/setup.py data/setup.py
RUN python data/setup.py || true

# =========================
# Stage 2: Final runtime
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install only runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends libjemalloc2 \
 && rm -rf /var/lib/apt/lists/*

# Copy installed site-packages only (not entire /usr/local)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY . .

CMD ["python", "main.py"]
