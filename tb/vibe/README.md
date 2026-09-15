# Vibe-UB-Switch testbench (UVM / xsim)

Truth sources: `docs/Vibe-UB-Switch-architecture-spec.md` (AS-0.1), FS-0.2.7
(Overlay B: NW `data[511:0]`; 640b = DLL↔PCS; credit 1024 = **cell**).
Old `tb/` (`ub_*`) is void and is **not** compiled here.

DUT top: `rtl/top/vibe_ub_switch.sv`. This tree does **not** modify `rtl/`.

The gate is a UVM 1.2 environment on AMD Vivado **xsim**. Interfaces, sequences,
and checkers follow AS-0.1 product pins and Overlay-B `vld`/`ready` names.

## Layout

```
tb/vibe/uvm/
  if/vibe_if.sv             PMA / cfg_wr / NW-512 / probe / leaf unit IFs
  pkg/vibe_uvm_pkg.sv       items, agents, AS scoreboard, env, tests
  tb/vibe_fab_tb_top.sv     fabric+mgmt suite DUT
  tb/vibe_switch_tb_top.sv  vibe_ub_switch product pins
  tb/vibe_unit_tb_top.sv    leaf units
  scripts/run_xsim.sh
```

## Why fabric-level + unit + top smoke

G1 lives in `vibe_port_sel` / `vibe_route_lu` / `vibe_fabric` → `vibe_irq_agg`.
PHY/DLL/PCS MUSTs are unit-tested against the matching `vibe_*` module.

- **Gate for G1 / routing / SAF / CFG / length / irq / port-device reset:**
  `uvm/tb/vibe_fab_tb_top.sv` (`make suite`).
- **Units:** credit 1024-cell, LMSM Idle→Discovery, BCRC, VL RR, AFIFO occ≥10,
  identity/CNA, irq sticky OR, G1 in port_sel, named negatives (`make units`).
- **Top:** `tc_top_smoke` — product pins, `cfg_wr_*`.

`rt_shortest_unimpl` is probed as `u_fab.rt_shortest_unimpl` (32-bit saturating).

## Run

Requires Vivado `xvlog`/`xelab`/`xsim` on `PATH` (UVM 1.2 via `-L uvm`).

```bash
make -C tb/vibe sim              # suite + units + top + neg
make -C tb/vibe suite
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units
make -C tb/vibe top
make -C tb/vibe sim-icarus       # legacy iverilog tree
```

Logs: `tb/vibe/results/`.

xsim needs a Vivado Simulator license (`~/.Xilinx/Xilinx.lic` or `XILINXD_LICENSE_FILE`).

Original Icarus module TCs under `tb/vibe/tests/` remain as sources; `make sim-icarus` still runs that tree. New work goes through UVM + xsim.

## Agents and checkers (AS)

| Agent / checker | AS |
|-----------------|----|
| `vibe_cfg_if` / cfg agent | §10/§18 `cfg_wr_*` + sticky `irq_logic` |
| `vibe_pma_if` / pma agent | §3/§18 512b PMA, no ready, lane slice 128b |
| `vibe_nw4_if` / nw agent | §3 Overlay B 512b `vld`/`ready` |
| G1 scoreboard | §2 RT=10/11 drop, saturating `rt_shortest_unimpl`, irq |
| length checker | §8 16–4300 B |
| CFG6 checker | §9 terminate vs forward |
| SAF checker | §8 no xbar until assembled |
| transit ICRC | §13 fabric does not recompute CCI/LBF |

## G1 rules implemented in tests

- RT=10 / RT=11: drop, do not forward, do not rewrite RT, do not treat as RT=00/01.
- No Dijkstra / shortest-path.
- Counter `rt_shortest_unimpl` saturates at `32'hFFFF_FFFF`.
- `irq_logic` sticky; clear by static `cfg_wr` or device reset.
- Detector is `vibe_port_sel` + fabric `g1_comb`; not a protocol ERROR.
