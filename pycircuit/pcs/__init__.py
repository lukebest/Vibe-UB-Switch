"""PCS (``rtl/pcs``). Stage-7: ``vibe_pcs_scramble``. Stage-8: ``vibe_ebch16``. Stage-9: ``vibe_pcs_tx_cw2beat``. Stage-10: ``vibe_pcs_tx_amctl``. Stage-11: ``vibe_rs128_120_enc``. Stage-12: ``vibe_rs128_120_dec``. Stage-13: ``vibe_pcs_rx_deskew``. Stage-14: ``vibe_pcs_rx_amctl_lock``. Leave tx/pack/FEC wrap/g1/rx/unpack for later."""

from .vibe_pcs_scramble import build
from .vibe_pcs_scramble import build as vibe_pcs_scramble
from .vibe_ebch16 import build as vibe_ebch16
from .vibe_pcs_tx_cw2beat import build as vibe_pcs_tx_cw2beat
from .vibe_pcs_tx_amctl import build as vibe_pcs_tx_amctl
from .vibe_rs128_120_enc import build as vibe_rs128_120_enc
from .vibe_rs128_120_dec import build as vibe_rs128_120_dec
from .vibe_pcs_rx_deskew import build as vibe_pcs_rx_deskew
from .vibe_pcs_rx_amctl_lock import build as vibe_pcs_rx_amctl_lock

__all__ = [
    "build",
    "vibe_pcs_scramble",
    "vibe_ebch16",
    "vibe_pcs_tx_cw2beat",
    "vibe_pcs_tx_amctl",
    "vibe_rs128_120_enc",
    "vibe_rs128_120_dec",
    "vibe_pcs_rx_deskew",
    "vibe_pcs_rx_amctl_lock",
]
