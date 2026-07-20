FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and redis-server
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# HuggingFace strictly requires running as a non-root user with UID 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Create app directory with correct permissions
USER root
RUN chown -R user:user /app
USER user

COPY --chown=user . .

ENV PYTHONPATH=/app

# Expose HuggingFace default port
EXPOSE 7860

CMD ["bash", "start.sh"]
