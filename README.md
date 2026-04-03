# Vibe-UB-Switch

UB Protocol 4x400Gbps ASIC Switch — RTL design and functional simulation verification via vibe coding.

Spec reference: https://www.unifiedbus.com

## Overview

This project implements a 4-port UB Protocol switch targeting ASIC implementation. Each port operates at 400Gbps (4 lanes x 100Gbps PAM4). The design follows the UB 7-layer AI/HPC interconnect architecture with 640-bit flits and RS(128,120) FEC.

## Architecture

```
                        ub_switch_top
                    ┌─────────────────────┐
                    │                     │
    Port 0 ◄──────►│    ub_xbar_fabric   │◄──────► Port 3
                    │      (4x4 Crossbar) │
    Port 1 ◄──────►│                     │◄──────► Port 2
                    └─────────────────────┘

    Each ub_port:
    ┌─────────────────────────────────────────────────┐
    │  Network Layer (NW)  ←→  ub_nw_tx / ub_nw_rx    │
    │  Data Link Layer (DLL) ←→ ub_dll_tx/rx_engine    │
    │  CDC  ←→  ub_cdc_async_fifo                      │
    │  PCS TX/RX Pipeline (FEC, Scrambler, Gearbox)    │
    │  LMSM (Link Management State Machine)            │
    └─────────────────────────────────────────────────┘
```

### Key Parameters

| Parameter | Value |
|-----------|-------|
| Ports | 4 |
| Per-port bandwidth | 400 Gbps (4 x 100Gbps PAM4 lanes) |
| Flit width | 640 bits |
| FEC | RS(128,120) |
| Crossbar | 4x4, round-robin arbitration |
| Output queue | Store-and-forward, depth 8 |
| DL clock | 1.25 GHz |
| PCS clock | 875 MHz |
| Routing | DCNA-based (bits [511:496] of 512b packet) |

## Directory Structure

```
Vibe-UB-switch/
├── rtl/
│   ├── top/            # Switch top-level
│   │   └── ub_switch_top.v
│   ├── port/           # Port wrapper + CSR
│   │   ├── ub_port.v
│   │   └── ub_port_csr.v
│   ├── nw/             # Network layer
│   │   ├── ub_nw_csr.v
│   │   ├── ub_nw_tx.v
│   │   ├── ub_nw_rx.v
│   │   └── ub_nw_icrc.v
│   ├── dll/            # Data Link Layer
│   │   ├── ub_dll_tx_engine.v
│   │   ├── ub_dll_rx_engine.v
│   │   ├── ub_dll_flow_ctrl.v
│   │   ├── ub_dll_retry_ctrl.v
│   │   ├── ub_dll_segmenter.v
│   │   ├── ub_dll_reassembler.v
│   │   ├── ub_dll_crc32.v
│   │   └── ub_dll_crc_check.v
│   ├── pcs/            # Physical Coding Sublayer
│   │   ├── ub_pcs_tx_pipe.v       # TX pipeline top
│   │   ├── ub_pcs_rx_pipe.v       # RX pipeline top
│   │   ├── ub_pcs_tx_gearbox.v    # 640b→512b width conversion
│   │   ├── ub_pcs_rx_gearbox.v    # 512b→640b width conversion
│   │   ├── ub_pcs_fec_enc.v       # RS(128,120) encoder
│   │   ├── ub_pcs_fec_dec.v       # RS(128,120) decoder
│   │   ├── ub_pcs_fec_ibm.v       # IBM algorithm for FEC
│   │   ├── ub_pcs_fec_syndrome.v  # Syndrome calculator
│   │   ├── ub_pcs_fec_chien_forney.v  # Chien-Forney search
│   │   ├── ub_pcs_scrambler_lane.v    # Per-lane LFSR scrambler
│   │   ├── ub_pcs_descrambler_lane.v  # Per-lane descrambler
│   │   ├── ub_pcs_gray_coder.v        # PAM4 Gray encoder
│   │   ├── ub_pcs_gray_decoder.v      # PAM4 Gray decoder
│   │   ├── ub_pcs_amctl_gen_wide.v    # Alignment marker generator
│   │   ├── ub_pcs_amctl_lock.v        # AMCTL lock state machine
│   │   ├── ub_pcs_lmsm.v             # Link Management SM
│   │   ├── ub_pcs_lane_dist.v         # Lane distributor
│   │   ├── ub_pcs_lane_dedist.v       # Lane de-distributor
│   │   └── ub_pcs_lane_aligner.v      # Lane deskew/alignment
│   ├── cdc/            # Clock Domain Crossing
│   │   ├── ub_cdc_async_fifo.v
│   │   └── ub_cdc_gray_sync.v
│   └── switch/         # Crossbar fabric
│       ├── ub_xbar_fabric.v   # 4x4 crossbar with output queues
│       ├── ub_xbar_arbiter.v  # Round-robin arbiter
│       └── ub_xbar_outq.v     # Store-and-forward output queue
├── tb/
│   ├── cdc/            # CDC async FIFO testbench
│   ├── pcs/            # PCS unit testbenches
│   ├── dll/            # DLL unit testbenches
│   ├── nw/             # Network layer testbenches
│   └── switch/         # Crossbar + switch top testbenches
└── README.md
```

