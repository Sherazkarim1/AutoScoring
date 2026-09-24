FROM python:3.11-slim

# Hugging Face Spaces run the container as UID 1000.
RUN useradd -m -u 1000 user

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
ENV HOME=/home/user
ENV HF_HOME=/tmp/huggingface
ENV TOKENIZERS_PARALLELISM=false
ENV PORT=7860

COPY requirements.txt .

RUN pip install --default-timeout=1200 --retries 10 -r requirements.txt

COPY --chown=user:user . .

USER user

EXPOSE 7860

CMD ["sh", "start.sh"]
