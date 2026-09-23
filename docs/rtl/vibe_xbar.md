# vibe_xbar

Fabric 4-port crossbar (AS-0.1 §8). Decision I
stage-33 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(seventh fabric helper under `pycircuit/fabric/`, after
`vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel` / `vibe_voq_egr` / `vibe_saf_ing`) under
the pycircuit → rtl flow. Output queued. Ingress RR on
conflict. One full packet per grant. Down ports get no
data DLLDP. Mgmt bypass does not enter xbar.
Self-contained (no child instances). Seventh fabric leaf
after `vibe_fecn_mark` / `vibe_vl_rr` / `vibe_route_lu` /
`vibe_port_sel` / `vibe_voq_egr` / `vibe_saf_ing`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_xbar.py` |
| Product SV | `rtl/fabric/vibe_xbar.sv` |
| Instantiator | `vibe_fabric` (`u_xbar`); unit TC (`tc_xbar_unit`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `782f2181` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; clears `lock` / `locked` / `rr` |
| `status_up[3:0]` | in | up ports may grant; down ports emit no data |
| `in_data[511:0][0:3]` | in | ingress NW beat per port |
| `in_vld[3:0]` | in | beat valid this cycle |
| `in_sop[3:0]` | in | start of packet |
| `in_eop[3:0]` | in | end of packet |
| `in_dst[1:0][0:3]` | in | requested egress |
| `in_ready[3:0]` | out | accept (`cand_vld && out_ready` at winner) |
| `out_data[511:0][0:3]` | out | candidate grant data (independent of `out_ready`) |
| `out_vld[3:0]` | out | accept valid (`cand_vld && out_ready`) |
| `out_sop[3:0]` | out | candidate SOP |
| `out_eop[3:0]` | out | candidate EOP |
| `out_ready[3:0]` | in | egress accept (VOQ `wr_ready`) |

This is **not** PCS tx / rx tops (later stages), **not**
remaining DLL wraps (`vibe_dll_tx`, dll top), and **not**
`vibe_fabric` top. Stage-1..32 leaves are left intact.
Does **not** instantiate children.

## Flow

Two combo always blocks plus one async-low sequential.
Candidate grant is independent of `out_ready` so VOQ
`wr_vl` (from `out_data` / `out_sop`) cannot combo-loop
with `wr_ready` (UNOPTFLAT `xb_r`). Accept (`out_vld` /
`in_ready`) still requires `out_ready` — same fire.

State: `lock[1:0][0:3]`, `locked[0:3]`, `rr[1:0][0:3]`.
Combo temps: `req[3:0]`, `win[1:0]`, `cand_vld[3:0]`,
`cand_src[1:0][0:3]`. Full combo defaults each iteration
so Verilator does not infer LATCH on `req` / `win`.
Arbitration is unchanged — unlocked ports still rebuild
`req` and start `win` at `rr[e]`.

Per egress `e`: if `!status_up[e]`, no data. Else if
`locked[e]` and `in_vld[lock[e]] && in_dst[lock[e]]==e`,
hold grant. Else RR from `rr[e]` among
`in_vld && in_dst==e`. Then if `cand_vld[e] &&
out_ready[e]`: `out_vld[e]=1`, `in_ready[cand_src[e]]=1`.

`!rst_n` → `lock` / `locked` / `rr` = 0. Else on
`out_vld && out_ready`: lock winner until EOP; SOP
starts lock; EOP clears `locked` and
`rr <= lock+1`. One full packet per grant.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_xbar
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`, unpacked
array ports, candidate/accept split, ingress RR, and
one-packet lock stay. Ports / behavior match stock
(header-only vs stock). Official `.vlt` is not expanded.
