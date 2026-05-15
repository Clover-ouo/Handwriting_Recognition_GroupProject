"""Inference service for handwritten formula recognition."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image
from torchvision import transforms

from ..config import Settings
from ..modeling.formula_transformer import FormulaTransformer

# Image processing constants
DEFAULT_RESIZE_FILTER = Image.Resampling.LANCZOS  # Resampling filter for resizing.
HALF_DIVISOR = 2  # Divisor used to split padding on both sides.
TOKEN_START_INDEX = 1  # Start index for decoding token sequences.
BATCH_INDEX = 0  # Index for selecting the first batch item.
LAST_INDEX = -1  # Index for selecting the last token in a sequence.


@dataclass(frozen=True)
class ModelArtifacts:
    """Container for loaded model and vocabulary assets."""

    model: FormulaTransformer
    stoi: Dict[str, int]
    itos: Dict[int, str]
    pad_id: int
    bos_id: int
    eos_id: int


class ModelService:
    """Service to load models and run inference."""

    def __init__(self, settings: Settings) -> None:
        """Initialize service with application settings."""
        self._settings = settings
        self._artifacts: ModelArtifacts | None = None
        self._device: torch.device | None = None

    def load(self) -> None:
        """Load model checkpoint and vocabulary into memory."""
        checkpoint_path = self._settings.resolve_model_checkpoint_path()
        vocab_path = self._settings.resolve_model_vocab_path()
        self._validate_readable_file(checkpoint_path)
        self._validate_readable_file(vocab_path)
        self._device = _select_device(self._settings.device_preference)
        stoi, itos = _load_vocab(vocab_path)
        pad_id = stoi["<pad>"]
        bos_id = stoi["<bos>"]
        eos_id = stoi["<eos>"]
        model = _load_model(checkpoint_path, len(stoi), pad_id, self._device)
        self._artifacts = ModelArtifacts(
            model=model,
            stoi=stoi,
            itos=itos,
            pad_id=pad_id,
            bos_id=bos_id,
            eos_id=eos_id,
        )

    def is_loaded(self) -> bool:
        """Return True when model assets are loaded."""
        return self._artifacts is not None and self._device is not None

    def device_name(self) -> str:
        """Return the device name used for inference."""
        if self._device is None:
            return "unknown"
        return str(self._device)

    def predict(self, image: Image.Image, target_height: int, target_width: int, max_len: int) -> str:
        """Run inference and return the predicted LaTeX string."""
        if self._artifacts is None or self._device is None:
            raise RuntimeError("Model artifacts are not loaded.")
        transform = _build_transform(
            target_height=target_height,
            target_width=target_width,
            padding_fill=self._settings.image_padding_fill,
            normalize_mean=self._settings.normalize_mean_tuple(),
            normalize_std=self._settings.normalize_std_tuple(),
        )
        image_tensor = transform(image).unsqueeze(0).to(self._device)
        ids = _greedy_decode(
            model=self._artifacts.model,
            image_tensor=image_tensor,
            bos_id=self._artifacts.bos_id,
            eos_id=self._artifacts.eos_id,
            pad_id=self._artifacts.pad_id,
            max_len=max_len,
            device=self._device,
        )
        tokens = _decode_tokens(ids, self._artifacts.itos, self._artifacts.eos_id)
        return " ".join(tokens)

    def ensure_upload_dir(self) -> None:
        """Create upload directory if needed and validate write permissions."""
        upload_dir = self._settings.resolve_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        if not upload_dir.is_dir():
            raise NotADirectoryError(f"Upload path is not a directory: {upload_dir}")
        if not os.access(upload_dir, os.W_OK):
            raise PermissionError(f"Upload directory is not writable: {upload_dir}")

    def save_upload(self, filename: str, data: bytes, request_id: str) -> Path:
        """Save upload bytes to disk and return saved path."""
        safe_name = Path(filename).name if filename else f"{request_id}.bin"
        target_path = self._settings.resolve_upload_dir() / f"{request_id}_{safe_name}"
        with target_path.open("wb") as f:
            f.write(data)
        return target_path

    @staticmethod
    def _validate_readable_file(path: Path) -> None:
        """Validate that a file exists and is readable."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not os.access(path, os.R_OK):
            raise PermissionError(f"File is not readable: {path}")


