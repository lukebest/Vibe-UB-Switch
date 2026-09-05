# reports/signoff/

Keepers-only until OpenSTA (or later DRC/LVS) **actually runs**.
Do not hand-write WNS/TNS.

路径 **B** 已选定（2026-09-05，Luke via PM）：本目录继续 keepers-only，本闸不追 Sky130 顶层 map / OpenSTA。见 [`PLAN-2026-09-04.md`](PLAN-2026-09-04.md) **Decision / 已选定**。

下一闸提案（不是签核通过 / not a passed signoff）：
[`PLAN-2026-09-04.md`](PLAN-2026-09-04.md)

工具若跑过，应出现：`sta.log`、`sta_wns_tns.rpt`、`sta_checks.rpt`；
未跑 DRC/LVS 时为 `drc.rpt` / `lvs.rpt` 的 `STATUS: not_run`。
见 [`../README.md`](../README.md)。
