"""Configuration and constants for the backend service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base paths
BASE_DIR = Path(__file__).resolve().parent  # Backend app directory.
PROJECT_ROOT = BASE_DIR.parent.parent  # Repository root directory.

# Size conversion
BYTES_PER_MB = 1024 * 1024  # Number of bytes per megabyte (>= 1).

# Default application settings
DEFAULT_APP_NAME = "Formula Recognition API"  # Display name for the FastAPI app.
DEFAULT_API_PREFIX = "/api/v1"  # Base prefix for API routes (leading slash required).
DEFAULT_API_VERSION = "0.1.0"  # Semantic version for the API service.
DEFAULT_LOG_LEVEL = "INFO"  # Logging level string (INFO, DEBUG, WARNING, ERROR).
DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173"
)  # Comma-separated frontend origins.
DEFAULT_LOG_SEPARATOR_LENGTH = 80  # Length of log separator lines (>= 10).
DEFAULT_DURATION_DECIMALS = 2  # Decimal places for timing logs (0-6 recommended).

# Model paths and selection
DEFAULT_MODEL_DIR = PROJECT_ROOT / "OtherInfo" / "ModelCode" / "model" / "checkpoints"  # Base path for model files.
DEFAULT_MODEL_CHECKPOINT_FILE = "best_acc.pt"  # Default checkpoint filename.
DEFAULT_MODEL_VOCAB_FILE = "vocab.json"  # Default vocabulary filename.

# Image preprocessing defaults
DEFAULT_IMAGE_HEIGHT = 128  # Default input height for model preprocessing (> 0).
DEFAULT_IMAGE_WIDTH = 512  # Default input width for model preprocessing (> 0).
DEFAULT_IMAGE_PADDING_FILL = 255  # Padding fill value for image background (0-255).
DEFAULT_IMAGE_NORMALIZE_MEAN_CSV = "0.5,0.5,0.5"  # Normalization mean per channel (0-1).
DEFAULT_IMAGE_NORMALIZE_STD_CSV = "0.5,0.5,0.5"  # Normalization std per channel (> 0).

# Decoding defaults
DEFAULT_MAX_DECODE_LEN = 256  # Maximum decode length for greedy decoding (> 0).

# Upload handling
DEFAULT_UPLOAD_DIR = PROJECT_ROOT / "uploaded_documents"  # Directory for uploaded files.
DEFAULT_MAX_UPLOAD_MB = 10  # Maximum upload size in megabytes (> 0).
DEFAULT_UPLOAD_CHUNK_MB = 1  # Upload read chunk size in megabytes (> 0).
DEFAULT_ALLOWED_IMAGE_TYPES = "image/png,image/jpeg,image/webp"  # Comma-separated allowed MIME types.
DEFAULT_ALLOWED_IMAGE_EXTENSIONS = ".png,.jpg,.jpeg,.webp"  # Comma-separated allowed file extensions.

# Text-to-speech defaults
DEFAULT_TTS_OUTPUT_DIR = PROJECT_ROOT / "generated_audio"  # Directory for generated audio files.
DEFAULT_TTS_RATE = 200  # Default speech rate in words per minute.
DEFAULT_TTS_VOLUME = 1.0  # Default speech volume (0.0-1.0).
DEFAULT_TTS_LANGUAGE = "en"  # Default language for text-to-speech.
DEFAULT_TTS_VOICE_ID = ""  # Default voice identifier (empty uses engine default).
DEFAULT_TTS_AUDIO_FORMAT = "wav"  # Audio format for generated speech files.

# LLM defaults
DEFAULT_LLM_PROVIDER = ""  # Default LLM provider identifier.
DEFAULT_LLM_MODEL = ""  # Default LLM model name.
DEFAULT_LLM_DEFAULT_MODEL = ""  # Backup LLM model name.
DEFAULT_LLM_TIMEOUT_MS = 60000  # Default LLM timeout in milliseconds.
DEFAULT_LLM_MAX_TOKENS = 4096  # Default maximum tokens for LLM output.
DEFAULT_LLM_TEMPERATURE = 0.2  # Default LLM temperature (0-2).
DEFAULT_LLM_TOP_P = 1.0  # Default LLM nucleus sampling probability (0-1).
DEFAULT_LLM_MAX_RETRIES = 2  # Default number of LLM retries.
DEFAULT_OPENAI_API_BASE = "https://api.openai.com"  # Default OpenAI API base URL.
DEFAULT_ANTHROPIC_API_BASE = "https://api.anthropic.com/v1/messages"  # Default Anthropic API URL.
DEFAULT_ANTHROPIC_API_VERSION = "2023-06-01"  # Default Anthropic API version header.
DEFAULT_HUGGINGFACE_API_BASE = "https://api-inference.huggingface.co/models"  # Hugging Face API base.
DEFAULT_COHERE_API_BASE = "https://api.cohere.ai/v1/generate"  # Cohere generate API URL.

# Device selection
DEFAULT_DEVICE_PREFERENCE = "auto"  # Device preference: auto, cpu, or cuda.
FLOAT_TRIPLET_LENGTH = 3  # Expected length for comma-separated float triplets.
FLOAT_TRIPLET_INDEX_FIRST = 0  # Index for first float in triplet.
FLOAT_TRIPLET_INDEX_SECOND = 1  # Index for second float in triplet.
FLOAT_TRIPLET_INDEX_THIRD = 2  # Index for third float in triplet.

# Error codes
ERROR_CODE_INVALID_FILE = "INVALID_FILE"  # Error code for malformed or missing file input.
ERROR_CODE_UNSUPPORTED_TYPE = "UNSUPPORTED_MEDIA_TYPE"  # Error code for unsupported file types.
ERROR_CODE_FILE_TOO_LARGE = "FILE_TOO_LARGE"  # Error code for uploads exceeding size limit.
ERROR_CODE_INVALID_IMAGE = "INVALID_IMAGE"  # Error code for unreadable image content.
ERROR_CODE_MODEL_NOT_READY = "MODEL_NOT_READY"  # Error code when model assets are unavailable.
ERROR_CODE_INFERENCE_FAILED = "INFERENCE_FAILED"  # Error code for inference failures.
ERROR_CODE_REQUEST_VALIDATION = "REQUEST_VALIDATION_FAILED"  # Error code for request validation errors.
ERROR_CODE_INVALID_TEXT = "INVALID_TEXT"  # Error code for invalid text input.
ERROR_CODE_UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"  # Error code for unsupported TTS language.
ERROR_CODE_TTS_FAILED = "TTS_FAILED"  # Error code for text-to-speech failures.
ERROR_CODE_INVALID_TTS_SETTINGS = "INVALID_TTS_SETTINGS"  # Error code for invalid TTS parameters.
ERROR_CODE_INVALID_LATEX = "INVALID_LATEX"  # Error code for invalid LaTeX input.
ERROR_CODE_LLM_CONFIG = "LLM_CONFIG_ERROR"  # Error code for missing LLM configuration.
ERROR_CODE_LLM_REQUEST = "LLM_REQUEST_FAILED"  # Error code for LLM request failures.
ERROR_CODE_LLM_RESPONSE = "LLM_RESPONSE_INVALID"  # Error code for invalid LLM responses.
ERROR_CODE_INVALID_REQUEST = "INVALID_REQUEST"  # Error code for malformed request payloads.

# Request metadata
REQUEST_ID_HEADER = "X-Request-ID"  # HTTP header name for the request identifier.


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default=DEFAULT_APP_NAME, description="FastAPI application name.")
    api_prefix: str = Field(default=DEFAULT_API_PREFIX, description="Base prefix for API routes.")
    api_version: str = Field(default=DEFAULT_API_VERSION, description="API semantic version.")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, description="Logging level string.")
    cors_allow_origins: str = Field(
        default=DEFAULT_CORS_ALLOW_ORIGINS,
        description="Comma-separated allowed CORS origins for browser clients.",
    )
    log_separator_length: int = Field(
        default=DEFAULT_LOG_SEPARATOR_LENGTH,
        description="Length of log separator lines.",
    )
    duration_decimals: int = Field(
        default=DEFAULT_DURATION_DECIMALS,
        description="Decimal precision for timing logs.",
    )
    model_dir: Path = Field(default=DEFAULT_MODEL_DIR, description="Base directory for model files.")
    model_checkpoint_file: str = Field(
        default=DEFAULT_MODEL_CHECKPOINT_FILE,
        description="Model checkpoint filename or relative path.",
    )
    model_vocab_file: str = Field(
        default=DEFAULT_MODEL_VOCAB_FILE,
        description="Vocabulary filename or relative path.",
    )
    image_height: int = Field(default=DEFAULT_IMAGE_HEIGHT, description="Default input image height.")
    image_width: int = Field(default=DEFAULT_IMAGE_WIDTH, description="Default input image width.")
    image_padding_fill: int = Field(
        default=DEFAULT_IMAGE_PADDING_FILL,
        description="Padding fill value for image background.",
    )
    image_normalize_mean: str = Field(
        default=DEFAULT_IMAGE_NORMALIZE_MEAN_CSV,
        description="Normalization mean per image channel, comma-separated.",
    )
    image_normalize_std: str = Field(
        default=DEFAULT_IMAGE_NORMALIZE_STD_CSV,
        description="Normalization std per image channel, comma-separated.",
    )
    max_decode_len: int = Field(default=DEFAULT_MAX_DECODE_LEN, description="Max decoding length.")
    upload_dir: Path = Field(default=DEFAULT_UPLOAD_DIR, description="Directory for uploads.")
    max_upload_mb: int = Field(default=DEFAULT_MAX_UPLOAD_MB, description="Max upload size in MB.")
    upload_chunk_mb: int = Field(
        default=DEFAULT_UPLOAD_CHUNK_MB,
        description="Upload read chunk size in MB.",
    )
    allowed_image_types: str = Field(
        default=DEFAULT_ALLOWED_IMAGE_TYPES,
        description="Comma-separated allowed MIME types.",
    )
    allowed_image_extensions: str = Field(
        default=DEFAULT_ALLOWED_IMAGE_EXTENSIONS,
        description="Comma-separated allowed file extensions.",
    )
    tts_output_dir: Path = Field(
        default=DEFAULT_TTS_OUTPUT_DIR,
        description="Directory for generated speech audio files.",
    )
    tts_rate: int = Field(default=DEFAULT_TTS_RATE, description="Default speech rate.")
    tts_volume: float = Field(default=DEFAULT_TTS_VOLUME, description="Default speech volume.")
    tts_default_language: str = Field(
        default=DEFAULT_TTS_LANGUAGE,
        description="Default language for text-to-speech.",
    )
    tts_voice_id: str = Field(
        default=DEFAULT_TTS_VOICE_ID,
        description="Default voice ID for text-to-speech.",
    )
    tts_audio_format: str = Field(
        default=DEFAULT_TTS_AUDIO_FORMAT,
        description="Audio format for generated speech files.",
    )
    llm_provider: str = Field(default=DEFAULT_LLM_PROVIDER, description="LLM provider identifier.")
    llm_model: str = Field(default=DEFAULT_LLM_MODEL, description="LLM model name.")
    llm_default_model: str = Field(default=DEFAULT_LLM_DEFAULT_MODEL, description="Fallback LLM model name.")
    openai_api_key: str = Field(default="", description="OpenAI API key.")
    openai_api_base: str = Field(default=DEFAULT_OPENAI_API_BASE, description="OpenAI API base URL.")
    openai_org: str = Field(default="", description="OpenAI organization ID.")
    azure_openai_key: str = Field(default="", description="Azure OpenAI API key.")
    azure_openai_endpoint: str = Field(default="", description="Azure OpenAI endpoint URL.")
    azure_openai_deployment: str = Field(default="", description="Azure OpenAI deployment name.")
    azure_openai_api_version: str = Field(default="", description="Azure OpenAI API version.")
    anthropic_api_key: str = Field(default="", description="Anthropic API key.")
    anthropic_api_base: str = Field(default=DEFAULT_ANTHROPIC_API_BASE, description="Anthropic API URL.")
    anthropic_api_version: str = Field(
        default=DEFAULT_ANTHROPIC_API_VERSION,
        description="Anthropic API version header.",
    )
    huggingface_api_key: str = Field(default="", description="Hugging Face API key.")
    huggingface_api_base: str = Field(
        default=DEFAULT_HUGGINGFACE_API_BASE,
        description="Hugging Face API base URL.",
    )
    cohere_api_key: str = Field(default="", description="Cohere API key.")
    cohere_api_base: str = Field(default=DEFAULT_COHERE_API_BASE, description="Cohere API URL.")
    llm_timeout_ms: int = Field(default=DEFAULT_LLM_TIMEOUT_MS, description="LLM timeout in milliseconds.")
    llm_max_tokens: int = Field(default=DEFAULT_LLM_MAX_TOKENS, description="LLM max tokens.")
    llm_temperature: float = Field(default=DEFAULT_LLM_TEMPERATURE, description="LLM temperature.")
    llm_top_p: float = Field(default=DEFAULT_LLM_TOP_P, description="LLM top-p value.")
    llm_max_retries: int = Field(default=DEFAULT_LLM_MAX_RETRIES, description="LLM max retries.")
    device_preference: str = Field(
        default=DEFAULT_DEVICE_PREFERENCE,
        description="Device preference: auto, cpu, or cuda.",
    )

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR.parent / ".env"),
        extra="ignore",
        env_ignore_empty=True,
    )

    def upload_chunk_bytes(self) -> int:
        """Return upload read chunk size in bytes."""
        return self.upload_chunk_mb * BYTES_PER_MB

    def max_upload_bytes(self) -> int:
        """Return maximum upload size in bytes."""
        return self.max_upload_mb * BYTES_PER_MB

    def allowed_image_types_list(self) -> List[str]:
        """Return allowed MIME types as a list."""
        return [item.strip() for item in self.allowed_image_types.split(",") if item.strip()]

    def cors_allow_origins_list(self) -> List[str]:
        """Return allowed CORS origins as a list."""
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]

    def allowed_image_extensions_list(self) -> List[str]:
        """Return allowed file extensions as a list."""
        return [item.strip().lower() for item in self.allowed_image_extensions.split(",") if item.strip()]

    def resolve_model_checkpoint_path(self) -> Path:
        """Return resolved path for the model checkpoint."""
        return self._resolve_relative_path(self.resolve_model_dir(), self.model_checkpoint_file)

    def resolve_model_vocab_path(self) -> Path:
        """Return resolved path for the model vocabulary."""
        return self._resolve_relative_path(self.resolve_model_dir(), self.model_vocab_file)

    def resolve_model_dir(self) -> Path:
        """Return resolved path for the model directory."""
        return self._resolve_relative_path(PROJECT_ROOT, str(self.model_dir))

    def resolve_upload_dir(self) -> Path:
        """Return resolved path for the upload directory."""
        return self._resolve_relative_path(PROJECT_ROOT, str(self.upload_dir))

    def resolve_tts_output_dir(self) -> Path:
        """Return resolved path for the TTS output directory."""
        return self._resolve_relative_path(PROJECT_ROOT, str(self.tts_output_dir))

    def normalize_mean_tuple(self) -> tuple[float, float, float]:
        """Return normalization mean as a tuple of floats."""
        return self._parse_float_triplet(self.image_normalize_mean)

    def normalize_std_tuple(self) -> tuple[float, float, float]:
        """Return normalization std as a tuple of floats."""
        return self._parse_float_triplet(self.image_normalize_std)

    @staticmethod
    def _resolve_relative_path(base_dir: Path, candidate: str) -> Path:
        """Resolve candidate as absolute or relative to base_dir."""
        path = Path(candidate)
        return path if path.is_absolute() else base_dir / path

    @staticmethod
    def _parse_float_triplet(csv_value: str) -> tuple[float, float, float]:
        """Parse a comma-separated triple of floats."""
        parts = [item.strip() for item in csv_value.split(",") if item.strip()]
        if len(parts) != FLOAT_TRIPLET_LENGTH:
            raise ValueError("Expected three comma-separated float values.")
        return (
            float(parts[FLOAT_TRIPLET_INDEX_FIRST]),
            float(parts[FLOAT_TRIPLET_INDEX_SECOND]),
            float(parts[FLOAT_TRIPLET_INDEX_THIRD]),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
