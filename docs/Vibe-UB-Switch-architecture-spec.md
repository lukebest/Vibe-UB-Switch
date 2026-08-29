# Vibe-UB-Switch Architecture Specification AS-0.1

Status: locked subset for this RTL revision.  
Sources: public Unified Bus (UB) 2.0 + this architecture spec only.  
This document does not add musts beyond AS-0.1.

---

## 1. Outcome and non-goals

This revision implements synthesizable Verilog/SystemVerilog RTL for the locked subset of a 4-port independent UB Switch (Entity 0, Port 0..3).

- Hierarchical RTL; one module per file where practical.
- Fabric is store-and-forward (no cut-through). A full packet is assembled before the crossbar.
- Do not implement UBFM, CAQM, NPI filter datapath, Transport/Transaction/Function endpoint, or analog PMA (Gray coding, precoding, SerDes).
- Do not wait for G2–G9 (Max Index, extra interrupt pins, extra reset pins, CNA default value, `lmsm_go` source, credit-threshold unit, package pins, RXEQ_Optimize). Implement as this spec says.
- Existing `rtl/` and `tb/` trees from prior revisions are void and are not a source of signal names, depths, SCNA-compare routing, 640-bit-as-flit, depth-8 queues, or CDC ready formulas.

---

## 2. Locked subset (must work)

4-port independent UB Switch, Entity 0, Port 0..3.

- Routing: `CFG0_ROUTE_TABLE` dest → 4-bit egress bitmap.
  - RT=00: per-flow sticky round-robin.
  - RT=01: per-packet round-robin.
  - Flow key `{CFG, src, dest, VL}`.
- **G1 (mandatory):** RT=10 and RT=11: DROP the packet, increment `rt_shortest_unimpl` counter, assert `irq_logic`. Do NOT Dijkstra. Do NOT treat as RT=00. Do NOT rewrite RT.
- Default routing table all-0 → port 0. No Port CNA, no SCNA compare, no flood/broadcast.
- U26 width chain + G1/G2 gearbox (see datapath).
- Per-lane gray-pointer AFIFO CDC 1.25 GHz ↔ 922 MHz.
- LMSM (this-rev subset), DLL SM, RETRY_REQ_SM, RETRY_ACK_SM, AMCTL lock per lane.

---

## 3. Clocks and product boundary

- `clk_fab` 1.25 GHz: fabric, DLL, PCS digital, LMSM, mgmt.
- Per port independent `txclk` / `rxclk` 922 MHz. Do not assume they are common.
- Product PMA (NO extra handshake names): `txdata[511:0]`, `txclk`, `rxdata[511:0]`, `rxclk`.
  - Slice: `[127:0]` = lane0, `[255:128]` = lane1, `[383:256]` = lane2, `[511:384]` = lane3.
- NW↔DLL and NW↔fabric: 640-bit `data` + `vld`/`ready` @ `clk_fab`. LinkReady participates in ready (U21). No extra enable names.
- Flit = 20 bytes, never 640-bit.

---

## 4. Module tree

```
vibe_ub_switch
├── port[3:0]
│   ├── pma_bnd
│   ├── afifo_tx[3:0], afifo_rx[3:0]   // gray pointers, depth 16 words
│   ├── pcs_tx (g1, fec dual RS(128,120)+interleave, scramble, amctl insert, pack G2)
│   ├── pcs_rx (amctl_lock x4, unpack, descramble, fec decode, deskew)
│   ├── lmsm
│   ├── dll (dll_sm, dll_tx, dll_rx, dll_credit, retry_buf depth 256 FS-must,
│   │        retry_req_sm, retry_ack_sm)
│   └── nw_adapt
├── fabric (saf_ing[3:0], route_lu, port_sel, xbar, voq_egr[3:0] x16 VL,
│           vl_rr[3:0], fecn_mark[3:0])
└── mgmt (cfg_space, cna_ep, irq_agg, rst_ctl)
```

No UBFM, no CAQM, no NPI filter datapath, no Transport/Transaction/Function endpoint, no analog PMA.

---

## 5. TX datapath (`clk_fab` then `txclk`)

