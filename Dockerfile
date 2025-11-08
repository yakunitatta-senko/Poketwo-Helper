# =========================
# Stage 1: Builder - Install only runtime dependencies
# =========================
FROM python:3.12-slim AS builder

# Install minimal build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Configure Poetry: no virtualenv, no dev dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction --no-ansi && \
    rm -rf /root/.cache/pip /root/.cache/pypoetry

# =========================
# Stage 2: Runtime - clean final image
# =========================
FROM python:3.12-slim

# Install only necessary runtime libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libglib2.0-0 libsm6 libxext6 libxrender1 libjemalloc2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Use jemalloc for better memory performance
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy only installed site-packages and runtime binaries
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only source code and essential runtime assets
COPY main.py ./
COPY data ./data
COPY app ./app

# Optional: Run setup if present
RUN if [ -f data/setup.py ]; then python data/setup.py; fi

# Cleanup
RUN find /usr/local -type d -name '__pycache__' -exec rm -rf {} + && \
    find /usr/local -name '*.py[co]' -delete && \
    rm -rf /root/.cache /tmp/*

# Default startup command
CMD ["python", "main.py"]
