# Vibe-UB-Switch firmware register manual

Status: documents `rtl/mgmt` on this commit only.  
Architecture: [AS-0.1](Vibe-UB-Switch-architecture-spec.md) (in-repo). RTL command width / Port Reset follow local AS-0.1.2.  
Machine-readable map: [rdl/vibe_ub_switch_mgmt.rdl](rdl/vibe_ub_switch_mgmt.rdl).  
C header: [`include/vibe_ub_switch_regs.h`](../include/vibe_ub_switch_regs.h).

Names, widths, resets, and command numbers in this file, the RDL, and the header are the same.

AS/FS vs `rtl/mgmt` wording diffs (facts only): [Vibe-UB-Switch-reg-diffs.md](Vibe-UB-Switch-reg-diffs.md). Firmware follows RTL.

---

## No MMIO

This RTL has **no address decode** in `rtl/mgmt` and **no APB / AXI / I2C / JTAG**.

Firmware does not read or write hex bus offsets. The firmware interface is a write-only static handshake on `vibe_ub_switch` pins, clocked by `clk_fab`:

| Pin | Width | Direction | RTL note |
|-----|-------|-----------|----------|
| `cfg_wr_vld` | 1 | in | write strobe |
| `cfg_wr_ready` | 1 | out | tied `1` in `vibe_cfg_space` |
| `cfg_wr_cmd` | **4** | in | command encoding = firmware address (AS-0.1.2). Opcodes 0–5; 6–15 ignore. |
| `cfg_wr_idx` | 16 | in | index / port select |
| `cfg_wr_data` | 32 | in | write data |
| `irq_logic` | 1 | out | sticky OR pin; firmware reads this pin only |

There is **no** product `cfg_rd_*` pin (AS §18). Port Reset bits are readable only as mgmt flops (`vibe_cfg_space.port_rst_rw1c`).

`cfg_wr_ready` is always 1, so every cycle with `cfg_wr_vld` is accepted.

There is no readable configuration-space window on this path. CFG6 terminate/reply in `vibe_cna_ep` **echos the request**; it does not return identity constants.

Official Appendix D MMIO offsets: **未知** (not implemented here).

---

## Command map (`address` = `cfg_wr_cmd`)

| address (`cfg_wr_cmd`) | Name | Action | access | reset (stored) |
|------------------------|------|--------|--------|----------------|
| 0 | `CMD_CNA` | write `CNA[15:0]`, set `cna_written` | WO | `CNA` = `16'h0` |
| 1 | `CMD_ROUTE_TABLE` | pulse route-table write into fabric | WO | RAM entry `32'h0` after `rst_n` / `device_rst` |
| 2 | `CMD_DEFAULT_BM` | write `default_bm[3:0]` | WO | `4'h0` |
| 3 | `CMD_PORT_RST` | Port Reset RW1C, port = `idx[1:0]`, bit = `data[0]` | RW1C | `Port Reset` = `0` (normal) |
| 4 | `CMD_DEVICE_RST` | WO pulse device reset | WO pulse | n/a (not a stored bit) |
| 5 | `CMD_LMSM_GO` | WO pulse `lmsm_go`, port = `idx[1:0]` | WO pulse | n/a (not a stored bit) |
| 6–15 | *(ignored)* | no config side effect | ignore | — |

Every accepted `cfg_wr`, including cmd 6–15, pulses `irq_clr`.

Route table RAM is in **fabric**, not mgmt. Mgmt only captures `rt_wr_en` / `rt_wr_idx` / `rt_wr_data` for one cycle.

---

## CMD_CNA — address 0

