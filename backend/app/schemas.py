"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

MIN_TEXT_LENGTH = 1  # Minimum accepted length for text-to-speech input.
MIN_LATEX_LENGTH = 1  # Minimum accepted length for LaTeX input.


class ImageSize(BaseModel):
    """Image size configuration used for model preprocessing."""

    height: int = Field(
        ...,
        description="Image height used for preprocessing in pixels.",
        json_schema_extra={"example": 128},
    )
    width: int = Field(
        ...,
        description="Image width used for preprocessing in pixels.",
        json_schema_extra={"example": 512},
    )


class ModelInfo(BaseModel):
    """Metadata about the model used for inference."""

    checkpoint: str = Field(
        ...,
        description="Model checkpoint path.",
        json_schema_extra={"example": "OtherInfo/ModelCode/model/checkpoints/best_acc.pt"},
    )
    vocab: str = Field(
        ...,
        description="Vocabulary path.",
        json_schema_extra={"example": "OtherInfo/ModelCode/model/checkpoints/vocab.json"},
    )
    device: str = Field(
        ...,
        description="Device used for inference.",
        json_schema_extra={"example": "cpu"},
    )


class InferenceResponse(BaseModel):
    """Response schema for LaTeX inference."""

    request_id: str = Field(
        ...,
        description="Unique request identifier.",
        json_schema_extra={"example": "096075d5-fd52-4571-b979-b6e45acb9768"},
    )
    latex: str = Field(
        ...,
        description="Predicted LaTeX string.",
        json_schema_extra={"example": "\\\\frac{8}{5} \\\\times 3 = \\\\frac{24}{5}"},
    )
    image_size: ImageSize = Field(..., description="Image size used for preprocessing.")
    model: ModelInfo = Field(..., description="Model metadata.")
    duration_ms: float = Field(..., description="Inference duration in milliseconds.")


class ErrorInfo(BaseModel):
    """Structured error response details."""

    code: str = Field(
        ...,
        description="Application-specific error code.",
        json_schema_extra={"example": "INVALID_REQUEST"},
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
        json_schema_extra={"example": "Invalid JSON. Escape backslashes in LaTeX (\\\\)."},
    )
    details: str | None = Field(default=None, description="Additional error details.")
    request_id: str | None = Field(default=None, description="Request identifier for tracing.")


class ErrorResponse(BaseModel):
    """Error response wrapper."""

    error: ErrorInfo = Field(..., description="Error payload.")


class TextToSpeechRequest(BaseModel):
    """Request schema for text-to-speech synthesis."""

    text: str = Field(
        ...,
        description="Text to synthesize into speech.",
        min_length=MIN_TEXT_LENGTH,
        json_schema_extra={"example": "What is eight-fifths multiplied by three?"},
    )
    language: str | None = Field(
        default=None,
        description="Language code for voice matching (e.g., en, zh, yue).",
        json_schema_extra={"example": "en"},
    )
    voice_id: str | None = Field(
        default=None,
        description="Explicit voice ID override (uses system voice list).",
    )
    rate: int | None = Field(
        default=None,
        description="Speech rate override in words per minute (50-400).",
        json_schema_extra={"example": 200},
    )
    volume: float | None = Field(
        default=None,
        description="Speech volume override (0.0-1.0).",
        json_schema_extra={"example": 1.0},
    )


class VoiceInfo(BaseModel):
    """Voice metadata for text-to-speech selection."""

    id: str = Field(..., description="Voice identifier.", json_schema_extra={"example": "HKEY_LOCAL_MACHINE\\SOFTWARE\\..."} )
    name: str = Field(..., description="Voice display name.", json_schema_extra={"example": "Microsoft David Desktop"} )
    languages: list[str] = Field(
        ...,
        description="Raw language tags provided by the system voice.",
        json_schema_extra={"example": ["en_US"]},
    )


class VoiceListResponse(BaseModel):
    """Response schema for available voices."""

    voices: list[VoiceInfo] = Field(..., description="Available system voices.")


class LatexToSpeechRequest(BaseModel):
    """Request schema for LaTeX-to-speech text conversion."""

    latex: str = Field(
        ...,
        description=(
            "LaTeX expression to convert. In JSON, escape backslashes (\\\\). "
            "Alternatively send text/plain body."
        ),
        min_length=MIN_LATEX_LENGTH,
        json_schema_extra={"example": "\\\\frac{8}{5} \\\\times 3 = \\\\frac{24}{5}"},
    )
    language: str | None = Field(
        default=None,
        description="Target language for spoken sentence (e.g., en, zh, yue).",
        json_schema_extra={"example": "en"},
    )


class LlmInfo(BaseModel):
    """Metadata about the LLM used for conversion."""

    provider: str = Field(
        ...,
        description="LLM provider identifier.",
        json_schema_extra={"example": "openai"},
    )
    model: str = Field(
        ...,
        description="LLM model name.",
        json_schema_extra={"example": "gpt-4o-mini"},
    )


class LatexToSpeechResponse(BaseModel):
    """Response schema for LaTeX-to-speech text conversion."""

    request_id: str = Field(
        ...,
        description="Unique request identifier.",
        json_schema_extra={"example": "096075d5-fd52-4571-b979-b6e45acb9768"},
    )
    sentence: str = Field(
        ...,
        description="Spoken sentence derived from LaTeX.",
        json_schema_extra={"example": "What is eight-fifths multiplied by three?"},
    )
    llm: LlmInfo = Field(..., description="LLM metadata.")
    duration_ms: float = Field(..., description="Conversion duration in milliseconds.")
