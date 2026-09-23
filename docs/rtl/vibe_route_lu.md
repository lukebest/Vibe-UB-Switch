# vibe_route_lu

Fabric CFG0_ROUTE_TABLE lookup (AS-0.1 §2/§8 +
FS-0.2.3 G1). Decision I stage-29 pyCircuit leaf.
Re-homes pre-Decision I stock RTL (third fabric helper
under `pycircuit/fabric/`, after `vibe_fecn_mark` /
`vibe_vl_rr`) under the pycircuit → rtl flow. dest →
4-bit egress bitmap. RT=10/11: DROP (pulse `drop_g1`).
No Dijkstra, no treat-as-RT=00, no RT rewrite. Fabric
saturates `rt_shortest_unimpl` and `irq_agg` sticks
`irq_logic` (not this leaf). Parameter `DEPTH=256`.
Self-contained (no child instances). Third fabric leaf
after `vibe_fecn_mark` / `vibe_vl_rr`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_route_lu.py` |
| Product SV | `rtl/fabric/vibe_route_lu.sv` |
| Instantiator | `vibe_fabric` (`u_rt`, `g_rt.u_rti`); unit TC (`tc_route_lu`) |
| SPEC / CR-B | Unchanged. Internal leaf; clocks/resets exempt |

## Ports (product)

Same as tip `4b463581` / freeze `302ac943`. Reset stays
**async active-low** (`or negedge rst_n`).

| Port | Dir | Notes |
|------|-----|--------|
| `clk` | in | fabric digital clock (`clk_fab`) |
| `rst_n` | in | dest-domain async active-low; with `device_rst` clears table + outputs |
| `device_rst` | in | OR'd into the reset clause (`!rst_n \|\| device_rst`) |
| `wr_en` | in | write `wr_data` into `tbl[wr_idx[7:0]]` |
| `wr_idx[15:0]` | in | table write index (low 8 bits) |
| `wr_data[31:0]` | in | table write data; lookup uses `[3:0]` |
| `dest[15:0]` | in | lookup dest (low 8 bits) |
| `rt[1:0]` | in | routing type; `2'b10` / `2'b11` drop |
| `lu_vld` | in | lookup valid this cycle |
| `bitmap[3:0]` | out | 4-bit egress bitmap (0 on drop / reset) |
| `drop_g1` | out | 1-cycle pulse when `lu_vld` and RT=10/11 |

Parameter `DEPTH` default 256. This is **not** PCS tx /
rx tops (later stages), **not** remaining DLL wraps
(`vibe_dll_tx`, dll top), and **not** `vibe_fabric` top.
Stage-1..28 leaves are left intact. Does **not**
instantiate children. No Dijkstra / RT rewrite.

## Flow

One async-low sequential. State: `tbl[0:DEPTH-1]`
(32-bit, init 0), `bitmap[3:0]`, `drop_g1`. Integer `i`
for the reset loop.

`!rst_n || device_rst` → every `tbl[i]=0`, `bitmap=0`,
`drop_g1=0`. Else `drop_g1 <= 0`. On `wr_en`:
`tbl[wr_idx[7:0]] <= wr_data`. On `lu_vld`: if
`rt==2'b10 || rt==2'b11` pulse `drop_g1` and
`bitmap=0`; else `bitmap <= tbl[dest[7:0]][3:0]`.

Count / irq aggregation lives in fabric / `irq_agg`,
not this leaf. `ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_route_lu
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so async-low `rst_n`,
`!rst_n || device_rst` table clear, RT=10/11 drop pulse,
and dest→bitmap lookup stay. Ports / behavior match
stock (header-only vs stock). Official `.vlt` is not
expanded.
