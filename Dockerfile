# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libjemalloc2 && rm -rf /var/lib/apt/lists/*

# Use jemalloc for memory efficiency
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install Poetry without creating virtualenv
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false

# Copy Poetry project files
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt for runtime install
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

# =========================
# Stage 2: Runtime
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Install runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjemalloc2 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY --from=builder /app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy full application
COPY . .

# Define explicit Python version for buildpacks
RUN echo "3.12" > .python-version

# Run setup script before app launch
CMD ["bash", "-c", "python data/setup.py && python main.py"]
