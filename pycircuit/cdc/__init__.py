"""CDC leaves (``rtl/cdc``). Stage-1: ``vibe_afifo``. Stage-3: ``vibe_sync2``. Stage-4: ``vibe_rst_sync``."""

from .vibe_afifo import build
from .vibe_afifo import build as vibe_afifo
from .vibe_sync2 import build as vibe_sync2
from .vibe_rst_sync import build as vibe_rst_sync

__all__ = ["build", "vibe_afifo", "vibe_sync2", "vibe_rst_sync"]
