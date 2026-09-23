"""vibe_pcs_tx_fec — PCS TX FEC wrap (AS-0.1 §5 T3).

Product module: ``rtl/pcs/vibe_pcs_tx_fec.sv``. Ports match tip
``ee5e8f4`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Internal leaf (``clk`` / ``rst_n`` / ``fec_mode[2:0]`` / 960b
``win_data`` / ``win_vld`` / ``win_ready`` / 1024b ``cw_data`` /
``cw_vld`` / ``cw_ready``); used by ``vibe_pcs_tx`` (``u_fec``).
Collects two 960b windows; encode or bypass; emits two 1024b
codewords. Instantiates stage-11 ``vibe_rs128_120_enc`` ×2
(``u_enc_a`` / ``u_enc_b``). T=4 default / T=2 / bypass
(``3'b010`` / ``3'b001`` / ``3'b000``). Bypass skips encoder,
still 6-flit align. ``win_ready = !have1``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``),
``include "vibe_ub_params.vh"``, two ``vibe_rs128_120_enc`` instances,
combo ``win_ready`` / symbol slices / ``enc_*_vld``, and the collect /
encode / bypass / emit always-block. Landed SV is hand-finished to
keep those freeze semantics. Leave RX FEC wrap / g1 / tx / rx tops
for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

WIN_W = 960
CW_W = 1024
PAR_W = 64
MODE_W = 3
CNT_W = 8
MSG_N = 120
# VIBE_FEC_BYPASS = 3'b000 (vibe_ub_params.vh). T=2 / T=4 both encode.
FEC_BYPASS = 0


def _cat_all(m: Circuit, *parts):
    """MSB-first concat of two or more slices."""
    acc = parts[0]
    for p in parts[1:]:
        acc = m.cat(acc, p)
    return acc


@module(name="vibe_pcs_tx_fec")
def build(m: Circuit) -> None:
    """Collect two 960b windows; encode or bypass; emit two 1024b CWs.

    Product ports (hand-finished SV)::

        clk, rst_n, fec_mode[2:0]
        win_data[959:0], win_vld, win_ready
        cw_data[1023:0], cw_vld, cw_ready

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``win_ready`` is combo
    ``!have1``. ``bypass`` is combo ``fec_mode == 0``. Product
    instantiates ``vibe_rs128_120_enc`` ×2; this frontend parks
    encoder ready as 1 and parity as 0 so the wrap shape stays.
    NBA last-wins matches stock (collect, then bypass emit, then
    symbol step, then pair_done, then encode emit).
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    fec_mode = m.input("fec_mode", width=MODE_W)
    win_data = m.input("win_data", width=WIN_W)
    win_vld = m.input("win_vld", width=1)
    cw_ready = m.input("cw_ready", width=1)

    w0 = m.out("w0", clk=clk, rst=rst, width=WIN_W, init=u(WIN_W, 0))
    w1 = m.out("w1", clk=clk, rst=rst, width=WIN_W, init=u(WIN_W, 0))
    have0 = m.out("have0", clk=clk, rst=rst, width=1, init=u(1, 0))
    have1 = m.out("have1", clk=clk, rst=rst, width=1, init=u(1, 0))
    sym_cnt = m.out("sym_cnt", clk=clk, rst=rst, width=CNT_W, init=u(CNT_W, 0))
    enc_go = m.out("enc_go", clk=clk, rst=rst, width=1, init=u(1, 0))
    enc_a_start = m.out("enc_a_start", clk=clk, rst=rst, width=1, init=u(1, 0))
    enc_b_start = m.out("enc_b_start", clk=clk, rst=rst, width=1, init=u(1, 0))
    cw_data = m.out("cw_data", clk=clk, rst=rst, width=CW_W, init=u(CW_W, 0))
    cw_vld = m.out("cw_vld", clk=clk, rst=rst, width=1, init=u(1, 0))
    pair_done = m.out("pair_done", clk=clk, rst=rst, width=1, init=u(1, 0))
    emit_b = m.out("emit_b", clk=clk, rst=rst, width=1, init=u(1, 0))
    cwa = m.out("cwa", clk=clk, rst=rst, width=CW_W, init=u(CW_W, 0))
    cwb = m.out("cwb", clk=clk, rst=rst, width=CW_W, init=u(CW_W, 0))

    win_ready = ~have1.out()
    bypass = fec_mode == FEC_BYPASS
    take = win_vld & win_ready
    take_w0 = take & ~have0.out()
    take_w1 = take & have0.out() & ~have1.out()
    start_enc = take_w1 & ~bypass
    ack_cw = cw_vld.out() & cw_ready
    # Frontend stand-in: encoder ready stays 1. Product uses instance rdy.
    enc_rdy = u(1, 1)
    step = enc_go.out() & enc_rdy
    last = step & (sym_cnt.out() == (MSG_N - 1))
    bypass_emit = have0.out() & have1.out() & bypass & ~cw_vld.out()
    enc_emit = pair_done.out() & ~cw_vld.out()
    bypass_a = bypass_emit & ~emit_b.out()
    bypass_b = bypass_emit & emit_b.out()
    enc_a = enc_emit & ~emit_b.out()
    enc_b = enc_emit & emit_b.out()
    # Product: {w*, 64'd0} bypass / {w*, parity} encode. Frontend parks par=0.
    par0 = u(PAR_W, 0)
    cw_w0 = _cat_all(m, w0.out(), par0)
    cw_w1 = _cat_all(m, w1.out(), par0)
    cw_win = _cat_all(m, win_data, par0)

    # Start pulses default 0 every cycle, then 1 on take_w1 encode.
    enc_a_start.set(u(1, 0))
    enc_b_start.set(u(1, 0))
    enc_a_start.set(u(1, 1), when=start_enc)
    enc_b_start.set(u(1, 1), when=start_enc)

    cw_vld.set(u(1, 0), when=ack_cw)

    w0.set(win_data, when=take_w0)
    have0.set(u(1, 1), when=take_w0)
    w1.set(win_data, when=take_w1)
    have1.set(u(1, 1), when=take_w1)
    cwa.set(cw_win, when=take_w1 & bypass)
    enc_go.set(u(1, 1), when=start_enc)
    sym_cnt.set(u(CNT_W, 0), when=start_enc)

    # Bypass emit (first CW = {w0,0}, second = {w1,0} then drop have*).
    cw_data.set(cw_w0, when=bypass_a)
    cw_vld.set(u(1, 1), when=bypass_a)
    emit_b.set(u(1, 1), when=bypass_a)
    cw_data.set(cw_w1, when=bypass_b)
    cw_vld.set(u(1, 1), when=bypass_b)
    emit_b.set(u(1, 0), when=bypass_b)
    have0.set(u(1, 0), when=bypass_b)
    have1.set(u(1, 0), when=bypass_b)

    enc_go.set(u(1, 0), when=last)
    sym_cnt.set(sym_cnt.out() + 1, when=step & ~last)

    # Frontend stand-in: last symbol sets pair_done. Product uses enc_*_done.
    cwa.set(cw_w0, when=last)
    cwb.set(cw_w1, when=last)
    pair_done.set(u(1, 1), when=last)

    cw_data.set(cwa.out(), when=enc_a)
    cw_vld.set(u(1, 1), when=enc_a)
    emit_b.set(u(1, 1), when=enc_a)
    cw_data.set(cwb.out(), when=enc_b)
    cw_vld.set(u(1, 1), when=enc_b)
    emit_b.set(u(1, 0), when=enc_b)
    pair_done.set(u(1, 0), when=enc_b)
    have0.set(u(1, 0), when=enc_b)
    have1.set(u(1, 0), when=enc_b)

    m.output("win_ready", win_ready)
    m.output("cw_data", cw_data.out())
    m.output("cw_vld", cw_vld.out())


build.__pycircuit_name__ = "vibe_pcs_tx_fec"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx_fec").emit_mlir())
