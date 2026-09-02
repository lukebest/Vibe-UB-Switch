# Wave audit index (Luke)

Named TCs dumped with `+DUMP` and rendered to PNG (matplotlib, no gtkwave).
Checker prose stays in [`../results/CHECKER_AUDIT.md`](../results/CHECKER_AUDIT.md).
Regenerate all: `make -C tb/vibe waves`.
One TC: `make -C tb/vibe waves TC=<name>`.

Clock in these dumps is Icarus `#1` with `timescale 1ns/1ps` → VCD unit **1 ps**, **period 2 ns**.
1 µs = **1250** `clk_fab` (`VIBE_US_CYC`) at 1.25 GHz.

| # | TC name | Spec | PNG | VCD | PASS log line |
|---|---------|------|-----|-----|----------------|
| 1 | `tc_rt10_must_drop` (suite) | AS-0.1 G1 / TP-RT-003: RT=10 DROP, `rt_shortest_unimpl` +1, sticky `irq_logic`, egress stays 0 | [`g1_rt10.png`](g1_rt10.png) | [`g1_rt10.vcd`](g1_rt10.vcd) | `PASS tc_rt10_must_drop` |
| 2 | `tc_cfg6_term_vs_fwd` (suite) | AS-0.1 §9: terminate local-CNA / NLP=1 / opc `0x10` targeting-us; else FORWARD | [`cfg6_term_vs_fwd.png`](cfg6_term_vs_fwd.png) | [`cfg6_term_vs_fwd.vcd`](cfg6_term_vs_fwd.vcd) | `PASS tc_cfg6_term_vs_fwd` |
| 3 | `tc_credit_1024_flit_bp` (unit) | FS-0.2.4 / G7: threshold **1024 is FLIT**, no divide-by-n on `pending` | [`credit_1024_flit.png`](credit_1024_flit.png) | [`credit_1024_flit.vcd`](credit_1024_flit.vcd) | `PASS tc_credit_1024_flit_bp` |
| 4 | `tc_credit_timeout_1us` (unit) | 1 µs credit-return timeout → `proto_err` (`vibe_dll_credit.to`) | [`credit_timeout_1us.png`](credit_timeout_1us.png) | [`credit_timeout_1us.vcd`](credit_timeout_1us.vcd) | `PASS tc_credit_timeout_1us` |
| 5 | `tc_deadlock_timeout_1us` (unit) | 1 µs VOQ deadlock (`vibe_voq_egr.age`) — **not** the credit counter | [`voq_deadlock_1us.png`](voq_deadlock_1us.png) | [`voq_deadlock_1us.vcd`](voq_deadlock_1us.vcd) | `PASS tc_deadlock_timeout_1us` |
| 6 | `tc_nw_pkt_pma_loopback` (unit) | TP-PHY-012: NW → PMA `txdata` looped to `rxdata` → `fab_rx` LPH+payload | [`nw_pkt_pma_loopback.png`](nw_pkt_pma_loopback.png) | [`nw_pkt_pma_loopback.vcd`](nw_pkt_pma_loopback.vcd) | `PASS tc_nw_pkt_pma_loopback` |

Each PNG is one annotated window (CFG6 / both 1 µs timeouts use a load+fire pair on one image): signal names, 0/1 or dec/hex values, a vertical marker at the score event, and expected-vs-actual caption.

How dumped:

- Suite: `make suite TC=<name> VVPFLAGS="+DUMP +DUMPFILE=tb/vibe/waves/<file>.vcd"`
- Units: same compile path as `scripts/run_units.sh`, plus `vvp +DUMP +DUMPFILE=...`
- `make waves` runs the audit set, confirms `PASS <name>`, then `scripts/vcd_to_png.py`

## Loopback (TP-PHY-012) — regenerate exactly

Compile **TB** against PR4 HEAD `rtl/` (sim only; do not commit `rtl/`):

```bash
git checkout origin/cursor/as01-rtl-82c7 -- rtl
git restore --staged rtl
make -C tb/vibe waves TC=tc_nw_pkt_pma_loopback
# restore TB-branch rtl before any commit:
git checkout HEAD -- rtl
```

That `make` line is:

```text
iverilog -g2012 -Irtl/common -Itb/vibe/common -Itb/vibe/env -Itb/vibe/tests \
  -o tb/vibe/results/tc_nw_pkt_pma_loopback_waves.vvp \
  tb/vibe/tests/tc_nw_pkt_pma_loopback.sv   # plus PORT_RTL from run_units.sh
vvp tb/vibe/results/tc_nw_pkt_pma_loopback_waves.vvp \
  +DUMP +DUMPFILE=tb/vibe/waves/nw_pkt_pma_loopback.vcd
python3 tb/vibe/scripts/vcd_to_png.py --waves tb/vibe/waves
```

PASS line: `PASS tc_nw_pkt_pma_loopback`  
(also: `scored : fab_rx LPH+payload after PMA loopback`)

Checker expected LPH is unchanged: CFG=3 RT=00 SCNA=A11A DCNA=B22B.

PNG is three stitched windows (TX accept / PMA nonzero+loopback / RX LPH) with vertical markers at inject (~68 ns), PMA activity (~578 ns), and `fab_rx` score (~879 ns).

### Signals dumped and labeled

| Group | VCD name | DUT / TB hier |
|-------|----------|----------------|
| TX/NW | `fab_tx_vld`, `fab_tx_ready` | `tc_nw_pkt_pma_loopback.fab_tx_*` |
| TX LPH | `wav_tx_cfg`, `wav_tx_rt`, `wav_tx_scna`, `wav_tx_dcna` | `vibe_lph_*` / `vibe_nth_*` of `fab_tx_data[639:480]` |
| PMA | `txdata[511:0]`, `rxdata[511:0]`, `txclk`, `rxclk` | port pins; `rxdata=txdata` |
| PMA pack | `wav_tx_nz`, `wav_rx_nz`, `wav_lb_eq`, `wav_lane0`, `wav_lane3` | `\|txdata`, `rxdata===txdata`, `txdata[31:0]`, `txdata[511:480]` |
| PMA strobes | `wav_ptxv`, `wav_txlv` | `u_p.p_txv`, `u_p.txlv` (`lane_vld`) |
| RX | `wav_am`, `wav_pcs_rx`, `wav_fec`, `fab_rx_vld` | `u_p.am_locked`, `u_p.pcs_rx_v`, `u_p.fec_fail`, `fab_rx_vld` |
| RX LPH | `wav_rx_cfg/rt/scna/dcna`, `wav_rx_lph_ok` | same extractors on `fab_rx_data`; `vibe_tb_nw_pma_lph_ok` |
