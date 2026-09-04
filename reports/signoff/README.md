# reports/signoff/

Keepers-only until OpenSTA (or later DRC/LVS) **actually runs**.
Do not hand-write WNS/TNS.

下一闸提案（不是签核通过 / not a passed signoff）：
[`PLAN-2026-09-04.md`](PLAN-2026-09-04.md)

工具若跑过，应出现：`sta.log`、`sta_wns_tns.rpt`、`sta_checks.rpt`；
未跑 DRC/LVS 时为 `drc.rpt` / `lvs.rpt` 的 `STATUS: not_run`。
见 [`../README.md`](../README.md)。
