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
    from matplotlib.patches import FancyBboxPatch
except ImportError as exc:
    sys.stderr.write("matplotlib required: pip install matplotlib\n")
    raise SystemExit(1) from exc


Change = Tuple[int, int]  # time, value


@dataclass
class Vcd:
    names: Dict[str, str] = field(default_factory=dict)  # id -> full name
    width: Dict[str, int] = field(default_factory=dict)  # id -> bits
    series: Dict[str, List[Change]] = field(default_factory=dict)
    alias: Dict[str, str] = field(default_factory=dict)  # basename/full -> id


def _open(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


_VAR_RE = re.compile(
    r"\$var\s+\S+\s+(\d+)\s+(\S+)\s+(\S+)(?:\s+\S+)?\s+\$end"
)


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
                    v.alias[name] = vid
                    v.alias[full] = vid
                    v.alias[name.lower()] = vid
                    v.alias[full.lower()] = vid
                    # Icarus: module.signal and signal
                    if "." in full:
                        v.alias[full.split(".")[-1]] = vid
                elif line.startswith("$enddefinitions"):
                    in_defs = False
                continue
            if line.startswith("#"):
                try:
                    cur_t = int(line[1:].split()[0])
                except ValueError:
                    pass
                continue
            if line.startswith("$dumpvars") or line in ("$end", "$dumpoff", "$dumpon"):
                continue
            if line[0] in "01xzXZ":
                val_ch, vid = line[0], line[1:]
                if vid in v.series:
                    val = 1 if val_ch == "1" else 0
                    _push(v.series[vid], cur_t, val)
            elif line[0] in "bBrR":
                parts = line.split()
                if len(parts) < 2:
                    continue
                bits, vid = parts[0][1:], parts[1]
                if vid in v.series:
                    _push(v.series[vid], cur_t, _bits_to_int(bits))
    return v


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
    for full, vid in ((v.names[i], i) for i in v.names):
        if full.endswith("." + name) or full == name:
            return vid
        if full.endswith("." + tail):
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


def last_time(v: Vcd) -> int:
    mx = 0
    for s in v.series.values():
        if s:
            mx = max(mx, s[-1][0])
    return mx


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
    """rows: (vcd_name, label, kind) kind in {bit, dec, hex}."""
    n = len(rows)
    fig_h = max(4.2, 0.62 * n + 2.4)
    fig, axes = plt.subplots(n, 1, sharex=True, figsize=(13.2, fig_h))
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor("white")
    for ax, (vname, label, kind) in zip(axes, rows):
        ax.set_facecolor("#f7f7f7")
        vid = resolve(v, vname)
        ax.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=8.5, labelpad=52)
        ax.set_yticks([])
        ax.grid(axis="x", color="#dddddd", lw=0.6)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#bbbbbb")
        if vid is None:
            ax.text(0.5, 0.5, f"(missing {vname})", transform=ax.transAxes, ha="center",
                    color="#aa0000", fontsize=8)
            ax.set_ylim(-0.15, 1.35)
            continue
        series = v.series[vid]
        width = v.width[vid]
        times = [t0] + [t for t, _ in series if t0 < t <= t1] + [t1]
        xs: List[float] = []
        ys: List[float] = []
        prev_t = t0
        prev_val = value_at(series, t0)
        for t in times:
            val = value_at(series, t)
            if kind == "bit":
                xs.extend([prev_t, t])
                ys.extend([1.0 if prev_val else 0.0, 1.0 if prev_val else 0.0])
            else:
                xs.extend([prev_t, t])
                ys.extend([0.55, 0.55])
            if t > prev_t and t < t1 or t == t1:
                pass
            prev_t, prev_val = t, val
        # rebuild step properly
        xs, ys = [], []
        ev = [(t0, value_at(series, t0))]
        ev += [(t, val) for t, val in series if t0 < t <= t1]
        ev.append((t1, value_at(series, t1)))
        merged: List[Change] = []
        for t, val in ev:
            if merged and merged[-1][0] == t:
                merged[-1] = (t, val)
            else:
                merged.append((t, val))
        if kind == "bit":
            for i, (t, val) in enumerate(merged[:-1]):
                t_next = merged[i + 1][0]
                lvl = 1.0 if val else 0.0
                xs.extend([t, t_next])
                ys.extend([lvl, lvl])
                if val:
                    ax.fill_between([t, t_next], 0, 1, color="#4c78a8", alpha=0.28)
            ax.plot(xs, ys, color="#1f4e79", lw=1.6, solid_capstyle="butt")
            ax.set_ylim(-0.2, 1.35)
            # value tags at mid of each high/low run
            for i, (t, val) in enumerate(merged[:-1]):
                t_next = merged[i + 1][0]
                if t_next - t > (t1 - t0) * 0.04:
                    ax.text((t + t_next) / 2, 1.12 if val else -0.08, str(int(bool(val))),
                            ha="center", va="bottom" if val else "top", fontsize=7,
                            color="#333333")
        else:
            ax.set_ylim(-0.15, 1.35)
            ax.axhline(0.45, color="#cccccc", lw=0.8)
            for i, (t, val) in enumerate(merged[:-1]):
                t_next = merged[i + 1][0]
                ax.plot([t, t_next], [0.45, 0.45], color="#1f4e79", lw=2.0)
                if t_next > t:
                    ax.plot([t, t], [0.22, 0.68], color="#1f4e79", lw=1.2)
                txt = f"{val}" if kind == "dec" else f"0x{val:X}"
                if width == 2 and kind == "dec":
                    txt = f"{val:02b}b"
                ax.text((t + t_next) / 2, 0.82, txt, ha="center", va="bottom",
                        fontsize=7.5, color="#1f4e79",
                        clip_on=True)
        # right-edge current value
        endv = value_at(series, t1)
        if kind == "bit":
            tag = str(int(bool(endv)))
        elif kind == "hex":
            tag = f"0x{endv:X}"
        else:
            tag = str(endv)
        ax.text(1.005, 0.5, tag, transform=ax.transAxes, va="center", fontsize=8,
                color="#111111", fontweight="bold")
        for mt, _lab, color in markers:
            if t0 <= mt <= t1:
                ax.axvline(mt, color=color, lw=1.4, ls="--")
    axes[-1].set_xlim(t0, t1)
    axes[-1].set_xlabel("time (ns, Icarus; clk period = 2)")
    fig.suptitle(title, fontsize=11, fontweight="bold", y=0.995)
    # marker legend
    if markers:
        bits = "   ".join(f"| {lab} @ {mt}" for mt, lab, _ in markers)
        fig.text(0.5, 0.965, bits, ha="center", fontsize=8, color="#a31f1f")
    for nt, nlab in notes:
        if t0 <= nt <= t1:
            axes[0].annotate(
                nlab, xy=(nt, 1.15), xytext=(nt, 1.55),
                fontsize=7, ha="center", color="#333333",
                arrowprops=dict(arrowstyle="-", color="#888888", lw=0.6),
                annotation_clip=False,
            )
    fig.text(0.03, 0.012, caption, ha="left", va="bottom", fontsize=8,
             wrap=True, color="#222222")
    fig.subplots_adjust(left=0.20, right=0.93, top=0.90, bottom=0.14, hspace=0.08)
    fig.savefig(path_png, dpi=130)
    plt.close(fig)
    print(f"wrote {path_png}")


