"""DLL (``rtl/dll``). CR-B token is ``dll``, not ``dl``. Stage-20: ``vibe_bcrc``."""

from .vibe_bcrc import build
from .vibe_bcrc import build as vibe_bcrc

__all__ = [
    "build",
    "vibe_bcrc",
]
