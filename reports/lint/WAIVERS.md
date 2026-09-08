# Verilator lint waivers — `vibe_ub_switch`

Tool: Verilator 5.020 (Debian).  
Command: `reports/lint/run_lint.sh`  
Log: [`vibe_ub_switch.lint.log`](vibe_ub_switch.lint.log)  
Config: [`vibe_ub_switch.vlt`](vibe_ub_switch.vlt)

**Result: 0 `%Error-*` codes.** `-Wno-fatal` is used so the warning volume does not fail the run.

Lint ECO 2026-09-08 (Luke-approved) cleared structural `-Wall` debt: **LATCH=0, UNOPTFLAT=0, BLKSEQ=0**. Remaining classes below stay waived. This change did not introduce a new warning class.

## Errors converted to waivers (`.vlt`)

| Rule | Where | Why waived |
|------|--------|------------|
| `UNSUPPORTED` | `vibe_pcs_rx.sv:5` `link_up = 1'b0`; `vibe_pcs_rx_fec.sv:14` / `vibe_pcs_rx_unpack.sv:17` `am_gap = 1'b0` | Verilator 5.020 does not allow default values on module inputs. Pins are always connected at instantiate. Pre-existing; not this change. |
| `BLKLOOPINIT` | `vibe_route_lu.sv` delayed assign to array inside `for` | Verilator 5.020 limitation. Pre-existing fabric route write; not this change. |

## Warning classes (`-Wall`)

| Class | Count | Waiver |
|-------|------:|--------|
| `UNUSEDPARAM` | 838 | `vibe_ub_params.vh` is `include`d per module (no ifndef). Most localparams are unused in any one file. Shared architecture bag; not a functional hole. `ROUTE_TABLE_DEPTH` on `vibe_cfg_space` is unused (pre-existing). **Not mass-cleaned.** |
| `UNUSEDSIGNAL` | 148 | Tied-off / observed-only wires (`disabled`, `cfg6_cons`, `rt_shortest_unimpl`, `drop_down`, AFIFO `wocc`/`wfull`, `cna_ep` `clk`/`rst_n`/`reply_ready`, identity constants). Hierarchical probes, not missing resets. Count is freeze `1ed4d350` remasure (5.020); nightly 154 was DUT `32a7f5e0` VOID. |
| `PINCONNECTEMPTY` | 37 | Intentional unused outputs: identity (`guid0`/`class_code`/`port_basic`/`port_cap` — not on pins; CFG6 echo), `cfg0_*`, `irq_rt`, lane `sdf`/`ack`/`out_vld`, FIFO occupancy. |
| `WIDTHTRUNC` | 30 | Pre-existing index / counter / header slices (fabric, DLL, PCS). |
| `WIDTHEXPAND` | 18 | Pre-existing implicit promotions. Same as above. |
| `VARHIDDEN` | 4 | `vibe_ub_fn.vh` function args `cna` / `cna_written` hide module ports in `vibe_fabric` and `vibe_cna_ep`. Include-file helper; behavior uses the function inputs. |

## Cleared by Lint ECO 2026-09-08

| Class | Was | Now | Root cause / fix |
|-------|----:|----:|------------------|
| `LATCH` | 2 | 0 | `vibe_xbar.sv` combo `req`/`win` not assigned on down / locked paths. Full combo defaults each iteration; RR grant still starts at `rr[e]`. |
| `UNOPTFLAT` | 2 | 0 | False ready/valid combo loop: `x_in_v` / `xb_r` via one `always @*` that both consumed `xb_in_r` and drove `fab_mgmt_cfg6_hit`. Split CFG6 hit from `saf_r`. Overlay B / fire / widths unchanged. |
| `BLKSEQ` | 2 | 0 | `vibe_saf_ing.sv` blocking `=` on `plen`/`dflits` in the clocked process. Temps are combo; sequential uses them with `<=` only. |

## This-change notes

- Structural lint only. No SPEC/TB. No interface fire/width change.
- **F1 / `ovf_l`:** `rtl/port/vibe_port.sv` CDC path not modified. CDC-WARN stays frozen.
- No `$display`, no `force`.
- `.vlt` unchanged (UNSUPPORTED + BLKLOOPINIT only).

## 未知 (unchanged)

- CFG6 opcode `0x10` payload packing / Appendix D offsets
- Product CNA default, Route Table Max Index, `PORT_BASIC`/`PORT_CAP` packing
- Product IRQ pin name / polarity / vector count
