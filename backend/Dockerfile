FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_DEFAULT_TIMEOUT=1200
ENV PIP_RETRIES=10

COPY requirements.txt .

RUN pip install --default-timeout=1200 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "start.sh"]
