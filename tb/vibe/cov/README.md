# Coverage

Icarus Verilog 12 has no line/toggle/FSM coverage engine.

Verilator 5.020 `--coverage` was attempted on `vibe_suite`. It did not produce
a report in this PR:

- `%Error-BLKLOOPINIT` in `vibe_route_lu` (NBA to array in a for-loop). Not
  patched (RTL freeze).
- Waiving that error still did not finish compiling `vibe_voq_egr` age loops
  in the time budget.

Honest numbers for the full `vibe_*` tree: **not collected**. Do not treat this as 100%.

A Verilator `--coverage --binary` build of `vibe_port_sel` plus `cov/tc_psel_cov.sv` **did compile and run** (`$finish` at line 35). Verilator 5.020’s `--binary` main did **not** write `coverage.dat` (no `%` line/toggle totals). Re-run: `make -C tb/vibe cov`.

What *was* executed on `vibe_*` (functional, Icarus):

| Module | How |
|--------|-----|
| `vibe_fabric` / `vibe_port_sel` / `vibe_route_lu` / `vibe_saf_ing` / `vibe_irq_agg` | G1 + suite |
| `vibe_cfg_space` / `vibe_cna_ep` / `vibe_mgmt` | suite + units |
| `vibe_dll_rx` / `vibe_icrc` / `vibe_vl_rr` / `vibe_dll_credit` / `vibe_lmsm` / `vibe_xbar` | units |
| `vibe_ub_switch` | top smoke (pins + hier `u_fab.rt_shortest_unimpl`) |

Re-try: `make -C tb/vibe cov` (may fail; report tool output as-is).
