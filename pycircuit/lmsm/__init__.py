"""LMSM (``rtl/lmsm``). Stage-49: ``vibe_lmsm`` (AS-0.1 §11 this-rev subset). Leaf FSM — no children."""

from .vibe_lmsm import build
from .vibe_lmsm import build as vibe_lmsm

__all__ = [
    "build",
    "vibe_lmsm",
]
