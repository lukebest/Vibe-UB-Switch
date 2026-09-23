# Changelog

## 2026-09-23 (Decision I stage-18 — vibe_pcs_rx_fec)

### Changed

- Next leaf `vibe_pcs_rx_fec` is described in `pycircuit/pcs/vibe_pcs_rx_fec.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_rx_fec.sv`. **Same ports /
  RX-FEC-wrap behavior** as tip `b7233f49` / freeze `302ac943`
  (`clk`, `rst_n`, `fec_mode[2:0]`, 512b `beat_data`,
  `beat_vld`, `beat_ready` / 960b `win_data`, `win_vld`,
  `win_ready`, `am_gap`, `fec_fail`; async-low `or negedge rst_n`;
  `include "vibe_ub_params.vh"` / `vibe_ub_fn.vh`; collect two
  512b beats; one-shot RS syndromes or bypass; emit 960b window
  or `fec_fail`; `am_gap` drops leftover `have_hi`;
  `beat_ready = !win_vld`). Self-contained (inline syndrome);
  does **not** instantiate `vibe_rs128_120_dec`. Pairs with
  stage-17 `vibe_pcs_tx_fec`. Ports / RX FEC wrap match
  stock (header-only vs stock; waived `am_gap` stays on
  line 14). Official `.vlt` not expanded. Not a chip rewrite.
  No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`,
  stage-2 `vibe_pma_bnd`, stage-3 `vibe_sync2`, stage-4
  `vibe_rst_sync`, stage-5 `vibe_gear_128_160`, stage-6
  `vibe_gear_160_128`, stage-7 `vibe_pcs_scramble`, stage-8
  `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`, stage-10
  `vibe_pcs_tx_amctl`, stage-11 `vibe_rs128_120_enc`,
  stage-12 `vibe_rs128_120_dec`, stage-13 `vibe_pcs_rx_deskew`,
  stage-14 `vibe_pcs_rx_amctl_lock`, stage-15
  `vibe_pcs_rx_unpack`, stage-16 `vibe_pcs_tx_pack`, and
  stage-17 `vibe_pcs_tx_fec` left intact. g1 / tx / rx tops
  not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_rx_fec`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-17 — vibe_pcs_tx_fec)

### Changed

- Next leaf `vibe_pcs_tx_fec` is described in `pycircuit/pcs/vibe_pcs_tx_fec.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_tx_fec.sv`. **Same ports /
  FEC-wrap behavior** as tip `ee5e8f4` / freeze `302ac943`
  (`clk`, `rst_n`, `fec_mode[2:0]`, 960b `win_data`,
  `win_vld`, `win_ready` / 1024b `cw_data`, `cw_vld`,
  `cw_ready`; async-low `or negedge rst_n`;
  `include "vibe_ub_params.vh"`; two `vibe_rs128_120_enc`
  instances `u_enc_a` / `u_enc_b`; collect two 960b windows;
  encode or bypass; emit two 1024b codewords;
  `win_ready = !have1`; T=4 / T=2 / bypass). Instantiates
  stage-11 `vibe_rs128_120_enc` ×2. Ports / FEC wrap match
  stock (header-only vs stock). Official `.vlt` not
  expanded. Not a chip rewrite. No SPEC CR. F1 `ovf_l` untouched.
  Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3
  `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5
  `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`, stage-7
  `vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
  `vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, stage-11
  `vibe_rs128_120_enc`, stage-12 `vibe_rs128_120_dec`, stage-13
  `vibe_pcs_rx_deskew`, stage-14 `vibe_pcs_rx_amctl_lock`,
  stage-15 `vibe_pcs_rx_unpack`, and stage-16 `vibe_pcs_tx_pack`
  left intact. RX FEC wrap / g1 / tx / rx tops not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_tx_fec`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-16 — vibe_pcs_tx_pack)

### Changed

