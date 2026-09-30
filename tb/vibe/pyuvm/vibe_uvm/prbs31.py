"""TB golden for PMA pin-idle PRBS31 (SPEC §4.4 / CR-PMA-IDLE-PRBS31).

Integer helpers match ``rtl/pma/vibe_pma_bnd.sv`` and
``pycircuit/pma/prbs31.py``:

  Poly: x^31 + x^28 + 1. Step: ``{s[29:0], s[30] ^ s[27]}`` (31-bit).
  Per-lane seed: ``{27'd1, lid[1:0], 2'b01}`` for lid=0..3.

No ``PMA_IDLE_MARK`` XOR. RX idle is the PRBS31 recurrence on each
128b slice (no un-XOR). PCS scramble(0) PRBS23 is not pin-idle.
"""

from __future__ import annotations

PRBS31_W = 31
PMA_LANE_W = 128
MASK128 = (1 << PMA_LANE_W) - 1
MASK512 = (1 << 512) - 1


def prbs31_seed_int(lid: int) -> int:
    """``{27'd1, lid[1:0], 2'b01}``."""
    return (1 << 4) | ((lid & 0x3) << 2) | 0x1


def prbs31_step_int(s: int) -> int:
    """One LFSR step: ``{s[30:0], s[30] ^ s[27]}`` (31-bit result)."""
    fb = ((s >> 30) ^ (s >> 27)) & 1
    return ((s << 1) & ((1 << PRBS31_W) - 1)) | fb


def prbs31_word_int(s: int) -> int:
    """128b window: bit *i* is LFSR[0] after *i* steps (LSB first)."""
    t = s & ((1 << PRBS31_W) - 1)
    w = 0
    for i in range(PMA_LANE_W):
        w |= (t & 1) << i
        t = prbs31_step_int(t)
    return w


def prbs31_adv128_int(s: int) -> int:
    t = s & ((1 << PRBS31_W) - 1)
    for _ in range(PMA_LANE_W):
        t = prbs31_step_int(t)
    return t


def prbs31_word_ok_int(w: int) -> bool:
    """Recurrence: ``w[i] == w[i-31] ^ w[i-28]`` for i=31..127."""
    for i in range(31, PMA_LANE_W):
        if ((w >> i) & 1) != (((w >> (i - 31)) ^ (w >> (i - 28))) & 1):
            return False
    return True


def prbs31_pack4(s0: int, s1: int, s2: int, s3: int) -> int:
    """512b concat: [127:0]=lane0 … [511:384]=lane3."""
    return (
        (prbs31_word_int(s3) << 384)
        | (prbs31_word_int(s2) << 256)
        | (prbs31_word_int(s1) << 128)
        | prbs31_word_int(s0)
    ) & MASK512


def prbs31_pack_ok(w: int) -> bool:
    for i in range(4):
        if not prbs31_word_ok_int((w >> (128 * i)) & MASK128):
            return False
    return True


def prbs31_seed_states() -> list[int]:
    return [prbs31_seed_int(lid) for lid in range(4)]


def prbs31_advance_states(states: list[int]) -> list[int]:
    return [prbs31_adv128_int(s) for s in states]


def prbs31_pack_states(states: list[int]) -> int:
    return prbs31_pack4(states[0], states[1], states[2], states[3])
