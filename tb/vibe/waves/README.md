# Wave audit index (Luke)

Named TCs dumped with `+DUMP` and rendered to PNG (matplotlib, no gtkwave).
Checker prose stays in [`../results/CHECKER_AUDIT.md`](../results/CHECKER_AUDIT.md).

**`make waves` lives on `main`** (this Overlay-B 512-bit TB PR).
It first shipped on `cursor/vibe-tb-g1-6065` (PR #9 / #10). If you see
`No rule to make target 'waves'`, you are on an older checkout — `git fetch origin && git checkout main`.

Clock in these dumps is Icarus `#1` with `timescale 1ns/1ps` → VCD unit **1 ps**, **period 2 ns**.
1 µs = **1250** `clk_fab` (`VIBE_US_CYC`) at 1.25 GHz.

| # | TC name | Spec | PNG | VCD | PASS log line |
|---|---------|------|-----|-----|----------------|
| 1 | `tc_rt10_must_drop` (suite) | AS-0.1 G1 / TP-RT-003: RT=10 DROP | [`g1_rt10.png`](g1_rt10.png) | [`g1_rt10.vcd`](g1_rt10.vcd) | `PASS tc_rt10_must_drop` |
| 2 | `tc_cfg6_term_vs_fwd` (suite) | AS-0.1 §9 CFG6 term vs FORWARD | [`cfg6_term_vs_fwd.png`](cfg6_term_vs_fwd.png) | [`cfg6_term_vs_fwd.vcd`](cfg6_term_vs_fwd.vcd) | `PASS tc_cfg6_term_vs_fwd` |
| 3 | `tc_credit_1024_flit_bp` (unit) | FS-0.2.7 / G7: 1024 is **CELL** | [`credit_1024_flit.png`](credit_1024_flit.png) | [`credit_1024_flit.vcd`](credit_1024_flit.vcd) | `PASS tc_credit_1024_flit_bp` |
| 4 | `tc_credit_timeout_1us` (unit) | 1 µs credit-return timeout | [`credit_timeout_1us.png`](credit_timeout_1us.png) | [`credit_timeout_1us.vcd`](credit_timeout_1us.vcd) | `PASS tc_credit_timeout_1us` |
| 5 | `tc_deadlock_timeout_1us` (unit) | 1 µs VOQ deadlock (not credit) | [`voq_deadlock_1us.png`](voq_deadlock_1us.png) | [`voq_deadlock_1us.vcd`](voq_deadlock_1us.vcd) | `PASS tc_deadlock_timeout_1us` |
| 6 | `tc_nw_pkt_pma_loopback` (unit) | TP-PHY-012 Overlay B: NW `data[511:0]` GOLDEN + SOP LPH `[511:352]` | [`nw_pkt_pma_loopback_data512.png`](nw_pkt_pma_loopback_data512.png) | [`nw_pkt_pma_loopback_data512.vcd`](nw_pkt_pma_loopback_data512.vcd) | `PASS tc_nw_pkt_pma_loopback` |

## Overlay B loopback (512-bit NW data) — copy-paste

On **`main`** the DUT is already Overlay B (PR8 / `a3ecec9f` lineage). Do not overlay or commit `rtl/`.

```bash
git fetch origin
git checkout main
make -C tb/vibe waves TC=tc_nw_pkt_pma_loopback
```

That `make` writes (no filename guessing):

| Output | Path |
|--------|------|
| VCD | `tb/vibe/waves/nw_pkt_pma_loopback_data512.vcd` |
| PNG | `tb/vibe/waves/nw_pkt_pma_loopback_data512.png` |
| PASS log | `tb/vibe/waves/nw_pkt_pma_loopback_data512.log` — must contain `PASS tc_nw_pkt_pma_loopback` |

Equivalent `vvp` line (what `scripts/run_waves.sh` runs):

```text
vvp tb/vibe/results/tc_nw_pkt_pma_loopback_waves.vvp \
  +DUMP +DUMPFILE=tb/vibe/waves/nw_pkt_pma_loopback_data512.vcd
python3 tb/vibe/scripts/vcd_to_png.py --waves tb/vibe/waves
```

PNG is three stitched windows: TX inject of `fab_tx_data[511:0]` / PMA `txdata`+`rxdata==txdata` / RX `fab_rx_data[511:0]===GOLDEN`.
SOP LPH is **`[511:352]`** (160b CFG/RT/SCNA/DCNA). Payload is **`[351:0]`**. Not README `[511:496]`.

### Signals dumped and labeled

| Group | VCD name | Meaning |
|-------|----------|---------|
| TX/NW | `fab_tx_vld`, `fab_tx_ready`, `fab_tx_data[511:0]` | Overlay B NW pin |
| TX SOP | `wav_tx_sop[159:0]` | `fab_tx_data[511:352]` |
| TX LPH fields | `wav_tx_cfg/rt/scna/dcna` | 160b layout on that SOP window |
| TX payload | `wav_tx_pld[351:0]` | `fab_tx_data[351:0]` |
| PMA | `txdata[511:0]`, `rxdata[511:0]`, `wav_lb_eq`, `wav_ptxv`, `wav_txlv` | product pins; `rxdata=txdata` |
| RX | `fab_rx_vld`, `fab_rx_data[511:0]`, `wav_rx_sop`, `wav_rx_pld` | recovered NW beat |
| RX score | `wav_rx_eq`, `wav_am`, `wav_pcs_rx`, `wav_fec` | GOLDEN match; `am_locked`; `fec_fail` |
