"""Shared compile-time constants and helpers (``rtl/common``)."""

from .params import (
    VIBE_AFIFO_AFULL_OCC,
    VIBE_AFIFO_DEPTH,
    VIBE_AFIFO_PTR_W,
    VIBE_LANE_FAB_W,
    VIBE_LANE_PMA_W,
    VIBE_N_LANE,
    VIBE_PMA_W,
)
from .gray import vibe_bin2gray5, vibe_gray2bin5

__all__ = [
    "VIBE_AFIFO_AFULL_OCC",
    "VIBE_AFIFO_DEPTH",
    "VIBE_AFIFO_PTR_W",
    "VIBE_LANE_FAB_W",
    "VIBE_LANE_PMA_W",
    "VIBE_N_LANE",
    "VIBE_PMA_W",
    "vibe_bin2gray5",
    "vibe_gray2bin5",
]
