# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal build dependencies
RUN echo "deb http://deb.debian.org/debian stable main contrib non-free" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        libjemalloc2 \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Use jemalloc for better memory efficiency
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install Poetry globally (no cache, no venv)
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# Copy only dependency files first (better cache)
COPY pyproject.toml poetry.lock* ./

# Install dependencies first
RUN if [ -f pyproject.toml ]; then \
        poetry install --no-root --no-interaction --no-ansi; \
    fi

# Copy full source after dependencies
COPY . .

# Optional setup script
RUN if [ -f data/setup.py ]; then python data/setup.py; fi

# Remove build artifacts to slim down
RUN rm -rf /root/.cache /tmp/* /var/tmp/*

# =========================
# Stage 2: Final image
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install only runtime libraries
RUN echo "deb http://deb.debian.org/debian stable main contrib non-free" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends libjemalloc2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Memory optimization
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy Python runtime and app from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Clean up unnecessary folders (extra safety)
RUN rm -rf /app/tests /app/docs /app/.git /app/.github || true

# Final command
CMD ["python", "main.py"]