- Next leaf `vibe_pcs_tx_pack` is described in `pycircuit/pcs/vibe_pcs_tx_pack.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_tx_pack.sv`. **Same ports /
  pack / AMCTL-insert behavior** as tip `ee5e8f4` / freeze `302ac943`
  (`clk`, `rst_n`, `sdf_period`, `afifo_afull`, 512b `beat_data`,
  `beat_vld`, `beat_ready` / 4×160b `lane0`..`lane3`, `lane_vld`,
  `lane_ready`, `am_word`; async-low `or negedge rst_n`;
  `include "vibe_ub_params.vh"`; four `vibe_pcs_tx_amctl` instances
  `u_am0`..`u_am3`; AMCTL on 640/512 symbol timer; `am_phase`
  0/1/2; pack 5×512 → emit 4×640; `afifo_afull` / `lane_ready`
  backpressure). Inverse of stage-15 `vibe_pcs_rx_unpack`.
  Instantiates stage-10 `vibe_pcs_tx_amctl`. Ports / pack / AMCTL
  insert match stock (header-only vs stock). Official `.vlt` not
  expanded. Not a chip rewrite. No SPEC CR. F1 `ovf_l` untouched.
  Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3
  `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5
  `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`, stage-7
  `vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
  `vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, stage-11
  `vibe_rs128_120_enc`, stage-12 `vibe_rs128_120_dec`, stage-13
  `vibe_pcs_rx_deskew`, stage-14 `vibe_pcs_rx_amctl_lock`, and
  stage-15 `vibe_pcs_rx_unpack` left intact. FEC wrap / g1 / tx /
  rx tops not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_tx_pack`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-15 — vibe_pcs_rx_unpack)

### Changed

- Next leaf `vibe_pcs_rx_unpack` is described in `pycircuit/pcs/vibe_pcs_rx_unpack.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_rx_unpack.sv`. **Same ports /
  unpack behavior** as tip `ebd1671` / freeze `302ac943`
  (`clk`, `rst_n`, 4×160b `lane0`..`lane3`, `lane_vld`,
  `am0`..`am3`, `am_gap` / 512b `beat_data`, `beat_vld`,
  `beat_ready`; async-low `or negedge rst_n`; stock
  `am_gap = 1'b0` default; combo `beat_vld = have`; combo
  `beat_data = acc[511:0]`; dual-buffer 4×640 → 5×512
  inverse G2; AMCTL skip; `am_gap` resets `n` only). Ports /
  unpack match stock (header-only vs stock; four-line banner
  so waived `am_gap` stays on line 17; official `.vlt` not
  expanded). Not a chip
  rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1
  `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3 `vibe_sync2`,
  stage-4 `vibe_rst_sync`, stage-5 `vibe_gear_128_160`,
  stage-6 `vibe_gear_160_128`, stage-7 `vibe_pcs_scramble`,
  stage-8 `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`,
  stage-10 `vibe_pcs_tx_amctl`, stage-11 `vibe_rs128_120_enc`,
  stage-12 `vibe_rs128_120_dec`, stage-13 `vibe_pcs_rx_deskew`,
  and stage-14 `vibe_pcs_rx_amctl_lock` left intact. FEC wrap /
  pack / g1 / tx / rx tops not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_rx_unpack`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-14 — vibe_pcs_rx_amctl_lock)

### Changed

