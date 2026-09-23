# Vibe-UB-Switch Python UVM 1.2 (uvm-python)

Primary verification gate. Accellera UVM 1.2 **Python functional equivalence**
via [lukebest/uvm-python](https://github.com/lukebest/uvm-python) + cocotb 1.9.x.

Does **not** modify `rtl/` or `include/`. Does not require Vivado xsim.

## Install pins

```
cocotb>=1.9.2,<2          # 2.x cannot import this library
cocotb-bus
cocotb-coverage
regex
uvm-python @ git+https://github.com/lukebest/uvm-python.git
```

```bash
make -C tb/vibe/pyuvm venv
# or: python3 -m venv tb/vibe/pyuvm/.venv && \
#      tb/vibe/pyuvm/.venv/bin/pip install -r tb/vibe/pyuvm/requirements.txt
```

## Run (no xvlog)

```bash
make -C tb/vibe sim              # default: this tree
make -C tb/vibe suite            # fabric+mgmt G1/CFG/SAF/length
make -C tb/vibe suite TC=tc_rt10_must_drop
make -C tb/vibe units            # leaf units + static/neg + port
make -C tb/vibe units TC=tc_vl_rr
make -C tb/vibe/pyuvm units TC=tc_vibe_afifo   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm afifo                    # same as units TC=tc_vibe_afifo
make -C tb/vibe/pyuvm units TC=tc_vibe_sync2   # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm sync2                    # same as units TC=tc_vibe_sync2
make -C tb/vibe/pyuvm units TC=tc_vibe_rst_sync  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rst_sync                 # same as units TC=tc_vibe_rst_sync
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_128_160  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_128_160             # same as units TC=tc_vibe_gear_128_160
make -C tb/vibe/pyuvm units TC=tc_vibe_gear_160_128  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm gear_160_128             # same as units TC=tc_vibe_gear_160_128
make -C tb/vibe/pyuvm units TC=tc_dll          # TP-DLL-004 full vibe_dll split
make -C tb/vibe/pyuvm dll                      # same as units TC=tc_dll (≠1/3 ≠4/3)
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_scramble  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm pcs_scramble             # same as units TC=tc_vibe_pcs_scramble
make -C tb/vibe/pyuvm units TC=tc_vibe_ebch16  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm ebch16                   # same as units TC=tc_vibe_ebch16
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_cw2beat  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm cw2beat                  # same as units TC=tc_vibe_pcs_tx_cw2beat
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_amctl  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm amctl                    # same as units TC=tc_vibe_pcs_tx_amctl
make -C tb/vibe/pyuvm units TC=tc_vibe_rs128_120_enc  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rs128_120_enc             # same as units TC=tc_vibe_rs128_120_enc
make -C tb/vibe/pyuvm units TC=tc_vibe_rs128_120_dec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rs128_120_dec             # same as units TC=tc_vibe_rs128_120_dec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_deskew  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm deskew                   # same as units TC=tc_vibe_pcs_rx_deskew
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_amctl_lock  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm amctl_lock               # same as units TC=tc_vibe_pcs_rx_amctl_lock
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_unpack  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm unpack                   # same as units TC=tc_vibe_pcs_rx_unpack
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_pack  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm pack                     # same as units TC=tc_vibe_pcs_tx_pack
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_fec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm tx_fec                   # same as units TC=tc_vibe_pcs_tx_fec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_rx_fec  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm rx_fec                   # same as units TC=tc_vibe_pcs_rx_fec
make -C tb/vibe/pyuvm units TC=tc_vibe_pcs_tx_g1  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm g1                       # same as units TC=tc_vibe_pcs_tx_g1
make -C tb/vibe/pyuvm tx_g1                    # same as g1 / tc_vibe_pcs_tx_g1
make -C tb/vibe/pyuvm units TC=tc_vibe_bcrc    # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm bcrc                     # same as units TC=tc_vibe_bcrc
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_credit  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm credit                   # same as units TC=tc_vibe_dll_credit
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm dll_sm                   # same as units TC=tc_vibe_dll_sm
make -C tb/vibe/pyuvm sm                       # same as dll_sm / tc_vibe_dll_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_rx  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm dll_rx                   # same as units TC=tc_vibe_dll_rx
make -C tb/vibe/pyuvm rx                       # same as dll_rx / tc_vibe_dll_rx
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_ack_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_ack_sm             # same as units TC=tc_vibe_dll_retry_ack_sm
make -C tb/vibe/pyuvm ack_sm                   # same as retry_ack_sm / tc_vibe_dll_retry_ack_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_buf  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_buf                # same as units TC=tc_vibe_dll_retry_buf
make -C tb/vibe/pyuvm buf                      # same as retry_buf / tc_vibe_dll_retry_buf
make -C tb/vibe/pyuvm units TC=tc_vibe_dll_retry_req_sm  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm retry_req_sm             # same as units TC=tc_vibe_dll_retry_req_sm
make -C tb/vibe/pyuvm req_sm                   # same as retry_req_sm / tc_vibe_dll_retry_req_sm
make -C tb/vibe/pyuvm units TC=tc_vibe_fecn_mark  # Decision-I leaf (module-level)
make -C tb/vibe/pyuvm fecn_mark                # same as units TC=tc_vibe_fecn_mark
make -C tb/vibe/pyuvm fecn                     # same as fecn_mark / tc_vibe_fecn_mark
make -C tb/vibe port TC=tc_port_smoke
make -C tb/vibe top              # vibe_ub_switch + peer PMA
make -C tb/vibe neg              # absent-feature scan
```

Simulator: `SIM=verilator` (baseline) or `SIM=icarus`.

```bash
make -C tb/vibe/pyuvm sim SIM=icarus
make -C tb/vibe/pyuvm units TC=tc_vl_rr SIM=icarus
make -C tb/vibe/pyuvm afifo SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm sync2 SIM=verilator   # or SIM=icarus
make -C tb/vibe/pyuvm rst_sync SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm gear_128_160 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm gear_160_128 SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm pcs_scramble SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm ebch16 SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm cw2beat SIM=verilator       # or SIM=icarus
make -C tb/vibe/pyuvm amctl SIM=verilator         # or SIM=icarus
make -C tb/vibe/pyuvm rs128_120_enc SIM=verilator # or SIM=icarus
make -C tb/vibe/pyuvm rs128_120_dec SIM=verilator # or SIM=icarus
make -C tb/vibe/pyuvm deskew SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm amctl_lock SIM=verilator    # or SIM=icarus
make -C tb/vibe/pyuvm unpack SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm pack SIM=verilator          # or SIM=icarus
make -C tb/vibe/pyuvm tx_fec SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm rx_fec SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm g1 SIM=verilator            # or SIM=icarus
make -C tb/vibe/pyuvm tx_g1 SIM=verilator         # same as g1
make -C tb/vibe/pyuvm bcrc SIM=verilator          # or SIM=icarus
make -C tb/vibe/pyuvm credit SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm dll_sm SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm sm SIM=verilator            # same as dll_sm
make -C tb/vibe/pyuvm dll_rx SIM=verilator        # or SIM=icarus
make -C tb/vibe/pyuvm rx SIM=verilator            # same as dll_rx
make -C tb/vibe/pyuvm retry_ack_sm SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm ack_sm SIM=verilator        # same as retry_ack_sm
make -C tb/vibe/pyuvm retry_buf SIM=verilator     # or SIM=icarus
make -C tb/vibe/pyuvm buf SIM=verilator           # same as retry_buf
make -C tb/vibe/pyuvm retry_req_sm SIM=verilator  # or SIM=icarus
make -C tb/vibe/pyuvm req_sm SIM=verilator        # same as retry_req_sm
make -C tb/vibe/pyuvm fecn_mark SIM=verilator     # or SIM=icarus
make -C tb/vibe/pyuvm fecn SIM=verilator          # same as fecn_mark
```

`tc_vibe_afifo` / `make afifo` is **module-level only** (reset, CDC integrity,
fill/`almost_full` at occ≥10, drain). It is **not** the full-chip consecutive-green
gate. Stock Icarus `tb/vibe/tests/tc_afifo_afull10.sv` remains optional control.

`tc_vibe_sync2` / `make sync2` is **module-level only** (reset `q==0`, stable `d`
reaches `q` after 2 posedges not 1, streaming 2-cycle delay, async `rst_n`
clears the pipe). It is **not** 1/3, 4/3, freeze, or signoff.

`tc_vibe_rst_sync` / `make rst_sync` is **module-level only** (async `rst_n_in`
asserts `rst_n_out` without a dest posedge, sync deassert after 2 dest clocks
not 1, mid-run re-assert clears both flops). It is **not** 1/3, 4/3, freeze,
or signoff. Stock Icarus `tb/vibe/tests/tc_rst_sync.sv` / `tc_rst_sync` remains
optional control.

`tc_vibe_gear_128_160` / `make gear_128_160` is **module-level only** (reset
idle / no spurious `out_vld`, 5×128 → exactly 4×160 with residue packing,
hold-full backpressure without drop/dup, phase wrap on a second group).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_gear_128_160.sv` / `tc_gear_128_160` remains optional
count-only control. This is **not** TP-DLL-004 / full-chip `tc_dll`
(`make -C tb/vibe/pyuvm dll` / `units TC=tc_dll` scores that ID).

`tc_vibe_gear_160_128` / `make gear_160_128` is **module-level only** (reset
idle / no spurious `out_vld`, 4×160 → exactly 5×128 with residue packing,
hold-full / `rbits==4` backpressure without drop/dup, phase wrap on a
second group). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_gear_160_128.sv` / `tc_gear_160_128` remains optional
count-only control. This is **not** TP-DLL-004 / full-chip `tc_dll`.

`tc_vibe_pcs_scramble` / `make pcs_scramble` is **module-level only** (reset
idle / async clear, known LID seed vs golden xmask, AMCTL/EEIB `en=0`
pass-through without LFSR advance, XOR round-trip). It is **not** 1/3,
4/3, freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_pcs_scramble.sv` /
`tc_pcs_scramble` remains optional control. Official TP-PHY-017 stays
scored by `tc_pcs_scramble`. This is **not** TP-DLL-004 / `gear_160_128`.

`tc_vibe_ebch16` / `make ebch16` is **module-level only** (combo idle /
no sequential hold, Table 3-5 encode LUT + default sel 31, unique invert
decode, min Hamming distance 8). The DUT has no `rst_n`. It is **not**
1/3, 4/3, freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_ebch16_lut.sv`
/ `tc_ebch16_lut` remains optional control. This is **not** TP-PHY-017 /
`pcs_scramble`.

`tc_vibe_pcs_tx_cw2beat` / `make cw2beat` is **module-level only**
(reset idle / no spurious `beat_vld`, 1024→exactly 2×512 high-then-low,
hold-full backpressure without drop/dup, second codeword after drain).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_pcs_cw2beat.sv` / `tc_pcs_cw2beat` remains optional
count-only control. Official TP-PHY-009 stays scored by `tc_pcs_cw2beat`.
This is **not** TP-PHY-017 / `pcs_scramble` / `ebch16`.

`tc_vibe_pcs_tx_amctl` / `make amctl` is **module-level only**
(reset / idle `ack=0`, 40-symbol eBCH-16 insert/align vs Table 3-5
BODY/END/LID/CTRL_TYPE/CTRL_DETAIL, all four `lane_id` LID mux arms,
`ack=req&&link_up`, combo hold). `clk` / `rst_n` / `sdf_period` are
unused in the assemble body. It is **not** 1/3, 4/3, freeze, or
signoff. Stock Icarus `tb/vibe/tests/tc_pcs_amctl.sv` / `tc_pcs_amctl`
remains optional control. Official TP-PHY-016 stays scored by
`tc_pcs_amctl`. This is **not** TP-PHY-009 / `cw2beat` / `ebch16`.

`tc_vibe_rs128_120_enc` / `make rs128_120_enc` is **module-level only**
(reset / idle `in_ready=0` `done=0` `parity=0`, systematic RS(128,120)
encode / 8-symbol parity vs golden GF(256) LFSR, `start` restart,
`in_vld` stall without a step, second message after `done`). It is
**not** 1/3, 4/3, freeze, or signoff. There is no stock Icarus leaf
`tc_rs128_120_enc`; FEC wrap TCs (`tc_pcs_fec_*`) remain the official
scorers for the instantiator. The Decision-I wrap leaf is
`tc_vibe_pcs_tx_fec` / `make tx_fec`. This is **not** TP-PHY-016 /
`amctl`.

`tc_vibe_rs128_120_dec` / `make rs128_120_dec` is **module-level only**
(reset / idle `in_ready=0` `done=0` `fec_fail=0` `data_out=0`,
RS(128,120) syndrome-check decode / `data_out` pack vs golden Horner,
valid CW `fec_fail=0` vs corrupted CW `fec_fail=1` (no correction),
`start` restart, `in_vld` stall without a step, second CW after
`done`). It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_rs_dec_syndrome.sv` / `tc_rs_dec_syndrome` remains
the official done-pulse scorer. The Decision-I wrap leaf is
`tc_vibe_pcs_rx_fec` / `make rx_fec`. This is **not** the encoder leaf /
`rs128_120_enc`.

`tc_vibe_pcs_rx_deskew` / `make deskew` is **module-level only**
(reset / idle `aligned=0` no spurious `out_vld`, staggered AMCTL
lane-skew absorb / first-AMCTL lock / `aligned`, factory
physical=logical pass-through with no lane swap, AM drop
`out_vld=0`, `in_vld` stall without a saw step, second data group
after lock). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_pcs_rx_deskew.sv` / `tc_pcs_rx_deskew`
remains the official staggered-AM / `out_vld` scorer. This is
**not** the decoder leaf / `rs128_120_dec`.

`tc_vibe_pcs_rx_amctl_lock` / `make amctl_lock` is **module-level
only** (reset / idle `locked=0` no spurious `is_amctl`/`sdf`/`edf`,
AMCTL detect on `match_w0`/`match_w1`/`match_pair`, `CONFIRM_N=3`
lock, `UNLOCK_N=3` legacy unlock, TX-layout sticky lock, all four
LID mux arms, `lid_bad` (U24, no swap), `in_vld` stall without a
confirm/unlock step). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_pcs_rx_amctl.sv` / `tc_pcs_rx_amctl`
remains the official 4-pair / LID / unlock / `lid_bad` scorer.
This is **not** the deskew leaf / `deskew`.

`tc_vibe_pcs_rx_unpack` / `make unpack` is **module-level
only** (reset / idle `beat_vld=0` no spurious beat, AMCTL
`am0..am3` skip, 4×640 → exactly 5×512 unpack vs golden
LSB-first pack, `beat_ready` hold without drop/dup, `am_gap`
n-reset that keeps an in-flight emit, dual-buffer `nxt_full`
/ acc swap, `lane_vld` stall without a take, second group
after drain). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_pcs_rx_unpack.sv` /
`tc_pcs_rx_unpack` remains the official `beat_vld` / `am_gap`
/ `nxt_full` scorer. This is **not** the AMCTL-lock leaf /
`amctl_lock`. Pairs with TX pack (`make pack` /
`tc_vibe_pcs_tx_pack`).

`tc_vibe_pcs_tx_pack` / `make pack` is **module-level
only** (reset / idle `lane_vld=0` `beat_ready` no spurious
emit, 5×512 → exactly 4×640 pack vs golden LSB-first inverse
of unpack, `lane_ready` / `afifo_afull` hold without
drop/dup, `beat_vld` stall without a take, AMCTL insert on
the 512 / 640-symbol timer with per-lane 40B halves, AM wait
until a finishing 4×640 emits, second group after drain).
It is **not** 1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_pcs_tx_pack.sv` / `tc_pcs_tx_pack`
remains the official `lane_vld` scorer. This is **not** the
RX unpack leaf / `unpack`.

`tc_vibe_pcs_tx_fec` / `make tx_fec` is **module-level
only** (reset / idle `win_ready=1` `cw_vld=0` no spurious CW,
two-window bypass `{w0,64'd0}` then `{w1,64'd0}`, T=4 / T=2
encode wrap vs golden RS(128,120) parity, `cw_ready` hold
without drop/dup, `win_vld` stall after the first window,
`win_ready=!have1` until both CWs drain, second pair after
drain). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_pcs_fec_*.sv` / `tc_pcs_fec_*`
remain the official wrap scorers. This is **not** the
encoder leaf / `rs128_120_enc`. Sits on stage-11 enc +
stage-16 pack.

`tc_vibe_pcs_rx_fec` / `make rx_fec` is **module-level
only** (reset / idle `beat_ready=1` `win_vld=0` no spurious
window, two-beat bypass `{hi, lo[511:64]}`, T=4 / T=2
syndrome-check unwrap vs golden RS(128,120) Horner, garbage
CW `fec_fail=1` without forwarding a 960, `win_ready` hold
(`beat_ready=!win_vld`), `beat_vld` stall after the first
half-CW, `am_gap` drop of leftover `have_hi`, second CW
after drain). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_pcs_rx_fec.sv` /
`tc_pcs_rx_fec` remains the official `win_vld` scorer.
This is **not** the decoder leaf / `rs128_120_dec`. Pairs
with TX FEC (`make tx_fec` / `tc_vibe_pcs_tx_fec`).

`tc_vibe_pcs_tx_g1` / `make g1` / `make tx_g1` is **module-level
only** (reset / idle `win_vld=0` no spurious 960, 6-Null idle fill,
isolated 4-flit + 2-Null complete, 1.5-beat rem-complete plus rem
leftover + 4-Null fill, `win_ready` hold without drop/dup, `in_vld`
stall at `nflit==4`, `link_up=0` no take / no idle fill, same-cycle
ack+take, second window after drain). It is **not** 1/3, 4/3, freeze,
or signoff. Stock Icarus `tb/vibe/tests/tc_pcs_tx_g1_window.sv` /
`tc_pcs_tx_g1_window` remains the official `win_vld` scorer. This is
**not** the TX FEC wrap / `tx_fec`. Feeds stage-17 `vibe_pcs_tx_fec`.

`tc_vibe_bcrc` / `make bcrc` is **module-level only** (reset / idle
`crc_word=0` `done=0` no spurious pulse, AS §12 CRC30 encode vs
golden init-all-1 / no invert / LSB-first 160b eat, `ERROR_FLAG` /
reserved packing, check DUT word vs golden residue, `start` restart
that wins over `in_vld`, `in_vld` stall without a step, `last`
without `in_vld`, second block after `done`). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_bcrc_crc30.sv` /
`tc_bcrc_crc30` remains the official bit31 / bit30 scorer. This is
**not** TP-DLL-004 / `dll`. First DLL leaf after PCS stage-1..19.

`tc_vibe_dll_credit` / `make credit` is **module-level only** (reset /
idle `pending=0` `credit_low=1` no `bp_nw` / `proto_err` / `fc_ovf`,
`credit_ret` grant already cells, consume `ceil(flits/n)` vs golden,
CFG0 skip, `grain_n=0` → 0, `consume_vld` stall without a step,
same-cycle `credit_ret` && `consume_vld`, 1023 vs 1024 cell thresh,
second consume after the first, `port_rst` / `!link_up` clear, 1µs
timeout → `proto_err`). It is **not** 1/3, 4/3, freeze, or signoff.
Stock Icarus `tb/vibe/tests/tc_credit_*.sv` / `tc_cfg0_no_credit`
remain the official cell-thresh / grain / CFG0 / timeout scorers.
This is **not** TP-DLL-004 / `dll`. Second DLL leaf after
`vibe_bcrc`.

`tc_vibe_dll_sm` / `make dll_sm` / `make sm` is **module-level
only** (reset → Disabled, `!link_up` / `port_rst` / `dll_error`
→ Disabled, walk Disabled → Param → Credit → Normal on
`param_ok` / `credit_ok`, `status_up` only in Normal, `disabled`
only in Disabled, hold in Normal). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus `tb/vibe/tests/tc_dll_sm_states.sv`
/ `tc_dll_sm_states` remains the official TP-DLL-001 / 002 / 003
scorer. This is **not** TP-DLL-004 / `dll`. Third DLL leaf after
`vibe_bcrc` / `vibe_dll_credit`.

`tc_vibe_dll_rx` / `make dll_rx` / `make rx` is **module-level
only** (reset / `port_rst` / `!link_up` clears, CFG0 terminate
does not enter fabric, PCS→NW packing / LPH / EOP leftover drop,
FEC fail → `start_retry`, `rx_ovf` on buffer full, ready/valid
handshake). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_cfg0_term_not_fabric.sv` /
`tc_dll_rx_errflag.sv` / `tc_fec_fail_gbn.sv` remain the official
TP scorers. This is **not** TP-DLL-004 / `dll`. Fourth DLL leaf
after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm`.

`tc_vibe_dll_retry_ack_sm` / `make retry_ack_sm` / `make ack_sm`
is **module-level only** (reset / `port_rst` clears to NORMAL,
`start_ack` → 1 Idle then 32 Ack, replay `RdPtr` from `RcvPtr`
until `WrPtr`, return to NORMAL). It is **not** 1/3, 4/3,
freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_retry_ack_replay.sv` / `tc_retry_ack_replay`
remains the official TP scorer. This is **not** TP-DLL-004 /
`dll`. Fifth DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx`.

`tc_vibe_dll_retry_buf` / `make retry_buf` / `make buf`
is **module-level only** (reset / `port_rst` / `!link_up` pointers
and free to reset values, `proto_err` cleared on hard `rst_n` only,
normal write advances `wr_ptr` and decrements free, `can_send`
tracks free vs `send_size`, Null and Retry writes do not enter,
ack release advances `tail`/`rcv` and restores free, overflow
`free+rel_size>256` asserts `proto_err`, `rd_ptr_i` returns the
stored flit). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_retry_buf_256.sv` / `tc_retry_buf_256`
remains the official TP scorer. This is **not** TP-DLL-004 /
`dll`. Sixth DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx` / `vibe_dll_retry_ack_sm`.

`tc_vibe_dll_retry_req_sm` / `make retry_req_sm` / `make req_sm`
is **module-level only** (reset / `port_rst` / `device_rst` clears
to NORMAL, `start_retry` → 1 Idle then 32 Req, REQ → WAIT or
RETRAIN at `NUM_RETRY` / `phy_retrain`, `wait_done_ack` → NORMAL,
WAIT timeout → REQ, RETRAIN 1-cycle then NORMAL or ERROR at
`NUM_PHY_REINIT`, ERROR waits Port/device reset). It is **not**
1/3, 4/3, freeze, or signoff. Stock Icarus
`tb/vibe/tests/tc_retry_req_gbn.sv` / `tc_retry_wait_retrain.sv`
remain the official TP scorers. This is **not** TP-DLL-004 /
`dll`. Seventh DLL leaf after `vibe_bcrc` / `vibe_dll_credit` /
`vibe_dll_sm` / `vibe_dll_rx` / `vibe_dll_retry_ack_sm` /
`vibe_dll_retry_buf`.

`tc_vibe_fecn_mark` / `make fecn_mark` / `make fecn`
is **module-level only** (combo idle / no clk / no `rst_n` / no
sequential hold, stock Mode `3'b100`/`3'b010` + VOQ watermark
`FECN_WM=24`, FECN `2'b00` unmarkable / `2'b11` already-severe /
non-markable modes, golden rewrite of FECN and LoC vs
pass-through). It is **not** 1/3, 4/3, freeze, or signoff. Stock
Icarus `tb/vibe/tests/tc_fecn_mark.sv` / `tc_fecn_mark` remains
the official TP scorer. This is **not** CAQM. First fabric leaf
after `vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm` / `vibe_dll_retry_buf` /
`vibe_dll_retry_req_sm`.

## Topology

```
UVMTest
 └─ UVMEnv
     ├─ Agent (Sequencer / Driver / Monitor)   # pull-mode
     └─ VibeAsScoreboard                       # G1, length, CFG6, SAF, ICRC
```

Phases / sequences / drivers are `async def` + `await`. Objections in `run_phase`.
ConfigDb outs are fresh empty lists. Types registered with `uvm_component_utils`
/ `uvm_object_utils`.

## Name mapping (old → new)

| Old gate | New |
|----------|-----|
| Icarus `vibe_suite.sv` tasks | `tc_suite_all` or `UVM_TESTNAME=tc_*` on `entry_fab` |
| SV UVM `+UVM_TESTNAME=` | same class name, Python UVM 1.2 |
| Icarus `tb/vibe/tests/tc_*.sv` | same `tc_*` class in `unit_leaf.py` / `unit_more.py` / `unit_pcs.py` / `unit_afifo.py` / `unit_sync2.py` / `unit_rst_sync.py` / `unit_gear_128_160.py` / `unit_gear_160_128.py` / `unit_dll.py` / `unit_pcs_scramble.py` / `unit_ebch16.py` / `unit_pcs_tx_cw2beat.py` / `unit_pcs_tx_amctl.py` / `unit_rs128_120_enc.py` / `unit_rs128_120_dec.py` / `unit_pcs_rx_deskew.py` / `unit_pcs_rx_amctl_lock.py` / `unit_pcs_rx_unpack.py` / `unit_pcs_tx_pack.py` / `unit_pcs_tx_fec.py` / `unit_pcs_rx_fec.py` / `unit_pcs_tx_g1.py` / `unit_bcrc.py` / `unit_dll_credit.py` / `unit_dll_sm.py` / `unit_dll_rx.py` / `unit_dll_retry_ack_sm.py` / `unit_dll_retry_buf.py` / `unit_dll_retry_req_sm.py` / `unit_fecn_mark.py` / `port_tests.py` / `static_tests.py` |
| Icarus `tc_afifo_afull10` | still `tc_afifo_afull10`; Decision-I module TC is `tc_vibe_afifo` |
| Icarus `tc_rst_sync` | still `tc_rst_sync`; Decision-I module TC is `tc_vibe_rst_sync` |
| Icarus `tc_gear_128_160` | still `tc_gear_128_160`; Decision-I module TC is `tc_vibe_gear_128_160` |
| Icarus `tc_gear_160_128` | still `tc_gear_160_128`; Decision-I module TC is `tc_vibe_gear_160_128` |
| Icarus `tc_pcs_scramble` | still `tc_pcs_scramble`; Decision-I module TC is `tc_vibe_pcs_scramble` |
| Icarus `tc_ebch16_lut` | still `tc_ebch16_lut`; Decision-I module TC is `tc_vibe_ebch16` |
| Icarus `tc_pcs_cw2beat` | still `tc_pcs_cw2beat`; Decision-I module TC is `tc_vibe_pcs_tx_cw2beat` |
| Icarus `tc_pcs_amctl` | still `tc_pcs_amctl`; Decision-I module TC is `tc_vibe_pcs_tx_amctl` |
| Icarus `tc_pcs_fec_*` (wrap) | still the FEC wrap scorers; Decision-I module TC is `tc_vibe_pcs_tx_fec` |
| Icarus `tc_rs_dec_syndrome` | still `tc_rs_dec_syndrome`; Decision-I module TC is `tc_vibe_rs128_120_dec` |
| Icarus `tc_pcs_rx_deskew` | still `tc_pcs_rx_deskew`; Decision-I module TC is `tc_vibe_pcs_rx_deskew` |
| Icarus `tc_pcs_rx_amctl` | still `tc_pcs_rx_amctl`; Decision-I module TC is `tc_vibe_pcs_rx_amctl_lock` |
| Icarus `tc_pcs_rx_unpack` | still `tc_pcs_rx_unpack`; Decision-I module TC is `tc_vibe_pcs_rx_unpack` |
| Icarus `tc_pcs_tx_pack` | still `tc_pcs_tx_pack`; Decision-I module TC is `tc_vibe_pcs_tx_pack` |
| Icarus `tc_pcs_rx_fec` | still `tc_pcs_rx_fec`; Decision-I module TC is `tc_vibe_pcs_rx_fec` |
| Icarus `tc_pcs_tx_g1_window` | still `tc_pcs_tx_g1_window`; Decision-I module TC is `tc_vibe_pcs_tx_g1` |
| Icarus `tc_bcrc_crc30` | still `tc_bcrc_crc30`; Decision-I module TC is `tc_vibe_bcrc` |
| Icarus `tc_credit_*` / `tc_cfg0_no_credit` | still those IDs; Decision-I module TC is `tc_vibe_dll_credit` |
| Icarus `tc_dll_sm_states` | still `tc_dll_sm_states`; Decision-I module TC is `tc_vibe_dll_sm` |
| Icarus `tc_cfg0_term_not_fabric` / `tc_dll_rx_errflag` / `tc_fec_fail_gbn` | still those IDs; Decision-I module TC is `tc_vibe_dll_rx` |
| Icarus `tc_retry_ack_replay` | still `tc_retry_ack_replay`; Decision-I module TC is `tc_vibe_dll_retry_ack_sm` |
| Icarus `tc_retry_buf_256` | still `tc_retry_buf_256`; Decision-I module TC is `tc_vibe_dll_retry_buf` |
| Icarus `tc_retry_req_gbn` / `tc_retry_wait_retrain` | still those IDs; Decision-I module TC is `tc_vibe_dll_retry_req_sm` |
| Icarus `tc_fecn_mark` | still `tc_fecn_mark`; Decision-I module TC is `tc_vibe_fecn_mark` |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` / `tc_cfg9_no_icrc` | fabric suite (`entry_fab` / `tc_suite_all`) |
| Icarus `tc_pcs_rx` / `tc_pcs_tx` (full stack) | still Icarus-only in this PR; leaf PCS units are ported |
| Icarus `tc_dll` (full stack) | `tc_dll` (`vibe_dll_cocotb_top`; **TP-DLL-004** >32-flit split ≤16×≤32) |
| Icarus `tc_timers_indep` | `tc_timers_indep` (`vibe_timers_indep_cocotb_top`) |
| Icarus `tc_fabric_g1` / `tc_fabric_line_holes` | fabric suite (`tc_suite_all`) |
| Icarus `tc_id_nports_entity0` / `tc_tp_holes` / `tc_neg_*` | `static_tests.py` (no simulator) |
| `make top` / `tc_top_smoke` | `entry_switch` / `tc_top_smoke` |
| `make neg` / `scan_absent.sh` | `static_tests.run_absent_scan` |
| `make sim-xsim` | deprecated secondary (needs xvlog) |

Identifiers (`tc_rt10_must_drop`, `tc_credit_1024_flit_bp`, …) are unchanged.
**Python correspondence** (HAS / GAP) lives in
[`tb/vibe/results/TP_PYUVM_MATRIX.md`](../results/TP_PYUVM_MATRIX.md).
`TP_TC_MATRIX.md` is the SV/UVM-biased scorer map — stock `tc_*.sv` alone
does not mean a Python TC exists. That matrix is **not** 1/3, 4/3, freeze, or signoff.

## Gate status (this tree)

Icarus (`SIM=icarus`) is the complete no-xvlog gate. Verilator is the
fabric/unit baseline (`--timing`); port/top hierarchical `Force` of LMSM
lock does not take effect under Verilator 5.020 + cocotb 1.9.2 VPI, so
those two stay Icarus.

| Bucket | Icarus | Verilator |
|--------|--------|-----------|
| `suite` (`tc_suite_all`, 28) | PASS | PASS |
| leaf units + static/neg + PCS | PASS (incl. `tc_phy_u26_chain`, `tc_timers_indep`) | `tc_vl_rr` PASS; fabric suite PASS |
| `tc_vibe_afifo` (module-level; ≠ full-chip gate) | PASS | PASS |
| `tc_vibe_sync2` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rst_sync` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_128_160` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_gear_160_128` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_dll` (full `vibe_dll`; **TP-DLL-004**; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_scramble` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_ebch16` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_cw2beat` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_amctl` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rs128_120_enc` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_rs128_120_dec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_deskew` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_amctl_lock` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_unpack` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_pack` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_fec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_rx_fec` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_pcs_tx_g1` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_bcrc` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_credit` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_rx` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_ack_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_buf` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_dll_retry_req_sm` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `tc_vibe_fecn_mark` (module-level; ≠ 1/3 ≠ 4/3 ≠ signoff) | PASS | PASS |
| `port` (smoke / TX / 100-pkt loopback) | PASS 100/100 | compile OK; LMSM Force bring-up does not reach ACTIVE |
| `top` (`tc_top_smoke`) | PASS | not scored (same Force path) |
| `neg` | PASS | n/a (no sim) |

#115 (`tc_port_smoke` / `tc_nw_pkt_pma_loopback` / `tc_top_smoke`) is **not**
failing on `main` with PR116. Checkers were **not** relaxed.

Not Python-sim in this PR (still `make sim-icarus`): full-stack `tc_pcs_rx`,
`tc_pcs_tx`. Full-stack `tc_dll` is now uvm-python and scores **TP-DLL-004**.
Leaf PCS units remain the scorers for those TPs.

## #115

PMA idle-PRBS ECO (`a658d141`) made Icarus `tc_port_smoke` /
`tc_nw_pkt_pma_loopback` / `tc_top_smoke` fail. PR116 landed a DUT fix on
`main`. This TB **does not** weaken those checkers. If they fail on a freeze
without that ECO, report them as DUT fails.

## Layout

```
tb/vibe/pyuvm/
  vibe_uvm/          items, vifs, agents, env, scoreboard, tests
                     tests/unit_afifo.py  Decision-I vibe_afifo (module-level)
                     tests/unit_sync2.py  Decision-I vibe_sync2 (module-level)
                     tests/unit_rst_sync.py  Decision-I vibe_rst_sync (module-level)
                     tests/unit_gear_128_160.py  Decision-I vibe_gear_128_160 (module-level)
                     tests/unit_gear_160_128.py  Decision-I vibe_gear_160_128 (module-level)
                     tests/unit_dll.py    full vibe_dll; TP-DLL-004 split
                     tests/unit_pcs_scramble.py  Decision-I vibe_pcs_scramble (module-level)
                     tests/unit_ebch16.py  Decision-I vibe_ebch16 (module-level)
                     tests/unit_pcs_tx_cw2beat.py  Decision-I vibe_pcs_tx_cw2beat (module-level)
                     tests/unit_pcs_tx_amctl.py  Decision-I vibe_pcs_tx_amctl (module-level)
                     tests/unit_rs128_120_enc.py  Decision-I vibe_rs128_120_enc (module-level)
                     tests/unit_rs128_120_dec.py  Decision-I vibe_rs128_120_dec (module-level)
                     tests/unit_pcs_rx_deskew.py  Decision-I vibe_pcs_rx_deskew (module-level)
                     tests/unit_pcs_rx_amctl_lock.py  Decision-I vibe_pcs_rx_amctl_lock (module-level)
                     tests/unit_pcs_rx_unpack.py  Decision-I vibe_pcs_rx_unpack (module-level)
                     tests/unit_pcs_tx_pack.py  Decision-I vibe_pcs_tx_pack (module-level)
                     tests/unit_pcs_tx_fec.py  Decision-I vibe_pcs_tx_fec (module-level)
                     tests/unit_pcs_rx_fec.py  Decision-I vibe_pcs_rx_fec (module-level)
                     tests/unit_pcs_tx_g1.py  Decision-I vibe_pcs_tx_g1 (module-level)
                     tests/unit_bcrc.py  Decision-I vibe_bcrc (module-level)
                     tests/unit_dll_credit.py  Decision-I vibe_dll_credit (module-level)
                     tests/unit_dll_sm.py  Decision-I vibe_dll_sm (module-level)
                     tests/unit_dll_rx.py  Decision-I vibe_dll_rx (module-level)
                     tests/unit_dll_retry_ack_sm.py  Decision-I vibe_dll_retry_ack_sm (module-level)
                     tests/unit_dll_retry_buf.py  Decision-I vibe_dll_retry_buf (module-level)
                     tests/unit_dll_retry_req_sm.py  Decision-I vibe_dll_retry_req_sm (module-level)
                     tests/unit_fecn_mark.py  Decision-I vibe_fecn_mark (module-level)
  tb/                cocotb Verilog wrappers (no SV UVM)
  entry_*.py         @cocotb.test() → await run_test(...)
  catalog.py         RTL lists + TC map
  run_gate.py        suite / units / top / neg
  requirements.txt
```