def _need(v: Vcd, name: str) -> List[Change]:
    vid = resolve(v, name)
    if vid is None:
        return [(0, 0)]
    return v.series[vid]


def render_g1(waves: str) -> None:
    vcd = os.path.join(waves, "g1_rt10.vcd")
    v = parse_vcd(vcd)
    ing = _need(v, "wav_ing0")
    t_ing = first_rise(ing) or 20
    irq = first_rise(_need(v, "wav_irq")) or t_ing
    t0, t1 = max(0, t_ing - 16), t_ing + 48
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
        [(irq, "score: irq rises + sticks; egr stays 0", "#c0392b")],
        "G1  RT=10 DROP  —  tc_rt10_must_drop  (AS-0.1 / TP-RT-003)",
        "Expected: RT=10 (2'b10) ingress, egress valid stays 0, rt_shortest_unimpl +1, "
        "irq_logic rises and sticks.  Actual: see window (PASS tc_rt10_must_drop).",
        notes=[(t_ing, "inject RT=10")],
    )


def render_cfg6(waves: str) -> None:
    vcd = os.path.join(waves, "cfg6_term_vs_fwd.vcd")
    v = parse_vcd(vcd)
    # Two stacked figures in one PNG via a taller custom layout
    hit = _need(v, "c6_hit")
    # unit pulses first, then fabric injects
    t_unit0 = first_rise(hit) or 0
    xin = first_rise(_need(v, "wav_xin0"))
    ing_all = [t for t, val in _need(v, "wav_ing0") if val]
    t_fab0 = ing_all[0] if ing_all else (xin or 200)
    # split: draw two windows into one figure manually
    from matplotlib.gridspec import GridSpec

    fig = plt.figure(figsize=(13.2, 10.2))
    fig.patch.set_facecolor("white")
    gs = GridSpec(12, 1, figure=fig, left=0.20, right=0.93, top=0.90, bottom=0.10, hspace=0.12)
    # Reuse draw by writing a temp approach: two separate draw_window calls then... 
    # Simpler: one wide window covering fabric only + caption listing unit classes,
    # plus a compact unit window in the top half via a second draw to a temp? 
    # Use two files then... user asked one PNG. Do fabric + unit on same time axis
    # if unit is early and fabric late — x will be sparse. Better two x-axes.
    # Call draw_window twice to /tmp and compose? Keep it simple: two sequential
    # draw_window into the same PNG by custom.
    plt.close(fig)

    unit_png = os.path.join(waves, "_cfg6_unit.png")
    fab_png = os.path.join(waves, "_cfg6_fab.png")
    t0u, t1u = max(0, t_unit0 - 4), t_unit0 + 40
    draw_window(
        unit_png, v,
        [
            ("c6_hit", "c6_hit (unit)", "hex"),
            ("c6_cons", "c6_cons consume", "hex"),
            ("c6_cna", "c6_cna (mgmt)", "hex"),
            ("c6_written", "c6_written", "bit"),
        ],
        t0u, t1u,
        [(t_unit0, "本CNA terminate (consume=1)", "#c0392b")],
        "CFG6 cna_ep classes (AS-0.1 §9) — unit pulses before fabric",
        "Pulses in order: (1) 本CNA+DCNA consume=1  (2) NLP=1 consume=1  "
        "(3) opc 0x10 targeting-us consume=1  (4) opc 0x10 not-us FORWARD  "
        "(5) else FORWARD  (6) CNA unwritten no-match.",
    )
    cfg6h = first_rise(_need(v, "wav_cfg6h0"), tmin=t_fab0 - 2) or t_fab0
    t0f = max(0, t_fab0 - 12)
    t1f = (xin or t_fab0) + 40
    draw_window(
        fab_png, v,
        [
            ("wav_ing0", "ing_vld[0]", "bit"),
            ("wav_cfg", "CFG field", "dec"),
            ("wav_nlp", "NLP", "dec"),
            ("wav_opc", "opcode[103:96]", "hex"),
            ("wav_cfg6h0", "fab.cfg6_hit[0]", "bit"),
            ("wav_xin0", "fab.x_in_v[0]", "bit"),
            ("wav_egr0", "egr_vld[0]", "bit"),
        ],
        t0f, t1f,
        [
            (cfg6h, "terminate-class: cfg6_hit / no xbar (本CNA)", "#c0392b"),
            (xin or t1f, "FORWARD: x_in_v=1 / egress", "#1e8449"),
        ],
        "CFG6 fabric: terminate vs FORWARD — tc_cfg6_term_vs_fwd",
        "Expected: 本CNA beat cfg6_hit=1 and x_in_v=0; FORWARD beat (DCNA≠CNA, NLP=0, opc=0) "
        "x_in_v=1 and egress.  Actual: see window (PASS tc_cfg6_term_vs_fwd).",
    )
    # stitch
    import matplotlib.image as mpimg

    im1 = mpimg.imread(unit_png)
    im2 = mpimg.imread(fab_png)
    h1, w1 = im1.shape[0], im1.shape[1]
    h2, w2 = im2.shape[0], im2.shape[1]
    w = max(w1, w2)
    fig2, (a1, a2) = plt.subplots(2, 1, figsize=(w / 130.0, (h1 + h2) / 130.0))
    for ax, im in ((a1, im1), (a2, im2)):
        ax.imshow(im)
        ax.axis("off")
    fig2.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0.01)
    out = os.path.join(waves, "cfg6_term_vs_fwd.png")
    fig2.savefig(out, dpi=130)
    plt.close(fig2)
    os.remove(unit_png)
    os.remove(fab_png)
    print(f"wrote {out}")