- Next leaf `vibe_pcs_rx_amctl_lock` is described in `pycircuit/pcs/vibe_pcs_rx_amctl_lock.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_rx_amctl_lock.sv`. **Same ports /
  AMCTL lock behavior** as tip `263aec6` / freeze `302ac943`
  (`clk`, `rst_n`, `in_vld`, 160b `in_data` / `locked`, `lid`,
  `lid_bad`, combo `is_amctl`, `sdf`, `edf`; async-low
  `or negedge rst_n`; `include "vibe_ub_params.vh"`;
  `VIBE_AMCTL_CONFIRM_N` = `UNLOCK_N` = 3; seven `vibe_ebch16`
  instances; hunt with 1-beat slip; TX-layout lock sticky
  through data; LID not {0,1,2,3} → `lid_bad`, U24 no lane
  swap). Ports / hunt / lock match stock (header-only vs
  stock). Not a chip rewrite. No SPEC CR. F1 `ovf_l`
  untouched. Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`,
  stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5
  `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`, stage-7
  `vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
  `vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`,
  stage-11 `vibe_rs128_120_enc`, stage-12 `vibe_rs128_120_dec`,
  and stage-13 `vibe_pcs_rx_deskew` left intact. FEC wrap /
  pack / g1 / tx / rx tops / unpack not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_rx_amctl_lock`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-13 — vibe_pcs_rx_deskew)

### Changed

- Next leaf `vibe_pcs_rx_deskew` is described in `pycircuit/pcs/vibe_pcs_rx_deskew.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_rx_deskew.sv`. **Same ports /
  AMCTL deskew behavior** as tip `ebd1671` / freeze `302ac943`
  (`clk`, `rst_n`, 4×160b `in0`..`in3`, `in_vld`, `am0`..`am3` /
  4×160b `out0`..`out3`, `out_vld`, `aligned`; async-low
  `or negedge rst_n`; combo `aligned = saw0 & saw1 & saw2 & saw3`;
  combo `out_vld = in_vld && !(am0|am1|am2|am3)`; pass-through
  `out0`..`out3`; first-AMCTL lock pointers; hunt FIFOs not
  reset). Factory physical=logical (U24): no lane swap and no
  delay once aligned. Ports / hunt / pass-through match stock
  (header-only vs stock). Not a chip rewrite. No SPEC CR. F1
  `ovf_l` untouched. Stage-1 `vibe_afifo`, stage-2
  `vibe_pma_bnd`, stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`,
  stage-5 `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`,
  stage-7 `vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
  `vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, stage-11
  `vibe_rs128_120_enc`, and stage-12 `vibe_rs128_120_dec` left
  intact. FEC wrap / pack / g1 / tx / rx tops / amctl_lock /
  unpack not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_rx_deskew`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-12 — vibe_rs128_120_dec)

### Changed

- Next leaf `vibe_rs128_120_dec` is described in `pycircuit/pcs/vibe_rs128_120_dec.py`
  and landed hand-finished at `rtl/pcs/vibe_rs128_120_dec.sv`. **Same ports /
  syndrome-check RS(128,120) decode behavior** as tip `984e3b9` / freeze `302ac943`
  (`clk`, `rst_n`, `start`, `in_vld`, `in_sym` / `in_ready`, `done`,
  `fec_fail`, 960b `data_out`; async-low `or negedge rst_n`;
  `include "vibe_ub_fn.vh"`; combo next-syndromes; `msg[0:119]` pack;
  combo `in_ready = busy && (cnt < 128)`). Ports / syndrome path /
  `data_out` pack match stock. Reset of `msg[0:119]` is unrolled NBA
  `msg[i] <= 8'd0` (same zeros as the stock reset `for`; leaf lint
  Error=0 without `BLKLOOPINIT` / `BLKSEQ`; Icarus-legal). Not a
  chip rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`, stage-2
  `vibe_pma_bnd`, stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`,
  stage-5 `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`, stage-7
  `vibe_pcs_scramble`, stage-8 `vibe_ebch16`, stage-9
  `vibe_pcs_tx_cw2beat`, stage-10 `vibe_pcs_tx_amctl`, and stage-11
  `vibe_rs128_120_enc` left intact. FEC wrap / pack / g1 / tx / rx /
  amctl_lock / deskew / unpack not in this leaf.
- Regenerator: `make -C pycircuit vibe_rs128_120_dec`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-11 — vibe_rs128_120_enc)

### Changed

