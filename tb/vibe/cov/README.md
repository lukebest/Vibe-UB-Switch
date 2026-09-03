# Coverage

Icarus Verilog 12 has no line/toggle/FSM coverage engine.

Verilator 5 `--coverage --coverage-line --coverage-toggle` is the source of
numbers. Prior failure modes (not faked):

- `%Error-BLKLOOPINIT` in `vibe_route_lu` — waived with `-Wno-BLKLOOPINIT`
  (RTL freeze; not patched).
- `--binary` generated `main()` did **not** write `coverage.dat` after
  `$finish`. Fixed by `scripts/run_verilator_cov.sh` custom main that calls
  `VerilatedCov::write()` after the timing loop.

Run: `make -C tb/vibe cov`

Outputs:

- `tb/vibe/cov/out/*.dat` per cluster, `merged.dat`
- `tb/vibe/results/cov_report.md` — line/toggle % for `vibe_*.sv` only
- `tb/vibe/results/cov_raw.txt` — `verilator_coverage` dump

Verilator has no VCS-style FSM report. FSM coverage is line hits on state
`case`/`if`. Gate is **LINE ≥95% + waiver** (do not chase 100%). Every
uncovered LINE is classified in `results/COVERAGE_HOLES.md`
(TB空洞 / DUT死代码 / TOOL). Functional coverage is the official 159 TPs.