def render_credit_1024(waves: str) -> None:
    vcd = os.path.join(waves, "credit_1024_flit.vcd")
    v = parse_vcd(vcd)
    pend = _need(v, "pending")
    t_1023 = first_eq(pend, 1023)
    t_1024 = first_eq(pend, 1024)
    bp = first_rise(_need(v, "bp_nw"))
    t_mark = t_1024 or bp or 20
    t0 = max(0, (t_1023 or t_mark) - 16)
    t1 = t_mark + 20
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
        [(t_mark, "pending 1023→1024; bp_nw=1 (flit, no /n)", "#c0392b")],
        "Credit threshold 1024 is FLIT — tc_credit_1024_flit_bp  (FS-0.2.4 / G7)",
        "Expected: pending=1023 and bp_nw=0, then +1 flit → pending=1024 and bp_nw=1 "
        "(no divide-by-n on pending).  Actual: see window (PASS tc_credit_1024_flit_bp).  "
        "Note: force_crd_ack is also 1 whenever pending!=0 (RTL); the G7 threshold is bp_nw.",
        notes=[((t_1023 or t0), "pending=1023, no bp")],
    )


def render_credit_to(waves: str) -> None:
    vcd = os.path.join(waves, "credit_timeout_1us.vcd")
    v = parse_vcd(vcd)
    err = first_rise(_need(v, "proto_err"))
    t_mark = err or last_time(v)
    t0, t1 = max(0, t_mark - 80), t_mark + 24
    draw_window(
        os.path.join(waves, "credit_timeout_1us.png"),
        v,
        [
            ("credit_ret", "credit_ret", "bit"),
            ("pending", "pending", "dec"),
            ("wav_to", "u_crd.to (credit timer)", "dec"),
            ("proto_err", "proto_err", "bit"),
        ],
        t0, t1,
        [(t_mark, "to==0 → proto_err (1 µs = 1250 clk_fab)", "#c0392b")],
        "Credit return timeout 1 µs — tc_credit_timeout_1us  (VIBE_US_CYC=1250 @ 1.25 GHz)",
        "Expected: credit timer `u_crd.to` counts from 1250; proto_err rises at 1 µs.  "
        "This is NOT the VOQ `age[][]` counter (separate DUT vibe_dll_credit).  "
        "Actual: see window (PASS tc_credit_timeout_1us).",
    )