- Next leaf `vibe_rs128_120_enc` is described in `pycircuit/pcs/vibe_rs128_120_enc.py`
  and landed hand-finished at `rtl/pcs/vibe_rs128_120_enc.sv`. **Same ports /
  systematic RS(128,120) encode behavior** as tip `984e3b9` / freeze `302ac943`
  (`clk`, `rst_n`, `start`, `in_vld`, `in_sym` / `in_ready`, `done`,
  64b `parity`; async-low `or negedge rst_n`; `include "vibe_ub_fn.vh"`;
  `vibe_gf256_mul` LFSR; combo `in_ready = busy && (cnt < 120)`;
  Table 3-2 `G0..G7`). Not a chip rewrite. No SPEC CR. F1 `ovf_l`
  untouched. Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3
  `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5 `vibe_gear_128_160`,
  stage-6 `vibe_gear_160_128`, stage-7 `vibe_pcs_scramble`, stage-8
  `vibe_ebch16`, stage-9 `vibe_pcs_tx_cw2beat`, and stage-10
  `vibe_pcs_tx_amctl` left intact. `vibe_pcs_tx_fec` / pack / g1 /
  tx wrap / rx / decoder not in this leaf.
- Regenerator: `make -C pycircuit vibe_rs128_120_enc`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-10 — vibe_pcs_tx_amctl)

### Changed

- Next leaf `vibe_pcs_tx_amctl` is described in `pycircuit/pcs/vibe_pcs_tx_amctl.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_tx_amctl.sv`. **Same ports /
  combo AMCTL assemble** as tip `92adf9b` / freeze `302ac943`
  (`clk`, `rst_n`, `link_up`, `sdf_period`, `lane_id`, `req` / `ack`,
  320b `amctl_40B`; seven `vibe_ebch16` instances; combo LID
  `case (lane_id)`; BODY/END/LID/CTRL_TYPE/CTRL_DETAIL). Not a chip
  rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`,
  stage-2 `vibe_pma_bnd`, stage-3 `vibe_sync2`, stage-4
  `vibe_rst_sync`, stage-5 `vibe_gear_128_160`, stage-6
  `vibe_gear_160_128`, stage-7 `vibe_pcs_scramble`, stage-8
  `vibe_ebch16`, and stage-9 `vibe_pcs_tx_cw2beat` left intact.
  `vibe_pcs_tx` / pack / FEC / RS / rx not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_tx_amctl`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-9 — vibe_pcs_tx_cw2beat)

### Changed

- Next leaf `vibe_pcs_tx_cw2beat` is described in `pycircuit/pcs/vibe_pcs_tx_cw2beat.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_tx_cw2beat.sv`. **Same ports /
  ready/valid beat-split behavior** as tip `c8804c0` / freeze `302ac943`
  (`clk`, `rst_n`, 1024b `cw_*` / 512b `beat_*`; async-low
  `or negedge rst_n`; `cw_ready = !have_hi && !have_lo`; high beat
  first). Not a chip rewrite. No SPEC CR. F1 `ovf_l` untouched.
  Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3 `vibe_sync2`,
  stage-4 `vibe_rst_sync`, stage-5 `vibe_gear_128_160`, stage-6
  `vibe_gear_160_128`, stage-7 `vibe_pcs_scramble`, and stage-8
  `vibe_ebch16` left intact. `vibe_pcs_tx` / amctl / pack / FEC / RS /
  rx not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_tx_cw2beat`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-8 — vibe_ebch16)

### Changed

- Next leaf `vibe_ebch16` is described in `pycircuit/pcs/vibe_ebch16.py`
  and landed hand-finished at `rtl/pcs/vibe_ebch16.sv`. **Same ports /
  combo LUT behavior** as tip `9f86cba` / freeze `302ac943` (`cw_sel[4:0]`
  → `cw[15:0]`; `always @* case (cw_sel)`; Table 3-5 sel 0..30;
  default `16'hFFFF`). Not a chip rewrite. No SPEC CR. F1 `ovf_l`
  untouched. Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`,
  stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5
  `vibe_gear_128_160`, stage-6 `vibe_gear_160_128`, and stage-7
  `vibe_pcs_scramble` left intact. `vibe_pcs_tx` / rx / FEC / RS /
  amctl not in this leaf.
- Regenerator: `make -C pycircuit vibe_ebch16`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-7 — vibe_pcs_scramble)

### Changed

- Next leaf `vibe_pcs_scramble` is described in `pycircuit/pcs/vibe_pcs_scramble.py`
  and landed hand-finished at `rtl/pcs/vibe_pcs_scramble.sv`. **Same ports /
  scramble behavior** as tip `5087843` / freeze `302ac943` (`clk`,
  `rst_n`, `lane_id`, `seed_load`, `en`, `in_vld`, 160b in/out;
  async-low `or negedge rst_n`; `en=0` pass-through AMCTL/EEIB;
  seed `{19'd1, lane_id, 2'b01}`). Not a chip rewrite. No SPEC CR.
  F1 `ovf_l` untouched. Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`,
  stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`, stage-5
  `vibe_gear_128_160`, and stage-6 `vibe_gear_160_128` left intact.
  `vibe_pcs_tx` / rx / FEC / RS not in this leaf.
- Regenerator: `make -C pycircuit vibe_pcs_scramble`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-6 — vibe_gear_160_128)

### Changed

- Next leaf `vibe_gear_160_128` is described in `pycircuit/cdc/vibe_gear_160_128.py`
  and landed hand-finished at `rtl/cdc/vibe_gear_160_128.sv`. **Same ports /
  residue behavior** as tip `cb4549f` / freeze `302ac943` (`clk`,
  `rst_n`, ready/valid 160 in / 128 out; 4×160 = 5×128; async-low
  `or negedge rst_n`; `in_ready = can_load && (rbits != 4)`). Not a
  chip rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`,
  stage-2 `vibe_pma_bnd`, stage-3 `vibe_sync2`, stage-4 `vibe_rst_sync`,
  and stage-5 `vibe_gear_128_160` left intact.
