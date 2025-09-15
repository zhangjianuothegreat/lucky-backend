FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "--log-level", "debug", "app:app"]
