"""PRBS31 helpers for product PMA pin-idle (SPEC §4.4 / CR-PMA-IDLE-PRBS31).

ITU-T O.150 PRBS31:
  Poly: x^31 + x^28 + 1. LFSR step: ``{s[30:0], s[30] ^ s[27]}`` (31-bit state).
  The 31-bit result of that step is ``{s[29:0], s[30] ^ s[27]}``.
  Per-lane seed: ``{27'd1, lid[1:0], 2'b01}`` for lid=0..3 (same lid packing
  idea as the old PRBS23 seed, 31-bit width). Non-zero seeds only.

Word: 128b window, bit *i* = LFSR[0] after *i* steps (LSB first), then
advance 128 steps per idle beat per lane — same structure as ``prbs23.py``.

No ``PMA_IDLE_MARK`` XOR. PRBS31 is a different poly than PCS scramble(0)
(PRBS23), so the decorated mark is unnecessary. RX idle detect is the
PRBS31 recurrence on each 128b slice (no un-XOR).
"""

from __future__ import annotations

try:
    from pycircuit import Circuit, u
except ImportError:  # integer helpers / self-check do not need the frontend
    Circuit = None
    u = None

PRBS31_W = 31
PMA_LANE_W = 128


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


def prbs31_step(m: Circuit, s):
    """Circuit ``{s[29:0], s[30] ^ s[27]}``. ``m.cat`` is MSB-first."""
    _ = m
    return m.cat(s.slice(lsb=0, width=30), s[30] ^ s[27])


def prbs31_word(m: Circuit, s):
    """Circuit 128b window (LSB = first LFSR[0])."""
    t = s
    bits = []
    for _ in range(PMA_LANE_W):
        bits.append(t[0])
        t = prbs31_step(m, t)
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


def prbs31_adv128(m: Circuit, s):
    t = s
    for _ in range(PMA_LANE_W):
        t = prbs31_step(m, t)
    return t


def prbs31_word_ok(m: Circuit, w):
    """True when 128b satisfies the PRBS31 recurrence (no un-XOR)."""
    _ = m
    ok = u(1, 1)
    for i in range(31, PMA_LANE_W):
        ok = ok & (w[i] == (w[i - 31] ^ w[i - 28]))
    return ok


def _self_check() -> None:
    """Prove seeds are non-zero and generated words satisfy recurrence."""
    words = []
    for lid in range(4):
        seed = prbs31_seed_int(lid)
        assert seed != 0, f"lid={lid} seed must be non-zero"
        assert seed == ((1 << 4) | ((lid & 3) << 2) | 1)
        w = prbs31_word_int(seed)
        assert prbs31_word_ok_int(w), f"lid={lid} seed word fails recurrence"
        nxt = prbs31_word_int(prbs31_adv128_int(seed))
        assert w != nxt, f"lid={lid} idle beat must change after 128 steps"
        assert prbs31_word_ok_int(nxt), f"lid={lid} next word fails recurrence"
        words.append(w)
    assert len(set(words)) == 4, "per-lane seeds must produce distinct words"
    # All-zero is the degenerate LFSR lockup (0==0^0). Not a TX seed. RX
    # treating it as idle (vld=0) is fine — it is not valid traffic.
    assert prbs31_word_ok_int(0)
    assert not prbs31_word_ok_int((1 << PMA_LANE_W) - 1)
    # Packed scramble(0)-shaped PRBS23 (x^23+x^18+1) is not PRBS31 idle.
    def _prbs23_step(s: int) -> int:
        return ((s << 1) & ((1 << 23) - 1)) | (((s >> 22) ^ (s >> 17)) & 1)

    t = (1 << 4) | 0x1
    scramble0 = 0
    for i in range(PMA_LANE_W):
        scramble0 |= (t & 1) << i
        t = _prbs23_step(t)
    assert not prbs31_word_ok_int(scramble0)


if __name__ == "__main__":
    _self_check()
    print("prbs31 self-check ok: recurrence, seed!=0, beat changes, !=PRBS23")
