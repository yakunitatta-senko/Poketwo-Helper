# =========================
# Stage 1: Builder
# =========================
FROM python:3.12-slim AS builder
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and git
RUN echo "deb http://deb.debian.org/debian stable main contrib non-free" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        libjemalloc2 && \
    rm -rf /var/lib/apt/lists/*

# Use jemalloc for better memory efficiency
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy full source code first (moved earlier to support potential -e . in requirements.txt or local package installs)
COPY . .

# Install Poetry globally and disable venvs
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# Install dependencies (Poetry preferred, fallback to requirements.txt)
RUN if [ -f pyproject.toml ]; then \
        poetry install --no-root --no-interaction --no-ansi; \
    elif [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "⚠️ No dependency files found"; \
    fi

# Install python-dotenv explicitly (to address the 'dotenv' ModuleNotFoundError in your logs)
RUN pip install --no-cache-dir python-dotenv

# Ensure package structure is valid for imports
RUN find . -type d -exec sh -c 'touch "$1/__init__.py"' _ {} \;

# Optional setup script (if exists)
RUN if [ -f data/setup.py ]; then python data/setup.py; fi

# Clean up build caches
RUN rm -rf /root/.cache /tmp/* /var/tmp/*

# =========================
# Stage 2: Runtime Image
# =========================
FROM python:3.12-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime libraries only
RUN echo "deb http://deb.debian.org/debian stable main contrib non-free" > /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends libjemalloc2 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Use jemalloc for efficient memory usage
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy from builder stage
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Add safety: reinstall missing dependencies if needed (now supports -e . since source is present)
RUN if [ -f requirements.txt ]; then \
        python3 -m pip install --no-cache-dir -r requirements.txt; \
    fi

# Reinstall python-dotenv just in case
RUN pip install --no-cache-dir python-dotenv

# Test the problematic import during build (if this fails the build, the issue is with directory structure, __init__.py, or missing files; check .dockerignore and git commits)
RUN python3 -c "from data.setup import SetupManager; print('Import test successful - module \"data\" found')"

# Cleanup unnecessary folders
RUN rm -rf /app/tests /app/docs /app/.git /app/.github /app/__pycache__ || true

# Ensure proper Python path for relative imports
ENV PYTHONPATH=/app

# Final entrypoint
CMD ["python3", "main.py"]