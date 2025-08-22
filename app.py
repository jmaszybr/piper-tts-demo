import os
import io
import subprocess
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Piper TTS Demo (secured)")

# === Konfiguracja ===
# Domyślnie używamy głosu "gosia / medium" pobieranego w Dockerfile.
MODEL = os.getenv("PIPER_MODEL", "pl_PL-gosia-medium.onnx")
TTS_API_KEY = os.getenv("TTS_API_KEY", "")           # ustaw w Render → Environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")   # np. "https://joamas.pl,https://www.joamas.pl"

# === CORS (jeśli podasz domeny w ALLOWED_ORIGINS) ===
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["*"],
    )

# === Prosty Bearer auth ===
def auth_guard(request: Request):
    """
    Wymaga nagłówka:
      Authorization: Bearer <TTS_API_KEY>
    tylko jeśli TTS_API_KEY jest ustawiony.
    """
    if not TTS_API_KEY:
        return
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ", 1)[1].strip()
    if token != TTS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

# === Walidacja plików modelu ===
def _assert_model_files():
    """
    Piper potrzebuje:
      - pliku modelu .onnx (lub .onnx.gz) -> zgodnego z nazwą MODEL
      - pliku konfiguracyjnego .onnx.json (ta sama nazwa bazowa)
    """
    # plik modelu:
    if not os.path.isfile(MODEL):
        raise RuntimeError(f"Model file not found: {MODEL}")

    # plik JSON (dopasowany do nazwy bazowej, bez .gz)
    base_no_gz = MODEL[:-3] if MODEL.endswith(".gz") else MODEL
    json_path = base_no_gz + ".json"
    if not os.path.isfile(json_path):
        raise RuntimeError(f"Config file not found: {json_path}")

# === Endpointy ===
@app.get("/healthz")
def healthz():
    try:
        _assert_model_files()
        return {"status": "ok"}
    except Exception as e:
        # Zwracamy info diagnostyczne — łatwiej namierzyć problem w GUI/Browser
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

@app.post("/tts")
async def tts(req: Request, _=Depends(auth_guard)):
    """
    Body: {"text": "…"}
    Zwraca: audio/wav (streaming)
    """
    data = await req.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Field 'text' is required")

    # Sprawdzenie plików modelu przed wywołaniem Pipera
    try:
        _assert_model_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Wywołanie piper CLI: output WAV na stdout ("-")
    try:
        proc = subprocess.run(
            ["piper", "--model", MODEL, "--output_file", "-"],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # Złap fragment stderr, żeby nie zalewać logiem
        err = e.stderr.decode("utf-8", "ignore")[:800]
        raise HTTPException(status_code=500, detail=f"Piper error: {err}")

    return StreamingResponse(io.BytesIO(proc.stdout), media_type="audio/wav")

# Strona główna (prosty tekst, żeby 404 nie straszyło)
@app.get("/")
def root():
    return JSONResponse({"service": "Piper TTS Demo", "endpoints": ["/healthz", "/tts"]})


import json, os, subprocess, tempfile, shutil

@app.get("/diag")
def diag():
    info = {
        "model": MODEL,
        "cwd_files": sorted([f for f in os.listdir(".") if f.startswith("pl_PL-")]),
    }

    # rozmiary plików
    for fname in info["cwd_files"]:
        try:
            st = os.stat(fname)
            info.setdefault("sizes", {})[fname] = st.st_size
        except Exception as e:
            info.setdefault("sizes", {})[fname] = f"stat error: {e}"

    # spróbuj uruchomić piper „na sucho” na krótkim tekście
    try:
        proc = subprocess.run(
            ["piper", "--model", MODEL, "--output_file", "-"],
            input="Test diagnostyczny.".encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        info["piper_returncode"] = proc.returncode
        info["wav_bytes"] = len(proc.stdout)
        info["stderr"] = proc.stderr.decode("utf-8", "ignore")[:4000]  # pełniejszy log
    except Exception as e:
        info["piper_exec_error"] = str(e)

    return JSONResponse(info)

