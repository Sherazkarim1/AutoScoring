FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir easyocr==1.7.2 --no-deps

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python migrate.py && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
