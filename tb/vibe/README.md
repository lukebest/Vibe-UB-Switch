# Vibe-UB-Switch testbench

Truth sources: `docs/Vibe-UB-Switch-architecture-spec.md` (AS-0.1), FS-0.2.7
(Overlay B: NW `data[511:0]`; 640b = DLL↔PCS; credit 1024 = **cell**).
Old `tb/` (`ub_*`) is void and is **not** compiled here.

DUT top: `rtl/top/vibe_ub_switch.sv`. This tree does **not** modify `rtl/`.

## Primary gate: uvm-python (no xvlog)

The default `make sim` is **Python UVM 1.2** on
[lukebest/uvm-python](https://github.com/lukebest/uvm-python) + cocotb **1.9.x**
(`>=1.9.2,<2`; cocotb 2.x is incompatible). Simulators: **Verilator** (baseline)
and **Icarus** (`SIM=icarus`).

```bash
make -C tb/vibe/pyuvm venv          # pin deps (see pyuvm/requirements.txt)
make -C tb/vibe sim                 # suite + units + top + neg
make -C tb/vibe suite
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units
make -C tb/vibe units TC=tc_vl_rr
make -C tb/vibe top
make -C tb/vibe sim SIM=icarus
```

Details, topology, and old→new name map: [`pyuvm/README.md`](pyuvm/README.md).

SV UVM + Vivado **xsim** (`tb/vibe/uvm/`) is **deprecated / secondary**. It still
builds if `xvlog` is on `PATH`: `make -C tb/vibe sim-xsim`.

Legacy Icarus module TCs (`tb/vibe/tests/` + `Makefile.icarus`) remain as the
historical 124-bucket source: `make -C tb/vibe sim-icarus`.

## Layout

```
tb/vibe/pyuvm/              Python UVM 1.2 (primary)
tb/vibe/uvm/                SV UVM 1.2 + xsim (deprecated)
tb/vibe/tests/              legacy Icarus module TCs
tb/vibe/env/                Icarus fabric/psel harnesses
```

## Why fabric-level + unit + top smoke

G1 lives in `vibe_port_sel` / `vibe_route_lu` / `vibe_fabric` → `vibe_irq_agg`.
PHY/DLL/PCS MUSTs are unit-tested against the matching `vibe_*` module.

- **Gate for G1 / routing / SAF / CFG / length / irq / port-device reset:**
  `pyuvm` fabric wrapper (`make suite`).
- **Units:** credit 1024-cell, LMSM Idle→Discovery, BCRC, VL RR, identity/CNA,
  named negatives (`make units`).
- **Top:** `tc_top_smoke` — product pins, `cfg_wr_*`.

`rt_shortest_unimpl` is probed as `u_fab.rt_shortest_unimpl` (32-bit saturating).

Logs: `tb/vibe/results/` (copied from `tb/vibe/pyuvm/results/`).

## Agents and checkers (AS)

| Agent / checker | AS |
|-----------------|----|
| cfg agent | §10/§18 `cfg_wr_*` + sticky `irq_logic` |
| pma agent | §3/§18 512b PMA, no ready, lane slice 128b |
| nw agent | §3 Overlay B 512b `vld`/`ready` |
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

## #115

Do not weaken `tc_port_smoke` / `tc_nw_pkt_pma_loopback` / `tc_top_smoke` to
hide a PMA idle-PRBS miss. If those still fail on freeze `a658d141` without the
PR116 ECO, list them as DUT fails.
