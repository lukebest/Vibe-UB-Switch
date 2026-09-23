# vibe_dll_retry_buf

DLL RETRY buffer (AS-0.1 §12). Decision I
stage-25 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(sixth DLL helper under `pycircuit/dll/`, after `vibe_bcrc`
/ `vibe_dll_credit` / `vibe_dll_sm` / `vibe_dll_rx` /
`vibe_dll_retry_ack_sm`) under the pycircuit → rtl flow.
Depth 256 FS-must. Null and Retry blocks do not enter.
`NumFreeBuf + ReleaseSize > 256` → DL Protocol Error.
Self-contained (no child instances). Sixth DLL leaf after
`vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/dll/vibe_dll_retry_buf.py` |
| Product SV | `rtl/dll/vibe_dll_retry_buf.sv` |
| Instantiator | `vibe_dll` (`u_rbuf`); unit TC (`tc_retry_buf_256`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `fc7c0151` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric / DLL digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low |
| `port_rst` | in | clear pointers / `freeb=256` (not `proto_err`) |
| `link_up` | in | 0: same clear as `port_rst` |
| `wr_en` | in | write request this cycle |
| `is_null` | in | Null block — does not enter |
| `is_retry` | in | Retry block — does not enter |
| `wr_flit[159:0]` | in | flit written at `wrp` |
| `send_size[7:0]` | in | send needs `num_free >= send_size` |
| `ack_rel` | in | ACK release this cycle |
| `rel_size[7:0]` | in | release count (wraps 8-bit ptrs) |
| `rd_ptr_i[7:0]` | in | combo read address |
| `rd_flit[159:0]` | out | combo `mem[rd_ptr_i]` |
| `wr_ptr[7:0]` | out | combo `wrp` |
| `tail_ptr[7:0]` | out | combo `tail` |
| `rcv_ptr[7:0]` | out | combo `rcv` |
| `num_free[8:0]` | out | combo `freeb` (init 256) |
| `proto_err` | out | sticky `freeb + rel_size > 256` |
| `can_send` | out | combo `freeb >= {1'b0, send_size}` |

No parameters. This is **not** PCS tx / rx tops (later
stages) and **not** remaining DLL wraps (`retry_req_sm`,
`vibe_dll_tx`, dll top). Stage-1..24 leaves are left
intact. Does **not** instantiate children.
`include "vibe_ub_params.vh"` (stock; `VIBE_RETRY_BUF_DEPTH`
is 256).

## Flow

One always block plus combo ptr / free / read. State:
`wrp[7:0]`, `tail[7:0]`, `rcv[7:0]`, `freeb[8:0]` (init
256), `proto_err`, `mem[0:255]` (160b; not cleared on
reset).

`!rst_n` → pointers 0, `freeb=256`, `proto_err=0`.
`port_rst || !link_up` → same pointer / free clear;
`proto_err` stays (stock sticky). Else write
`wr_en && !is_null && !is_retry && can_send` →
`mem[wrp]<=wr_flit`, `wrp+1`, `freeb-1`. Release
`ack_rel`: if `freeb+rel_size>256` set `proto_err`; else
`freeb+=rel_size`, `tail+=rel_size`, `rcv+=rel_size`.
Same-cycle write + legal release: last NBA to `freeb`
wins (release), matching stock.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_dll_retry_buf
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, depth 256,
Null/Retry skip, sticky proto_err on over-release, and
combo `can_send` / `rd_flit` stay. Ports / behavior
match stock (header-only vs stock). Official `.vlt` is
not expanded.
