# Changelog

## Unreleased

### Added

- Firmware-facing management register documentation for the write-only static handshake (`cfg_wr_*`). This is not MMIO; there is no APB/AXI/I2C/JTAG decode in `rtl/mgmt`.
  - `docs/rdl/vibe_ub_switch_mgmt.rdl` — SystemRDL command map (`address` = `cfg_wr_cmd`)
  - `include/vibe_ub_switch_regs.h` — bare-metal C header (cmd 0–5, field masks, identity constants, `irq_logic` pin)
  - `docs/Vibe-UB-Switch-register-map.md` — firmware register manual, gap table, Port Reset as WO pulse (not RW1C)
