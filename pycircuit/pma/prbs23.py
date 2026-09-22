"""PRBS23 helpers matching ``rtl/pma/vibe_pma_bnd.sv`` product functions.

Poly is x^23+x^18+1 (``s[22] ^ s[17]`` feedback). Seed is
``{19'd1, lid[1:0], 2'b01}`` — same as ``vibe_pcs_scramble``. Pin-idle
XORs ``PMA_IDLE_MARK`` so decorated idle is not a raw PRBS / scramble(0)
window (issue #115).
"""

from __future__ import annotations

from pycircuit import Circuit, u

# Not itself a PRBS23 word. MSB-only mark; RX un-XORs before recurrence.
PMA_IDLE_MARK = 1 << 127
PRBS23_W = 23
PMA_LANE_W = 128


def prbs23_seed_int(lid: int) -> int:
    """``{19'd1, lid[1:0], 2'b01}``."""
    return (1 << 4) | ((lid & 0x3) << 2) | 0x1


def prbs23_step_int(s: int) -> int:
    """One LFSR step: ``{s[21:0], s[22] ^ s[17]}``."""
    fb = ((s >> 22) ^ (s >> 17)) & 1
    return ((s << 1) & ((1 << PRBS23_W) - 1)) | fb


def prbs23_word_int(s: int) -> int:
    """128b window: bit *i* is LFSR[0] after *i* steps (LSB first)."""
    t = s & ((1 << PRBS23_W) - 1)
    w = 0
    for i in range(PMA_LANE_W):
        w |= (t & 1) << i
        t = prbs23_step_int(t)
    return w


def prbs23_adv128_int(s: int) -> int:
    t = s & ((1 << PRBS23_W) - 1)
    for _ in range(PMA_LANE_W):
        t = prbs23_step_int(t)
    return t


def prbs23_word_ok_int(w: int) -> bool:
    """Undecorated recurrence: ``w[i] == w[i-23] ^ w[i-18]`` for i=23..127."""
    for i in range(23, PMA_LANE_W):
        if ((w >> i) & 1) != (((w >> (i - 23)) ^ (w >> (i - 18))) & 1):
            return False
    return True


def decorate_idle_int(word: int) -> int:
    return word ^ PMA_IDLE_MARK


def prbs23_step(m: Circuit, s):
    """Circuit ``{s[21:0], s[22] ^ s[17]}``. ``m.cat`` is MSB-first."""
    _ = m
    return m.cat(s.slice(lsb=0, width=22), s[22] ^ s[17])


def prbs23_word(m: Circuit, s):
    """Circuit 128b window (LSB = first LFSR[0])."""
    t = s
    bits = []
    for _ in range(PMA_LANE_W):
        bits.append(t[0])
        t = prbs23_step(m, t)
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


def prbs23_adv128(m: Circuit, s):
    t = s
    for _ in range(PMA_LANE_W):
        t = prbs23_step(m, t)
    return t


def prbs23_word_ok(m: Circuit, w):
    """True when undecorated 128b satisfies the PRBS23 recurrence."""
    _ = m
    ok = u(1, 1)
    for i in range(23, PMA_LANE_W):
        ok = ok & (w[i] == (w[i - 23] ^ w[i - 18]))
    return ok
