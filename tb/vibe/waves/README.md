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
| 6 | `tc_nw_pkt_pma_loopback` (unit) | TP-PHY-012 Overlay B: **100** unique NW `data[511:0]` packets + SOP LPH `[511:352]` | [`nw_pkt_pma_loopback_data512.png`](nw_pkt_pma_loopback_data512.png) | [`nw_pkt_pma_loopback_data512.vcd`](nw_pkt_pma_loopback_data512.vcd) | `PASS tc_nw_pkt_pma_loopback` |

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

PNG is four stitched windows: TX Fabric↔NW inject / Link NW↔DLL (512b) + DLL↔PCS (640b) / PMA `pcs_pma_txdata`+`pma_pcs_rxdata==pcs_pma_txdata` / RX `nw_fab_data[511:0]===GOLDEN`.
SOP LPH is **`[511:352]`** (160b CFG/RT/SCNA/DCNA). Payload is **`[351:0]`**. Not README `[511:496]`.

`$dumpvars` lists Overlay-B **product interfaces** (not `$dumpvars(0, whole_tb)`). NW↔DLL and DLL↔PCS are dumped as **hierarchical DUT wires** (`u_p.nw_dll_*`, …) plus TB aliases of the same nets (CR-B `{src}_{dst}_{meaning}`, freeze `1ed4d350`).

### Where to look (NW↔DLL / DLL↔PCS)

Open `tb/vibe/waves/nw_pkt_pma_loopback_data512.vcd` in gtkwave/Surfer and expand:

`tc_nw_pkt_pma_loopback` → **`u_p`** (`vibe_port`)

| Interface | Hierarchical VCD path (DUT) | Also at TC top (alias) |
|-----------|-----------------------------|------------------------|
| NW→DLL 512b | `tc_nw_pkt_pma_loopback.u_p.nw_dll_vld`, `u_p.nw_dll_ready`, `u_p.nw_dll_data[511:0]` | `nw_dll_vld/ready/data` |
| DLL→NW 512b | `tc_nw_pkt_pma_loopback.u_p.dll_nw_vld`, `u_p.dll_nw_ready`, `u_p.dll_nw_data[511:0]` | `dll_nw_vld/ready/data` |
| DLL→PCS 640b | `tc_nw_pkt_pma_loopback.u_p.dll_pcs_vld`, `u_p.dll_pcs_ready`, `u_p.dll_pcs_data[639:0]` | `dll_pcs_vld/ready/data` |
| PCS→DLL 640b | `tc_nw_pkt_pma_loopback.u_p.pcs_dll_vld`, `u_p.pcs_dll_ready`, `u_p.pcs_dll_data[639:0]` | `pcs_dll_vld/ready/data` |

Confirm the dump (header only; do not `grep` the whole value stream):

```bash
grep -E '^\$var |^\$scope ' tb/vibe/waves/nw_pkt_pma_loopback_data512.vcd \
  | grep -E 'u_p|nw_dll_|dll_nw_|dll_pcs_|pcs_dll_'
```

You must see `$scope module u_p` and `$var` lines for `nw_dll_vld`, `nw_dll_data`, `dll_pcs_vld`, `dll_pcs_data`, `pcs_dll_*`, `dll_nw_*`.
`make waves` fails the TC if those names are absent. The PNG Link window is labeled `u_p.nw_dll_*` / `u_p.dll_pcs_*` around the first handshake (not stretched to RX).

### Signals dumped and labeled

| Group | VCD name | Meaning / DUT path |
|-------|----------|--------------------|
| Clocks/reset | `clk_fab`, `txclk`, `rxclk`, `rst_n`, `port_rst`, `device_rst`, `link_ready`, `status_up` | TB pins + `u_p.link_ready` |
| Fabric↔NW | `fab_nw_vld`, `fab_nw_ready`, `fab_nw_data[511:0]`, `nw_fab_vld`, `nw_fab_ready`, `nw_fab_data[511:0]` | `vibe_port` pins (keep) |
| TX SOP | `wav_tx_sop[159:0]` | `fab_nw_data[511:352]` |
| TX LPH fields | `wav_tx_cfg/rt/scna/dcna` | 160b layout on that SOP window |
| TX payload | `wav_tx_pld[351:0]` | `fab_nw_data[351:0]` |
| NW↔DLL (512b) | `u_p.nw_dll_data[511:0]`, `u_p.nw_dll_vld`, `u_p.nw_dll_ready`, `u_p.dll_nw_data[511:0]`, `u_p.dll_nw_vld`, `u_p.dll_nw_ready` | `vibe_port` wires (also TB aliases of the same names) |
| DLL↔PCS (640b) | `u_p.dll_pcs_data[639:0]`, `u_p.dll_pcs_vld`, `u_p.dll_pcs_ready`, `u_p.pcs_dll_data[639:0]`, `u_p.pcs_dll_vld`, `u_p.pcs_dll_ready` | `vibe_port` wires (also TB aliases of the same names) |
| PCS↔PMA | `pcs_pma_txdata[511:0]`, `pma_pcs_rxdata[511:0]`, `wav_lb_eq` | product pins; `pma_pcs_rxdata=pcs_pma_txdata` |
| PMA lanes | `afifo_pma_lane0..3[127:0]`, `afifo_pma_lane_vld`, `pma_afifo_lane0..3[127:0]`, `pma_afifo_lane_vld` | `u_p.u_pma` ports / `vibe_port` wires |
| PMA score | `wav_ptxv`, `wav_txlv`, `wav_lane0`, `wav_lane3` | `afifo_pma_lane_vld`; `pcs_afifo_lane_vld`; packed lane slices |
| RX | `nw_fab_vld`, `nw_fab_data[511:0]`, `wav_rx_sop`, `wav_rx_pld` | recovered NW beat |
| RX score | `wav_rx_eq`, `wav_am`, `wav_pcs_rx`, `wav_fec` | GOLDEN match; `am_locked`; `fec_fail` |