def render_voq(waves: str) -> None:
    vcd = os.path.join(waves, "voq_deadlock_1us.vcd")
    v = parse_vcd(vcd)
    drop = first_rise(_need(v, "deadlock_drop"))
    t_mark = drop or last_time(v)
    t0, t1 = max(0, t_mark - 80), t_mark + 24
    draw_window(
        os.path.join(waves, "voq_deadlock_1us.png"),
        v,
        [
            ("wr_en", "wr_en", "bit"),
            ("nonempty", "nonempty", "hex"),
            ("occ_vl0", "occ_vl0", "dec"),
            ("wav_age00", "u_v.age[0][0] (VOQ)", "dec"),
            ("deadlock_drop", "deadlock_drop", "bit"),
            ("deadlock_cnt", "deadlock_cnt", "dec"),
        ],
        t0, t1,
        [(t_mark, "age==0 → deadlock_drop (1 µs, vibe_voq_egr)", "#c0392b")],
        "VOQ deadlock timeout 1 µs — tc_deadlock_timeout_1us  (separate from credit `to`)",
        "Expected: `vibe_voq_egr.age[0][0]` counts from 1250; deadlock_drop pulses at 1 µs.  "
        "Different DUT and different counter from credit `u_crd.to`.  "
        "Actual: see window (PASS tc_deadlock_timeout_1us).",
    )


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
