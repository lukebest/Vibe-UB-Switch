# Vibe-UB-Switch register interface diffs (AS / FS vs `rtl/mgmt`)

Status: facts only. This list does **not** choose a side and is **not** a fix list.  
Do not change AS, FS, or RTL from this document.

Firmware artifacts follow **RTL**: `cfg_wr_cmd[2:0]`, pin `irq_logic`, **no MMIO**.

| Artifact | Path |
|----------|------|
| In-repo AS | [Vibe-UB-Switch-architecture-spec.md](Vibe-UB-Switch-architecture-spec.md) (AS-0.1) |
| Local overlay cited here | AS-0.1.2 / FS-0.2.3 / FS-0.2.7 (true FS is outside this repo) |
| UB 2.0 Appendix D | [UB-spec.md](UB-spec.md) Table D-103 Port Rst |
| RTL source | `rtl/mgmt/*`, `rtl/top/vibe_ub_switch.sv` ports |
| Firmware map (RTL) | [Vibe-UB-Switch-register-map.md](Vibe-UB-Switch-register-map.md), [rdl/vibe_ub_switch_mgmt.rdl](rdl/vibe_ub_switch_mgmt.rdl), [`include/vibe_ub_switch_regs.h`](../include/vibe_ub_switch_regs.h) |

---

## 1. `cfg_wr_cmd` width

| Side | Statement |
|------|-----------|
| Local AS-0.1.2 | `cfg_wr_cmd` is **4 bits** |
| In-repo AS-0.1 §10 / §18 | names `cfg_wr_cmd` without a width; opcodes 0–5 + others ignore |
| RTL / top | `cfg_wr_cmd[2:0]` (**3 bits**) on `vibe_cfg_space`, `vibe_mgmt`, `vibe_ub_switch` |
| Header / RDL | follow RTL **3 bits**. Do not invent cmd 8–15 |

Opcodes 0–5 still fit in 3 bits. cmd 6/7 are the remaining 3-bit encodings; RTL ignores them except they still pulse `irq_clr`.

---

## 2. Port Reset access type

| Side | Statement |
|------|-----------|
| FS / Appendix D | Table D-103 **Port Rst**, field **Port Reset**, attribute **RW1C** (`RW1C_DE0_EO`) |
| In-repo AS-0.1 §10 | “Port Reset RW1C per port” |
| RTL | write-only **1-cycle pulse**: `cfg_wr_cmd=3`, port = `cfg_wr_idx[1:0]` → `port_rst_pulse`. No readable bit, no RW1C CSR |

Header / RDL / register map document RTL as **WO pulse** and mark the RW1C name as a gap. They do not implement a fake RW1C register.

---

## 3. Identity constants not readable

| Side | Statement |
|------|-----------|
| AS-0.1 §10 | Must implement GUID Type `0x3`, Class `0x03`/`0x00`, `CFG0_PORT_BASIC` / `CAP` constants |
| TP-ID-001 (FS-0.2.7 / AS-0.1.2) | software can identify the device as an independent UB Switch (GUID Type / Class Code) |
| RTL | `guid0=32'h00000003`, `class_code=32'h00000300`, `PORT_BASIC=32'h00040402`, `PORT_CAP=32'h00000104` exist as combo assigns in `vibe_cfg_space` |
| RTL hookup | those four outputs are **tied off** in `vibe_mgmt`. Not on chip pins. Not readable via `cfg_wr` |

Firmware treats them as compile-time constants (`VIBE_GUID0`, …) with access = **not readable this RTL**. Official `PORT_BASIC` / `PORT_CAP` bit packing remains **未知**.

---

## 4. CFG6 reply is echo-only

| Side | Statement |
|------|-----------|
| AS-0.1 §9 / §13 | CFG6 terminate when DCNA matches a **written** CNA (or NLP=1 / opcode `0x10`); `cna_ep` is the sender/receiver ICRC point |
| RTL `vibe_cna_ep` | on terminate, `reply_data` **echos** `cfg6_data`. No identity or CSR payload is inserted |
| RTL `icrc_fail` | hardwired `0` in `vibe_cna_ep` |

CFG6 is not a register-read path for GUID / Class / `PORT_BASIC` / `PORT_CAP`.

---

## 5. No per-cause IRQ CSR

| Side | Statement |
|------|-----------|
| FS Appendix D | per-cause error/status bits (RW1C / RW1CS style) in configuration space |
| AS-0.1 §10 / §15 | single sticky `irq_logic`, OR of listed errors; no extra product IRQ pins |
| RTL | 1-bit sticky OR in `vibe_irq_agg`. **No per-cause status register**. Firmware reads pin `irq_logic` only |

Header / RDL expose `irq_logic` as a **pin** (width/mask helpers only). No fake status address.

---

## 6. IRQ clear: any static write; Port Reset pulse does not

| Side | Statement |
|------|-----------|
| AS-0.1 §10 | `irq_logic` sticky; clear on **static write or reset** |
| RTL `vibe_cfg_space` | **every** accepted `cfg_wr` (cmd 0–7, including ignored 6/7) pulses `irq_clr` |
| RTL `vibe_irq_agg` / `vibe_mgmt` | clear on `irq_clr`, `rst_n`, or `device_rst` (`irq_clr \| device_rst`) |
| RTL Port Reset | `port_rst` is **not** an `irq_agg` clear input |

A cmd=3 write still pulses `irq_clr` because it is a static write. The Port Reset **pulse** (`port_rst`) itself does not clear `irq_logic`.

---

## Firmware alignment (unchanged)

Humans use this list to compare texts. Firmware continues to follow RTL:

- address = `cfg_wr_cmd[2:0]`
- pin `irq_logic`, no MMIO, no APB/AXI/I2C/JTAG
- Port Reset = `VIBE_CMD_PORT_RST` WO pulse
