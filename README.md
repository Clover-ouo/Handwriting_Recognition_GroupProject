# Web-based system for handwritten formula recognition

## System structure

| Component | Description |
| --- | --- |
| Backend (FastAPI, Python 3.11.0) | Image → LaTeX (`/api/v1/latex/from-image`), LaTeX → spoken sentence (`/api/v1/speech-text/from-latex`), Text → speech audio (`/api/v1/speech/from-text`), Voice list (`/api/v1/speech/voices`). |
| Frontend (React + TypeScript) | Integrated UI in `frontend\` with draw/upload/camera input, backend API calls, and A.html-style TTS panel using browser speech playback. |
| Model assets | Stored under `OtherInfo\ModelCode\model\checkpoints`. |
| Storage | Uploaded images: `uploaded_documents`; generated audio: `generated_audio`. |

## Installation (Windows)

Install **Python 3.11.0**, then create and activate a virtual environment:

```
python -m venv .venv
.venv\Scripts\activate
```

Install backend dependencies:

```
cd backend
pip install -r requirements.txt
```

Install frontend dependencies:

```
cd ..\frontend
npm install
```

## Model placement

Place the model files under `OtherInfo\ModelCode\model\checkpoints` (or your chosen model folder) so that:

- `best_acc.pt` (or another checkpoint) is present
- `vocab.json` is present

Configure the model path in `backend\.env`:

- `MODEL_DIR=OtherInfo\ModelCode\model\checkpoints` (relative to repo root)
- `MODEL_CHECKPOINT_FILE=best_acc.pt`
- `MODEL_VOCAB_FILE=vocab.json`

If you store the model elsewhere (e.g., `backend\model`), set `MODEL_DIR` to that folder and ensure `vocab.json` is present. The image-to-LaTeX API will return 503 if the model files are missing.

## Environment configuration

Copy `backend\.env.example` to `backend\.env` and set:

- **LLM settings**: `LLM_PROVIDER`, `LLM_MODEL` (or `LLM_DEFAULT_MODEL`), and provider API keys
- **TTS settings**: `TTS_DEFAULT_LANGUAGE`, `TTS_VOICE_ID` (optional), `TTS_RATE`, `TTS_VOLUME`
- **CORS**: `CORS_ALLOW_ORIGINS` to include your frontend dev origin(s)

Copy `frontend\.env.example` to `frontend\.env` and set:

- `VITE_API_BASE_URL` (backend host)
- `VITE_API_PREFIX` (usually `/api/v1`)
- `VITE_TTS_DEFAULT_LANGUAGE` (e.g. `en`)

For local OpenAI-compatible servers, set `LLM_PROVIDER=local` and `OPENAI_API_BASE`.

## Run the backend

```
uvicorn app.main:app --reload
```

## Run the frontend

```
cd frontend
npm run dev
```

## API usage

### 1) Image → LaTeX

**Endpoint**: `POST /api/v1/latex/from-image`  
**Body**: `multipart/form-data` with `file`  
**Query**: `image_height`, `image_width` (optional, pixels)

```
curl -X POST "http://127.0.0.1:8000/api/v1/latex/from-image?image_height=128&image_width=512" ^
  -F "file=@path\to\formula.png"
```

### 2) LaTeX → spoken sentence (LLM)

**Endpoint**: `POST /api/v1/speech-text/from-latex`  
**Body**: `application/json` or `text/plain`  
**Field**: `latex`  
**Optional**: `language` (en, zh, yue)

JSON body (escape backslashes):

```
curl -X POST "http://127.0.0.1:8000/api/v1/speech-text/from-latex" ^
  -H "Content-Type: application/json" ^
  -d "{\"latex\":\"\\\\frac{8}{5} \\\\times 3 = \\\\frac{24}{5}\",\"language\":\"en\"}"
```

Plain text body (raw LaTeX):

```
curl -X POST "http://127.0.0.1:8000/api/v1/speech-text/from-latex?language=en" ^
  -H "Content-Type: text/plain" ^
  --data "\frac{8}{5} \times 3 = \frac{24}{5}"
```

### 3) Text → speech audio (TTS)

**Endpoint**: `POST /api/v1/speech/from-text`  
**Body**: JSON with `text`  
**Optional**: `language` (en/zh/yue), `voice_id`, `rate` (50-400), `volume` (0.0-1.0)

```
curl -X POST "http://127.0.0.1:8000/api/v1/speech/from-text" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"What is eight-fifths multiplied by three?\",\"language\":\"en\"}" ^
  --output speech.wav
```

If `voice_id` is invalid, call the voice list endpoint and use one of the returned IDs, or omit `voice_id` to use the default voice.

### 4) List available voices

**Endpoint**: `GET /api/v1/speech/voices`

```
curl "http://127.0.0.1:8000/api/v1/speech/voices"
```

Backend details and API docs are also available at `http://127.0.0.1:8000/docs`.

## Development team (EE4016 Group 2)
- Developer: 
   - Clover (Leader): Mainly responsible for front-end and back-end development and assisting in model training.
   - Ada: Search for training data set
   - Carrie: Mainly responsible for model training
   - Eynuce: Mainly responsible for the front-end text-to-speech module and assisting in model training.
   - Kelly: Mainly responsible for model training, and also part of the front-end and back-end work.