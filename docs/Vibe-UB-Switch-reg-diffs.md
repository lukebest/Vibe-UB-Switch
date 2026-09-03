# Vibe-UB-Switch register interface — firmware contract vs snapshot RTL

**Firmware contract = architecture spec** (in-repo AS-0.1 + local AS-0.1.2 `cfg_wr_cmd` width).  
Header, RDL, and the register manual follow **AS**. They do **not** follow a snapshot of `rtl/mgmt`.

A prior firmware reading that treated `cfg_wr_cmd[2:0]` and Port Reset as a write-only pulse is **void**. Those RTL-vs-AS mismatches are **no longer the firmware contract**. The design engineer is changing RTL separately. **Do not claim current `rtl/mgmt` already matches AS.**

This list is alignment for humans. It is not a license to edit AS or `rtl/` here.

| Artifact | Path |
|----------|------|
| Firmware contract | [Vibe-UB-Switch-architecture-spec.md](Vibe-UB-Switch-architecture-spec.md) (AS-0.1), AS-0.1.2 cmd width |
| Header / RDL / manual | [`include/vibe_ub_switch_regs.h`](../include/vibe_ub_switch_regs.h), [rdl/vibe_ub_switch_mgmt.rdl](rdl/vibe_ub_switch_mgmt.rdl), [Vibe-UB-Switch-register-map.md](Vibe-UB-Switch-register-map.md) |
| Snapshot RTL (void for firmware) | `rtl/mgmt/*`, `rtl/top/vibe_ub_switch.sv` — being changed elsewhere |
| FS name (Port Reset) | [UB-spec.md](UB-spec.md) Table D-103 **Port Rst.Port Reset** RW1C |

---

## Firmware contract (AS) — what the header implements

### `cfg_wr_cmd[3:0]` (4 bits)

AS-0.1.2: `cfg_wr_cmd` is **4 bits**. Encodings (AS §10): 0=CNA, 1=route entry, 2=Default bitmap, 3=Port Reset, 4=device reset, 5=`lmsm_go`; **other values reserved/ignored**.

C macros use a 4-bit cmd (`VIBE_CFG_WR_CMD_WIDTH=4`, `VIBE_PACK_CMD`). Do not invent opcodes 6–15.

### Port Reset is RW1C

AS §10: “Port Reset RW1C per port.” FS: **Port Rst.Port Reset** RW1C.

Firmware contract:

- Software-visible **per-port bit**, reset **0**, **readable**, **write-1-clears**
- `cfg_wr_cmd=3` **writes 1** to the selected port bit (`cfg_wr_idx[1:0]`)
- Firmware can observe the bit until W1C
- **No MMIO address**

AS §4 places this in `mgmt` / `cfg_space`. AS §10 names only the **static write** pins (`cfg_wr_*`). AS does **not** name `cfg_rd_*`. RW1C readability is via that static interface; the **read-data path is 未知**. Do not invent `cfg_rd_*`.

Device reset and `lmsm_go` remain command pulses (AS §10), not RW1C bits.

### Still no MMIO

No APB/AXI/I2C/JTAG. No Appendix D offsets. Address = `cfg_wr_cmd[3:0]`. Pin `irq_logic` only (no per-cause IRQ CSR).

### Identity still compile-time

AS §10 requires GUID Type `0x3`, Class `0x03`/`0x00`, `PORT_BASIC` / `CAP` constants. AS does **not** add a GUID / identity read. Header keeps compile-time `VIBE_GUID0` / `VIBE_CLASS_CODE` / `VIBE_PORT_BASIC` / `VIBE_PORT_CAP`.

### IRQ clear (AS)

AS §10: `irq_logic` sticky; **clear on static write or reset**. Firmware reads the pin. Product pin name / polarity / vector count: **未知**.

### CNA

AS §10: 16-bit mgmt CNA, **static write only**. AS §9: power-on CNA default UNKNOWN; do not match DCNA until a static write.

---

## Snapshot RTL — void for firmware (do not treat as contract)

Current in-tree `rtl/mgmt` / top ports may still show a **3-bit** `cfg_wr_cmd` and a **1-cycle WO pulse** for cmd=3. That snapshot is **void** for firmware. It is **not** what the header, RDL, or register manual implement.

Do **not** document firmware as “follow RTL 3 bits” or “Port Reset is WO pulse.” Do **not** claim the snapshot already implements AS RW1C or `cfg_wr_cmd[3:0]`.

---

## Gaps that remain 未知 (unchanged)

| Topic | Note |
|-------|------|
| Port Reset RW1C read-data path | AS names no `cfg_rd_*` |
| Appendix D MMIO offsets | AS has no MMIO |
| `PORT_BASIC` / `PORT_CAP` bit packing | constants only |
| CNA product default | UNKNOWN |
| Route Table Max Index | DEPTH=256 is architecture default |
| IRQ package name / polarity / vector count | one logical `irq_logic` |
| G1 counter firmware-readable | AS requires count + irq, not a `cfg_wr` read |
