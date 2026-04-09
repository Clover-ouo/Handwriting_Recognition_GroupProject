"""Text-to-speech service using an open-source offline engine."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List, Dict, Any

import pyttsx3

from ..config import Settings

# Voice selection defaults
DEFAULT_VOICE_ALIAS = "default"  # Alias used when no language is provided.

# Output formatting
AUDIO_EXTENSION_SEPARATOR = "."  # Separator for file extension.
SUPPORTED_TTS_AUDIO_FORMATS = ("wav",)  # Supported output audio formats.
EMPTY_FILE_SIZE_BYTES = 0  # Expected file size for empty outputs.

# Validation limits
MIN_TEXT_LENGTH = 1  # Minimum accepted text length.
MIN_TTS_RATE = 50  # Minimum speech rate in words per minute.
MAX_TTS_RATE = 400  # Maximum speech rate in words per minute.
MIN_TTS_VOLUME = 0.0  # Minimum volume (0.0).
MAX_TTS_VOLUME = 1.0  # Maximum volume (1.0).

# Language alias groups
LANGUAGE_ALIASES = {
    "en": ("en", "english"),
    "zh": ("zh", "zh-cn", "chinese", "mandarin", "cmn"),
    "yue": ("yue", "cantonese", "zh-hk", "zh-yue"),
}

# Tokenization
TOKEN_SPLIT_PATTERN = r"[\s\-]+"  # Pattern used to split voice metadata into tokens.
VOICE_ID_NOT_FOUND_HINT = "Use /api/v1/speech/voices to list available voice IDs."  # Hint for invalid voice IDs.
VOICE_LANGUAGE_UNKNOWN = "unknown"  # Placeholder for unknown language entries.


class TextToSpeechService:
    """Service wrapper for text-to-speech synthesis."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the service with application settings."""
        self._settings = settings

    def ensure_output_dir(self) -> Path:
        """Ensure the TTS output directory exists and is writable."""
        output_dir = self._settings.resolve_tts_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        if not output_dir.is_dir():
            raise NotADirectoryError(f"TTS output path is not a directory: {output_dir}")
        if not os.access(output_dir, os.W_OK):
            raise PermissionError(f"TTS output directory is not writable: {output_dir}")
        return output_dir

    def synthesize_to_file(
        self,
        text: str,
        request_id: str,
        language: str,
        voice_id: str | None,
        rate: int,
        volume: float,
    ) -> Path:
        """Generate speech audio and return the saved file path."""
        normalized_text = text.strip()
        if len(normalized_text) < MIN_TEXT_LENGTH:
            raise InvalidTextError("Text must not be empty.")
        _validate_rate(rate)
        _validate_volume(volume)
        _validate_audio_format(self._settings.tts_audio_format)
        output_dir = self.ensure_output_dir()
        output_path = output_dir / f"{request_id}{AUDIO_EXTENSION_SEPARATOR}{self._settings.tts_audio_format}"
        engine = pyttsx3.init()
        _apply_voice(engine, language, voice_id)
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        engine.save_to_file(normalized_text, str(output_path))
        engine.runAndWait()
        if not output_path.exists():
            raise TtsGenerationError("TTS output file was not created.")
        if output_path.stat().st_size == EMPTY_FILE_SIZE_BYTES:
            raise TtsGenerationError("TTS output file is empty.")
        return output_path

    @staticmethod
    def cleanup_file(path: Path) -> None:
        """Remove a temporary audio file if it exists."""
        if path.exists():
            path.unlink()

    def list_voices(self) -> List[Dict[str, Any]]:
        """Return available system voices with metadata."""
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        return [
            {
                "id": voice.id,
                "name": voice.name,
                "languages": _extract_voice_languages(voice),
            }
            for voice in voices
        ]


def _validate_rate(rate: int) -> None:
    """Validate speech rate range."""
    if rate < MIN_TTS_RATE or rate > MAX_TTS_RATE:
        raise InvalidTtsSettingsError(
            f"Speech rate must be between {MIN_TTS_RATE} and {MAX_TTS_RATE}."
        )


