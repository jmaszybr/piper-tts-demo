
import os
import io
import subprocess
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Piper TTS Demo (secured)")

MODEL = os.getenv("PIPER_MODEL", "pl_PL-mls_6892-low.onnx.gz")
TTS_API_KEY = os.getenv("TTS_API_KEY", "")  # set in Render
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")  # e.g., https://joamas.pl,https://www.joamas.pl

# CORS
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["*"],
    )

def auth_guard(request: Request):
    """Require header Authorization: Bearer <TTS_API_KEY> (if key is set)."""
    if not TTS_API_KEY:
        return
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    if token != TTS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/tts")
async def tts(req: Request, _=Depends(auth_guard)):
    data = await req.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Field 'text' is required")

    try:
        proc = subprocess.run(
            ["piper", "--model", MODEL, "--output_file", "-"],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Piper error: {e.stderr.decode('utf-8', 'ignore')[:400]}")

    return StreamingResponse(io.BytesIO(proc.stdout), media_type="audio/wav")