## Module Hierarchy

```
ub_switch_top
├── ub_port [x4] (u_port0..u_port3)
│   ├── ub_port_csr
│   │   └── ub_nw_csr
│   ├── ub_dll_tx_engine
│   │   ├── ub_dll_segmenter
│   │   ├── ub_dll_crc32
│   │   ├── ub_dll_flow_ctrl
│   │   └── ub_dll_retry_ctrl
│   ├── ub_dll_rx_engine
│   │   ├── ub_dll_reassembler
│   │   └── ub_dll_crc_check
│   ├── ub_cdc_async_fifo (TX CDC)
│   │   └── ub_cdc_gray_sync [x2]
│   ├── ub_cdc_async_fifo (RX CDC)
│   │   └── ub_cdc_gray_sync [x2]
│   ├── ub_pcs_tx_pipe
│   │   ├── ub_pcs_tx_gearbox
│   │   ├── ub_pcs_fec_enc
│   │   ├── ub_pcs_scrambler_lane [x4]
│   │   ├── ub_pcs_amctl_gen_wide
│   │   ├── ub_pcs_lane_dist
│   │   ├── ub_pcs_gray_coder_lane [x4]
│   │   └── ub_pcs_gray_coder
│   ├── ub_pcs_rx_pipe
│   │   ├── ub_pcs_gray_decoder
│   │   ├── ub_pcs_gray_decoder_lane [x4]
│   │   ├── ub_pcs_lane_dedist
│   │   ├── ub_pcs_lane_aligner
│   │   ├── ub_pcs_amctl_lock [x4]
│   │   ├── ub_pcs_descrambler_lane [x4]
│   │   ├── ub_pcs_rx_gearbox
│   │   └── ub_pcs_fec_dec
│   │       ├── ub_pcs_fec_syndrome
│   │       ├── ub_pcs_fec_ibm
│   │       └── ub_pcs_fec_chien_forney
│   └── ub_pcs_lmsm
└── ub_xbar_fabric (u_xbar)
    ├── ub_xbar_arbiter [x4]
    └── ub_xbar_outq [x4]
```

## Simulation

All testbenches use Icarus Verilog (`iverilog`) with SystemVerilog extensions (`-g2012`).

### Compile & Run

