# Vibe-UB-Switch firmware register manual

Status: firmware contract is the **architecture spec** (AS-0.1 + AS-0.1.2 `cfg_wr_cmd` width), **not** a snapshot of `rtl/mgmt`.  
A 3-bit RTL cmd bus / write-only Port Reset pulse is **void** for firmware. RTL is being changed separately; this manual does not claim current `rtl/mgmt` already matches.

Architecture: [AS-0.1](Vibe-UB-Switch-architecture-spec.md).  
Machine-readable map: [rdl/vibe_ub_switch_mgmt.rdl](rdl/vibe_ub_switch_mgmt.rdl).  
C header: [`include/vibe_ub_switch_regs.h`](../include/vibe_ub_switch_regs.h).  
Contract vs snapshot notes: [Vibe-UB-Switch-reg-diffs.md](Vibe-UB-Switch-reg-diffs.md).

Names, widths, resets, and command numbers in this file, the RDL, and the header are the same.

---

## No MMIO

AS §10 / §18: **no APB / AXI / I2C / JTAG**, no extra interrupt pins. There is no address decode and no Appendix D MMIO window.

Firmware does not use hex bus offsets. The firmware interface is the AS **static write** handshake on `vibe_ub_switch`, clocked by `clk_fab`:

| Pin | Width | Direction | AS note |
|-----|-------|-----------|---------|
| `cfg_wr_vld` | 1 | in | write strobe |
| `cfg_wr_ready` | 1 | out | `vld`/`ready` (AS §10) |
| `cfg_wr_cmd` | **4** | in | command encoding = firmware address (AS-0.1.2). Encodings 0–5 used; 6–15 reserved/ignored |
| `cfg_wr_idx` | 16 | in | index / port select |
| `cfg_wr_data` | 32 | in | write data |
| `irq_logic` | 1 | out | sticky OR pin; firmware reads this pin only |

AS names **no `cfg_rd_*` pins**. Do not invent a read bus or MMIO offsets.

Official Appendix D MMIO offsets: **未知** (not in AS).

---

## Command map (`address` = `cfg_wr_cmd[3:0]`)

| address (`cfg_wr_cmd`) | Name | Action | access | reset (stored) |
|------------------------|------|--------|--------|----------------|
| 0 | `CMD_CNA` | write `CNA[15:0]` (static write only) | WO | product CNA default **未知** |
| 1 | `CMD_ROUTE_TABLE` | write route-table entry | WO | entry `[3:0]` = `4'h0` (table all-0) |
| 2 | `CMD_DEFAULT_BM` | write `default_bm[3:0]` | WO | `4'h0` |
| 3 | `CMD_PORT_RST` | write 1 to per-port Port Reset bit `idx[1:0]` | **RW1C** | `PORT_RST` = `0` per port |
| 4 | `CMD_DEVICE_RST` | Entity 0 device reset | WO pulse | n/a |
| 5 | `CMD_LMSM_GO` | pulse `lmsm_go`, port = `idx[1:0]` | WO pulse | n/a |
| 6–15 | *(reserved)* | ignored | ignore | — |

Accepted static writes clear `irq_logic` (AS §10: sticky; clear on static write or reset).

---

## CMD_CNA — address 0