Write `cfg_wr_cmd = 0` (`VIBE_CMD_CNA`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `CNA` | `cfg_wr_data[15:0]` | 16 | `16'h0` | WO |

`cfg_wr_data[31:16]` and `cfg_wr_idx` unused.

**Side effects**

- Sets internal `cna_written` (reset `0`). DCNA match is gated by `cna_written`; a reset `CNA` of 0 is **not** a valid product CNA.
- Product CNA power-on default: **未知**.
- Pulses `irq_clr`.

---

## CMD_ROUTE_TABLE — address 1

Write `cfg_wr_cmd = 1` (`VIBE_CMD_ROUTE_TABLE`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `RT_BM` | `cfg_wr_data[3:0]` | 4 | `4'h0` (fabric RAM) | WO |
| `RT_IDX` | `cfg_wr_idx[15:0]` | 16 | `16'h0` (captured `rt_wr_idx`) | WO |

`cfg_wr_data[31:0]` is captured in full; lookup uses `[3:0]` only (AS-0.1.2).  
`cfg_wr_idx[15:0]` is captured in full; fabric RAM indexes `[7:0]` (`DEPTH=256`).

`DEPTH=256` is the architecture default, **not** product Route Table Max Index (**未知**).

**Side effects**

- One-cycle `rt_wr_en` into fabric.
- Pulses `irq_clr`.

---

## CMD_DEFAULT_BM — address 2

Write `cfg_wr_cmd = 2` (`VIBE_CMD_DEFAULT_BM`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `default_bm` | `cfg_wr_data[3:0]` | 4 | `4'h0` | WO |

`cfg_wr_data[31:4]` and `cfg_wr_idx` unused.

**Side effects**

- Pulses `irq_clr`.

AS-0.1.2: default all-0 → port 0 at the fabric.

---

## CMD_PORT_RST — address 3

Write `cfg_wr_cmd = 3` (`VIBE_CMD_PORT_RST`).

UB Appendix D.5.6 Table D-103 **Port Rst**, field **Port Reset**, bit 0, `RW1C_DE0_EO`: 1 = reset, 0 = normal. RSVD `[31:1]` RO.

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `PORT` | `cfg_wr_idx[1:0]` | 2 | n/a | port select |
| `Port Reset` | `cfg_wr_data[0]` | 1 | `1'b0` (normal) | **RW1C** |

Write `cfg_wr_data[0] == 1` is W1C: apply that port’s Port Reset sequence and set the stored bit to 1 (reset). `vibe_rst_ctl` holds `port_rst` while the bit reads 1; hardware returns the bit to 0 when the hold ends. Write `cfg_wr_data[0] == 0` does **not** start Port Reset.

The four stored bits live in `vibe_cfg_space.port_rst_rw1c` (inside mgmt). There is **no** top-level read pin.

CFG6 R/W of this bit: AS names CFG6 for the subset. Official opcode `0x10` payload packing / Appendix D offsets are **未知**. `vibe_cna_ep` still echos the request.

**Side effects**

- Write-1 starts `port_rst_pulse[PORT]` (stretched by `vibe_rst_ctl`).
- Pulses `irq_clr` because every static write does.
- The Port Reset **hold** (`port_rst`) itself does **not** clear `irq_logic`.

AS-0.1.2 (port `p` only): that port → LMSM `Link_Idle`, `DLL_Disabled`, retry pointers 0, `NumFreeBuf=256`. Does not reset other ports or the global route table.

---

## CMD_DEVICE_RST — address 4

Write `cfg_wr_cmd = 4` (`VIBE_CMD_DEVICE_RST`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| *(none stored)* | idx and data unused | — | n/a | **WO pulse** |

Not an RW1C readable bit.

**Side effects**

- Pulses `device_rst_pulse` (stretched by `vibe_rst_ctl`).
- Pulses `irq_clr`. `vibe_mgmt` also clears irq with `irq_clr | device_rst`.
- `device_rst` into `vibe_cfg_space` clears `CNA` to `16'h0`, `cna_written` to `0`, `default_bm` to `4'h0`.

AS-0.1.2: device reset must not by itself force `DLL_Disabled`; LMSM → `Link_Idle`.

---

## CMD_LMSM_GO — address 5

Write `cfg_wr_cmd = 5` (`VIBE_CMD_LMSM_GO`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `PORT` | `cfg_wr_idx[1:0]` | 2 | n/a | **WO pulse** |

`cfg_wr_data` unused. Not an RW1C readable bit.

**Side effects**

- Pulses `lmsm_go_pulse[PORT]`.
- Pulses `irq_clr`.

---

## irq_logic (pin, not a CSR)

`irq_logic` is a **1-bit sticky OR** of error inputs in `vibe_irq_agg`. There is **no per-cause status register** and no status address.

Firmware reads the **pin** only (`VIBE_IRQ_LOGIC_WIDTH` / `VIBE_IRQ_LOGIC_MASK` in the header are pin helpers, not an address).

| Clear source | Clears `irq_logic`? |
|--------------|---------------------|
| Any accepted `cfg_wr` (cmd 0–15) | yes (`irq_clr`) |
| `rst_n` | yes |
| `device_rst` | yes (`irq_clr \| device_rst` in `vibe_mgmt`) |
| Port Reset hold (`port_rst`) | **no** |

`icrc_fail` from `vibe_cna_ep` is **hardwired 0**, so that input never sets the sticky bit in this RTL.

Product IRQ pin name, polarity, and vector count: **未知**. This RTL exposes one pin named `irq_logic` (AS-0.1.2 describes it as an active-high level).

---

## Identity constants (not readable this RTL)

These exist as combinational constants in `vibe_cfg_space` and are **tied off** in `vibe_mgmt`. They are not on chip pins and are not readable via `cfg_wr` or CFG6.

| Name | Value | width | access |
|------|-------|-------|--------|
| `guid0` | `32'h00000003` | 32 | not readable this RTL |
| `class_code` | `32'h00000300` | 32 | not readable this RTL |
| `PORT_BASIC` | `32'h00040402` | 32 | not readable this RTL |
| `PORT_CAP` | `32'h00000104` | 32 | not readable this RTL |

Header: `VIBE_GUID0`, `VIBE_CLASS_CODE`, `VIBE_PORT_BASIC`, `VIBE_PORT_CAP`.  
`PORT_BASIC` / `PORT_CAP` official bit packing: **未知**.

---

## Gap table (未知 — do not speculate)

| Topic | What this RTL shows | Gap |
|-------|---------------------|-----|
| IRQ pin name / polarity / vector count | one pin `irq_logic` | product/package name, polarity, vector count **未知** |
| Reset pin polarity | pin `rst_n` used active-low in RTL | product reset polarity **未知** |
| CNA product default | flop reset `16'h0`, match gated by `cna_written==0` | power-on CNA value **未知**; 0 is not a valid CNA |
| Route Table Max Index | fabric RAM `DEPTH=256`, index `[7:0]` | product Max Index **未知** |
| `PORT_BASIC` / `PORT_CAP` bit packing | constants `32'h00040402` / `32'h00000104` | official field packing **未知** |
| Appendix D MMIO offsets | no MMIO | official offsets **未知** |
| G1 counter firmware-readable | internal `rt_shortest_unimpl` (fabric/top), not on `cfg_wr` | firmware-readable G1 counter **未知** / not provided |
| CFG6 read of Port Reset / identity | `vibe_cna_ep` echos the request | opcode `0x10` payload packing **未知** |

---

## Firmware write recipe (no bus)

1. Drive `cfg_wr_cmd` with `VIBE_CMD_*` (0–5).
2. Drive `cfg_wr_idx` / `cfg_wr_data` using `VIBE_PACK_*` (or the matching shift/mask).
3. Pulse `cfg_wr_vld` for one `clk_fab` cycle. `cfg_wr_ready` is tied 1.
4. Read `irq_logic` from the pin if needed. Clear it with any static write, `rst_n`, or device reset.

Example: set CNA, then default bitmap.

```c
#include "vibe_ub_switch_regs.h"

/* cmd=0, idx=0, data=VIBE_PACK_CNA(cna) */
/* cmd=2, idx=0, data=VIBE_PACK_DEFAULT_BM(bm) */
```
