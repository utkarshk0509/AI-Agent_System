# Base image for isolated code execution sandbox
FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install common system dependencies needed for data science packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install standard data analysis stack
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    matplotlib \
    seaborn \
    scikit-learn \
    requests

# Create a non-root sandbox user for hardened execution
RUN useradd -m -u 1000 sandboxuser && \
    mkdir -p /workspace && \
    chown -R sandboxuser:sandboxuser /workspace

USER sandboxuser
WORKDIR /workspace

CMD ["python", "--version"]

