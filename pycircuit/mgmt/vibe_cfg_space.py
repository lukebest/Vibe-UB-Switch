"""vibe_cfg_space — static write cfg_wr_* (AS-0.1.2 §10 / UB Table D-103).

Product module: ``rtl/mgmt/vibe_cfg_space.sv``. Ports match tip
``6f790520``. Decision I UNFROZEN (do not re-pin freeze).
SPEC / CR-B names are unchanged. Internal leaf
(``clk`` / ``rst_n`` / ``device_rst`` / ``cfg_wr_vld`` /
``cfg_wr_ready`` / 4b ``cfg_wr_cmd`` / 16b ``cfg_wr_idx`` /
32b ``cfg_wr_data`` / 16b ``cna`` / ``cna_written`` /
4b ``default_bm`` / ``rt_wr_en`` / 16b ``rt_wr_idx`` /
32b ``rt_wr_data`` / 4b ``port_rst_pulse`` /
4b ``port_rst_hold`` / 4b ``port_rst_rw1c`` /
``device_rst_pulse`` / 4b ``lmsm_go_pulse`` / ``irq_clr`` /
32b ``guid0`` / 32b ``class_code`` / 32b ``port_basic`` /
32b ``port_cap``). Parameter ``ROUTE_TABLE_DEPTH`` default
256 (unused in the body). Fifth / last non-wrap mgmt leaf
after stage-38 ``vibe_rst_ctl``, stage-39 ``vibe_mgmt_byp``,
stage-40 ``vibe_irq_agg``, and stage-41 ``vibe_cna_ep``.
``cfg_wr_cmd`` is 4 bits: 0=CNA, 1=route entry, 2=Default
bitmap, 3=Port Reset (RW1C per port), 4=device reset,
5=pulse ``lmsm_go``; 6–15 ignore (``irq_clr`` still pulses
on any accepted write). Port Reset (cmd=3): Table D-103
field Port Reset bit 0, RW1C_DE0_EO. Four stored bits
(``port_rst_rw1c``), one per port. Port =
``cfg_wr_idx[1:0]``. Write ``data[0]==1`` is W1C: start
that port's sequence and keep the bit 1 while ``rst_ctl``
holds; HW returns the bit to 0 when the hold ends.
``data[0]==0`` does not start Port Reset. Bits live in
these mgmt flops — no product ``cfg_rd_*`` pin (AS §18).
Official opcode 0x10 payload packing / Appendix D offsets
are 未知 — do not invent. ``vibe_cna_ep`` still echos the
CFG6 request. Self-contained (no child instances).
Instantiated by ``vibe_mgmt``.

pyCircuit registers are dest-domain **synchronous active-high** reset.
Product RTL uses **async active-low** ``rst_n`` (``or negedge rst_n``)
and stock **synchronous** ``device_rst`` (same ``if`` as
``!rst_n``; not on the sensitivity list). Landed SV is
hand-finished to keep those tip semantics. Leave the
``vibe_mgmt`` / ``vibe_port`` / ``vibe_top`` wraps for
later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
CMD_W = 4
IDX_W = 16
DATA_W = 32
CNA_W = 16
CONST_W = 32

# rtl/common/vibe_ub_params.vh — GUID / Class / CFG0 (AS-0.1 §10)
VIBE_GUID_TYPE = 0x03
VIBE_CLASS_CODE = 0x0300
VIBE_PORT_BASIC = 0x00040402
VIBE_PORT_CAP = 0x00000104

CMD_CNA = 0
CMD_RT = 1
CMD_DEFAULT_BM = 2
CMD_PORT_RST = 3
CMD_DEV_RST = 4
CMD_LMSM_GO = 5


def _cat_lsb_first(m: Circuit, bits):
    """Pack ``bits[0]`` as LSB (``m.cat`` is MSB-first)."""
    acc = bits[0]
    for b in bits[1:]:
        acc = m.cat(b, acc)
    return acc


@module(name="vibe_cfg_space")
def build(m: Circuit) -> None:
    """Static write ``cfg_wr_*``. Port Reset stays stock RW1C.

    Product ports (hand-finished SV)::

        clk, rst_n, device_rst
        cfg_wr_vld, cfg_wr_ready, cfg_wr_cmd[3:0]
        cfg_wr_idx[15:0], cfg_wr_data[31:0]
        cna[15:0], cna_written, default_bm[3:0]
        rt_wr_en, rt_wr_idx[15:0], rt_wr_data[31:0]
        port_rst_pulse[3:0], port_rst_hold[3:0], port_rst_rw1c[3:0]
        device_rst_pulse, lmsm_go_pulse[3:0], irq_clr
        guid0[31:0], class_code[31:0], port_basic[31:0], port_cap[31:0]

    pyCircuit clock is ``clk``. Reset here is ``rst`` (active-high).
    Finish maps it to async-low ``rst_n``. ``device_rst`` is a
    data pin: last ``.set`` so it wins over writes (stock
    ``if (!rst_n || device_rst)``). Combo: ``cfg_wr_ready=1``,
    GUID / Class / CFG0 constants, ``wr_acc``, ``wr_port``,
    ``wr_port_rst_w1c``, ``hold_fall`` (same-cycle W1C masks
    the HW clear). Pulse flops default 0; ``irq_clr`` on any
    accepted write (cmd 0–15). No ``cfg_rd_*`` pin. Do not
    invent opcode 0x10 / Appendix D packing.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    device_rst = m.input("device_rst", width=1)
    cfg_wr_vld = m.input("cfg_wr_vld", width=1)
    cfg_wr_cmd = m.input("cfg_wr_cmd", width=CMD_W)
    cfg_wr_idx = m.input("cfg_wr_idx", width=IDX_W)
    cfg_wr_data = m.input("cfg_wr_data", width=DATA_W)
    port_rst_hold = m.input("port_rst_hold", width=PORT_N)

    cfg_wr_ready = u(1, 1)
    wr_acc = cfg_wr_vld & cfg_wr_ready
    wr_port = cfg_wr_idx.slice(lsb=0, width=2)
    data0 = cfg_wr_data.slice(lsb=0, width=1)
    wr_port_rst_w1c = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_PORT_RST)) & data0

    cmd0 = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_CNA))
    cmd1 = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_RT))
    cmd2 = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_DEFAULT_BM))
    cmd4 = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_DEV_RST))
    cmd5 = wr_acc & (cfg_wr_cmd == u(CMD_W, CMD_LMSM_GO))

    cna = m.out("cna", clk=clk, rst=rst, width=CNA_W, init=u(CNA_W, 0))
    cna_written = m.out("cna_written", clk=clk, rst=rst, width=1, init=u(1, 0))
    default_bm = m.out("default_bm", clk=clk, rst=rst, width=PORT_N, init=u(PORT_N, 0))
    rt_wr_en = m.out("rt_wr_en", clk=clk, rst=rst, width=1, init=u(1, 0))
    rt_wr_idx = m.out("rt_wr_idx", clk=clk, rst=rst, width=IDX_W, init=u(IDX_W, 0))
    rt_wr_data = m.out("rt_wr_data", clk=clk, rst=rst, width=DATA_W, init=u(DATA_W, 0))
    device_rst_pulse = m.out(
        "device_rst_pulse", clk=clk, rst=rst, width=1, init=u(1, 0)
    )
    irq_clr = m.out("irq_clr", clk=clk, rst=rst, width=1, init=u(1, 0))

    # Pulse flops default 0 every cycle; write / device_rst last.
    rt_wr_en.set(u(1, 0))
    rt_wr_en.set(u(1, 1), when=cmd1)
    rt_wr_en.set(u(1, 0), when=device_rst)
    device_rst_pulse.set(u(1, 0))
    device_rst_pulse.set(u(1, 1), when=cmd4)
    device_rst_pulse.set(u(1, 0), when=device_rst)
    irq_clr.set(u(1, 0))
    irq_clr.set(u(1, 1), when=wr_acc)
    irq_clr.set(u(1, 0), when=device_rst)

    cna.set(cfg_wr_data.slice(lsb=0, width=CNA_W), when=cmd0)
    cna.set(u(CNA_W, 0), when=device_rst)
    cna_written.set(u(1, 1), when=cmd0)
    cna_written.set(u(1, 0), when=device_rst)
    default_bm.set(cfg_wr_data.slice(lsb=0, width=PORT_N), when=cmd2)
    default_bm.set(u(PORT_N, 0), when=device_rst)
    rt_wr_idx.set(cfg_wr_idx, when=cmd1)
    rt_wr_idx.set(u(IDX_W, 0), when=device_rst)
    rt_wr_data.set(cfg_wr_data, when=cmd1)
    rt_wr_data.set(u(DATA_W, 0), when=device_rst)

    # Per-port RW1C / pulse. hold_fall masks same-cycle W1C (stock).
    pulse_bits = []
    go_bits = []
    rw1c_bits = []
    for i in range(PORT_N):
        h = port_rst_hold.slice(lsb=i, width=1)
        hd = m.out(
            f"port_rst_hold_d_{i}", clk=clk, rst=rst, width=1, init=u(1, 0)
        )
        hd.set(h)
        hd.set(u(1, 0), when=device_rst)
        is_port = wr_port == u(2, i)
        w1c_i = wr_port_rst_w1c & is_port
        hold_fall = hd.out() & ~h & ~w1c_i

        rw = m.out(f"port_rst_rw1c_{i}", clk=clk, rst=rst, width=1, init=u(1, 0))
        # HW clear first; W1C write-1 last so retrigger keeps the bit.
        rw.set(u(1, 0), when=hold_fall)
        rw.set(u(1, 1), when=w1c_i)
        rw.set(u(1, 0), when=device_rst)
        rw1c_bits.append(rw.out())

        pp = m.out(
            f"port_rst_pulse_{i}", clk=clk, rst=rst, width=1, init=u(1, 0)
        )
        pp.set(u(1, 0))
        pp.set(u(1, 1), when=w1c_i)
        pp.set(u(1, 0), when=device_rst)
        pulse_bits.append(pp.out())

        gp = m.out(
            f"lmsm_go_pulse_{i}", clk=clk, rst=rst, width=1, init=u(1, 0)
        )
        gp.set(u(1, 0))
        gp.set(u(1, 1), when=cmd5 & is_port)
        gp.set(u(1, 0), when=device_rst)
        go_bits.append(gp.out())

    m.output("cfg_wr_ready", cfg_wr_ready)
    m.output("cna", cna.out())
    m.output("cna_written", cna_written.out())
    m.output("default_bm", default_bm.out())
    m.output("rt_wr_en", rt_wr_en.out())
    m.output("rt_wr_idx", rt_wr_idx.out())
    m.output("rt_wr_data", rt_wr_data.out())
    m.output("port_rst_pulse", _cat_lsb_first(m, pulse_bits))
    m.output("port_rst_rw1c", _cat_lsb_first(m, rw1c_bits))
    m.output("device_rst_pulse", device_rst_pulse.out())
    m.output("lmsm_go_pulse", _cat_lsb_first(m, go_bits))
    m.output("irq_clr", irq_clr.out())
    m.output("guid0", u(CONST_W, VIBE_GUID_TYPE))
    m.output("class_code", u(CONST_W, VIBE_CLASS_CODE))
    m.output("port_basic", u(CONST_W, VIBE_PORT_BASIC))
    m.output("port_cap", u(CONST_W, VIBE_PORT_CAP))


build.__pycircuit_name__ = "vibe_cfg_space"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_cfg_space").emit_mlir())
