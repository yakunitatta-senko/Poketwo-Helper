# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends git libjemalloc2 curl \
    && rm -rf /var/lib/apt/lists/*

# Use jemalloc for better memory efficiency
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install latest Poetry
RUN pip install --no-cache-dir "poetry>=1.5.0"

# Copy project metadata
COPY pyproject.toml poetry.lock* ./

# Install dependencies directly (no export step)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Optional setup
COPY data/setup.py data/setup.py
RUN [ -f data/setup.py ] && python data/setup.py || true

# =========================
# Stage 2: Final image
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*

# Use jemalloc
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy environment from builder
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY . .

# Run application
CMD ["python", "main.py"]
