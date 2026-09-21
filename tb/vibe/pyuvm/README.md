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
make -C tb/vibe port TC=tc_port_smoke
make -C tb/vibe top              # vibe_ub_switch + peer PMA
make -C tb/vibe neg              # absent-feature scan
```

Simulator: `SIM=verilator` (baseline) or `SIM=icarus`.

```bash
make -C tb/vibe/pyuvm sim SIM=icarus
make -C tb/vibe/pyuvm units TC=tc_vl_rr SIM=icarus
```

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
| Icarus `tb/vibe/tests/tc_*.sv` | same `tc_*` class in `unit_leaf.py` / `unit_more.py` / `unit_pcs.py` / `port_tests.py` / `static_tests.py` |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` / `tc_cfg9_no_icrc` | fabric suite (`entry_fab` / `tc_suite_all`) |
| Icarus `tc_pcs_rx` / `tc_pcs_tx` (full stack) | still Icarus-only in this PR; leaf PCS units are ported |
| Icarus `tc_dll` (full stack) | still Icarus-only; leaf DLL SM/credit/retry/rx/tx units are ported |
| Icarus `tc_timers_indep` | `tc_timers_indep` (`vibe_timers_indep_cocotb_top`) |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` | fabric suite (`tc_suite_all`) |
| Icarus `tc_id_nports_entity0` / `tc_tp_holes` / `tc_neg_*` | `static_tests.py` (no simulator) |
| `make top` / `tc_top_smoke` | `entry_switch` / `tc_top_smoke` |
| `make neg` / `scan_absent.sh` | `static_tests.run_absent_scan` |
| `make sim-xsim` | deprecated secondary (needs xvlog) |

Identifiers (`tc_rt10_must_drop`, `tc_credit_1024_flit_bp`, …) are unchanged so
`TP_TC_MATRIX.md` still scores.

## Gate status (this tree)

Icarus (`SIM=icarus`) is the complete no-xvlog gate. Verilator is the
fabric/unit baseline (`--timing`); port/top hierarchical `Force` of LMSM
lock does not take effect under Verilator 5.020 + cocotb 1.9.2 VPI, so
those two stay Icarus.

| Bucket | Icarus | Verilator |
|--------|--------|-----------|
| `suite` (`tc_suite_all`, 28) | PASS | PASS |
| leaf units + static/neg + PCS | PASS (incl. `tc_phy_u26_chain`, `tc_timers_indep`) | `tc_vl_rr` PASS; fabric suite PASS |
| `port` (smoke / TX / 100-pkt loopback) | PASS 100/100 | compile OK; LMSM Force bring-up does not reach ACTIVE |
| `top` (`tc_top_smoke`) | PASS | not scored (same Force path) |
| `neg` | PASS | n/a (no sim) |

#115 (`tc_port_smoke` / `tc_nw_pkt_pma_loopback` / `tc_top_smoke`) is **not**
failing on `main` with PR116. Checkers were **not** relaxed.

Not Python-sim in this PR (still `make sim-icarus`): full-stack `tc_pcs_rx`,
`tc_pcs_tx`, `tc_dll`. Leaf PCS/DLL units cover the same TPs.

## #115

PMA idle-PRBS ECO (`a658d141`) made Icarus `tc_port_smoke` /
`tc_nw_pkt_pma_loopback` / `tc_top_smoke` fail. PR116 landed a DUT fix on
`main`. This TB **does not** weaken those checkers. If they fail on a freeze
without that ECO, report them as DUT fails.

## Layout

```
tb/vibe/pyuvm/
  vibe_uvm/          items, vifs, agents, env, scoreboard, tests
  tb/                cocotb Verilog wrappers (no SV UVM)
  entry_*.py         @cocotb.test() → await run_test(...)
  catalog.py         RTL lists + TC map
  run_gate.py        suite / units / top / neg
  requirements.txt
```
