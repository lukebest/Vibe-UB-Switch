# Vibe-UB-Switch testbench (new)

Truth sources: `docs/Vibe-UB-Switch-architecture-spec.md` (AS-0.1), FS-0.2.3 G1,
and FS-0.2.4 credit lock (1024 = **flit**). Old `tb/` (`ub_*`) is void and is
**not** compiled here.

DUT top: `rtl/top/vibe_ub_switch.sv`. This tree does **not** modify `rtl/`.

## Why fabric-level + unit + top smoke

G1 lives in `vibe_port_sel` / `vibe_route_lu` / `vibe_fabric` → `vibe_irq_agg`.
PHY/DLL/PCS MUSTs are unit-tested against the matching `vibe_*` module.

- **Gate for G1 / routing / SAF / CFG / length / irq / port-device reset:**
  `env/vibe_fabric_harness.sv` (`make suite`, 26 TCs).
- **Units:** PHY width, FEC T=4/T=2/bypass, AMCTL, LMSM Idle→Discovery, DLL SM,
  BCRC, VL0–15 RR, retry 256, GBN, credit 1024-flit + 1 µs timeout, VOQ deadlock
  1 µs (separate), AFIFO, ICRC, CFG0, named negatives (`make units`).
- **Top:** `tc_top_smoke` — pins, `cfg_wr_*`, hierarchical
  `dut.u_fab.rt_shortest_unimpl` (not a product port).

`rt_shortest_unimpl` is probed as `u_fab.rt_shortest_unimpl` (32-bit saturating).

## FS-0.2.4 / G7 (closed)

Credit return threshold **1024 is flit**. Pending path is `pend += credit_ret_n`
with **no divide-by-n**. `tc_credit_1024_flit_bp`: 1023 flit → no `bp_nw`;
1024 flit → `bp_nw` and `force_crd_ack`. Consume still uses `ceil_div` by grain
(cells) — that is not the G7 unit.

## Run

Requires Icarus Verilog 12 (`iverilog`/`vvp`). Verilator 5 for coverage.

```bash
make -C tb/vibe sim              # suite + units + top + neg
make -C tb/vibe suite            # 26 fabric/mgmt TCs
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units
make -C tb/vibe top
make -C tb/vibe neg
make -C tb/vibe cov              # real line/toggle; custom coverage.dat write
```

Equivalent: `scripts/sim/run_vibe.sh` / `suite` / `cov`.

Logs: `tb/vibe/results/`. Coverage: `tb/vibe/results/cov_report.md`.

## G1 rules implemented in tests

- RT=10 / RT=11: drop, do not forward, do not rewrite RT, do not treat as RT=00/01.
- No Dijkstra / shortest-path.
- Counter `rt_shortest_unimpl` saturates at `32'hFFFF_FFFF`.
- `irq_logic` sticky; clear by static `cfg_wr` or device reset.
- Detector is `vibe_port_sel` + fabric `g1_comb`; not a protocol ERROR.
