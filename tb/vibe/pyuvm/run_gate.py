#!/usr/bin/env python3
"""Orchestrate uvm-python regressions. Writes Icarus-style PASS/FAIL logs."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from catalog import (
    FAB_RTL, FAB_TOP, INC, PORT_RTL, PORT_TESTS, PORT_TOP, SUITE_TESTS,
    SWITCH_TOP, TOP_RTL, UNIT_SIM,
)
from vibe_uvm.tests.static_tests import run_absent_scan, run_all_static

PYUVM = Path(__file__).resolve().parent
RES = PYUVM / "results"
TBV_RES = PYUVM.parent / "results"


def _venv_env() -> dict:
    env = os.environ.copy()
    venv_bin = str(PYUVM / ".venv" / "bin")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(PYUVM) + os.pathsep + env.get("PYTHONPATH", "")
    env["COCOTB_REDUCED_LOG_FMT"] = "1"
    return env


def _run_cocotb(name: str, toplevel: str, sources: list[str], module: str,
                sim: str) -> int:
    RES.mkdir(parents=True, exist_ok=True)
    log = RES / f"{name}.log"
    build = PYUVM / "sim_build" / name
    if build.exists():
        shutil.rmtree(build)
    env = _venv_env()
    env["UVM_TESTNAME"] = name
    env["SIM"] = sim
    cmd = [
        "make", "-C", str(PYUVM), "-f", "Makefile.cocotb",
        f"SIM={sim}",
        f"TOPLEVEL={toplevel}",
        f"MODULE={module}",
        f"UVM_TESTNAME={name}",
        f"SIM_BUILD={build}",
        "VERILOG_SOURCES=" + " ".join(sources),
        "VERILOG_INCLUDE_DIRS=" + " ".join(INC),
    ]
    print(f"RUN {name} TOPLEVEL={toplevel} SIM={sim}", flush=True)
    with log.open("w") as fh:
        p = subprocess.run(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT, text=True)
    text = log.read_text(encoding="utf-8", errors="replace")
    # Echo PASS/FAIL to stdout for summarize.sh when we tee.
    for line in text.splitlines():
        if line.startswith(("PASS ", "FAIL ", "NOTE ", "HOLE ", "SUITE", "WARN")):
            print(line, flush=True)
    if p.returncode != 0 and "PASS " + name not in text and "FAIL " + name not in text:
        print(f"FAIL {name} (sim rc={p.returncode})", flush=True)
        with log.open("a") as fh:
            fh.write(f"\nFAIL {name} (sim rc={p.returncode})\n")
        return 1
    if "FAIL " + name in text or f"FAIL {name} " in text:
        return 1
    return 0


def run_suite(sim: str, tc: str | None) -> int:
    sources = [FAB_TOP] + FAB_RTL
    names = [tc] if tc else ["tc_suite_all"]
    if tc and tc not in SUITE_TESTS:
        print(f"unknown suite TC {tc}", file=sys.stderr)
        return 2
    rc = 0
    for name in names:
        rc |= _run_cocotb(name, "vibe_fab_cocotb_top", sources, "entry_fab", sim)
    return rc


def run_units(sim: str, tc: str | None) -> int:
    rc = 0
    if tc is None:
        print("==== static / official-neg / holes ====", flush=True)
        static_log = RES
        RES.mkdir(parents=True, exist_ok=True)
        sl = RES / "static.log"
        from io import StringIO
        import contextlib
        buf = StringIO()
        with contextlib.redirect_stdout(buf):
            rc |= 1 if run_all_static() else 0
        sl.write_text(buf.getvalue())
        print(buf.getvalue(), end="")
        if tc is None:
            pass
    table = {n: (top, src, mod) for n, top, src, mod in UNIT_SIM}
    table.update({n: (top, src, mod) for n, top, src, mod in PORT_TESTS})
    names = [tc] if tc else [n for n, *_ in UNIT_SIM] + [n for n, *_ in PORT_TESTS]
    if tc and tc not in table and tc not in {"static", "neg"}:
        print(f"unknown unit TC {tc}", file=sys.stderr)
        return 2
    if tc in {"static", "neg"}:
        return rc
    for name in names:
        top, src, mod = table[name]
        rc |= _run_cocotb(name, top, src, mod, sim)
    return rc


def run_port(sim: str, tc: str | None) -> int:
    names = [tc] if tc else [n for n, *_ in PORT_TESTS]
    table = {n: (top, src, mod) for n, top, src, mod in PORT_TESTS}
    rc = 0
    for name in names:
        top, src, mod = table[name]
        rc |= _run_cocotb(name, top, src, mod, sim)
    return rc


def run_top(sim: str) -> int:
    return _run_cocotb(
        "tc_top_smoke", "vibe_switch_cocotb_top",
        [SWITCH_TOP] + TOP_RTL, "entry_switch", sim,
    )


def run_neg() -> int:
    RES.mkdir(parents=True, exist_ok=True)
    log = RES / "neg_absent.log"
    from io import StringIO
    import contextlib
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        rc = 1 if run_absent_scan() else 0
    log.write_text(buf.getvalue())
    print(buf.getvalue(), end="")
    return rc


def _copy_logs():
    TBV_RES.mkdir(parents=True, exist_ok=True)
    for log in RES.glob("*.log"):
        shutil.copy2(log, TBV_RES / log.name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bucket", choices=["gate", "suite", "units", "port", "top", "neg", "sim"])
    ap.add_argument("--tc", default=None)
    ap.add_argument("--sim", default=os.environ.get("SIM", "verilator"))
    args = ap.parse_args()
    RES.mkdir(parents=True, exist_ok=True)
    rc = 0
    if args.bucket in ("suite", "gate", "sim"):
        rc |= run_suite(args.sim, args.tc if args.bucket == "suite" else args.tc)
    if args.bucket in ("units", "gate", "sim"):
        rc |= run_units(args.sim, args.tc if args.bucket == "units" else None)
    if args.bucket == "port":
        rc |= run_port(args.sim, args.tc)
    if args.bucket in ("top", "gate", "sim"):
        rc |= run_top(args.sim)
    if args.bucket in ("neg", "gate", "sim"):
        rc |= run_neg()
    _copy_logs()
    return rc


if __name__ == "__main__":
    sys.exit(main())
