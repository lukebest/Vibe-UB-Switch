"""DLL (``rtl/dll``). CR-B token is ``dll``, not ``dl``. Stage-21: ``vibe_dll_credit``."""

from .vibe_bcrc import build as vibe_bcrc
from .vibe_dll_credit import build
from .vibe_dll_credit import build as vibe_dll_credit

__all__ = [
    "build",
    "vibe_bcrc",
    "vibe_dll_credit",
]
