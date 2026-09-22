"""5-bit gray helpers matching ``vibe_bin2gray5`` / ``vibe_gray2bin5``.

Used by ``vibe_afifo``. Same functions live in ``rtl/common/vibe_ub_fn.vh``.
"""

from __future__ import annotations

from pycircuit import Circuit


def vibe_bin2gray5(m: Circuit, b):
    """``(b >> 1) ^ b`` on 5 bits (AS-0.1 §7)."""
    _ = m
    return (b >> 1) ^ b


def vibe_gray2bin5(m: Circuit, g):
    """Prefix-XOR degray, MSB first. Matches ``vibe_ub_fn.vh``."""
    b4 = g[4]
    b3 = b4 ^ g[3]
    b2 = b3 ^ g[2]
    b1 = b2 ^ g[1]
    b0 = b1 ^ g[0]
    return m.cat(b4, b3, b2, b1, b0)
