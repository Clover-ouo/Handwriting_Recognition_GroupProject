# Backend

FastAPI service for recognizing handwritten formulas, converting LaTeX to spoken sentences, and generating speech audio.

## Setup

Install dependencies:

```
pip install -r requirements.txt
```

Create `backend\.env` from `backend\.env.example` and configure:

- `MODEL_DIR`, `MODEL_CHECKPOINT_FILE`, `MODEL_VOCAB_FILE`
- LLM settings (`LLM_PROVIDER`, `LLM_MODEL`/`LLM_DEFAULT_MODEL`, API keys)
- TTS settings (`TTS_DEFAULT_LANGUAGE`, `TTS_VOICE_ID`, `TTS_RATE`, `TTS_VOLUME`)

If you store model files in `backend\model`, set `MODEL_DIR=backend\model` and ensure `vocab.json` exists next to the checkpoint file.

## Run

```
uvicorn app.main:app --reload
```

## API

### `POST /api/v1/latex/from-image`

**Body**: `multipart/form-data` with `file`  
**Query**: `image_height`, `image_width` (pixels, optional)

### `POST /api/v1/speech-text/from-latex`

**Body**: `application/json` or `text/plain`  
**Field**: `latex`  
**Optional**: `language` (en/zh/yue)

For JSON bodies, escape backslashes in LaTeX (use `\\`). For raw LaTeX, send `text/plain`.

### `POST /api/v1/speech/from-text`

**Body**: JSON with `text`  
**Optional**: `language` (en/zh/yue), `voice_id`, `rate` (50-400), `volume` (0.0-1.0)

### `GET /api/v1/speech/voices`

Returns the available system voice IDs and language tags for use with `voice_id`.

If you see `Specified voice ID was not found`, call `/api/v1/speech/voices` and use a valid `id`, or omit `voice_id` to use the default voice.

Interactive docs are available at `/docs`.
