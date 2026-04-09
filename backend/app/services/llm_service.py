"""LLM service for converting LaTeX into spoken sentences."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from ..config import Settings

# Provider identifiers
LLM_PROVIDER_OPENAI = "openai"  # OpenAI-compatible provider.
LLM_PROVIDER_AZURE = "azure"  # Azure OpenAI provider.
LLM_PROVIDER_ANTHROPIC = "anthropic"  # Anthropic provider.
LLM_PROVIDER_HUGGINGFACE = "huggingface"  # Hugging Face Inference API.
LLM_PROVIDER_COHERE = "cohere"  # Cohere provider.
LLM_PROVIDER_LOCAL = "local"  # Local OpenAI-compatible provider.

# Prompt defaults
SYSTEM_PROMPT = (
    "You convert LaTeX math into a single spoken sentence. "
    "Return only the sentence without quotes, LaTeX, or extra commentary."
)  # System prompt for LLM guidance.
USER_PROMPT_TEMPLATE = "LaTeX: {latex}\nLanguage: {language}\nSentence:"  # User prompt template.

# OpenAI path handling
OPENAI_API_VERSION_PATH = "/v1"  # OpenAI API base path.

# Retry behavior
DEFAULT_RETRY_BACKOFF_MS = 500  # Initial backoff delay in milliseconds.
MAX_RETRY_BACKOFF_MS = 4000  # Maximum backoff delay in milliseconds.
RETRY_BACKOFF_MULTIPLIER = 2  # Exponential backoff multiplier.
RETRY_COUNTER_START = 0  # Initial retry counter.

# Response parsing
MIN_OUTPUT_LENGTH = 1  # Minimum length for LLM output.
PREFIX_ANSWER = "answer:"  # Prefix to strip from LLM output.
PREFIX_SENTENCE = "sentence:"  # Prefix to strip from LLM output.
PREFIX_BULLET = "- "  # Prefix for bullet responses.


@dataclass(frozen=True)
class LlmResult:
    """Result of LLM text generation."""

    text: str
    provider: str
    model: str


class LlmService:
    """Service wrapper for LLM requests."""

    def __init__(self, settings: Settings) -> None:
        """Initialize service with application settings."""
        self._settings = settings

    async def generate_spoken_text(self, latex: str, language: str) -> LlmResult:
        """Generate spoken sentence from LaTeX using the configured LLM."""
        normalized_latex = latex.strip()
        if not normalized_latex:
            raise InvalidLatexError("LaTeX input must not be empty.")
        provider = self._resolve_provider()
        model = self._resolve_model()
        prompt = USER_PROMPT_TEMPLATE.format(latex=normalized_latex, language=language)
        output = await self._request_with_retries(provider, model, prompt)
        sentence = _sanitize_output(output)
        if len(sentence) < MIN_OUTPUT_LENGTH:
            raise LlmResponseError("LLM output was empty.")
        return LlmResult(text=sentence, provider=provider, model=model)

    def _resolve_provider(self) -> str:
        """Return normalized provider identifier."""
        provider = self._settings.llm_provider.strip().lower()
        if not provider:
            raise LlmConfigError("LLM_PROVIDER is not configured.")
        return provider

    def _resolve_model(self) -> str:
        """Return the model identifier to use."""
        model = self._settings.llm_model.strip() or self._settings.llm_default_model.strip()
        if not model:
            raise LlmConfigError("LLM_MODEL or LLM_DEFAULT_MODEL must be configured.")
        return model

    async def _request_with_retries(self, provider: str, model: str, prompt: str) -> str:
        """Send the LLM request with retry logic."""
        timeout_seconds = self._settings.llm_timeout_ms / 1000
        retries = max(self._settings.llm_max_retries, RETRY_COUNTER_START)
        delay_ms = DEFAULT_RETRY_BACKOFF_MS
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            for attempt in range(RETRY_COUNTER_START, retries + 1):
                try:
                    return await self._dispatch_request(client, provider, model, prompt)
                except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                    if attempt >= retries:
                        raise LlmRequestError(str(exc)) from exc
                    await asyncio.sleep(delay_ms / 1000)
                    delay_ms = min(delay_ms * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_BACKOFF_MS)
        raise LlmRequestError("LLM request failed after retries.")

    async def _dispatch_request(
        self,
        client: httpx.AsyncClient,
        provider: str,
        model: str,
        prompt: str,
    ) -> str:
        """Dispatch request to the appropriate provider."""
        if provider == LLM_PROVIDER_OPENAI:
            return await _call_openai(client, self._settings, model, prompt)
        if provider == LLM_PROVIDER_AZURE:
            return await _call_azure_openai(client, self._settings, model, prompt)
        if provider == LLM_PROVIDER_ANTHROPIC:
            return await _call_anthropic(client, self._settings, model, prompt)
        if provider == LLM_PROVIDER_HUGGINGFACE:
            return await _call_huggingface(client, self._settings, model, prompt)
        if provider == LLM_PROVIDER_COHERE:
            return await _call_cohere(client, self._settings, model, prompt)
        if provider == LLM_PROVIDER_LOCAL:
            return await _call_openai(client, self._settings, model, prompt)
        raise LlmConfigError(f"Unsupported LLM_PROVIDER: {provider}")


class LlmError(Exception):
    """Base class for LLM errors."""


class InvalidLatexError(LlmError):
    """Raised when the LaTeX input is invalid."""


class LlmConfigError(LlmError):
    """Raised when LLM configuration is incomplete."""


class LlmRequestError(LlmError):
    """Raised when an LLM request fails."""


class LlmResponseError(LlmError):
    """Raised when an LLM response cannot be parsed."""


def _build_chat_payload(settings: Settings, model: str, prompt: str) -> Dict[str, Any]:
    """Build a chat-completions payload."""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": settings.llm_temperature,
        "top_p": settings.llm_top_p,
        "max_tokens": settings.llm_max_tokens,
    }


async def _call_openai(client: httpx.AsyncClient, settings: Settings, model: str, prompt: str) -> str:
    """Call OpenAI-compatible chat completion API."""
    if not settings.openai_api_key:
        raise LlmConfigError("OPENAI_API_KEY is not configured.")
    base = settings.openai_api_base.rstrip("/")
    api_base = base if base.endswith(OPENAI_API_VERSION_PATH) else f"{base}{OPENAI_API_VERSION_PATH}"
    url = f"{api_base}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    if settings.openai_org:
        headers["OpenAI-Organization"] = settings.openai_org
    payload = _build_chat_payload(settings, model, prompt)
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return _extract_openai_content(data)


async def _call_azure_openai(client: httpx.AsyncClient, settings: Settings, model: str, prompt: str) -> str:
    """Call Azure OpenAI chat completion API."""
    if not settings.azure_openai_key:
        raise LlmConfigError("AZURE_OPENAI_KEY is not configured.")
    if not settings.azure_openai_endpoint:
        raise LlmConfigError("AZURE_OPENAI_ENDPOINT is not configured.")
    deployment = settings.azure_openai_deployment.strip() or model
    if not deployment:
        raise LlmConfigError("AZURE_OPENAI_DEPLOYMENT is not configured.")
    api_version = settings.azure_openai_api_version.strip()
    if not api_version:
        raise LlmConfigError("AZURE_OPENAI_API_VERSION is not configured.")
    endpoint = settings.azure_openai_endpoint.rstrip("/")
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"
    params = {"api-version": api_version}
    headers = {"api-key": settings.azure_openai_key}
    payload = _build_chat_payload(settings, model, prompt)
    response = await client.post(url, headers=headers, params=params, json=payload)
    response.raise_for_status()
    data = response.json()
    return _extract_openai_content(data)


async def _call_anthropic(client: httpx.AsyncClient, settings: Settings, model: str, prompt: str) -> str:
    """Call Anthropic messages API."""
    if not settings.anthropic_api_key:
        raise LlmConfigError("ANTHROPIC_API_KEY is not configured.")
    url = settings.anthropic_api_base.rstrip("/")
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": settings.anthropic_api_version,
    }
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
        "top_p": settings.llm_top_p,
    }
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return _extract_anthropic_content(data)


async def _call_huggingface(client: httpx.AsyncClient, settings: Settings, model: str, prompt: str) -> str:
    """Call Hugging Face Inference API."""
    if not settings.huggingface_api_key:
        raise LlmConfigError("HUGGINGFACE_API_KEY is not configured.")
    base = settings.huggingface_api_base.rstrip("/")
    url = f"{base}/{model}"
    headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
    payload = {
        "inputs": f"{SYSTEM_PROMPT}\n{prompt}",
        "parameters": {
            "max_new_tokens": settings.llm_max_tokens,
            "temperature": settings.llm_temperature,
            "top_p": settings.llm_top_p,
            "return_full_text": False,
        },
    }
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return _extract_huggingface_content(data)


async def _call_cohere(client: httpx.AsyncClient, settings: Settings, model: str, prompt: str) -> str:
    """Call Cohere generate API."""
    if not settings.cohere_api_key:
        raise LlmConfigError("COHERE_API_KEY is not configured.")
    url = settings.cohere_api_base.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.cohere_api_key}"}
    payload = {
        "model": model,
        "prompt": f"{SYSTEM_PROMPT}\n{prompt}",
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
        "p": settings.llm_top_p,
    }
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return _extract_cohere_content(data)


def _extract_openai_content(data: Dict[str, Any]) -> str:
    """Extract content from OpenAI-style responses."""
    choices = data.get("choices", [])
    if not choices:
        raise LlmResponseError("OpenAI response missing choices.")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not content:
        raise LlmResponseError("OpenAI response missing content.")
    return str(content)


def _extract_anthropic_content(data: Dict[str, Any]) -> str:
    """Extract content from Anthropic responses."""
    content_items = data.get("content", [])
    if not content_items:
        raise LlmResponseError("Anthropic response missing content.")
    text = content_items[0].get("text")
    if not text:
        raise LlmResponseError("Anthropic response missing text.")
    return str(text)


def _extract_huggingface_content(data: Any) -> str:
    """Extract content from Hugging Face responses."""
    if isinstance(data, list) and data:
        text = data[0].get("generated_text")
        if text:
            return str(text)
    if isinstance(data, dict) and "generated_text" in data:
        return str(data["generated_text"])
    raise LlmResponseError("Hugging Face response missing generated text.")


def _extract_cohere_content(data: Dict[str, Any]) -> str:
    """Extract content from Cohere responses."""
    generations = data.get("generations", [])
    if not generations:
        raise LlmResponseError("Cohere response missing generations.")
    text = generations[0].get("text")
    if not text:
        raise LlmResponseError("Cohere response missing text.")
    return str(text)


def _sanitize_output(text: str) -> str:
    """Normalize the LLM output to a single sentence."""
    cleaned = text.strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()
    if "\n" in cleaned:
        cleaned = cleaned.splitlines()[0].strip()
    lowered = cleaned.lower()
    if lowered.startswith(PREFIX_ANSWER):
        cleaned = cleaned[len(PREFIX_ANSWER) :].strip()
        lowered = cleaned.lower()
    if lowered.startswith(PREFIX_SENTENCE):
        cleaned = cleaned[len(PREFIX_SENTENCE) :].strip()
        lowered = cleaned.lower()
    if cleaned.startswith(PREFIX_BULLET):
        cleaned = cleaned[len(PREFIX_BULLET) :].strip()
    return cleaned
