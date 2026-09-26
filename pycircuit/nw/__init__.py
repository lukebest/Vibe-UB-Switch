"""Network adapt (``rtl/nw``). Stage-36: ``vibe_icrc``. Stage-37: ``vibe_nw_adapt``."""

from .vibe_icrc import build as vibe_icrc
from .vibe_nw_adapt import build
from .vibe_nw_adapt import build as vibe_nw_adapt

__all__ = [
    "build",
    "vibe_icrc",
    "vibe_nw_adapt",
]
