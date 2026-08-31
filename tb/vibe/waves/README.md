# Wave audit index (Luke)

Five named TCs dumped with `+DUMP` and rendered to PNG (matplotlib, no gtkwave).
Checker prose stays in [`../results/CHECKER_AUDIT.md`](../results/CHECKER_AUDIT.md).
Regenerate: `make -C tb/vibe waves`.

Clock in these dumps is Icarus `#1` with `timescale 1ns/1ps` → VCD unit **1 ps**, **period 2 ns**.
1 µs = **1250** `clk_fab` (`VIBE_US_CYC`) at 1.25 GHz.

| # | TC name | Spec | PNG | VCD | PASS log line |
|---|---------|------|-----|-----|----------------|
| 1 | `tc_rt10_must_drop` (suite) | AS-0.1 G1 / TP-RT-003: RT=10 DROP, `rt_shortest_unimpl` +1, sticky `irq_logic`, egress stays 0 | [`g1_rt10.png`](g1_rt10.png) | [`g1_rt10.vcd`](g1_rt10.vcd) | `PASS tc_rt10_must_drop` |
| 2 | `tc_cfg6_term_vs_fwd` (suite) | AS-0.1 §9: terminate local-CNA / NLP=1 / opc `0x10` targeting-us; else FORWARD | [`cfg6_term_vs_fwd.png`](cfg6_term_vs_fwd.png) | [`cfg6_term_vs_fwd.vcd`](cfg6_term_vs_fwd.vcd) | `PASS tc_cfg6_term_vs_fwd` |
| 3 | `tc_credit_1024_flit_bp` (unit) | FS-0.2.4 / G7: threshold **1024 is FLIT**, no divide-by-n on `pending` | [`credit_1024_flit.png`](credit_1024_flit.png) | [`credit_1024_flit.vcd`](credit_1024_flit.vcd) | `PASS tc_credit_1024_flit_bp` |
| 4 | `tc_credit_timeout_1us` (unit) | 1 µs credit-return timeout → `proto_err` (`vibe_dll_credit.to`) | [`credit_timeout_1us.png`](credit_timeout_1us.png) | [`credit_timeout_1us.vcd`](credit_timeout_1us.vcd) | `PASS tc_credit_timeout_1us` |
| 5 | `tc_deadlock_timeout_1us` (unit) | 1 µs VOQ deadlock (`vibe_voq_egr.age`) — **not** the credit counter | [`voq_deadlock_1us.png`](voq_deadlock_1us.png) | [`voq_deadlock_1us.vcd`](voq_deadlock_1us.vcd) | `PASS tc_deadlock_timeout_1us` |

Each PNG is one annotated window (CFG6 / both 1 µs timeouts use a load+fire pair on one image): signal names, 0/1 or dec/hex values, a vertical marker at the score event, and expected-vs-actual caption.

How dumped:

- Suite: `make suite TC=<name> VVPFLAGS="+DUMP +DUMPFILE=tb/vibe/waves/<file>.vcd"`
- Units: same compile path as `scripts/run_units.sh`, plus `vvp +DUMP +DUMPFILE=...`
- `make waves` runs all five, confirms `PASS <name>`, then `scripts/vcd_to_png.py`
