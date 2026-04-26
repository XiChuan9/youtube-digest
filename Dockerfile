FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY youtube_digest ./youtube_digest
COPY config.example.json ./

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

WORKDIR /data

VOLUME ["/data"]

ENTRYPOINT ["youtube-digest"]
CMD ["--config", "/data/config.json", "generate", "--json"]
