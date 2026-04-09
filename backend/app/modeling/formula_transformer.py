"""Transformer model definition for formula recognition."""

from __future__ import annotations

import math
import torch
import torch.nn as nn
import torchvision.models as models

# Architecture defaults
DEFAULT_POS_ENCODING_MAX_LEN = 2048  # Maximum sequence length for positional encoding (> 0).
DEFAULT_D_MODEL = 256  # Default model dimension (> 0).
DEFAULT_NHEAD = 8  # Default number of attention heads (> 0).
DEFAULT_DECODER_LAYERS = 4  # Default number of decoder layers (> 0).
DEFAULT_FEEDFORWARD_DIM = 1024  # Default feedforward dimension (> 0).
DEFAULT_DROPOUT = 0.1  # Default dropout probability (0-1).
POS_ENCODING_BASE = 10000.0  # Base value for sinusoidal positional encoding (> 1).
POS_ENCODING_START = 0  # Start index for positional encoding ranges.
POS_ENCODING_STEP = 2  # Step size for even/odd positional encoding indices.
POS_ENCODING_ODD_START = 1  # Start index for odd positional encoding channels.
MASK_DIAGONAL_OFFSET = 1  # Diagonal offset for causal mask creation.
MASK_FILL_VALUE = 1  # Fill value for upper-triangular mask creation.
RESNET_FEATURE_DEPTH = 512  # Feature channel size from ResNet-18 backbone.
RESNET_TRUNCATE_LAYERS = 2  # Number of layers to drop from ResNet-18.


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding module."""

    def __init__(self, d_model: int, max_len: int = DEFAULT_POS_ENCODING_MAX_LEN) -> None:
        """Initialize positional encoding with model dimension and max length."""
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(POS_ENCODING_START, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(POS_ENCODING_START, d_model, POS_ENCODING_STEP).float()
            * (-math.log(POS_ENCODING_BASE) / d_model)
        )
        pe[:, POS_ENCODING_START::POS_ENCODING_STEP] = torch.sin(position * div_term)
        pe[:, POS_ENCODING_ODD_START::POS_ENCODING_STEP] = torch.cos(position * div_term)
        pe = pe.unsqueeze(1)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encodings to the input tensor."""
        seq_len = x.size(0)
        return x + self.pe[:seq_len]


class CNNEncoder(nn.Module):
    """CNN encoder that extracts visual features from input images."""

    def __init__(self, d_model: int = DEFAULT_D_MODEL) -> None:
        """Initialize the CNN encoder with projection to model dimension."""
        super().__init__()
        backbone = models.resnet18(weights=None)
        self.features = nn.Sequential(*list(backbone.children())[:-RESNET_TRUNCATE_LAYERS])
        self.proj = nn.Linear(RESNET_FEATURE_DEPTH, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode image tensor into a sequence of features."""
        f = self.features(x)
        batch_size, channels, height, width = f.shape
        f = f.permute(0, 2, 3, 1).contiguous().view(batch_size, height * width, channels)
        f = self.proj(f)
        return f


class FormulaTransformer(nn.Module):
    """Image-to-LaTeX transformer model."""

    def __init__(
        self,
        vocab_size: int,
        pad_id: int,
        d_model: int = DEFAULT_D_MODEL,
        nhead: int = DEFAULT_NHEAD,
        num_decoder_layers: int = DEFAULT_DECODER_LAYERS,
        dim_feedforward: int = DEFAULT_FEEDFORWARD_DIM,
        dropout: float = DEFAULT_DROPOUT,
    ) -> None:
        """Initialize the model with vocabulary size and decoder configuration."""
        super().__init__()
        self.pad_id = pad_id
        self.encoder = CNNEncoder(d_model=d_model)
        self.token_emb = nn.Embedding(vocab_size, d_model, padding_idx=pad_id)
        self.pos_enc_tgt = PositionalEncoding(d_model=d_model)
        self.pos_enc_mem = PositionalEncoding(d_model=d_model)
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=False,
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_decoder_layers)
        self.out = nn.Linear(d_model, vocab_size)

    @staticmethod
    def _generate_square_subsequent_mask(sz: int, device: torch.device) -> torch.Tensor:
        """Generate an upper-triangular mask for causal decoding."""
        mask = torch.triu(torch.ones(sz, sz, device=device), diagonal=MASK_DIAGONAL_OFFSET)
        mask = mask.masked_fill(mask == MASK_FILL_VALUE, float("-inf"))
        return mask

    def forward(
        self,
        images: torch.Tensor,
        tgt_input: torch.Tensor,
        tgt_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Run the model forward pass for decoding."""
        memory = self.encoder(images)
        memory = memory.transpose(0, 1)
        memory = self.pos_enc_mem(memory)
        tgt = self.token_emb(tgt_input)
        tgt = tgt.transpose(0, 1)
        tgt = self.pos_enc_tgt(tgt)
        tgt_mask = self._generate_square_subsequent_mask(tgt.size(0), tgt.device)
        decoded = self.decoder(
            tgt=tgt,
            memory=memory,
            tgt_mask=tgt_mask,
            tgt_key_padding_mask=tgt_padding_mask,
        )
        logits = self.out(decoded).transpose(0, 1)
        return logits
