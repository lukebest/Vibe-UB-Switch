# Changelog

## Unreleased

### Changed

- Firmware register artifacts now follow the **architecture spec**, not a `rtl/mgmt` snapshot. `cfg_wr_cmd` is **4 bits**. Port Reset is **RW1C** (per-port bit, reset 0, write-1-clears). A 3-bit RTL cmd / WO-pulse snapshot is void for firmware. RTL is not modified here.
  - `include/vibe_ub_switch_regs.h` — 4-bit cmd macros; `PORT_RST` RW1C
  - `docs/rdl/vibe_ub_switch_mgmt.rdl` — `cfg_wr_cmd[3:0]`; `PORT_RST` `onwrite=woclr`
  - `docs/Vibe-UB-Switch-register-map.md` — AS contract manual
  - `docs/Vibe-UB-Switch-reg-diffs.md` — rewritten: header follows AS; do not claim current RTL matches

### Added

- Firmware-facing management register documentation for the AS static-write handshake (`cfg_wr_*`). This is not MMIO; no APB/AXI/I2C/JTAG.
  - `docs/rdl/vibe_ub_switch_mgmt.rdl`
  - `include/vibe_ub_switch_regs.h`
  - `docs/Vibe-UB-Switch-register-map.md`
  - `docs/Vibe-UB-Switch-reg-diffs.md`
