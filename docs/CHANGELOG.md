# Changelog

## Unreleased

### Changed

- Static-write interface matches AS-0.1.2: `cfg_wr_cmd` is **4 bits** on `vibe_ub_switch` / `vibe_mgmt` / `vibe_cfg_space`. Opcodes 0–5; 6–15 ignore (`irq_clr` still pulses).
- Port Reset is **RW1C per port** (Table D-103): stored bits in `vibe_cfg_space.port_rst_rw1c`. Write `cfg_wr_data[0]==1` starts that port’s sequence; HW returns the bit to 0 when `rst_ctl` hold ends. Write 0 does not start reset. No top-level read pin. CFG6 payload packing remains 未知 (echo).
- Firmware artifacts follow RTL: `include/vibe_ub_switch_regs.h`, `docs/rdl/vibe_ub_switch_mgmt.rdl`, `docs/Vibe-UB-Switch-register-map.md`.

### Added

- `docs/STATUS.md` and `docs/RISKS.md` — 2026-09-04 Asia/Shanghai snapshot (gates, module matrix, open issue/PR counts, top risks). Docs only; no RTL/SPEC/TB change.
- Firmware-facing management register documentation for the static handshake (`cfg_wr_*`). This is not MMIO; there is no APB/AXI/I2C/JTAG decode in `rtl/mgmt`.
  - `docs/rdl/vibe_ub_switch_mgmt.rdl` — SystemRDL command map (`address` = `cfg_wr_cmd`)
  - `include/vibe_ub_switch_regs.h` — bare-metal C header (cmd 0–5, field masks, identity constants, `irq_logic` pin)
  - `docs/Vibe-UB-Switch-register-map.md` — firmware register manual, gap table
  - `docs/Vibe-UB-Switch-reg-diffs.md` — standalone AS/FS vs `rtl/mgmt` difference list (facts only; firmware follows RTL `cfg_wr_cmd[3:0]` + RW1C Port Reset + `irq_logic`, no MMIO)

## 2026-09-03 (SPEC-0.1 freeze)

### Changed

- `docs/SPEC.md` promoted from freeze-candidate to **已冻结** (SPEC-0.1); human approved; aligned RTL `32a7f5e0`; §非目标 nine HOLEs retained; no functional change.

### Added

- Historical record (past tense): `docs/SPEC.md` was first published as freeze candidate SPEC-0.1-freeze-candidate (author Xia). Coverage holes (nine HOLEs) were moved from requirement text into §非目标. RTL SHA `32a7f5e0` is the matching RTL reference, not a functional rewrite of this SPEC.
