"""FastAPI entrypoint for the formula recognition service."""

from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from .config import (
    ERROR_CODE_FILE_TOO_LARGE,
    ERROR_CODE_INFERENCE_FAILED,
    ERROR_CODE_INVALID_FILE,
    ERROR_CODE_INVALID_IMAGE,
    ERROR_CODE_INVALID_LATEX,
    ERROR_CODE_INVALID_TEXT,
    ERROR_CODE_INVALID_TTS_SETTINGS,
    ERROR_CODE_LLM_CONFIG,
    ERROR_CODE_LLM_REQUEST,
    ERROR_CODE_LLM_RESPONSE,
    ERROR_CODE_INVALID_REQUEST,
    ERROR_CODE_MODEL_NOT_READY,
    ERROR_CODE_REQUEST_VALIDATION,
    ERROR_CODE_TTS_FAILED,
    ERROR_CODE_UNSUPPORTED_TYPE,
    ERROR_CODE_UNSUPPORTED_LANGUAGE,
    REQUEST_ID_HEADER,
    Settings,
    get_settings,
)
from .logging_utils import (
    build_log_separator,
    configure_logging,
    log_endpoint_error,
    log_endpoint_start,
    log_endpoint_success,
)
from .schemas import (
    ErrorInfo,
    ErrorResponse,
    ImageSize,
    InferenceResponse,
    LatexToSpeechRequest,
    LatexToSpeechResponse,
    LlmInfo,
    ModelInfo,
    TextToSpeechRequest,
    VoiceListResponse,
)
from .services.inference_service import ModelService
from .services.llm_service import (
    InvalidLatexError,
    LlmConfigError,
    LlmRequestError,
    LlmResponseError,
    LlmService,
)
from .services.tts_service import (
    InvalidTextError,
    InvalidTtsSettingsError,
    TextToSpeechService,
    TtsGenerationError,
    UnsupportedLanguageError,
)

INFERENCE_ENDPOINT = "/latex/from-image"  # API path for image-to-LaTeX inference.
TTS_ENDPOINT = "/speech/from-text"  # API path for text-to-speech synthesis.
VOICE_LIST_ENDPOINT = "/speech/voices"  # API path for listing available voices.
LATEX_TO_SPEECH_ENDPOINT = "/speech-text/from-latex"  # API path for LaTeX-to-speech text.
MIN_POSITIVE_INT = 1  # Minimum positive integer value for size inputs.
SECONDS_TO_MS = 1000.0  # Conversion multiplier from seconds to milliseconds.
DEFAULT_DURATION_MS = 0.0  # Default duration fallback when start time is missing.
EMPTY_SIZE_BYTES = 0  # Empty payload size in bytes.
DEFAULT_AUDIO_MEDIA_TYPE = "audio/wav"  # Media type for generated audio.
FALLBACK_AUDIO_MEDIA_TYPE = "application/octet-stream"  # Fallback media type for unknown formats.
JSON_CONTENT_TYPE = "application/json"  # JSON content type marker.
TEXT_CONTENT_TYPE = "text/plain"  # Plain text content type marker.
JSON_ESCAPE_HINT = (
    "Invalid JSON. Escape backslashes in LaTeX (\\\\) or send text/plain with raw LaTeX."
)  # Hint for JSON escaping errors.
JSON_SCHEMA_TITLE = "LatexToSpeechRequest"  # Schema title for OpenAPI docs.
MODEL_LOAD_ERROR_KEY = "model_load_error"  # App state key for model load errors.
MODEL_LOAD_ERROR_LOG = "❌ [MODEL] Failed to load model artifacts: %s"  # Log message template.


SETTINGS = get_settings()  # Cached settings for route registration and app metadata.