def _select_device(preference: str) -> torch.device:
    """Select device based on preference and availability."""
    normalized = preference.strip().lower()
    if normalized == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if normalized == "cpu":
        return torch.device("cpu")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_vocab(vocab_path: Path) -> tuple[Dict[str, int], Dict[int, str]]:
    """Load vocabulary mappings from JSON file."""
    with vocab_path.open("r", encoding="utf-8") as f:
        vocab_obj = json.load(f)
    stoi = vocab_obj["stoi"]
    itos = {int(k): v for k, v in vocab_obj["itos"].items()}
    return stoi, itos


def _load_model(
    checkpoint_path: Path,
    vocab_size: int,
    pad_id: int,
    device: torch.device,
) -> FormulaTransformer:
    """Load model weights from a checkpoint file."""
    ckpt = torch.load(checkpoint_path, map_location=device)
    cfg = ckpt["config"]
    model = FormulaTransformer(
        vocab_size=vocab_size,
        pad_id=pad_id,
        d_model=cfg["d_model"],
        nhead=cfg["nhead"],
        num_decoder_layers=cfg["decoder_layers"],
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model


def _build_transform(
    target_height: int,
    target_width: int,
    padding_fill: int,
    normalize_mean: tuple[float, float, float],
    normalize_std: tuple[float, float, float],
) -> transforms.Compose:
    """Create image preprocessing pipeline."""
    return transforms.Compose(
        [
            transforms.Lambda(
                lambda img: _resize_with_padding(
                    img=img,
                    target_height=target_height,
                    target_width=target_width,
                    fill=padding_fill,
                )
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=normalize_mean, std=normalize_std),
        ]
    )


def _resize_with_padding(img: Image.Image, target_height: int, target_width: int, fill: int) -> Image.Image:
    """Resize image with aspect ratio preserved and pad to target size."""
    img_width, img_height = img.size
    scale = min(target_width / img_width, target_height / img_height)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    resized = img.resize((new_width, new_height), DEFAULT_RESIZE_FILTER)
    delta_width = target_width - new_width
    delta_height = target_height - new_height
    padding = (
        delta_width // HALF_DIVISOR,
        delta_height // HALF_DIVISOR,
        delta_width - delta_width // HALF_DIVISOR,
        delta_height - delta_height // HALF_DIVISOR,
    )
    return transforms.functional.pad(resized, padding, fill=fill)


def _greedy_decode(
    model: FormulaTransformer,
    image_tensor: torch.Tensor,
    bos_id: int,
    eos_id: int,
    pad_id: int,
    max_len: int,
    device: torch.device,
) -> List[int]:
    """Greedy decode the model output token IDs."""
    model.eval()
    tokens = [bos_id]
    with torch.no_grad():
        for _ in range(max_len):
            tgt_input = torch.tensor([tokens], dtype=torch.long, device=device)
            tgt_padding_mask = tgt_input.eq(pad_id)
            logits = model(image_tensor, tgt_input, tgt_padding_mask=tgt_padding_mask)
            next_id = int(torch.argmax(logits[BATCH_INDEX, LAST_INDEX]).item())
            tokens.append(next_id)
            if next_id == eos_id:
                break
    return tokens


def _decode_tokens(token_ids: List[int], itos: Dict[int, str], eos_id: int) -> List[str]:
    """Convert token IDs to LaTeX token strings."""
    tokens: List[str] = []
    for token_id in token_ids[TOKEN_START_INDEX:]:
        if token_id == eos_id:
            break
        tokens.append(itos.get(token_id, "<unk>"))
    return tokens
