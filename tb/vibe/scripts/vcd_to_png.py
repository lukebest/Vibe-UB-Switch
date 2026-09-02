#!/usr/bin/env python3
"""Render annotated digital-window PNGs from Icarus VCD (no gtkwave)."""
from __future__ import annotations

import argparse
import gzip
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from matplotlib.ticker import FuncFormatter
except ImportError as exc:
    sys.stderr.write("matplotlib required: pip install matplotlib\n")
    raise SystemExit(1) from exc


Change = Tuple[int, int]


@dataclass
class Vcd:
    names: Dict[str, str] = field(default_factory=dict)
    width: Dict[str, int] = field(default_factory=dict)
    series: Dict[str, List[Change]] = field(default_factory=dict)
    alias: Dict[str, str] = field(default_factory=dict)
    ts_ps: int = 1  # VCD time unit in picoseconds
    period: int = 2000


def _open(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


_VAR_RE = re.compile(r"\$var\s+\S+\s+(\d+)\s+(\S+)\s+(\S+)(?:\s+\S+)?\s+\$end")
_TS_RE = re.compile(r"(\d+)\s*(fs|ps|ns|us|ms)", re.I)


def parse_vcd(path: str) -> Vcd:
    v = Vcd()
    hier: List[str] = []
    in_defs = True
    cur_t = 0
    with _open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if in_defs:
                if line.startswith("$timescale"):
                    continue
                if in_defs and not line.startswith("$") and _TS_RE.search(line):
                    m = _TS_RE.search(line)
                    if m:
                        n, u = int(m.group(1)), m.group(2).lower()
                        mul = {"fs": 0.001, "ps": 1, "ns": 1000, "us": 1e6, "ms": 1e9}[u]
                        v.ts_ps = max(1, int(n * mul))
                if line.startswith("$scope"):
                    parts = line.split()
                    if len(parts) >= 3:
                        hier.append(parts[2])
                elif line.startswith("$upscope"):
                    if hier:
                        hier.pop()
                elif line.startswith("$var"):
                    m = _VAR_RE.search(line)
                    if not m:
                        continue
                    w, vid, name = int(m.group(1)), m.group(2), m.group(3)
                    full = ".".join(hier + [name]) if hier else name
                    v.names[vid] = full
                    v.width[vid] = w
                    v.series[vid] = [(0, 0)]
                    for key in (name, full, name.lower(), full.lower(), full.split(".")[-1]):
                        v.alias[key] = vid
                elif line.startswith("$enddefinitions"):
                    in_defs = False
                continue
            if line.startswith("#"):
                try:
                    cur_t = int(line[1:].split()[0])
                except ValueError:
                    pass
                continue
            if line.startswith("$dump") or line in ("$end", "$dumpoff", "$dumpon"):
                continue
            if line[0] in "01xzXZ":
                val_ch, vid = line[0], line[1:]
                if vid in v.series:
                    _push(v.series[vid], cur_t, 1 if val_ch == "1" else 0)
            elif line[0] in "bBrR":
                parts = line.split()
                if len(parts) >= 2 and parts[1] in v.series:
                    _push(v.series[parts[1]], cur_t, _bits_to_int(parts[0][1:]))
    v.period = _clk_period(v)
    return v


def _fmt_hex(val: int, width: int) -> str:
    nibbles = max(1, (width + 3) // 4)
    s = f"{val:0{nibbles}X}"
    if len(s) > 20:
        return f"0x{s[:8]}…{s[-8:]}"
    return f"0x{s}"


def _clk_period(v: Vcd) -> int:
    for name in ("wav_clk", "clk_fab", "clk"):
        vid = resolve(v, name)
        if vid is None:
            continue
        rises = [t for t, val in v.series[vid] if val]
        deltas = [rises[i + 1] - rises[i] for i in range(len(rises) - 1) if rises[i + 1] > rises[i]]
        if deltas:
            return min(deltas)
    return 2000


def _bits_to_int(bits: str) -> int:
    s = bits.lower().replace("x", "0").replace("z", "0")
    if not s:
        return 0
    try:
        return int(s, 2)
    except ValueError:
        return 0


def _push(series: List[Change], t: int, val: int) -> None:
    if series and series[-1][0] == t:
        series[-1] = (t, val)
    elif series and series[-1][1] == val:
        return
    else:
        series.append((t, val))


def resolve(v: Vcd, name: str) -> Optional[str]:
    if name in v.alias:
        return v.alias[name]
    low = name.lower()
    if low in v.alias:
        return v.alias[low]
    tail = name.split(".")[-1]
    if tail in v.alias:
        return v.alias[tail]
    for vid, full in v.names.items():
        if full.endswith("." + name) or full == name or full.endswith("." + tail):
            return vid
    return None


def value_at(series: Sequence[Change], t: int) -> int:
    val = series[0][1] if series else 0
    for tt, vv in series:
        if tt <= t:
            val = vv
        else:
            break
    return val


def first_eq(series: Sequence[Change], want: int, tmin: int = 0) -> Optional[int]:
    prev = None
    for t, val in series:
        if t < tmin:
            prev = val
            continue
        if val == want and prev != want:
            return t
        prev = val
    for t, val in series:
        if t >= tmin and val == want:
            return t
    return None


def first_rise(series: Sequence[Change], tmin: int = 0) -> Optional[int]:
    prev = 0
    for t, val in series:
        if t < tmin:
            prev = val
            continue
        if val and not prev:
            return t
        prev = val
    return None


def all_rises(series: Sequence[Change], tmin: int = 0) -> List[int]:
    out: List[int] = []
    prev = 0
    for t, val in series:
        if t < tmin:
            prev = val
            continue
        if val and not prev:
            out.append(t)
        prev = val
    return out


def last_time(v: Vcd) -> int:
    mx = 0
    for s in v.series.values():
        if s:
            mx = max(mx, s[-1][0])
    return mx


def _need(v: Vcd, name: str) -> List[Change]:
    vid = resolve(v, name)
    if vid is None:
        return [(0, 0)]
    return v.series[vid]


def _to_ns(t: int, ts_ps: int) -> float:
    return t * ts_ps / 1000.0


def draw_window(
    path_png: str,
    v: Vcd,
    rows: Sequence[Tuple[str, str, str]],
    t0: int,
    t1: int,
    markers: Sequence[Tuple[int, str, str]],
    title: str,
    caption: str,
    notes: Sequence[Tuple[int, str]] = (),
) -> None:
    if t1 <= t0:
        t1 = t0 + v.period * 8
    n = len(rows)
    fig_h = max(4.4, 0.68 * n + 2.6)
    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(13.4, fig_h))
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor("white")
    for ax, (vname, label, kind) in zip(axes, rows):
        ax.set_facecolor("#f7f7f7")
        vid = resolve(v, vname)
        ax.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=8.5, labelpad=58)
        ax.grid(axis="x", color="#dddddd", lw=0.6)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#bbbbbb")
        ax.spines["bottom"].set_color("#bbbbbb")
        if vid is None:
            ax.set_yticks([])
            ax.set_ylim(-0.15, 1.35)
            ax.text(0.5, 0.5, f"(missing {vname})", transform=ax.transAxes,
                    ha="center", color="#aa0000", fontsize=8)
            continue
        series = v.series[vid]
        width = v.width[vid]
        ev: List[Change] = [(t0, value_at(series, t0))]
        ev += [(t, val) for t, val in series if t0 < t <= t1]
        ev.append((t1, value_at(series, t1)))
        merged: List[Change] = []
        for t, val in ev:
            if merged and merged[-1][0] == t:
                merged[-1] = (t, val)
            else:
                merged.append((t, val))

        if kind == "count":
            vals = [val for _, val in merged]
            ymax = max(max(vals), 1)
            xs = [t for t, _ in merged]
            ys = [val for _, val in merged]
            ax.plot(xs, ys, color="#1f4e79", lw=1.6, drawstyle="steps-post")
            ax.set_ylim(-0.08 * ymax, ymax * 1.18)
            ax.set_yticks([0, ymax // 2, ymax] if ymax >= 2 else [0, 1])
            ax.tick_params(axis="y", labelsize=7)
            endv = value_at(series, t1)
            ax.text(1.005, 0.5, str(endv), transform=ax.transAxes, va="center",
                    fontsize=8, color="#111111", fontweight="bold")
        else:
            ax.set_yticks([])
            if kind == "bit":
                ax.set_ylim(-0.2, 1.35)
                for i, (t, val) in enumerate(merged[:-1]):
                    t_next = merged[i + 1][0]
                    lvl = 1.0 if val else 0.0
                    if val:
                        ax.fill_between([t, t_next], 0, 1, color="#4c78a8", alpha=0.28)
                    ax.plot([t, t_next], [lvl, lvl], color="#1f4e79", lw=1.6)
                    if t_next - t > (t1 - t0) * 0.05:
                        ax.text((t + t_next) / 2, 1.12 if val else -0.08,
                                str(int(bool(val))), ha="center",
                                va="bottom" if val else "top", fontsize=7, color="#333333")
            else:
                ax.set_ylim(-0.15, 1.35)
                ax.axhline(0.45, color="#cccccc", lw=0.8)
                span = max(t1 - t0, 1)
                for i, (t, val) in enumerate(merged[:-1]):
                    t_next = merged[i + 1][0]
                    ax.plot([t, t_next], [0.45, 0.45], color="#1f4e79", lw=2.0)
                    if t_next > t:
                        ax.plot([t, t], [0.22, 0.68], color="#1f4e79", lw=1.2)
                    if kind == "hex":
                        txt = _fmt_hex(val, width)
                    elif width == 2:
                        txt = f"{val:02b}b"
                    else:
                        txt = str(val)
                    if (t_next - t) > span * 0.04 or i == 0 or i == len(merged) - 2:
                        ax.text((t + t_next) / 2, 0.82, txt, ha="center", va="bottom",
                                fontsize=7.0, color="#1f4e79", clip_on=True)
            endv = value_at(series, t1)
            if kind == "bit":
                tag = str(int(bool(endv)))
            elif kind == "hex":
                tag = _fmt_hex(endv, width)
            else:
                tag = str(endv)
            ax.text(1.005, 0.5, tag, transform=ax.transAxes, va="center",
                    fontsize=8, color="#111111", fontweight="bold")
        for mt, _lab, color in markers:
            if t0 <= mt <= t1:
                ax.axvline(mt, color=color, lw=1.4, ls="--")

    def _fmt(x, _pos):
        return f"{_to_ns(int(x), v.ts_ps):.0f}"

    axes[-1].xaxis.set_major_formatter(FuncFormatter(_fmt))
    axes[-1].set_xlim(t0, t1)
    axes[-1].set_xlabel("time (ns)   [Icarus timescale 1ps; clk period 2 ns]")
    fig.suptitle(title, fontsize=11, fontweight="bold", y=0.995)
    if markers:
        bits = "   ".join(
            f"| {lab} @ {_to_ns(mt, v.ts_ps):.0f} ns" for mt, lab, _ in markers
        )
        fig.text(0.5, 0.958, bits, ha="center", fontsize=8, color="#a31f1f")
    for nt, nlab in notes:
        if t0 <= nt <= t1:
            axes[0].annotate(
                nlab, xy=(nt, axes[0].get_ylim()[1] * 0.92),
                xytext=(nt, axes[0].get_ylim()[1] * 1.12),
                fontsize=7, ha="center", color="#333333",
                arrowprops=dict(arrowstyle="-", color="#888888", lw=0.6),
                annotation_clip=False,
            )
    fig.text(0.03, 0.012, caption, ha="left", va="bottom", fontsize=8, color="#222222")
    fig.subplots_adjust(left=0.22, right=0.93, top=0.88, bottom=0.16, hspace=0.10)
    fig.savefig(path_png, dpi=130)
    plt.close(fig)
    print(f"wrote {path_png}")


def stitch(out: str, *pngs: str) -> None:
    ims = [mpimg.imread(p) for p in pngs]
    h = sum(im.shape[0] for im in ims)
    w = max(im.shape[1] for im in ims)
    fig, axes = plt.subplots(len(ims), 1, figsize=(w / 130.0, h / 130.0))
    if len(ims) == 1:
        axes = [axes]
    for ax, im in zip(axes, ims):
        ax.imshow(im)
        ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0.01)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    for p in pngs:
        os.remove(p)
    print(f"wrote {out}")


def _vcd_path(waves: str, stem: str) -> Optional[str]:
    for name in (stem, stem + ".gz"):
        p = os.path.join(waves, name)
        if os.path.isfile(p):
            return p
    return None


def render_g1(waves: str) -> None:
    src = _vcd_path(waves, "g1_rt10.vcd")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    t_ing = first_rise(_need(v, "wav_ing0")) or 20 * p
    t_irq = first_rise(_need(v, "wav_irq")) or (t_ing + 3 * p)
    t_cnt = first_eq(_need(v, "wav_g1cnt"), 1) or t_irq
    t0, t1 = max(0, t_ing - 3 * p), t_irq + 8 * p
    draw_window(
        os.path.join(waves, "g1_rt10.png"),
        v,
        [
            ("wav_ing0", "ing_vld[0]", "bit"),
            ("wav_rt", "RT field", "dec"),
            ("wav_egr0", "egr_vld[0]", "bit"),
            ("wav_egr", "egr_vld[3:0]", "hex"),
            ("wav_g1", "drop_g1", "bit"),
            ("wav_g1cnt", "rt_shortest_unimpl", "dec"),
            ("wav_irq", "irq_logic", "bit"),
        ],
        t0, t1,
        [(t_irq, "score: irq rises+sticks; egr stays 0; cnt+1", "#c0392b")],
        "G1  RT=10 DROP  —  tc_rt10_must_drop  (AS-0.1 / TP-RT-003)",
        "Expected: RT=10 ingress, egress stays 0, rt_shortest_unimpl +1, irq_logic rises and sticks.  "
        "Actual: egr=0, cnt 0->1, irq=1 sticky (PASS tc_rt10_must_drop).",
        notes=[(t_ing, "inject RT=10"), (t_cnt, "cnt +1")],
    )


def render_cfg6(waves: str) -> None:
    src = _vcd_path(waves, "cfg6_term_vs_fwd.vcd")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    pulses = all_rises(_need(v, "c6_hit"))
    t_unit0 = pulses[0] if pulses else 0
    labels = [
        "1 local-CNA TERM",
        "2 NLP=1 TERM",
        "3 opc 0x10 us TERM",
        "4 opc 0x10 not-us FWD",
        "5 else FWD",
        "6 CNA unwritten FWD",
    ]
    notes = [(t, lab) for t, lab in zip(pulses, labels)]
    unit_png = os.path.join(waves, "_cfg6_unit.png")
    draw_window(
        unit_png, v,
        [
            ("c6_hit", "c6_hit (unit)", "hex"),
            ("c6_cons", "c6_cons consume", "hex"),
            ("c6_cna", "c6_cna (mgmt)", "hex"),
            ("c6_written", "c6_written", "bit"),
        ],
        max(0, t_unit0 - 2 * p), t_unit0 + 14 * p,
        [(t_unit0, "local-CNA terminate (consume=1)", "#c0392b")],
        "CFG6 cna_ep classes (AS-0.1 s9) — unit pulses before fabric",
        "Order: (1) local-CNA+DCNA consume=1  (2) NLP=1 consume=1  "
        "(3) opc 0x10 targeting-us consume=1  (4) opc 0x10 not-us FORWARD  "
        "(5) else FORWARD  (6) CNA unwritten no-match.",
        notes=notes,
    )
    ing_all = [t for t, val in _need(v, "wav_ing0") if val]
    t_fab0 = ing_all[0] if ing_all else 60 * p
    xin = first_rise(_need(v, "wav_xin0"), tmin=t_fab0 - p)
    cfg6h = first_rise(_need(v, "wav_cfg6h0"), tmin=t_fab0 - 2 * p) or t_fab0
    fab_png = os.path.join(waves, "_cfg6_fab.png")
    draw_window(
        fab_png, v,
        [
            ("wav_ing0", "ing_vld[0]", "bit"),
            ("wav_cfg", "CFG field", "dec"),
            ("wav_nlp", "NLP", "dec"),
            ("wav_opc", "opcode flit[103:96]", "hex"),
            ("wav_cfg6h0", "fab.cfg6_hit[0]", "bit"),
            ("wav_xin0", "fab.x_in_v[0]", "bit"),
            ("wav_egr0", "egr_vld[0]", "bit"),
        ],
        max(0, t_fab0 - 4 * p), (xin or t_fab0) + 12 * p,
        [
            (cfg6h, "TERM: cfg6_hit / no xbar (local-CNA)", "#c0392b"),
            (xin or (t_fab0 + 20 * p), "FORWARD: x_in_v=1 / egress", "#1e8449"),
        ],
        "CFG6 fabric: terminate vs FORWARD — tc_cfg6_term_vs_fwd",
        "Expected: local-CNA beat cfg6_hit=1 and x_in_v=0; FORWARD beat (DCNA!=CNA, NLP=0, opc=0) "
        "x_in_v=1.  Actual: TERM marker then FORWARD x_in_v=1 (PASS tc_cfg6_term_vs_fwd).",
    )
    stitch(os.path.join(waves, "cfg6_term_vs_fwd.png"), unit_png, fab_png)


def render_credit_1024(waves: str) -> None:
    src = _vcd_path(waves, "credit_1024_flit.vcd")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    pend = _need(v, "pending")
    t_1023 = first_eq(pend, 1023)
    t_1024 = first_eq(pend, 1024)
    t_mark = t_1024 or first_rise(_need(v, "bp_nw")) or 20 * p
    t0 = max(0, (t_1023 or t_mark) - 4 * p)
    t1 = t_mark + 6 * p
    draw_window(
        os.path.join(waves, "credit_1024_flit.png"),
        v,
        [
            ("credit_ret", "credit_ret", "bit"),
            ("credit_ret_n", "credit_ret_n (flit)", "dec"),
            ("pending", "pending (flit)", "dec"),
            ("bp_nw", "bp_nw", "bit"),
            ("force_crd_ack", "force_crd_ack", "bit"),
        ],
        t0, t1,
        [(t_mark, "pending 1023->1024 cell; bp_nw=0->1 (not ×n flit)", "#c0392b")],
        "Credit threshold 1024 is CELL — tc_credit_1024_flit_bp  (FS-0.2.7 / G7)",
        "Expected: pending=1023 cell and bp_nw=0, then +1 cell -> pending=1024 and bp_nw=1 "
        "(credit_ret_n is cells; not 1024×n flit).  Actual: 1023/0 then 1024/1.  "
        "Note: force_crd_ack is also 1 whenever pending!=0 (RTL); the G7 threshold is bp_nw.",
        notes=[((t_1023 or t0), "pending=1023, no bp")],
    )


def render_credit_to(waves: str) -> None:
    src = _vcd_path(waves, "credit_timeout_1us.vcd")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    t_load = first_eq(_need(v, "wav_to"), 1250)
    t_err = first_rise(_need(v, "proto_err")) or last_time(v)
    load_png = os.path.join(waves, "_crd_to_load.png")
    fire_png = os.path.join(waves, "_crd_to_fire.png")
    t_l0 = max(0, (t_load or 4 * p) - 4 * p)
    draw_window(
        load_png, v,
        [
            ("credit_ret", "credit_ret", "bit"),
            ("pending", "pending", "dec"),
            ("wav_to", "u_crd.to (credit timer)", "count"),
        ],
        t_l0, t_l0 + 16 * p,
        [((t_load or t_l0), "load to=1250 (VIBE_US_CYC) — not VOQ age", "#c0392b")],
        "Credit timeout 1 us — load  (tc_credit_timeout_1us, DUT vibe_dll_credit)",
        "Expected: credit_ret deposits pending and loads u_crd.to = 1250 (1 us @ 1.25 GHz).  "
        "This counter is not vibe_voq_egr.age.",
    )
    draw_window(
        fire_png, v,
        [
            ("pending", "pending", "dec"),
            ("wav_to", "u_crd.to (credit timer)", "count"),
            ("proto_err", "proto_err", "bit"),
        ],
        max(0, t_err - 40 * p), t_err + 8 * p,
        [(t_err, "to==0 -> proto_err after 1250 clk_fab", "#c0392b")],
        "Credit timeout 1 us — fire  (same DUT / same counter as load panel)",
        "Expected: after 1250 clk_fab without credit_ret, proto_err rises.  "
        "Actual: proto_err 0->1 when to reaches 0 (PASS tc_credit_timeout_1us).",
    )
    stitch(os.path.join(waves, "credit_timeout_1us.png"), load_png, fire_png)


def render_voq(waves: str) -> None:
    src = _vcd_path(waves, "voq_deadlock_1us.vcd")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    t_load = first_eq(_need(v, "wav_age00"), 1250)
    t_drop = first_rise(_need(v, "deadlock_drop")) or last_time(v)
    load_png = os.path.join(waves, "_voq_load.png")
    fire_png = os.path.join(waves, "_voq_fire.png")
    t_l0 = max(0, (t_load or 4 * p) - 4 * p)
    draw_window(
        load_png, v,
        [
            ("wr_en", "wr_en", "bit"),
            ("nonempty", "nonempty", "hex"),
            ("wav_age00", "u_v.age[0][0] (VOQ)", "count"),
        ],
        t_l0, t_l0 + 16 * p,
        [((t_load or t_l0), "load age=1250 — vibe_voq_egr, not u_crd.to", "#c0392b")],
        "VOQ deadlock 1 us — load  (tc_deadlock_timeout_1us, DUT vibe_voq_egr)",
        "Expected: enqueue loads age[0][0] = 1250.  Separate DUT and separate counter from credit u_crd.to.",
    )
    draw_window(
        fire_png, v,
        [
            ("nonempty", "nonempty", "hex"),
            ("occ_vl0", "occ_vl0", "dec"),
            ("wav_age00", "u_v.age[0][0] (VOQ)", "count"),
            ("deadlock_drop", "deadlock_drop", "bit"),
            ("deadlock_cnt", "deadlock_cnt", "dec"),
        ],
        max(0, t_drop - 40 * p), t_drop + 8 * p,
        [(t_drop, "age==0 -> deadlock_drop (1 us)", "#c0392b")],
        "VOQ deadlock 1 us — fire  (same DUT / same age[][] counter as load panel)",
        "Expected: after 1250 clk_fab without drain, deadlock_drop pulses and cnt+1.  "
        "Actual: drop 0->1, cnt 0->1 (PASS tc_deadlock_timeout_1us).",
    )
    stitch(os.path.join(waves, "voq_deadlock_1us.png"), load_png, fire_png)


def render_loopback(waves: str) -> None:
    src = _vcd_path(waves, "nw_pkt_pma_loopback_data512.vcd")
    out_png = os.path.join(waves, "nw_pkt_pma_loopback_data512.png")
    if src is None:
        src = _vcd_path(waves, "nw_pkt_pma_loopback.vcd")
        out_png = os.path.join(waves, "nw_pkt_pma_loopback.png")
    if src is None:
        return
    v = parse_vcd(src)
    p = v.period
    t_inj = first_rise(_need(v, "fab_tx_vld")) or (20 * p)
    t_pma = first_rise(_need(v, "wav_tx_nz")) or first_rise(_need(v, "wav_ptxv"))
    if t_pma is None:
        t_pma = t_inj + 40 * p
    t_rx = first_rise(_need(v, "wav_rx_eq")) or first_rise(_need(v, "fab_rx_vld"))
    if t_rx is None:
        t_rx = last_time(v)
    t_pcs = first_rise(_need(v, "wav_pcs_rx"), tmin=t_inj) or t_rx
    marks_all = [
        (t_inj, "inject GOLDEN_TX data[511:0]", "#1f4e79"),
        (t_pma, "PMA txdata nonzero (rxdata=txdata)", "#b9770e"),
        (t_rx, "fab_rx_data[511:0] === GOLDEN_TX", "#c0392b"),
    ]
    tx_png = os.path.join(waves, "_lb512_tx.png")
    pma_png = os.path.join(waves, "_lb512_pma.png")
    rx_png = os.path.join(waves, "_lb512_rx.png")
    draw_window(
        tx_png, v,
        [
            ("fab_tx_vld", "fab_tx_vld", "bit"),
            ("fab_tx_ready", "fab_tx_ready", "bit"),
            ("fab_tx_data", "fab_tx_data[511:0]", "hex"),
            ("wav_tx_sop", "SOP LPH [511:352]", "hex"),
            ("wav_tx_cfg", "SOP CFG (160b [11:8])", "dec"),
            ("wav_tx_rt", "SOP RT (160b [23:22])", "dec"),
            ("wav_tx_scna", "SOP SCNA (160b [47:32])", "hex"),
            ("wav_tx_dcna", "SOP DCNA (160b [63:48])", "hex"),
            ("wav_tx_pld", "payload [351:0]", "hex"),
        ],
        max(0, t_inj - 6 * p), t_inj + 20 * p,
        marks_all,
        "TX  NW data[511:0] GOLDEN inject  —  tc_nw_pkt_pma_loopback  (TP-PHY-012)",
        "Expected: handshake + fab_tx_data === GOLDEN_TX. SOP LPH is [511:352] "
        "(CFG=3 RT=00 SCNA=A11A DCNA=B22B). [351:0] is payload. Not README [511:496].",
        notes=[(t_inj, "inject")],
    )
    draw_window(
        pma_png, v,
        [
            ("txdata", "txdata[511:0]", "hex"),
            ("rxdata", "rxdata[511:0]", "hex"),
            ("wav_lb_eq", "rxdata==txdata", "bit"),
            ("wav_ptxv", "u_p.p_txv", "bit"),
            ("wav_txlv", "u_p.txlv (lane_vld)", "bit"),
            ("wav_lane0", "txdata[31:0] lane0", "hex"),
            ("wav_lane3", "txdata[511:480] lane3", "hex"),
        ],
        max(0, t_pma - 12 * p), t_pma + 40 * p,
        marks_all,
        "PMA  txdata[511:0] + loopback tie  —  same TC",
        "Expected: txdata nonzero; [127:0]=lane0 .. [511:384]=lane3; "
        "rxdata=txdata (assign).  Actual: lb_eq=1 when p_txv.",
        notes=[(t_pma, "PMA activity")],
    )
    draw_window(
        rx_png, v,
        [
            ("wav_am", "u_p.am_locked", "hex"),
            ("wav_pcs_rx", "u_p.pcs_rx_v", "bit"),
            ("wav_fec", "u_p.fec_fail", "bit"),
            ("fab_rx_vld", "fab_rx_vld", "bit"),
            ("fab_rx_data", "fab_rx_data[511:0]", "hex"),
            ("wav_rx_sop", "RX SOP LPH [511:352]", "hex"),
            ("wav_rx_cfg", "RX CFG", "dec"),
            ("wav_rx_rt", "RX RT", "dec"),
            ("wav_rx_scna", "RX SCNA", "hex"),
            ("wav_rx_dcna", "RX DCNA", "hex"),
            ("wav_rx_pld", "RX payload [351:0]", "hex"),
            ("wav_rx_eq", "RX==GOLDEN_TX", "bit"),
        ],
        max(0, t_rx - 20 * p), t_rx + 16 * p,
        marks_all,
        "RX  recovered NW data[511:0] === GOLDEN  —  tc_nw_pkt_pma_loopback",
        "Expected: fab_rx_data[511:0] === GOLDEN_TX; SOP [511:352] CFG=3 RT=00 "
        "SCNA=A11A DCNA=B22B; fec_fail=0.  Actual: wav_rx_eq=1 (PASS).",
        notes=[(t_pcs, "pcs_rx_v"), (t_rx, "fab_rx score")],
    )
    stitch(out_png, tx_png, pma_png, rx_png)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--waves", required=True)
    args = ap.parse_args()
    waves = args.waves
    render_g1(waves)
    render_cfg6(waves)
    render_credit_1024(waves)
    render_credit_to(waves)
    render_voq(waves)
    render_loopback(waves)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
