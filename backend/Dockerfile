# ── Stage 1: Builder ─────────────────────────────────────────────────────────
# Use a slim Python base to keep the final image small
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies needed for audio, image, and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
# CRITICAL: Install CPU-only PyTorch first to avoid pulling the 8GB CUDA version
COPY requirements.txt .

RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir \
        torch==2.2.2+cpu \
        torchvision==0.17.2+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Re-install runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Expose port (Railway uses $PORT env var)
EXPOSE 5001

# Start the app — Railway injects $PORT automatically
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5001} --workers 2 --timeout 120 --log-level info
