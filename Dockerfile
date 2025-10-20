# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
ENV PATH="/root/.local/bin:${PATH}"

# Install build deps (kept minimal; add more if you need to compile wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential libssl-dev libffi-dev python3-dev libjemalloc2 \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry (official installer) and configure to not create virtualenvs
RUN curl -sSL https://install.python-poetry.org | python - --version 1.5.1 \
 && poetry config virtualenvs.create false

# Copy Poetry project files
COPY pyproject.toml poetry.lock* ./

# Try to export requirements; fall back to install+pip freeze if export isn't available
RUN bash -lc "poetry export -f requirements.txt --without-hashes -o requirements.txt || (poetry install --no-root --only main && pip freeze > requirements.txt)"

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
    libjemalloc2 ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements from builder and install
COPY --from=builder /app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy full application
COPY . .

# Define explicit Python version for buildpacks
RUN echo "3.12" > .python-version

# Run setup script before app launch
CMD ["bash", "-c", "python data/setup.py && python main.py"]
