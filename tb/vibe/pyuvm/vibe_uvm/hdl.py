"""Cocotb signal helpers. Treat X as unresolved (not a silent 0)."""


def is_x(sig) -> bool:
    try:
        v = sig.value
        if hasattr(v, "is_resolvable"):
            return not v.is_resolvable
        return False
    except Exception:
        return True


def ival(sig, default=None):
    try:
        v = sig.value
        if hasattr(v, "is_resolvable") and not v.is_resolvable:
            return default
        return int(v)
    except Exception:
        return default


def bit(sig, idx: int) -> int:
    v = ival(sig, 0)
    if v is None:
        return 0
    return (v >> idx) & 1


def sset(sig, val) -> None:
    sig.value = val


def hier(dut, path: str):
    """Walk a dotted HDL path. Generate `g_port[0]` works on Icarus arrays
    and Verilator flattened `g_port__BRA__0__KET__` / cocotb `_id` names."""
    cur = dut
    for part in path.split("."):
        if part.endswith("]") and "[" in part:
            name, rest = part.split("[", 1)
            idx = int(rest[:-1])
            got = None
            try:
                got = getattr(cur, name)[idx]
            except Exception:
                got = None
            if got is None:
                try:
                    got = cur._id(part, extended=False)
                except Exception:
                    got = None
            if got is None:
                try:
                    got = getattr(cur, f"{name}__BRA__{idx}__KET__")
                except Exception:
                    got = None
            if got is None:
                got = getattr(cur, part)
            cur = got
        else:
            cur = getattr(cur, part)
    return cur
