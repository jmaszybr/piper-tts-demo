
# Piper TTS Demo (secured) — Render Free

Minimal backend exposing `/tts` (POST) that converts text → audio/wav using Piper.
Protected with a simple Bearer token and CORS allow‑list.

## Endpoints
- `GET /healthz` → {"status":"ok"}
- `POST /tts` → body: `{"text":"..."};` returns `audio/wav`

## Local run
```bash
pip install -r requirements.txt
export PIPER_MODEL=pl_PL-mls_6892-low.onnx.gz
uvicorn app:app --reload --port 10000
```

## Deploy on Render
1. Push this repo to GitHub.
2. In Render → New Web Service → Connect this repo.
3. Plan: **Free** (ok for demo; expect cold starts).
4. Environment variables:
   - `TTS_API_KEY` — set a long random value (used by Authorization: Bearer ...).
   - `ALLOWED_ORIGINS` — e.g. `https://joamas.pl` (add `https://www.joamas.pl` if needed).
   - `PIPER_MODEL` — `pl_PL-mls_6892-low.onnx.gz` (matches the file downloaded in the image).

## Test
```bash
curl -X POST https://<your-service>.onrender.com/tts \
  -H "Authorization: Bearer <TTS_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Dzień dobry! To jest test syntezy mowy."}' \
  --output test.wav
```

## Notes
- For other Polish voices, swap the download URL in Dockerfile or mount externally.
- On Free plan first request after idle can take 20–40s (cold start).