- Regenerator: `make -C pycircuit vibe_gear_160_128`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-5 — vibe_gear_128_160)

### Changed

- Next leaf `vibe_gear_128_160` is described in `pycircuit/cdc/vibe_gear_128_160.py`
  and landed hand-finished at `rtl/cdc/vibe_gear_128_160.sv`. **Same ports /
  dual-residue behavior** as tip `195d380` / freeze `302ac943` (`clk`,
  `rst_n`, ready/valid 128 in / 160 out; 5×128 = 4×160; async-low
  `or negedge rst_n`). Not a chip rewrite. No SPEC CR. F1 `ovf_l`
  untouched. Stage-1 `vibe_afifo`, stage-2 `vibe_pma_bnd`, stage-3
  `vibe_sync2`, and stage-4 `vibe_rst_sync` left intact.
  `vibe_gear_160_128` not in this leaf.
- Regenerator: `make -C pycircuit vibe_gear_128_160`. Regime remains
  **UNFROZEN** (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-4 — vibe_rst_sync)

### Changed

- Next leaf `vibe_rst_sync` is described in `pycircuit/cdc/vibe_rst_sync.py`
  and landed hand-finished at `rtl/cdc/vibe_rst_sync.sv`. **Same ports /
  2-FF behavior** as tip `49421f9` / freeze `302ac943` (`clk`, `rst_n_in`,
  `rst_n_out`; async assert on `rst_n_in`, sync release into `clk`). Not a
  chip rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`,
  stage-2 `vibe_pma_bnd`, and stage-3 `vibe_sync2` left intact. Gear not
  in this leaf.
- Regenerator: `make -C pycircuit vibe_rst_sync`. Regime remains **UNFROZEN**
  (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-23 (Decision I stage-3 — vibe_sync2)

### Changed

- Next leaf `vibe_sync2` is described in `pycircuit/cdc/vibe_sync2.py`
  and landed hand-finished at `rtl/cdc/vibe_sync2.sv`. **Same ports /
  2-FF behavior** as tip `7cf680f` / freeze `302ac943` (`clk`, `rst_n`,
  `d`, `q`; `parameter int W`; async-low `or negedge rst_n`). Not a
  chip rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`
  and stage-2 `vibe_pma_bnd` left intact. `vibe_rst_sync` / gear not
  in this leaf.