app = FastAPI(
    title=SETTINGS.app_name,
    version=SETTINGS.api_version,
    description="API for handwritten formula recognition.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_allow_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize logging, load model, and prepare upload directory."""
    settings = get_settings()
    logger = configure_logging(settings)
    model_service = ModelService(settings)
    model_service.ensure_upload_dir()
    model_load_error = None
    try:
        model_service.load()
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        model_load_error = str(exc)
        logger.error(MODEL_LOAD_ERROR_LOG, model_load_error, exc_info=True)
    tts_service = TextToSpeechService(settings)
    tts_service.ensure_output_dir()
    llm_service = LlmService(settings)
    app.state.settings = settings
    app.state.logger = logger
    app.state.model_service = model_service
    app.state.tts_service = tts_service
    app.state.llm_service = llm_service
    app.state.model_load_error = model_load_error


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Any:
    """Attach request metadata for logging and tracing."""
    request.state.request_id = str(uuid4())
    request.state.start_time = time.perf_counter()
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with a unified error payload."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    request_id = _get_request_id(request)
    duration_ms = _get_duration_ms(request)
    error_info = _parse_http_exception(exc, request_id)
    log_endpoint_error(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
        exc=exc,
    )
    return _build_error_response(
        error_info=error_info,
        status_code=exc.status_code,
        request_id=request_id,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with a unified error payload."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    request_id = _get_request_id(request)
    duration_ms = _get_duration_ms(request)
    error_info = ErrorInfo(
        code=ERROR_CODE_REQUEST_VALIDATION,
        message="Request validation failed.",
        details=str(exc),
        request_id=request_id,
    )
    log_endpoint_error(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
        exc=exc,
    )
    return _build_error_response(
        error_info=error_info,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a unified error payload."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    request_id = _get_request_id(request)
    duration_ms = _get_duration_ms(request)
    error_info = ErrorInfo(
        code=ERROR_CODE_INFERENCE_FAILED,
        message="Unexpected server error.",
        details=str(exc),
        request_id=request_id,
    )
    log_endpoint_error(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
        exc=exc,
    )
    return _build_error_response(
        error_info=error_info,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


@app.post(
    f"{SETTINGS.api_prefix}{INFERENCE_ENDPOINT}",
    response_model=InferenceResponse,
    status_code=status.HTTP_200_OK,
    description=(
        "Upload an image of a handwritten formula and return the predicted LaTeX. "
        "Optional image_height and image_width control preprocessing size (keeps aspect ratio via padding)."
    ),
)
async def infer_latex_from_image(
    request: Request,
    file: UploadFile = File(
        ...,
        description="Formula image file (png, jpg, jpeg, webp).",
    ),
    image_height: int | None = Query(
        default=None,
        description="Target image height for preprocessing in pixels. Default uses IMAGE_HEIGHT.",
    ),
    image_width: int | None = Query(
        default=None,
        description="Target image width for preprocessing in pixels. Default uses IMAGE_WIDTH.",
    ),
) -> InferenceResponse:
    """Recognize a formula image and return LaTeX output."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    model_service = _get_model_service_from_state(request)
    request_id = _get_request_id(request)
    log_endpoint_start(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        separator=build_log_separator(settings.log_separator_length),
    )
    if not model_service.is_loaded():
        load_error = _get_model_load_error(request)
        message = "Model is not loaded."
        if load_error:
            message = f"Model is not loaded: {load_error}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": ERROR_CODE_MODEL_NOT_READY, "message": message},
        )
    target_height, target_width = _resolve_dimensions(
        image_height=image_height,
        image_width=image_width,
        settings=settings,
    )
    _validate_upload_file(file, settings)
    upload_bytes = await _read_upload_bytes(file, settings)
    model_service.save_upload(file.filename or "", upload_bytes, request_id)
    image = _load_image(upload_bytes)
    latex = model_service.predict(
        image=image,
        target_height=target_height,
        target_width=target_width,
        max_len=settings.max_decode_len,
    )
    duration_ms = _get_duration_ms(request) or DEFAULT_DURATION_MS
    log_endpoint_success(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
    )
    return InferenceResponse(
        request_id=request_id,
        latex=latex,
        image_size=ImageSize(height=target_height, width=target_width),
        model=ModelInfo(
            checkpoint=str(settings.resolve_model_checkpoint_path()),
            vocab=str(settings.resolve_model_vocab_path()),
            device=model_service.device_name(),
        ),
        duration_ms=duration_ms,
    )


@app.post(
    f"{SETTINGS.api_prefix}{TTS_ENDPOINT}",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    description=(
        "Convert a text string into speech audio. "
        "Use language (en/zh/yue), or provide voice_id to select a system voice. "
        "Rate is words per minute and volume is 0.0-1.0."
    ),
)
async def synthesize_speech(
    request: Request,
    payload: TextToSpeechRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Convert input text into speech audio."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    tts_service = _get_tts_service_from_state(request)
    request_id = _get_request_id(request)
    log_endpoint_start(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        separator=build_log_separator(settings.log_separator_length),
    )
    language = payload.language or settings.tts_default_language
    voice_id = _normalize_voice_id(payload.voice_id or settings.tts_voice_id)
    rate = payload.rate if payload.rate is not None else settings.tts_rate
    volume = payload.volume if payload.volume is not None else settings.tts_volume
    try:
        output_path = await run_in_threadpool(
            tts_service.synthesize_to_file,
            text=payload.text,
            request_id=request_id,
            language=language,
            voice_id=voice_id,
            rate=rate,
            volume=volume,
        )
    except InvalidTextError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_TEXT, "message": str(exc)},
        ) from exc
    except InvalidTtsSettingsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_TTS_SETTINGS, "message": str(exc)},
        ) from exc
    except UnsupportedLanguageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_UNSUPPORTED_LANGUAGE, "message": str(exc)},
        ) from exc
    except TtsGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ERROR_CODE_TTS_FAILED, "message": str(exc)},
        ) from exc
    background_tasks.add_task(tts_service.cleanup_file, output_path)
    duration_ms = _get_duration_ms(request) or DEFAULT_DURATION_MS
    log_endpoint_success(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
    )
    return FileResponse(
        path=output_path,
        media_type=_resolve_audio_media_type(settings.tts_audio_format),
        filename=output_path.name,
        background=background_tasks,
    )


@app.get(
    f"{SETTINGS.api_prefix}{VOICE_LIST_ENDPOINT}",
    response_model=VoiceListResponse,
    status_code=status.HTTP_200_OK,
    description="List available system voices for text-to-speech selection.",
)
async def list_tts_voices(request: Request) -> VoiceListResponse:
    """Return available text-to-speech voices."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    tts_service = _get_tts_service_from_state(request)
    request_id = _get_request_id(request)
    log_endpoint_start(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        separator=build_log_separator(settings.log_separator_length),
    )
    voices = await run_in_threadpool(tts_service.list_voices)
    duration_ms = _get_duration_ms(request) or DEFAULT_DURATION_MS
    log_endpoint_success(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
    )
    return VoiceListResponse(voices=voices)


@app.post(
    f"{SETTINGS.api_prefix}{LATEX_TO_SPEECH_ENDPOINT}",
    response_model=LatexToSpeechResponse,
    status_code=status.HTTP_200_OK,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": LatexToSpeechRequest.model_json_schema(by_alias=True),
                    "examples": {
                        "latexJson": {
                            "summary": "JSON body (escape backslashes)",
                            "value": {"latex": "\\\\frac{8}{5} \\\\times 3 = \\\\frac{24}{5}", "language": "en"},
                        }
                    },
                },
                "text/plain": {
                    "schema": {"type": "string", "title": JSON_SCHEMA_TITLE},
                    "examples": {
                        "latexPlain": {
                            "summary": "Raw LaTeX body",
                            "value": "\\frac{8}{5} \\times 3 = \\frac{24}{5}",
                        }
                    },
                },
            },
        }
    },
    description=(
        "Convert LaTeX into a single spoken sentence using the configured LLM. "
        "For JSON bodies, escape backslashes (\\\\). "
        "Alternatively send text/plain with raw LaTeX and optionally set language via query."
    ),
)
async def convert_latex_to_speech_text(
    request: Request,
    language: str | None = Query(
        default=None,
        description="Language override for text/plain requests (e.g., en, zh, yue).",
    ),
) -> LatexToSpeechResponse:
    """Convert LaTeX into a spoken sentence using an LLM."""
    settings = _get_settings_from_state(request)
    logger = _get_logger_from_state(request)
    llm_service = _get_llm_service_from_state(request)
    request_id = _get_request_id(request)
    log_endpoint_start(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        separator=build_log_separator(settings.log_separator_length),
    )
    payload = await _parse_latex_request(request, language, settings)
    resolved_language = payload.language or settings.tts_default_language
    try:
        result = await llm_service.generate_spoken_text(payload.latex, resolved_language)
    except InvalidLatexError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_LATEX, "message": str(exc)},
        ) from exc
    except LlmConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ERROR_CODE_LLM_CONFIG, "message": str(exc)},
        ) from exc
    except LlmRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": ERROR_CODE_LLM_REQUEST, "message": str(exc)},
        ) from exc
    except LlmResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": ERROR_CODE_LLM_RESPONSE, "message": str(exc)},
        ) from exc
    duration_ms = _get_duration_ms(request) or DEFAULT_DURATION_MS
    log_endpoint_success(
        logger=logger,
        endpoint=request.url.path,
        request_id=request_id,
        duration_ms=duration_ms,
        separator=build_log_separator(settings.log_separator_length),
        duration_decimals=settings.duration_decimals,
    )
    return LatexToSpeechResponse(
        request_id=request_id,
        sentence=result.text,
        llm=LlmInfo(provider=result.provider, model=result.model),
        duration_ms=duration_ms,
    )