def _validate_volume(volume: float) -> None:
    """Validate speech volume range."""
    if volume < MIN_TTS_VOLUME or volume > MAX_TTS_VOLUME:
        raise InvalidTtsSettingsError(
            f"Speech volume must be between {MIN_TTS_VOLUME} and {MAX_TTS_VOLUME}."
        )


def _validate_audio_format(audio_format: str) -> None:
    """Validate supported audio format."""
    normalized = audio_format.strip().lower()
    if normalized not in SUPPORTED_TTS_AUDIO_FORMATS:
        raise InvalidTtsSettingsError(f"Unsupported audio format: {audio_format}")


def _apply_voice(engine: pyttsx3.Engine, language: str, voice_id: str | None) -> None:
    """Select and apply a voice based on language or explicit voice ID."""
    voices = engine.getProperty("voices")
    if voice_id:
        match = next((voice for voice in voices if voice.id == voice_id), None)
        if match is None:
            raise InvalidTtsSettingsError(
                f"Specified voice ID was not found. {VOICE_ID_NOT_FOUND_HINT}"
            )
        engine.setProperty("voice", match.id)
        return
    normalized_language = _normalize_language(language)
    if normalized_language == DEFAULT_VOICE_ALIAS:
        return
    aliases = LANGUAGE_ALIASES.get(normalized_language, (normalized_language,))
    selected = _select_voice_by_aliases(voices, aliases)
    if selected is None:
        raise UnsupportedLanguageError(f"No available voice for language: {language}")
    engine.setProperty("voice", selected.id)


class TextToSpeechError(Exception):
    """Base class for text-to-speech errors."""


class InvalidTextError(TextToSpeechError):
    """Raised when the input text is invalid."""


class InvalidTtsSettingsError(TextToSpeechError):
    """Raised when TTS settings such as rate or volume are invalid."""


class UnsupportedLanguageError(TextToSpeechError):
    """Raised when a language-specific voice cannot be found."""


class TtsGenerationError(TextToSpeechError):
    """Raised when speech generation fails."""


def _select_voice_by_aliases(voices: Iterable, aliases: Iterable[str]):
    """Return the first voice whose metadata contains any alias token."""
    normalized_aliases = [alias.lower() for alias in aliases]
    for voice in voices:
        tokens = _voice_tokens(voice)
        if any(alias in tokens for alias in normalized_aliases):
            return voice
    return None


def _voice_tokens(voice) -> set[str]:
    """Extract searchable tokens from a voice object."""
    tokens = set()
    tokens.update(_split_tokens(str(getattr(voice, "id", ""))))
    tokens.update(_split_tokens(str(getattr(voice, "name", ""))))
    languages = getattr(voice, "languages", [])
    for entry in languages:
        text = entry.decode("utf-8", errors="ignore") if isinstance(entry, (bytes, bytearray)) else str(entry)
        tokens.update(_split_tokens(text))
    return tokens


def _extract_voice_languages(voice) -> List[str]:
    """Extract raw language entries from a voice object."""
    languages = getattr(voice, "languages", [])
    result = []
    for entry in languages:
        text = entry.decode("utf-8", errors="ignore") if isinstance(entry, (bytes, bytearray)) else str(entry)
        cleaned = text.strip()
        result.append(cleaned if cleaned else VOICE_LANGUAGE_UNKNOWN)
    return result


def _split_tokens(text: str) -> set[str]:
    """Split text into lowercase tokens."""
    normalized = text.lower().replace("_", "-")
    return {segment for segment in re.split(TOKEN_SPLIT_PATTERN, normalized) if segment}


def _normalize_language(language: str) -> str:
    """Normalize language input for matching."""
    normalized = language.strip().lower()
    return normalized if normalized else DEFAULT_VOICE_ALIAS