```bash
# CDC async FIFO
iverilog -g2012 -o /tmp/cdc.vvp tb/cdc/ub_cdc_async_fifo_tb.v rtl/cdc/ub_cdc_async_fifo.v rtl/cdc/ub_cdc_gray_sync.v
vvp /tmp/cdc.vvp

# PCS TX/RX loopback
iverilog -g2012 -Irtl/common -o /tmp/pcs.vvp tb/pcs/ub_pcs_tx_rx_loopback_tb.v rtl/pcs/ub_pcs_tx_pipe.v rtl/pcs/ub_pcs_rx_pipe.v rtl/pcs/ub_pcs_tx_gearbox.v rtl/pcs/ub_pcs_rx_gearbox.v rtl/pcs/ub_pcs_scrambler_lane.v rtl/pcs/ub_pcs_descrambler_lane.v rtl/pcs/ub_pcs_amctl_gen_wide.v rtl/pcs/ub_pcs_gray_coder_lane.v rtl/pcs/ub_pcs_gray_decoder_lane.v rtl/pcs/ub_pcs_gray_coder.v rtl/pcs/ub_pcs_gray_decoder.v rtl/pcs/ub_pcs_fec_enc.v rtl/pcs/ub_pcs_fec_dec.v rtl/pcs/ub_pcs_fec_ibm.v rtl/pcs/ub_pcs_fec_syndrome.v rtl/pcs/ub_pcs_fec_chien_forney.v rtl/pcs/ub_pcs_lane_dist.v rtl/pcs/ub_pcs_lane_dedist.v rtl/pcs/ub_pcs_lane_aligner.v rtl/pcs/ub_pcs_amctl_lock.v
vvp /tmp/pcs.vvp

# DLL loopback
iverilog -g2012 -o /tmp/dll.vvp tb/dll/ub_dll_loopback_tb.v rtl/dll/ub_dll_tx_engine.v rtl/dll/ub_dll_rx_engine.v rtl/dll/ub_dll_flow_ctrl.v rtl/dll/ub_dll_retry_ctrl.v rtl/dll/ub_dll_segmenter.v rtl/dll/ub_dll_reassembler.v rtl/dll/ub_dll_crc32.v rtl/dll/ub_dll_crc_check.v
vvp /tmp/dll.vvp

# Crossbar fabric
iverilog -g2012 -o /tmp/xbar.vvp tb/switch/ub_xbar_fabric_tb.v rtl/switch/ub_xbar_fabric.v rtl/switch/ub_xbar_arbiter.v rtl/switch/ub_xbar_outq.v
vvp /tmp/xbar.vvp

# Full switch top-level
iverilog -g2012 -Irtl/common -o /tmp/stb.vvp tb/switch/ub_switch_top_tb.v rtl/top/ub_switch_top.v rtl/port/ub_port.v rtl/port/ub_port_csr.v rtl/nw/ub_nw_csr.v rtl/pcs/ub_pcs_lmsm.v rtl/dll/ub_dll_tx_engine.v rtl/dll/ub_dll_rx_engine.v rtl/dll/ub_dll_flow_ctrl.v rtl/dll/ub_dll_retry_ctrl.v rtl/pcs/ub_pcs_tx_pipe.v rtl/pcs/ub_pcs_rx_pipe.v rtl/pcs/ub_pcs_tx_gearbox.v rtl/pcs/ub_pcs_rx_gearbox.v rtl/pcs/ub_pcs_scrambler_lane.v rtl/pcs/ub_pcs_descrambler_lane.v rtl/pcs/ub_pcs_amctl_gen_wide.v rtl/pcs/ub_pcs_gray_coder_lane.v rtl/pcs/ub_pcs_gray_decoder_lane.v rtl/pcs/ub_pcs_gray_coder.v rtl/pcs/ub_pcs_gray_decoder.v rtl/pcs/ub_pcs_fec_enc.v rtl/pcs/ub_pcs_fec_dec.v rtl/pcs/ub_pcs_fec_ibm.v rtl/pcs/ub_pcs_fec_syndrome.v rtl/pcs/ub_pcs_fec_chien_forney.v rtl/cdc/ub_cdc_async_fifo.v rtl/cdc/ub_cdc_gray_sync.v rtl/switch/ub_xbar_fabric.v rtl/switch/ub_xbar_arbiter.v rtl/switch/ub_xbar_outq.v
vvp /tmp/stb.vvp
```

### Testbench Summary