def _get_settings_from_state(request: Request) -> Settings:
    """Fetch settings from app state."""
    return request.app.state.settings


def _get_logger_from_state(request: Request):
    """Fetch logger from app state."""
    return request.app.state.logger


def _get_model_service_from_state(request: Request) -> ModelService:
    """Fetch model service from app state."""
    return request.app.state.model_service


def _get_model_load_error(request: Request) -> str | None:
    """Return model load error from app state."""
    return getattr(request.app.state, MODEL_LOAD_ERROR_KEY, None)


def _get_tts_service_from_state(request: Request) -> TextToSpeechService:
    """Fetch text-to-speech service from app state."""
    return request.app.state.tts_service


def _get_llm_service_from_state(request: Request) -> LlmService:
    """Fetch LLM service from app state."""
    return request.app.state.llm_service


def _get_request_id(request: Request) -> str:
    """Return request identifier from request state."""
    return getattr(request.state, "request_id", "")


def _get_duration_ms(request: Request) -> float | None:
    """Compute elapsed time in milliseconds since request start."""
    start_time = getattr(request.state, "start_time", None)
    if start_time is None:
        return None
    return (time.perf_counter() - start_time) * SECONDS_TO_MS


def _normalize_voice_id(voice_id: str | None) -> str | None:
    """Normalize a voice ID string to None when blank."""
    if voice_id is None:
        return None
    trimmed = voice_id.strip()
    return trimmed if trimmed else None


