"""PCS (``rtl/pcs``). Stage-7: ``vibe_pcs_scramble``. Stage-8: ``vibe_ebch16``. Stage-9: ``vibe_pcs_tx_cw2beat``. Stage-10: ``vibe_pcs_tx_amctl``. Leave tx/pack/FEC/RS/rx for later."""

from .vibe_pcs_scramble import build
from .vibe_pcs_scramble import build as vibe_pcs_scramble
from .vibe_ebch16 import build as vibe_ebch16
from .vibe_pcs_tx_cw2beat import build as vibe_pcs_tx_cw2beat
from .vibe_pcs_tx_amctl import build as vibe_pcs_tx_amctl

__all__ = [
    "build",
    "vibe_pcs_scramble",
    "vibe_ebch16",
    "vibe_pcs_tx_cw2beat",
    "vibe_pcs_tx_amctl",
]