- Regenerator: `make -C pycircuit vibe_sync2`. Regime remains **UNFROZEN**
  (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-22 (Decision I stage-2 — vibe_pma_bnd)

### Changed

- Next leaf `vibe_pma_bnd` is described in `pycircuit/pma/vibe_pma_bnd.py`
  (PRBS helpers in `pycircuit/pma/prbs23.py`) and landed hand-finished at
  `rtl/pma/vibe_pma_bnd.sv`. **Same CR-B ports and idle-PRBS behavior** as
  tip `ef3f121` / freeze `302ac943` (issue #115 / PR116 `PMA_IDLE_MARK`).
  Not a chip rewrite. No SPEC CR. F1 `ovf_l` untouched. Stage-1 `vibe_afifo`
  left intact.
- Regenerator: `make -C pycircuit vibe_pma_bnd`. Regime remains **UNFROZEN**
  (Path B hold). Do not treat this leaf as a new freeze pin.

## 2026-09-22 (Decision I stage-1 — pyCircuit scaffold + vibe_afifo)

### Changed

- RTL freeze `302ac943` is **unfrozen** for a lukebest/pyCircuit (pyc4.0 /
  pycircuit-hisi / pycc) redesign. **SPEC functional semantics and CR-B
  interface names are unchanged** (`{src}_{dst}_{meaning}`, `dll` not `dl`).
- First leaf `vibe_afifo` is described in `pycircuit/cdc/vibe_afifo.py` and
  landed hand-finished at `rtl/cdc/vibe_afifo.sv` (same ports / gray-pointer
  behavior as freeze). Not a chip rewrite. F1 `ovf_l` untouched.
- Toolchain pin: lukebest/pyCircuit `43cc5918e3d09ecc0c814cabef6c1384cb9980ae`
  (pycircuit-hisi 0.1.0). Regenerator: `make -C pycircuit vibe_afifo`.

## 2026-09-22 (Decision I UNFROZEN / redesign, Asia/Shanghai)

### Changed

- **Breaks** / voids the written idle-mark port freeze aligned to RTL `302ac943` (`302ac943c3737c288f3af6c4857bb3a9b1683a26`) as the **current** pin. Historical lineage stays (merge-trace `df7c286e` / earlier pins remain history).
- Decision **I** (Luke, 2026-09-22 Asia/Shanghai): UNFROZEN for `lukebest/pyCircuit` redesign. No interface semantic CR in this step.
- Old new-series 1/3 (PR122) vs DUT `302ac943` (stock Icarus) **does not continue**. 2/3 **does not start**.
- Design will redesign with `lukebest/pyCircuit` (pyc4.0: Python DSL → MLIR → Verilog) against SPEC-0.2 / FS-0.2.7 locked facts, emit into `rtl/`.
- After rewrite lands, verification primary gate is `tb/vibe` uvm-python (`make -C tb/vibe sim`, PR119). Stock Icarus becomes secondary/compare — **not** the consecutive-green primary gate unless Luke decides otherwise.
- Naming / functional widths / protocol / handshake in SPEC body are **unchanged** unless a later CR. F1 `ovf_l` unchanged. Path B / FPGA deferred unchanged.
- No new freeze SHA yet — pin is **blank / UNFROZEN** until redesign RTL is accepted and re-pinned later.

## 2026-09-21 (#115 idle-mark freeze, Asia/Shanghai)

### Changed

- **Breaks** the PMA ECO port freeze aligned to RTL `a658d141` (`a658d14163b0e66b3875ee42a7dcc8a10024ba51`). That pin's new-series 1/3 (PR114) **FAILED** 121/124 — issue #115: `vibe_pma_bnd` idle-PRBS drop ≠ packed-beat valid on Icarus loopback.
- Design RTL ECO (PR116 tip) distinguishes PMA pin-idle from PCS scramble(0) so packed RX valid recovers. No TB change for this ECO. No reopen of txclk→rxclk CDC.
- Naming and functional interfaces are **unchanged**. Ports remain CR-B `{src}_{dst}_{meaning}` (`dll` not `dl`). Widths, fire rules, handshake semantics, and protocol remain SPEC-0.2 **CR-applied（命名）** / `32a7f5e0`.
- New RTL freeze SHA: `302ac943` (`302ac943c3737c288f3af6c4857bb3a9b1683a26`). Merge: `df7c286e` (`df7c286e184b4a48fedc5d5ae7eff06cee193c5c`, PR116) — **merge-trace only**, not the freeze pin. Same role as old `a658d141` / earlier `982ddd0a` / `1ed4d350` / `32a7f5e0`.
- Old `a658d141` consecutive greens attempt (PR114 FAIL, not green) does **not** count (do not restart from it).
- Verification must restart new consecutive greens 1/3 against DUT=`302ac943` using **stock Icarus** (same gate as PR114), after this pin. pyuvm/PR119 is a separate acceptance gate, not this 1/3.
- Decision **F1** (`ovf_l` permanent frozen WARN/waiver) is **unchanged**.
- PR118 lint+CDC clean (main `932037f9`) is **evidence only**, not a freeze pin change by itself. Lint Error=0 NEW=0; CDC NEW=0; F1 `ovf_l` still frozen WARN. PR119 TB rewrite is TB-only, not a freeze pin.

## 2026-09-21 (PMA ECO freeze, Asia/Shanghai)

### Changed

- **Breaks** the Lint ECO port freeze aligned to RTL `982ddd0a` (`982ddd0a54cf19dbeb39cf8f8f523c4e26e593f6`). That pin was **BROKEN** after Luke pushed PRBS23 + `txrst_n`/`rxrst_n`. Decision **H** was hold-pin until ECO clean.
- Since `982ddd0a`: PRBS23 in PMA; `txrst_n`/`rxrst_n` added then ECO removed input defaults (`= 1'b1`); PMA loopback CDC ECO closed (rxclk idle-poly no longer samples txclk data).
- Naming and functional interfaces are **unchanged**. Ports remain CR-B `{src}_{dst}_{meaning}` (`dll` not `dl`). Widths, fire rules, handshake semantics, and protocol remain SPEC-0.2 **CR-applied（命名）** / `32a7f5e0`.
- New RTL freeze SHA: `a658d141` (`a658d14163b0e66b3875ee42a7dcc8a10024ba51`). Merge: `f234d4b0` (`f234d4b036a1639fa9855de01743d04696bf5cb7`, PR109) — **merge-trace only**, not the freeze pin. Same role as old `982ddd0a` / earlier `1ed4d350` / `32a7f5e0`.
- Old `982ddd0a` consecutive greens 3/3 are **CLOSED 历史保留** (historically closed / voided for counting; do not restart from them).
- Verification must restart new consecutive greens 1/3 against DUT=`a658d141` (not yet started; Xia pin is the gate).
- Decision **F1** (`ovf_l` permanent frozen WARN/waiver) is **unchanged**.
- PR111 lint+CDC clean (main `014939c7`) is **evidence only**, not a freeze pin change by itself. Lint Error=0 NEW=0 (GONE `txrst_n`/`rxrst_n` UNSUPPORTED); CDC NEW=0 (GONE PMA loopback); F1 `ovf_l` still frozen WARN.

## 2026-09-08 (Lint ECO freeze)

### Changed

- **Breaks** the CR-B port freeze aligned to RTL `1ed4d350`. Luke-approved Lint ECO (PR62): structural clear of LATCH / UNOPTFLAT / BLKSEQ. UNUSEDPARAM stays waiver. Decision **F1** (`ovf_l` permanent frozen WARN/waiver) is **unchanged** (`rtl/port/vibe_port.sv` untouched).
- Naming and functional interfaces are **unchanged**. Ports remain CR-B `{src}_{dst}_{meaning}` (`dll` not `dl`). Widths, fire rules, handshake semantics, and protocol remain SPEC-0.1 / `32a7f5e0`.
- New RTL freeze SHA: `982ddd0a` (`982ddd0a54cf19dbeb39cf8f8f523c4e26e593f6`). Merge: `581d9d34` (`581d9d34c6f7e27f80bdbd46e648343af5e40780`) — **merge-trace only**, not the freeze pin. Same role as old `1ed4d350` / earlier `32a7f5e0`.
- CR-B consecutive greens 3/3 **voided**. Verification restarts 1/3 against `982ddd0a`.

## 2026-09-08 (CR-B interface naming)

### Changed

- **Breaks** the SPEC-0.1 freeze aligned to RTL `32a7f5e0`, **naming only**. Record: [`docs/cr/CR-IFACE-RENAME-B-2026-09-08.md`](cr/CR-IFACE-RENAME-B-2026-09-08.md) (Luke Option B, 2026-09-08). Inventory: [`docs/cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md`](cr/CR-IFACE-NAMING-DRAFT-2026-09-08.md).
- `docs/SPEC.md` → SPEC-0.2 **CR-applied（命名）**; `docs/Vibe-UB-Switch-architecture-spec.md` product / datapath tables use `{src}_{dst}_{meaning}` (`dll` not `dl`). RTL ports landed at freeze SHA `1ed4d350` (PR51 merge `777865f0` / `777865f073faba87a564f876636db1ebe0e19790`). Old freeze `32a7f5e0` is **superseded for ports**.
- Functional widths, fire rules, handshake semantics, and protocol are **unchanged**. Decision **F1** (`ovf_l` permanent frozen WARN/waiver) is unchanged. Consecutive greens 3/3 **voided** (renamed DUT landed); new series only after reports against `1ed4d350`.
- New RTL freeze SHA: `1ed4d350` (`1ed4d35006848e6275e93d9bd2fc4e7f7af348f1`). Merge: `777865f0` (`777865f073faba87a564f876636db1ebe0e19790`). Same role as old `32a7f5e0`, now superseded for ports. 

### Added

- SPEC §1.1 naming convention (tokens, `_vld`/`_ready`, clocks/resets exempt, approved interface table).

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