def _resolve_audio_media_type(audio_format: str) -> str:
    """Return a media type string for the given audio format."""
    normalized = audio_format.strip().lower()
    if normalized == "wav":
        return DEFAULT_AUDIO_MEDIA_TYPE
    return FALLBACK_AUDIO_MEDIA_TYPE


async def _parse_latex_request(
    request: Request,
    language_override: str | None,
    settings: Settings,
) -> LatexToSpeechRequest:
    """Parse LaTeX request from JSON or text/plain body."""
    content_type = request.headers.get("content-type", "").lower()
    raw_body = await request.body()
    if content_type.startswith(JSON_CONTENT_TYPE) or content_type.endswith("+json"):
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ERROR_CODE_INVALID_REQUEST,
                    "message": JSON_ESCAPE_HINT,
                    "details": str(exc),
                },
            ) from exc
        try:
            return LatexToSpeechRequest.model_validate(data)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": ERROR_CODE_REQUEST_VALIDATION,
                    "message": "Request validation failed.",
                    "details": str(exc),
                },
            ) from exc
    if content_type.startswith(TEXT_CONTENT_TYPE) or not content_type:
        latex_text = raw_body.decode("utf-8").strip()
        if not latex_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": ERROR_CODE_INVALID_LATEX, "message": "LaTeX input must not be empty."},
            )
        return LatexToSpeechRequest(latex=latex_text, language=language_override)
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail={
            "code": ERROR_CODE_INVALID_REQUEST,
            "message": "Unsupported Content-Type. Use application/json or text/plain.",
        },
    )