| Stage | Function |
|-------|----------|
| T0 | `nw_adapt` 640b `vld`/`ready` |
| T1 | `dll_tx`: slice 640b = 4 flits + BCRC; backpressure if credit low / retry full / REQ\|WAIT dropping data / pending credit ≥ 1024 |
| T2 | `pcs_tx_g1`: collect 6 flits (640b = 4 flits so 1.5 beats + 320b remainder). Idle: insert Null Block to fill FEC window. |
| T3 | `pcs_tx_fec`: two RS(128,120) interleaved; T=4 default / T=2 / bypass (`3'b010` / `3'b001` / `3'b000`). Bypass skips encoder, still 6-flit align. |
| T4 | `pcs_tx_cw2beat`: 1024b codeword as two 512b beats. |
| T5 | `pcs_tx_pack` G2: 512b beats + AMCTL (outside FEC) → 640b = 4×160 into AFIFOs. `almost_full` backpresses. |
| T6 | `afifo_tx` write 160b @ `clk_fab` |
| T7 | read 128b @ `txclk` with 32b residue gearbox |
| T8 | `pma_bnd` concatenates to `txdata`. NO PMA ready. |

AMCTL: 40 symbol/lane, eBCH-16; data period every 640 symbols after SDF; other LMSM states every 512 symbols. Insert after FEC, before G2.

Scramble LTB, not AMCTL/EEIB. Gray/precoding NOT implemented (PMA).

TX may backpressure NW stage by stage.

---

## 6. RX inverse

`rxdata` 4×128 @ `rxclk` → `afifo_rx` (overflow: drop beat, count, irq; no PMA ready) → 160b @ `clk_fab` → unpack/strip AMCTL/deskew → 2×512 codeword → RS decode (fail → `fec_fail` to DLL for Go-Back-N; no `hi_FEC_BER`) → `dll_rx` BCRC + CFG0 terminate → `nw_adapt` 640b to fabric.

U24: no polarity/lane-swap training. Factory assume physical lane = logical. If `AMCTL.LID` not `{0,1,2,3}`, fail to Link_Idle or Retrain, do not swap lanes.

---

## 7. AFIFO CDC

- Depth 16, pointer 5 bits, binary→gray, 2-FF sync, degray.
- `almost_full` at occupancy ≥ 10 (write domain).
- TX 160→128 residue on read domain; RX 128→160 dual residue.
- Do not copy prior-revision ready formulas.

---

## 8. Fabric

SAF: do not present to xbar until EOP / full declared length. Max packet 4300 B; length not in 16–4300 B → Packet Length Error, drop, irq.

After assemble, 8 stages: descriptor, length, NTH/LPH parse, CFG classify, ICRC only if we are the target (transit MUST NOT recompute ICRC even if CCI/LBF rewritten), `route_lu`, `port_sel`, xbar grant.

Available ports = bitmap AND `DLL_Status_Up`. Empty after filter → Default; Default all-0 → port 0; if port 0 also Down, drop+count, no flood.

VL from header. VL0–15 hardware present. VL scheduling RR among non-empty VOQs of an egress; FCFS within VL. No SL.

FECN: if `CCI.Mode` is `3'b100` or `3'b010`, and local congestion (VOQ occ ≥ `FECN_WM`, default 24 = 3/4 of 32) is worse than the packet mark, rewrite FECN and LoC. Else don't. Not CAQM.

Deadlock timeout 1 µs = 1250 `clk_fab` cycles from VOQ enqueue; expire → drop+count+irq. Separate from credit-return 1 µs.

xbar: output queued, ingress RR on conflict, one full packet per grant. Down ports get no data DLLDP. mgmt bypass FIFO does not enter xbar; mgmt reply injects on the ingress port's TX before `nw_adapt_tx`, priority over VOQ.

---

## 9. CFG classify

- CFG0: terminate/generate in per-port DLL, never enters fabric.
- CFG 3/4/5/7/9 and reserved 1, 2, 8, 10–15: forward (unless dest is us for applicable types).
- CFG6: terminate if `DCNA` == mgmt CNA AND CNA has been statically written, OR `NLP=1` enumerate, OR opcode `0x10` targeting this device; else forward.
- Power-on CNA default UNKNOWN: do not match DCNA against any reset value until a static write has occurred.
- No homemade flood.

---

## 10. Config / reset / irq (logical only)

No APB/AXI/I2C/JTAG pins, no extra interrupt pins.

Static write, `clk_fab`, `vld`/`ready`:

