# Vibe-UB-Switch testbench (new)

Truth sources: `docs/Vibe-UB-Switch-architecture-spec.md` (AS-0.1) and FS-0.2.3 G1
rules in the task/PR. Old `tb/` (ub_*) is void and is **not** compiled here.

DUT top: `rtl/top/vibe_ub_switch.sv`. This tree does **not** modify `rtl/`.

## Why fabric-level + top smoke

G1 lives in `vibe_port_sel` / `vibe_route_lu` / `vibe_fabric` (`drop_g1`,
`rt_shortest_unimpl`) → `vibe_irq_agg.irq_logic`. Driving that from PMA 512b
needs PCS/DLL/LMSM packet BFMs that this revision does not provide.

- **Gate for G1 / routing / SAF / CFG6 / length / irq:** hierarchical
  `vibe_fabric` + `vibe_mgmt` harness (`env/vibe_fabric_harness.sv`).
- **Top:** `tc_top_smoke` — pins, `cfg_wr_*`, hierarchical
  `dut.u_fab.rt_shortest_unimpl` (not a product port).
- **Unit:** CFG0 (`vibe_dll_rx`), ICRC (`vibe_icrc`), VL RR, credit-1024 HOLE,
  LMSM absence of Probe/QDLWS.

`rt_shortest_unimpl` is probed as `u_fab.rt_shortest_unimpl` (32-bit saturating).

## Run

Requires Icarus Verilog 12 (`iverilog`/`vvp`). Optional: Verilator 5 for coverage.

```bash
# all new TCs (gate)
make -C tb/vibe sim

# G1 / fabric suite only
make -C tb/vibe suite

# one named TC
make -C tb/vibe suite TC=tc_rt10_must_drop

# unit + top + absent-feature scan
make -C tb/vibe units
make -C tb/vibe top
make -C tb/vibe neg

# line/toggle coverage on vibe_* used by the suite (honest tool output)
make -C tb/vibe cov
```

Equivalent:

```bash
scripts/sim/run_vibe.sh          # sim
scripts/sim/run_vibe.sh suite
scripts/sim/run_vibe.sh cov
```

Logs: `tb/vibe/results/*.log`. Old `tb/pcs`, `tb/dll`, `tb/switch`, … are not run.

## G1 rules implemented in tests

- RT=10 / RT=11: drop, do not forward, do not rewrite RT, do not treat as RT=00/01.
- No Dijkstra / shortest-path.
- Counter `rt_shortest_unimpl` saturates at `32'hFFFF_FFFF`.
- `irq_logic` sticky; clear by static `cfg_wr` or device reset.
- Detector is `vibe_port_sel` + fabric `g1_comb`; not a protocol ERROR.