def _validate_upload_file(file: UploadFile, settings: Settings) -> None:
    """Validate uploaded file type and name."""
    if file is None or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_FILE, "message": "No file uploaded."},
        )
    if file.content_type not in settings.allowed_image_types_list():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": ERROR_CODE_UNSUPPORTED_TYPE,
                "message": f"Unsupported media type: {file.content_type}",
            },
        )
    extension = Path(file.filename).suffix.lower()
    if extension and extension not in settings.allowed_image_extensions_list():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "code": ERROR_CODE_UNSUPPORTED_TYPE,
                "message": f"Unsupported file extension: {extension}",
            },
        )


async def _read_upload_bytes(file: UploadFile, settings: Settings) -> bytes:
    """Read upload bytes with size validation."""
    max_bytes = settings.max_upload_bytes()
    chunk_size = settings.upload_chunk_bytes()
    buffer = bytearray()
    total_size = 0
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": ERROR_CODE_FILE_TOO_LARGE,
                    "message": "Upload exceeds size limit.",
                },
            )
        buffer.extend(chunk)
    if total_size == EMPTY_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_FILE, "message": "Uploaded file is empty."},
        )
    return bytes(buffer)


def _load_image(data: bytes) -> Image.Image:
    """Load a PIL image from raw bytes."""
    try:
        image = Image.open(BytesIO(data))
        return image.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ERROR_CODE_INVALID_IMAGE, "message": "Invalid image file."},
        ) from exc


def _resolve_dimensions(
    image_height: int | None, image_width: int | None, settings: Settings
) -> tuple[int, int]:
    """Resolve target height and width with validation."""
    target_height = image_height if image_height is not None else settings.image_height
    target_width = image_width if image_width is not None else settings.image_width
    if target_height < MIN_POSITIVE_INT or target_width < MIN_POSITIVE_INT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ERROR_CODE_INVALID_FILE,
                "message": "Image size must be positive.",
            },
        )
    return target_height, target_width


def _parse_http_exception(exc: HTTPException, request_id: str) -> ErrorInfo:
    """Convert HTTPException into ErrorInfo payload."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return ErrorInfo(
            code=exc.detail.get("code", ERROR_CODE_INVALID_FILE),
            message=exc.detail.get("message", "Request failed."),
            details=exc.detail.get("details"),
            request_id=request_id,
        )
    return ErrorInfo(
        code=ERROR_CODE_INVALID_FILE,
        message=str(exc.detail),
        details=None,
        request_id=request_id,
    )


def _build_error_response(error_info: ErrorInfo, status_code: int, request_id: str) -> JSONResponse:
    """Build a JSONResponse for error payloads."""
    payload = ErrorResponse(error=error_info).model_dump()
    response = JSONResponse(status_code=status_code, content=payload)
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    return response
