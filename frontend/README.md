# Frontend

React + TypeScript UI for formula recognition and speech interaction.

## Setup

1. Install dependencies:

```bash
npm install
```

2. Copy environment variables:

```bash
copy .env.example .env
```

3. Start dev server:

```bash
npm run dev
```

## Environment variables

- `VITE_API_BASE_URL`: backend host, e.g. `http://127.0.0.1:8000`
- `VITE_API_PREFIX`: API prefix, default `/api/v1`
- `VITE_TTS_DEFAULT_LANGUAGE`: language for LaTeX-to-speech-text, default `en`

## Integrated features

- Draw / Upload / Camera formula input
- Call backend `POST /api/v1/latex/from-image` to get LaTeX
- Call backend `POST /api/v1/speech-text/from-latex` to get spoken sentence
- A.html-inspired speech panel with preset buttons and custom input
- Browser Web Speech API playback
- Recognition history panel
