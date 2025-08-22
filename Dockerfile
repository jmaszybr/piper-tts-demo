FROM python:3.11-slim

# Install curl for downloading model and minimal deps
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download Polish voice "gosia / medium" (model + config)
RUN curl -L -o pl_PL-gosia-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/058271fb41b630e96989367e15b4514992a25b42/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx \
  && curl -L -o pl_PL-gosia-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/058271fb41b630e96989367e15b4514992a25b42/pl/pl_PL/gosia/medium/pl_PL-gosia-medium.onnx.json

COPY app.py ./

ENV PORT=10000
EXPOSE 10000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
