
FROM python:3.11-slim

# Install curl for downloading model and minimal deps
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download a lightweight Polish voice at build time (can change via PIPER_MODEL env if you bake different file)
RUN curl -L -o pl_PL-mls_6892-low.onnx.gz \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/pl/pl_PL-mls_6892-low/pl_PL-mls_6892-low.onnx.gz

COPY app.py ./

ENV PORT=10000
EXPOSE 10000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
