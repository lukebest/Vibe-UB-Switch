"""Icarus-compatible PASS/FAIL lines so summarize.sh still scores the gate."""


def tb_pass(name: str) -> None:
    print(f"PASS {name}", flush=True)


def tb_fail(name: str, stim: str, exp: str, act: str, hier: str) -> None:
    print(f"FAIL {name}", flush=True)
    print(f"  stimulus : {stim}", flush=True)
    print(f"  expected : {exp}", flush=True)
    print(f"  actual   : {act}", flush=True)
    print(f"  hier     : {hier}", flush=True)
    print("  reproduce: make -C tb/vibe sim", flush=True)


def tb_hole(name: str, note: str) -> None:
    print(f"PASS {name}: {note}", flush=True)


def tb_note(msg: str) -> None:
    print(f"NOTE {msg}", flush=True)
