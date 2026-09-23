# vibe_fecn_mark

Fabric FECN mark (AS-0.1 §8). Decision I
stage-27 pyCircuit leaf. Re-homes pre-Decision I stock RTL
(first fabric helper under `pycircuit/fabric/`, after DLL
stage-20..26) under the pycircuit → rtl flow. Combo: if
CCI.Mode is `3'b100` or `3'b010` and local congestion
(`voq_occ >= FECN_WM`, default 24) is worse than the packet
FECN, rewrite FECN and LoC; else pass-through. Not CAQM.
Self-contained (no child instances). First fabric leaf after
`vibe_bcrc` / `vibe_dll_credit` / `vibe_dll_sm` /
`vibe_dll_rx` / `vibe_dll_retry_ack_sm` /
`vibe_dll_retry_buf` / `vibe_dll_retry_req_sm`.
**No SPEC / CR-B semantic change.**

| | |
|---|---|
| Python | `pycircuit/fabric/vibe_fecn_mark.py` |
| Product SV | `rtl/fabric/vibe_fecn_mark.sv` |
| Instantiator | `vibe_fabric` (`u_fecn`); unit TC (`tc_fecn_mark`) |
| SPEC / CR-B | Unchanged. Internal leaf; no clocks/resets |

## Ports (product)

Same as tip `c33bb143` / freeze `302ac943`. Combo. No clock.
No ready.

| Port | Dir | Notes |
|------|-----|--------|
| `cci_in[15:0]` | in | packet CCI (`Mode[15:13]`, FECN `[1:0]`) |
| `voq_occ[5:0]` | in | local VOQ occupancy (VL0 in `vibe_fabric`) |
| `cci_out[15:0]` | out | rewrite or pass-through |
| `marked` | out | combo `markable_mode && worse` |

Parameter `FECN_WM` default 24 (3/4 of VOQ 32). This is
**not** PCS tx / rx tops (later stages) and **not**
remaining DLL wraps (`vibe_dll_tx`, dll top). Stage-1..26
leaves are left intact. Does **not** instantiate children.
Not CAQM.

## Flow

Combo wires only. `mode = cci_in[15:13]`,
`fecn = cci_in[1:0]`, `cong = (voq_occ >= FECN_WM[5:0])`,
`markable_mode = (mode==3'b100) || (mode==3'b010)`.
`2'b00` unmarkable; `2'b10` none; `2'b01` light;
`2'b11` severe. `local_lvl = cong ? 2'b11 : 2'b10`.
`worse = cong && (fecn!=2'b00) && (local_lvl>fecn)`.
`marked = markable_mode && worse`. When marked,
`cci_out = {mode, 3'b000, LoC=0, cci_in[8:2], local_lvl}`;
else `cci_out = cci_in`.

`ovf_l` (F1) is **not** in this module.

## Regenerate

```bash
make -C pycircuit vibe_fecn_mark
```

Details and toolchain pin: [`pycircuit/README.md`](../../pycircuit/README.md).
Landed SV is hand-finished so the combo FECN / LoC rewrite
stays. Ports / behavior match stock (header-only vs stock).
Official `.vlt` is not expanded.