- `cfg_wr_cmd`: 0=CNA, 1=route entry, 2=Default bitmap, 3=Port Reset, 4=device reset, 5=pulse `lmsm_go`; others ignore
- `cfg_wr_idx[15:0]`, `cfg_wr_data[31:0]`

Must implement:

- GUID Type `0x3`, Class `0x03`/`0x00`
- `CFG0_PORT_BASIC` / `CAP` constants (4 ports, x4, Mode-2 106.25 G)
- `CFG0_ROUTE_TABLE` + Default (reset all-0)
- Port Reset RW1C per port
- Entity 0 device reset
- 16-bit mgmt CNA (static write only)

`ROUTE_TABLE_DEPTH` parameter, RTL default 256 (architecture-chosen, NOT a product Max Index). Entries 32-bit, only `[3:0]` meaningful.

`irq_logic`: active-high level, OR of observable errors (see error table). Sticky; clear on static write or reset. Single bit, no extra product IRQ pins.

Device reset: clear RW config to unwritten (CNA unwritten). MUST NOT by itself force `DLL_Disabled`. LMSM → Link_Idle.

Port Reset port `p`: that port LMSM Link_Idle, `DLL_Disabled`, retry pointers 0, `NumFreeBuf=256`. Do not reset other ports or the global route table.

DLL credit/retry ERROR: stop TX/RX that port, wait Port Reset or device reset (not UBFM).

---

## 11. LMSM (per port) — implement these states only

`Link_Idle` → `Discovery` (on `lmsm_go`; NO Probe, NO RXEQ_Optimize even if the official single-rate path wants it).

`Discovery.Active` / `Confirm`, `Config.Active` / `Check` / `Confirm`, `Send_NullBlock` (`LinkUp=1`; 8 nulls → `Link_Active`; 2 ms timeout), `Link_Active` (`LinkUp=1`, `LinkReady=1` at locked 106.25 G), `Retrain.Active` / `Confirm` (do not change rate), `EQ.*` if Config negotiated EQ (`Passive` 64 ms, `Active` 24 ms / 48 ms > DR4).

Width result must be x4 else fail to `Link_Idle`. Lane 0 fail → Retrain, no downshift.

Timers on `clk_fab` (1.25 GHz: 1 µs = 1250):

- `Discovery.Active` 10 µs from Retrain/Config else 24 ms
- Confirm 48 ms
- `Config.*` 2 ms
- `Send_NullBlock` 2 ms
- `Retrain.Active` 24 ms
- pre-FEC BER + FEC select 22 ms

Do NOT implement: Probe, RXEQ_Optimize, Change_Speed, QDLWS, optical, missing Fig 3-28 arcs, polarity/lane-swap training, fast downshift.

No business flits to DLL until trained.

---

## 12. DLL

States: `Disabled` (`LinkUp==0` → always), `Param_Init`, `Credit_Init`, `Normal` (`Status_Up`).

Entity reset must not force `Disabled`.

Negotiate; on fail use official defaults BUT VL1–15 hardware must remain usable (`VL_ENABLE` default `0x1`, others enable via CFG later):

- `DATA_CREDIT_GRAIN` 4 cell/VL
- CTRL 1
- `FEATURE_ID=1`
- `RXBUF_VL_SHARE=0`
- `DATA_ACK_GRAIN` 32 flit
- `CTRL_ACK_GRAIN` 1
- `FLOW_CTRL_SIZE` 8 flit/cell

BCRC CRC30 poly \(x^{30}+x^{28}+x^{26}+x^{24}+x^{23}+x^{21}+x^{19}+x^{16}+x^{14}+x^{11}+x^{9}+x^{7}+x^{6}+x^{4}+x^{2}+1\), init all-1, no invert. bit31 reserved, bit30 `ERROR_FLAG`.

`retry_buf` depth 256 FS-must. `NumFreeBuf` init 256; `WrPtr`/`TailPtr`/`RdPtr`/`RcvPtr` init 0. Null and Retry blocks do not enter. Send needs `NumFreeBuf >= SendSize`. ACK release; `NumFreeBuf + ReleaseSize > 256` → DL Protocol Error.

`RETRY_REQ_SM`:

