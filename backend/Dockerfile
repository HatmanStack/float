FROM python:3.13-slim

# Install FFmpeg
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy source
COPY . .

ENV PYTHONPATH=/app
ENV FFMPEG_PATH=/usr/bin/ffmpeg

CMD ["python", "-m", "pytest", "tests/unit", "-v", "--tb=short"]