| Phase | Testbench | Description | Status |
|-------|-----------|-------------|--------|
| 1 | `tb/cdc/ub_cdc_async_fifo_tb.v` | Async FIFO with gray-code CDC, dual-clock read/write | PASS |
| 2 | `tb/pcs/ub_pcs_tx_rx_loopback_tb.v` | PCS TX→RX loopback: gearbox, RS-FEC, scrambler, gray coder | PASS |
| 3 | `tb/dll/ub_dll_loopback_tb.v` | DLL TX→RX loopback: 5-flit sequence, CRC, null filtering | PASS |
| 4 | `tb/switch/ub_xbar_fabric_tb.v` | 4x4 crossbar: unicast routing + round-robin contention | PASS |
| 5 | `tb/pcs/ub_pcs_tx_rx_loopback_tb.v` | PCS loopback with dual-clock CDC integration | PASS |
| 6 | `tb/switch/ub_switch_top_tb.v` | Full 4-port switch top: routing, simultaneous, contention | PASS |

### Unit Testbenches

| Testbench | Target |
|-----------|--------|
| `tb/pcs/ub_pcs_fec_enc_tb.v` | RS(128,120) FEC encoder |
| `tb/pcs/ub_pcs_fec_dec_tb.v` | RS(128,120) FEC decoder |
| `tb/pcs/ub_pcs_fec_dec_loopback_tb.v` | FEC encode→decode loopback |
| `tb/pcs/ub_pcs_scrambler_tb.v` | LFSR scrambler |
| `tb/pcs/ub_pcs_descrambler_tb.v` | LFSR descrambler |
| `tb/pcs/ub_pcs_gray_coder_tb.v` | PAM4 Gray encoder |
| `tb/pcs/ub_pcs_gray_decoder_tb.v` | PAM4 Gray decoder |
| `tb/pcs/ub_pcs_lmsm_tb.v` | Link management state machine |
| `tb/pcs/ub_pcs_amctl_lock_tb.v` | AMCTL lock detection |
| `tb/pcs/ub_pcs_lane_aligner_tb.v` | Multi-lane deskew |
| `tb/pcs/ub_pcs_lane_dist_tb.v` | Lane distribution |
| `tb/pcs/ub_pcs_lane_dedist_tb.v` | Lane de-distribution |
| `tb/pcs/ub_pcs_ebch16_tb.v` | eBCH-16 lookup table |
| `tb/dll/ub_dll_crc32_tb.v` | CRC-32 generator |
| `tb/dll/ub_dll_crc32_parallel_tb.v` | Parallel CRC-32 |
| `tb/dll/ub_dll_crc_check_tb.v` | CRC-32 verifier |
| `tb/dll/ub_dll_segmenter_tb.v` | DLL segmenter |
| `tb/dll/ub_dll_reassembler_tb.v` | DLL reassembler |
| `tb/nw/ub_nw_csr_tb.v` | Network CSR |
| `tb/nw/ub_nw_tx_tb.v` | NW transmit |
| `tb/nw/ub_nw_rx_tb.v` | NW receive |

## Design Details

### Routing

Packets are routed by DCNA (Destination Component Name Address):
- Source port embeds DCNA in packet bits [511:496]
- Switch compares against per-port SCNA values configured via CSR
- Default SCNA: Port 0 = 0x0001, Port 1 = 0x0002, Port 2 = 0x0003, Port 3 = 0x0004

### Crossbar Fabric

- 4x4 non-blocking crossbar with per-output-port arbitration
- Round-robin arbiter with packet-level atomicity (SOP→EOP lock)
- Store-and-forward output queues (depth 8)
- Backpressure via per-output ready signal

### DLL Flow Control

- Credit-based: TX engine tracks available credits
- `nw_flit_ready = link_ready && tx_credit_avail && !retry_active && flit_ready`
- Go-Back-N retry with circular buffer

### PCS Pipeline

- TX: 640b gearbox → RS(128,120) FEC → per-lane scrambling → AMCTL insertion → lane distribution → PAM4 Gray coding
- RX: PAM4 Gray decoding → lane de-distribution → AMCTL lock → lane alignment → per-lane descrambling → FEC decode → 640b gearbox

### Clock Domain Crossing

- Dual-clock design: DL domain (1.25 GHz) and PCS domain (875 MHz)
- Asynchronous FIFO with 2-stage gray-code pointer synchronization
