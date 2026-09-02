# TP-0.3 regression — Overlay B 512-bit TB retarget + 100-packet loopback

Compiled **TB** on `cursor/vibe-tb-loopback-100-6065` against **`origin/main`**. **Zero `rtl/` diffs.** `rtl/` was not committed.

| Item | Value |
|------|--------|
| `origin/main` | `aa5d91c0480d5810a83f81086ff58718200ab4e2` |
| RTL tree SHA | `9d6f7f06354b43f4a3087451195dc1bea70eed78` |
| RTL message | Fix overlay-B remainder shift width and CNA first-flit opcode (`a3ecec9f`) |
| Gate | `make -C tb/vibe sim` (suite + units + top + neg) |

Spec: **FS-0.2.7 / AS-0.1.2**. Official 159 IDs unchanged. SOP LPH is `[511:352]` (`vibe_tb_mk_beat`). DLL↔PCS stays 640 (`vibe_tb_mk_pcs_beat`). Fabric/mgmt/NW pins are 512. Do not ask RTL to go back to 640.

## `make -C tb/vibe sim` (this revision)

| Bucket | pass | fail | compile_fail |
|--------|------|------|----------------|
| suite (`make suite`) | **27** | 0 | 0 |
| units (`make units`) | **85** | 0 | 0 |
| top (`make top`) | 0 | **1** | 0 |
| neg (`make neg`) | **10** | 0 | 0 |

Previously compile-fail / prune-FAIL TCs are **TB-fixed** (width mismatches were TB bugs):

| TC | Was | Now |
|----|-----|-----|
| suite (`vibe_fabric_harness` / `vibe_suite`) | compile_fail `[639:0]` | **27/27 PASS** |
| `tc_xbar_unit` | compile_fail | **PASS** |
| `tc_fabric_line_holes` | compile_fail | **PASS** |
| `tc_fabric_g1` | compile_fail | **PASS** |
| `tc_cna_ep` | compile_fail | **PASS** |
| `tc_mgmt` | compile_fail | **PASS** |
| `tc_cfg9_no_icrc` | compile_fail | **PASS** |
| `tc_saf_ing` | runtime (LPH pruned) | **PASS** |

Icarus note (TB-only, not an RTL widen): VOQ `wr_vl = vibe_lph_vl(vibe_nw512_flit0(xb_d))` combo-feeds xbar `out_ready` and delta-storms on the first RT=00 grant. Harness / `tc_cfg9_no_icrc` pin `wr_vl` so forward TCs can score `x_in_v` / SAF headers. G1/RT=10 still drop+count+sticky irq on the fabric cluster.

## `tc_nw_pkt_pma_loopback`

**PASS — 100 / 100 packets scored.**

- Each packet: unique `data[511:0]` (packet 0 = existing GOLDEN; others unique `[351:0]`).
- TX accepted `dll_tx` === that GOLDEN; RX `fab_rx_data[511:0]` === same GOLDEN, in order.
- `fec_fail=0`, `am_locked=1111`, `saw_deskew=1`.
- Reproduce: `make -C tb/vibe units` (or compile `tc_nw_pkt_pma_loopback.sv` + PORT_RTL).

## FAIL list (after Overlay B 512 + SOP LPH `[511:352]`)

These are **not** leftover 640-bit TB / iverilog `[639:512]` prune. Width is correct. Filed to **设计**.

| TC | stimulus | expected | actual | hier | reproduce |
|----|----------|----------|--------|------|-----------|
| `tc_top_smoke` | peer `fab_tx` = `vibe_tb_mk_beat` CFG3 **RT=10** SOP LPH `[511:352]`; `rxdata_0 = peer txdata`; wait 20000 `clk_fab` | `irq_logic=1` (G1 drop+count+sticky at top pin) | `irq_logic` stayed 0 (peer PMA `txdata` did go nonzero) | `dut.irq_logic` / `dut.u_fab.drop_g1` / `dut.u_mgmt` | `make -C tb/vibe top` |

Fabric-cluster G1 (`tc_fabric_g1`, suite `tc_rt10_must_drop` / `tc_rt_irq_logic_sticky`) **PASS**. Same-port Overlay B PMA loopback **PASS**. Cross-port top pin did not raise `irq_logic` with this stimulus.

## Overlay B content TCs (PASS)

| TC | Result |
|----|--------|
| `tc_phy_nw_dll_512b` | PASS |
| `tc_nw_adapt_linkready` | PASS |
| `tc_nw_pkt_to_pma_tx` | PASS |
| `tc_port_smoke` | PASS |
| `tc_nw_pkt_pma_loopback` | **PASS 100/100** |