- `NORMAL`, `REQ` (1 Idle + 32 Req; `NUM_RETRY+1`; ==15 or PHY retrain → `RETRAIN`), `WAIT` (timeout → `REQ`; default `RETRY_WAIT_CYC=12500` = 10 µs, parameter, legal 1 µs–10 s), `RETRAIN` (`NUM_PHY_REINIT+1`; ==4 → `ERROR`), `ERROR` wait Port/device reset → `NORMAL`.
- `NUM_RETRY=15`, `NUM_PHY_REINIT=4`.

`RETRY_ACK_SM`: `NORMAL`, `ACK` (1 Idle + 32 Ack then replay `RdPtr=RcvPtr` until `WrPtr`).

Go-Back-N on FEC fail or BCRC fail.

Credit consume `ceil(DLLDP_flits / n)`, `n` in `{1,2,4,8,...,128}` default 8. Max 65535 cells all VLs. No DLLDP but pending credit → `Crd_Ack`. Pending ≥ 1024 → backpressure NW and force `Crd_Ack`. Credit return timeout 1 µs → DL Protocol Error. Do NOT invent credit underflow. Do NOT silently enlarge RXBUF to 1024 cell/VL; `dll_rxbuf` = 1024 flit/VL exclusive (architecture-chosen).

DLLDP 1–512 flits; >32 flits split into ≤16 DLLDB of ≤32 flits. CFG0 DLLCB does not consume credit.

`LinkUp==0`: TX drop upper; incomplete RX DLLDP pad 0 + `ERROR_FLAG`; credit 0; pointers 0; `NumFreeBuf=256`; `Disabled`.

---

## 13. ICRC

CRC32 `0x04C11DB7` init `0xFFFFFFFF`, per-byte bit reverse then reverse+invert result. Mask CCI/LBF to 1s; IPv4 TTL/HeaderChecksum/ToS, IPv6 TC/FlowLabel/HopLimit, UDP checksum to 1s. CFG3/4 from IP header; CFG6/7 from NTH; CFG9 no ICRC. Compute/check only as sender/receiver (`cna_ep`). Transit path has NO ICRC unit.

---

## 14. Buffers (label params; FS-must vs architecture-chosen)

FS-must:

- `retry_buf` 256
- credit threshold comparator 1024
- credit timeout 1 µs
- deadlock 1 µs
- `NUM_RETRY` 15
- `NUM_PHY_REINIT` 4

Architecture-chosen (parameters, not functional musts; do NOT use prior-revision depth 8):

- afifo 16
- `dll_rxbuf` 1024 flit/VL
- `saf_ing` pkt_mem 128×640b
- voq 32 flit/VL/egress
- mgmt bypass 16×640b
- `FECN_WM=24`
- `AMCTL_CONFIRM_N=UNLOCK_N=3`
- `ROUTE_TABLE_DEPTH` default 256

---

## 15. Errors → `irq_logic` (sticky)

Must observe:

- RX buf overflow
- FC overflow
- DL Protocol Error (credit timeout and `NumFreeBuf` overflow)
- DL Retry Error (15×4)
- ICRC fail (receiver)
- Packet Length Error
- deadlock drop
- RT=10/11 unimplemented
- RX AFIFO overflow

Retry ACK timeout / rollover: count, follow auto-retry, not necessarily irq.

FEC fail: Go-Back-N first, not a standalone irq must.

No `hi_FEC_BER`. No NPI mismatch drop. No credit underflow code.

---

## 16. PHY

Mode-2 PAM4 106.25 Gbit/s x4 symmetric only. FEC RS(128,120) T=4 / T=2 / bypass, dual-encoder interleave. DLL encapsulation BCRC only.

---

## 17. Coding rules

- Verilog/SV, synthesizable. Explicit clocks/resets. No delays in RTL (`#0` ok in assertions only).
- Top module `vibe_ub_switch` with 4-port PMA + `clk_fab` + `rst_n` (logical) + `cfg_wr_*` + `irq_logic`.
- Comments cite this AS section, not prior-revision RTL.
- If a protocol constant is unknown in AS, keep it a parameter; do not invent pin names.

---

## 18. Product pins (this rev)

Logical only:

- `clk_fab`, `rst_n`
- per port: `txclk`, `rxclk`, `txdata[511:0]`, `rxdata[511:0]`
- `cfg_wr_vld`, `cfg_wr_ready`, `cfg_wr_cmd`, `cfg_wr_idx[15:0]`, `cfg_wr_data[31:0]`
- `irq_logic`

No extra interrupt pins, no extra reset pins, no APB/AXI/I2C/JTAG.
