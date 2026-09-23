"""PCS (``rtl/pcs``). Stage-7: ``vibe_pcs_scramble``. Stage-8: ``vibe_ebch16``. Stage-9: ``vibe_pcs_tx_cw2beat``. Stage-10: ``vibe_pcs_tx_amctl``. Stage-11: ``vibe_rs128_120_enc``. Stage-12: ``vibe_rs128_120_dec``. Leave tx/pack/FEC wrap/g1/rx/amctl_lock/deskew/unpack for later."""

from .vibe_pcs_scramble import build
from .vibe_pcs_scramble import build as vibe_pcs_scramble
from .vibe_ebch16 import build as vibe_ebch16
from .vibe_pcs_tx_cw2beat import build as vibe_pcs_tx_cw2beat
from .vibe_pcs_tx_amctl import build as vibe_pcs_tx_amctl
from .vibe_rs128_120_enc import build as vibe_rs128_120_enc
from .vibe_rs128_120_dec import build as vibe_rs128_120_dec

__all__ = [
    "build",
    "vibe_pcs_scramble",
    "vibe_ebch16",
    "vibe_pcs_tx_cw2beat",
    "vibe_pcs_tx_amctl",
    "vibe_rs128_120_enc",
    "vibe_rs128_120_dec",
]