Write `cfg_wr_cmd = 0` (`VIBE_CMD_CNA`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `CNA` | `cfg_wr_data[15:0]` | 16 | product default **未知** | WO |

`cfg_wr_data[31:16]` and `cfg_wr_idx` unused.

**Side effects**

- CNA is statically written (AS §10). DCNA match only after that write (AS §9). Do not treat 0 as a valid CNA.
- Clears `irq_logic` (static write).

---

## CMD_ROUTE_TABLE — address 1

Write `cfg_wr_cmd = 1` (`VIBE_CMD_ROUTE_TABLE`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `RT_BM` | `cfg_wr_data[3:0]` | 4 | `4'h0` | WO |
| `RT_IDX` | `cfg_wr_idx[15:0]` | 16 | — | WO |

AS §10: entries 32-bit, only `[3:0]` meaningful. `ROUTE_TABLE_DEPTH` default 256 is architecture-chosen, **not** product Max Index (**未知**).

**Side effects**

- Updates `CFG0_ROUTE_TABLE` at `RT_IDX`.
- Clears `irq_logic` (static write).

---

## CMD_DEFAULT_BM — address 2

Write `cfg_wr_cmd = 2` (`VIBE_CMD_DEFAULT_BM`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `default_bm` | `cfg_wr_data[3:0]` | 4 | `4'h0` | WO |

`cfg_wr_data[31:4]` and `cfg_wr_idx` unused.

**Side effects**

- Clears `irq_logic` (static write).

AS-0.1: default all-0 → port 0.

---

## CMD_PORT_RST — address 3 (RW1C)

Write `cfg_wr_cmd = 3` (`VIBE_CMD_PORT_RST`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `PORT_RST` | per-port bit; write `cfg_wr_data[0]=1` | 1 | `0` | **RW1C** |
| `PORT` | `cfg_wr_idx[1:0]` | 2 | n/a | select |

Four software-visible bits (`PORT_RST` for ports 0..3), each reset `0`. `cmd=3` **writes 1** to the bit selected by `idx[1:0]`. Firmware can observe that bit until **write-1-clears**.

This is **not** a write-only pulse. It is the AS/FS **Port Rst.Port Reset** RW1C bit.

**Read path**

Readability is via the static interface in mgmt/`cfg_space` (AS §4 / §10). AS names **no `cfg_rd_*`** and no read-data pins. The RW1C **read-data path is 未知**. Do not invent `cfg_rd_*` or an MMIO address.

**Side effects**

- Port Reset for port `p` (AS §10): that port LMSM `Link_Idle`, `DLL_Disabled`, retry pointers 0, `NumFreeBuf=256`. Does not reset other ports or the global route table.
- Clears `irq_logic` (static write or reset).

---

## CMD_DEVICE_RST — address 4

Write `cfg_wr_cmd = 4` (`VIBE_CMD_DEVICE_RST`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| *(none stored)* | idx and data unused | — | n/a | **WO pulse** |

Not an RW1C readable bit. Entity 0 device reset (AS §10): clear RW config to unwritten (CNA unwritten). Must not by itself force `DLL_Disabled`. LMSM → `Link_Idle`.

**Side effects**

- Clears `irq_logic` (reset).

---

## CMD_LMSM_GO — address 5

Write `cfg_wr_cmd = 5` (`VIBE_CMD_LMSM_GO`).

| Field | Pin / bits | width | reset | access |
|-------|------------|-------|-------|--------|
| `PORT` | `cfg_wr_idx[1:0]` | 2 | n/a | **WO pulse** |

`cfg_wr_data` unused. Not an RW1C bit. `Link_Idle` → `Discovery` on `lmsm_go` (AS §11).

**Side effects**

- Clears `irq_logic` (static write).

---

## irq_logic (pin, not a CSR)

`irq_logic` is a **1-bit sticky OR** of the errors listed in AS §15. There is **no per-cause status register** and no status address.

Firmware reads the **pin** only (`VIBE_IRQ_LOGIC_WIDTH` / `VIBE_IRQ_LOGIC_MASK` are pin helpers, not an address).

AS §10: sticky; **clear on static write or reset**. Single bit; no extra product IRQ pins.

Product IRQ pin name, polarity, and vector count: **未知**.

---

## Identity constants (compile-time)

AS §10 requires GUID Type `0x3`, Class `0x03`/`0x00`, and `CFG0_PORT_BASIC` / `CAP` constants. AS does **not** name a GUID / identity read on `cfg_wr_*`. Firmware holds them as compile-time constants.

| Name | Value | width | access |
|------|-------|-------|--------|
| `guid0` | `32'h00000003` | 32 | compile-time; not a `cfg_wr` read |
| `class_code` | `32'h00000300` | 32 | compile-time; not a `cfg_wr` read |
| `PORT_BASIC` | `32'h00040402` | 32 | compile-time; not a `cfg_wr` read |
| `PORT_CAP` | `32'h00000104` | 32 | compile-time; not a `cfg_wr` read |

Header: `VIBE_GUID0`, `VIBE_CLASS_CODE`, `VIBE_PORT_BASIC`, `VIBE_PORT_CAP`.  
`PORT_BASIC` / `PORT_CAP` official bit packing: **未知**.

---

## Gap table (未知 — do not speculate)

| Topic | AS / firmware contract | Gap |
|-------|------------------------|-----|
| Port Reset read-data path | RW1C bit is software-visible | AS names no `cfg_rd_*`; read-data path **未知** |
| IRQ pin name / polarity / vector count | one pin `irq_logic`, active-high level (AS) | product/package name, polarity, vector count **未知** |
| Reset pin polarity | logical `rst_n` (AS §18) | product reset polarity **未知** |
| CNA product default | static write only; do not match until written | power-on CNA value **未知** |
| Route Table Max Index | `ROUTE_TABLE_DEPTH` default 256 (architecture-chosen) | product Max Index **未知** |
| `PORT_BASIC` / `PORT_CAP` bit packing | constants required | official field packing **未知** |
| Appendix D MMIO offsets | no MMIO in AS | official offsets **未知** |
| G1 counter firmware-readable | AS requires `rt_shortest_unimpl` increment + `irq_logic` | firmware-readable counter **未知** |

---

## Firmware write recipe (no bus)

1. Drive `cfg_wr_cmd` with `VIBE_PACK_CMD(VIBE_CMD_*)` (4-bit, 0–5).
2. Drive `cfg_wr_idx` / `cfg_wr_data` using `VIBE_PACK_*`.
3. Handshake `cfg_wr_vld` / `cfg_wr_ready` on `clk_fab`.
4. Port Reset: `cmd=3`, `idx=VIBE_PACK_PORT(p)`, `data=VIBE_PACK_PORT_RST(1)` to write 1 to that port’s RW1C bit; write 1 again to clear. Observing the bit uses the static interface; read-data path **未知**.
5. Read `irq_logic` from the pin if needed. Clear with a static write or reset.

```c
#include "vibe_ub_switch_regs.h"

/* cmd=VIBE_PACK_CMD(VIBE_CMD_CNA), idx=0, data=VIBE_PACK_CNA(cna) */
/* cmd=VIBE_PACK_CMD(VIBE_CMD_PORT_RST), idx=VIBE_PACK_PORT(p),
   data=VIBE_PACK_PORT_RST(1) */
```
