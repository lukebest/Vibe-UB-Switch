# Verilator lint waivers — `vibe_ub_switch`

Tool: Verilator 5.020 (Debian).  
Command: `reports/lint/run_lint.sh`  
Log: [`vibe_ub_switch.lint.log`](vibe_ub_switch.lint.log)  
Config: [`vibe_ub_switch.vlt`](vibe_ub_switch.vlt)

**Result: 0 `%Error-*` codes.** `-Wno-fatal` is used so the warning volume does not fail the run. Every `-Wall` warning class below is waived.

This change did not introduce a new warning class. Port Reset RW1C / 4-bit `cfg_wr_cmd` lint clean aside from the shared `vibe_ub_params.vh` UNUSEDPARAM include (same as every other module).

## Errors converted to waivers (`.vlt`)

| Rule | Where | Why waived |
|------|--------|------------|
| `UNSUPPORTED` | `vibe_pcs_rx.sv:5` `link_up = 1'b0`; `vibe_pcs_rx_fec.sv:14` / `vibe_pcs_rx_unpack.sv:17` `am_gap = 1'b0` | Verilator 5.020 does not allow default values on module inputs. Pins are always connected at instantiate. Pre-existing; not this change. |
| `BLKLOOPINIT` | `vibe_route_lu.sv` delayed assign to array inside `for` | Verilator 5.020 limitation. Pre-existing fabric route write; not this change. |

## Warning classes (`-Wall`)

| Class | Count | Waiver |
|-------|------:|--------|
| `UNUSEDPARAM` | 838 | `vibe_ub_params.vh` is `include`d per module (no ifndef). Most localparams are unused in any one file. Shared architecture bag; not a functional hole. `ROUTE_TABLE_DEPTH` on `vibe_cfg_space` is unused (pre-existing). |
| `UNUSEDSIGNAL` | 154 | Tied-off / observed-only wires (`disabled`, `cfg6_cons`, `rt_shortest_unimpl`, `drop_down`, AFIFO `wocc`/`wfull`, `cna_ep` `clk`/`rst_n`/`reply_ready`, identity constants). Hierarchical probes, not missing resets. |
| `PINCONNECTEMPTY` | 37 | Intentional unused outputs: identity (`guid0`/`class_code`/`port_basic`/`port_cap` — not on pins; CFG6 echo), `cfg0_*`, `irq_rt`, lane `sdf`/`ack`/`out_vld`, FIFO occupancy. |
| `WIDTHTRUNC` | 30 | Pre-existing index / counter / header slices (fabric, DLL, PCS). Not introduced by 4-bit `cfg_wr_cmd`. |
| `WIDTHEXPAND` | 18 | Pre-existing implicit promotions. Same as above. |
| `VARHIDDEN` | 4 | `vibe_ub_fn.vh` function args `cna` / `cna_written` hide module ports in `vibe_fabric` and `vibe_cna_ep`. Include-file helper; behavior uses the function inputs. |
| `UNOPTFLAT` | 2 | Fabric ready/valid combo loops (`x_in_v`, `xb_r`). Pre-existing xbar/SAF handshake, not mgmt. |
| `LATCH` | 2 | `vibe_xbar.sv` combo `req`/`win` not assigned on every path. Pre-existing. (`vibe_cna_ep` temps are now initialized; no latch there.) |
| `BLKSEQ` | 2 | `vibe_saf_ing.sv` blocking `=` in a sequential process. Pre-existing. |

## This-change notes

- New `cfg_wr_cmd[3:0]` and Port Reset RW1C flops are fully assigned in a clocked `always`; no latch, no `$display`, no `force`.
- `irq_clr` still pulses on every accepted write, including opcodes 6–15.
- No top-level `cfg_rd_*` pin was added.

## 未知 (unchanged)

- CFG6 opcode `0x10` payload packing / Appendix D offsets
- Product CNA default, Route Table Max Index, `PORT_BASIC`/`PORT_CAP` packing
- Product IRQ pin name / polarity / vector count
