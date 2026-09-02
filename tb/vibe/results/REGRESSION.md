# TP-0.3 regression — 100-packet Overlay B loopback + full gate

Compiled **TB** on `cursor/vibe-tb-loopback-100-6065` against **`origin/main`** (no RTL overlay; `rtl/` not committed).

| Item | Value |
|------|--------|
| `origin/main` | `aa5d91c0480d5810a83f81086ff58718200ab4e2` |
| RTL SHA (files) | `a3ecec9f40e987e2dc49f586c34092c3ede5baa5` |
| RTL message | Fix overlay-B remainder shift width and CNA first-flit opcode |
| Gate | `make -C tb/vibe sim` (suite compile-failed; units + top + neg still run) |

Spec: **FS-0.2.7 / AS-0.1.2**. Official 159 IDs unchanged. SOP LPH is `[511:352]`.

## `tc_nw_pkt_pma_loopback`

**PASS — 100 / 100 packets scored.**

- Each packet: unique `data[511:0]` (packet 0 = existing GOLDEN; others unique `[351:0]`).
- TX accepted `dll_tx` === that GOLDEN; RX `fab_rx_data[511:0]` === same GOLDEN, in order.
- `fec_fail=0`, `am_locked=1111`, `saw_deskew=1`.
- Reproduce: `make -C tb/vibe units` (or compile `tc_nw_pkt_pma_loopback.sv` + PORT_RTL).

## Full regression counts

| Bucket | pass | fail | compile_fail |
|--------|------|------|----------------|
| suite (`make suite`) | 0 | 0 | **1** (harness; 7 width errors) |
| units (`make units`) | **78** | **7** | **6** (included in the 7) |
| top (`make top`) | 0 | **1** | 0 |
| neg (`make neg`) | **10** | 0 | 0 |

`make sim` exits at suite compile. Units/top/neg were run separately after that.

## FAIL list

**Not RTL data bugs on the 100-packet path.** The 100-packet loopback PASSed. Remaining FAILs are leftover **640-bit TB wires** vs Overlay B **512-bit** fabric/mgmt ports on main. Do **not** widen RTL back to 640.

### compile_fail (TB width)

| TC | Expected | Actual | hier | reproduce |
|----|----------|--------|------|-----------|
| suite (`vibe_fabric_harness` / `vibe_suite`) | TB `ing_data`/`egr_data`/`cfg6_*` match DUT `[511:0]` | TB still `[639:0]` | `vibe_fabric.ing_data` / `vibe_mgmt.cfg6_data` / `vibe_cna_ep` | `make -C tb/vibe suite` |
| `tc_xbar_unit` | TB `in_data`/`out_data` `[511:0]` | TB `[639:0]` | `vibe_xbar.in_data` | `make -C tb/vibe units` |
| `tc_fabric_line_holes` | fabric arrays `[511:0]` | TB `[639:0]` | `vibe_fabric.ing_data` | `make -C tb/vibe units` |
| `tc_fabric_g1` | same | TB `[639:0]` | `vibe_fabric.ing_data` | `make -C tb/vibe units` |
| `tc_cna_ep` | `cfg6_data`/`reply_data` `[511:0]` | TB `[639:0]` | `vibe_cna_ep.cfg6_data` | `make -C tb/vibe units` |
| `tc_mgmt` | same | TB `[639:0]` | `vibe_mgmt.cfg6_data` | `make -C tb/vibe units` |
| `tc_cfg9_no_icrc` | fabric arrays `[511:0]` | TB `[639:0]` | `vibe_fabric.ing_data` | `make -C tb/vibe units` |

### runtime FAIL (TB still drives 640; iverilog prunes `[639:512]`)

| TC | stimulus | expected | actual | hier | reproduce |
|----|----------|----------|--------|------|-----------|
| `tc_saf_ing` | 1 of 2 declared beats (`vibe_tb_mk_beat` 640b) | `pkt_vld=0` (SAF) | `1` | `u_s.pkt_vld` | `make -C tb/vibe units` |
| `tc_saf_ing` | oversize PLEN | `len_err` | `0` | `u_s.len_err` | `make -C tb/vibe units` |
| `tc_saf_ing` | 2 of 3 declared beats | `pkt_vld=0` | (finish) | `u_s.pkt_vld` | `make -C tb/vibe units` |
| `tc_top_smoke` | `rxdata_0` = peer txdata (RT=10 LPH) | `irq_logic=1` | `irq_logic` stayed 0 | `dut.irq_logic` / `dut.u_fab.drop_g1` | `make -C tb/vibe top` |

`tc_saf_ing` / `tc_top_smoke` LPH lives in the pruned high bits when TB is 640 and DUT is 512. Retarget those TCs to Overlay B (`[511:0]` + SOP `[511:352]`) before treating them as 设计 RTL FAILs.

## Overlay B content TCs (still PASS)

| TC | Result |
|----|--------|
| `tc_phy_nw_dll_512b` | PASS |
| `tc_nw_adapt_linkready` | PASS |
| `tc_nw_pkt_to_pma_tx` | PASS |
| `tc_port_smoke` | PASS |
| `tc_nw_pkt_pma_loopback` | **PASS 100/100** |
