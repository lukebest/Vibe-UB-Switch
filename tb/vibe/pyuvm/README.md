# Vibe-UB-Switch Python UVM 1.2 (uvm-python)

Primary verification gate. Accellera UVM 1.2 **Python functional equivalence**
via [lukebest/uvm-python](https://github.com/lukebest/uvm-python) + cocotb 1.9.x.

Does **not** modify `rtl/` or `include/`. Does not require Vivado xsim.

## Install pins

```
cocotb>=1.9.2,<2          # 2.x cannot import this library
cocotb-bus
cocotb-coverage
regex
uvm-python @ git+https://github.com/lukebest/uvm-python.git
```

```bash
make -C tb/vibe/pyuvm venv
# or: python3 -m venv tb/vibe/pyuvm/.venv && \
#      tb/vibe/pyuvm/.venv/bin/pip install -r tb/vibe/pyuvm/requirements.txt
```

## Run (no xvlog)

```bash
make -C tb/vibe sim              # default: this tree
make -C tb/vibe suite            # fabric+mgmt G1/CFG/SAF/length
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units            # leaf units + static/neg + port
make -C tb/vibe units TC=tc_vl_rr
make -C tb/vibe/pyuvm units TC=tc_vibe_afifo   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm afifo                    # same as units TC=tc_vibe_afifo
make -C tb/vibe/pyuvm units TC=tc_vibe_sync2   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm sync2                    # same as units TC=tc_vibe_sync2
make -C tb/vibe/pyuvm units TC=tc_vibe_rst_sync  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rst_sync                 # same as units TC=tc_vibe_rst_sync
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_128_160  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_128_160             # same as units TC=tc_vibe_gear_128_160
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_160_128  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_160_128             # same as units TC=tc_vibe_gear_160_128
make -C tb/vibe/pyuvm units TC=tc_dll          # TP-DLL-004 full vibe_dll split
make -C tb/vibe/pyuvm dll                      # same as units TC=tc_dll (≠1/3 ≠4/3)
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_scramble  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm pcs_scramble             # same as units TC=tc_vibe_pcs_scramble
make -C tb/vibe port TC=tc_port_smoke
make -C tb/vibe top              # vibe_ub_switch + peer PMA
make -C tb/vibe neg              # absent-feature scan
```

Simulator: `SIM=verilator` (baseline) or `SIM=icarus`.

```bash
make -C tb/vibe/pyuvm sim SIM=icarus
make -C tb/vibe/pyuvm units TC=tc_vl_rr SIM=icarus
make -C tb/vibe/pyuvm afifo SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm sync2 SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm rst_sync SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm gear_128_160 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm gear_160_128 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm pcs_scramble SIM=verilator  # or SIM=icarus
```

`tc_vibe_afifo` / `make afifo` is **module-level only** (reset, CDC integrity,
fill/`almost_full` at occ≥10, drain). It is **not** the full-chip consecutive-green
gate. Stock Icarus `tb/vibe/tests/tc_afifo_afull10.sv` remains optional control.

`tc_vibe_sync2` / `make sync2` is **module-level only** (reset `q==0`, stable `d`
reaches `q` after 2 posedges not 1, streaming 2-cycle delay, async `rst_n`
clears the pipe). It is **not** 1/3, 4/3, freeze, or signoff.

`tc_vibe_rst_sync` / `make rst_sync` is **module-level only** (async `rst_n_in`
asserts `rst_n_out` without a dest posedge, sync deassert after 2 dest clocks
not 1, mid-run re-assert clears both flops). It is **not** 1/3, 4/3, freeze,
or signoff. Stock Icarus `tb/vibe/tests/tc_rst_sync.sv` / `tc_rst_sync` remains
optional control.

`tc_vibe_gear_128_160` / `make gear_128_160` is **module-level only** (reset
idle / no spurious `out_vld`, 5×128 → exactly 4×160 with residue packing,
hold-full backpressure without drop/dup, phase wrap on a second group).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_gear_128_160.sv` / `tc_gear_128_160` remains optional
count-only control. This is **not** TP-DLL-004 / full-chip `tc_dll`
(`make -C tb/vibe/pyuvm dll` / `units TC=tc_dll` scores that ID).

`tc_vibe_gear_160_128` / `make gear_160_128` is **module-level only** (reset
idle / no spurious `out_vld`, 4×160 → exactly 5×128 with residue packing,
hold-full / `rbits==4` backpressure without drop/dup, phase wrap on a
second group). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_gear_160_128.sv` / `tc_gear_160_128` remains optional
count-only control. This is **not** TP-DLL-004 / full-chip `tc_dll`.

`tc_vibe_pcs_scramble` / `make pcs_scramble` is **module-level only** (reset
idle / async clear, known LID seed vs golden xmask, AMCTL/EEIB `en=0`
pass-through without LFSR advance, XOR round-trip). It is **not** 1/3,
4/3, freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_pcs_scramble.sv` /
`tc_pcs_scramble` remains optional control. Official TP-PHY-017 stays
scored by `tc_pcs_scramble`. This is **not** TP-DLL-004 / `gear_160_128`.

## Topology

```
UVMTest
 └─ UVMEnv
     ├─ Agent (Sequencer / Driver / Monitor)   # pull-mode
     └─ VibeAsScoreboard                       # G1, length, CFG6, SAF, ICRC
```

Phases / sequences / drivers are `async def` + `await`. Objections in `run_phase`.
ConfigDb outs are fresh empty lists. Types registered with `uvm_component_utils`
/ `uvm_object_utils`.

## Name mapping (old → new)

| Old gate | New |
|----------|-----|
| Icarus `vibe_suite.sv` tasks | `tc_suite_all` or `UVM_TESTNAME=tc_*` on `entry_fab` |
| SV UVM `+UVM_TESTNAME=` | same class name, Python UVM 1.2 |
| Icarus `tb/vibe/tests/tc_*.sv` | same `tc_*` class in `unit_leaf.py` / `unit_more.py` / `unit_pcs.py` / `unit_afifo.py` / `unit_sync2.py` / `unit_rst_sync.py` / `unit_gear_128_160.py` / `unit_gear_160_128.py` / `unit_dll.py` / `unit_pcs_scramble.py` / `port_tests.py` / `static_tests.py` |
| Icarus `tc_afifo_afull10` | still `tc_afifo_afull10`; Decision-I module TC is `tc_vibe_afifo` |
| Icarus `tc_rst_sync` | still `tc_rst_sync`; Decision-I module TC is `tc_vibe_rst_sync` |
| Icarus `tc_gear_128_160` | still `tc_gear_128_160`; Decision-I module TC is `tc_vibe_gear_128_160` |
| Icarus `tc_gear_160_128` | still `tc_gear_160_128`; Decision-I module TC is `tc_vibe_gear_160_128` |
| Icarus `tc_pcs_scramble` | still `tc_pcs_scramble`; Decision-I module TC is `tc_vibe_pcs_scramble` |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` / `tc_cfg9_no_icrc` | fabric suite (`entry_fab` / `tc_suite_all`) |
| Icarus `tc_pcs_rx` / `tc_pcs_tx` (full stack) | still Icarus-only in this PR; leaf PCS units are ported |
| Icarus `tc_dll` (full stack) | `tc_dll` (`vibe_dll_cocotb_top`; **TP-DLL-004** >32-flit split ≤16×≤32) |
| Icarus `tc_timers_indep` | `tc_timers_indep` (`vibe_timers_indep_cocotb_top`) |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` | fabric suite (`tc_suite_all`) |
| Icarus `tc_id_nports_entity0` / `tc_tp_holes` / `tc_neg_*` | `static_tests.py` (no simulator) |
| `make top` / `tc_top_smoke` | `entry_switch` / `tc_top_smoke` |
| `make neg` / `scan_absent.sh` | `static_tests.run_absent_scan` |
| `make sim-xsim` | deprecated secondary (needs xvlog) |

Identifiers (`tc_rt10_must_drop`, `tc_credit_1024_flit_bp`, …) are unchanged.
**Python correspondence** (HAS / GAP) lives in
[`tb/vibe/results/TP_PYUVM_MATRIX.md`](../results/TP_PYUVM_MATRIX.md).
`TP_TC_MATRIX.md` is the SV/UVM-biased scorer map — stock `tc_*.sv` alone
does not mean a Python TC exists. That matrix is **not** 1/3, 4/3, freeze, or signoff.

## Gate status (this tree)

Icarus (`SIM=icarus`) is the complete no-xvlog gate. Verilator is the
fabric/unit baseline (`--timing`); port/top hierarchical `Force` of LMSM
lock does not take effect under Verilator 5.020 + cocotb 1.9.2 VPI, so
those two stay Icarus.

| Bucket | Icarus | Verilator |
|--------|--------|-----------|
| `suite` (`tc_suite_all`, 28) | PASS | PASS |
| leaf units + static/neg + PCS | PASS (incl. `tc_phy_u26_chain`, `tc_timers_indep`) | `tc_vl_rr` PASS; fabric suite PASS |
| `tc_vibe_afifo` (module-level; ≠ full-chip gate) | PASS | PASS |
| `tc_vibe_sync2` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rst_sync` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_128_160` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_160_128` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_dll` (full `vibe_dll`; **TP-DLL-004**; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `port` (smoke / TX / 100-pkt loopback) | PASS 100/100 | compile OK; LMSM Force bring-up does not reach ACTIVE |
| `top` (`tc_top_smoke`) | PASS | not scored (same Force path) |
| `neg` | PASS | n/a (no sim) |

#115 (`tc_port_smoke` / `tc_nw_pkt_pma_loopback` / `tc_top_smoke`) is **not**
failing on `main` with PR116. Checkers were **not** relaxed.

Not Python-sim in this PR (still `make sim-icarus`): full-stack `tc_pcs_rx`,
`tc_pcs_tx`. Full-stack `tc_dll` is now uvm-python and scores **TP-DLL-004**.
Leaf PCS units remain the scorers for those TPs.

## #115

PMA idle-PRBS ECO (`a658d141`) made Icarus `tc_port_smoke` /
`tc_nw_pkt_pma_loopback` / `tc_top_smoke` fail. PR116 landed a DUT fix on
`main`. This TB **does not** weaken those checkers. If they fail on a freeze
without that ECO, report them as DUT fails.

## Layout

```
tb/vibe/pyuvm/
  vibe_uvm/          items, vifs, agents, env, scoreboard, tests
                     tests/unit_afifo.py  Decision-I vibe_afifo (module-level)
                     tests/unit_sync2.py  Decision-I vibe_sync2 (module-level)
                     tests/unit_rst_sync.py  Decision-I vibe_rst_sync (module-level)
                     tests/unit_gear_128_160.py  Decision-I vibe_gear_128_160 (module-level)
                     tests/unit_gear_160_128.py  Decision-I vibe_gear_160_128 (module-level)
                     tests/unit_dll.py    full vibe_dll; TP-DLL-004 split
                     tests/unit_pcs_scramble.py  Decision-I vibe_pcs_scramble (module-level)
  tb/                cocotb Verilog wrappers (no SV UVM)
  entry_*.py         @cocotb.test() → await run_test(...)
  catalog.py         RTL lists + TC map
  run_gate.py        suite / units / top / neg
  requirements.txt
```
