# impl/

Yosys / ORFS / OpenSTA bring-up for Vibe-UB-Switch (`sky130hd`).

- How to run, spec vs bring-up, tapeout disclaimer: [`docs/impl/README.md`](../docs/impl/README.md)
- ORFS + PDK obtainment: [`orfs/README.md`](orfs/README.md)
- Entry point: `make help` (this directory). Default is **not** P&R.

```bash
make -C impl help
make -C impl synth-smoke
```

This flow must not edit RTL function.
