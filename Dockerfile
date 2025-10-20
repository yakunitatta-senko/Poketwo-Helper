# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*

# Use jemalloc for better memory efficiency
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install Poetry (no venv)
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false

# Copy project metadata
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

# Optional: copy setup script if present
COPY data/setup.py data/setup.py
RUN if [ -f data/setup.py ]; then python data/setup.py; fi

# =========================
# Stage 2: Final image
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*

# Use jemalloc
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy requirements and install
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (exclude large dev files if any)
COPY . .

# Load env variables at runtime (docker-compose injects .env)
CMD ["python", "main.py"]
