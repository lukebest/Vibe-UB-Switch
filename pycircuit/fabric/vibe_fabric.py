"""vibe_fabric — chip fabric hierarchy wrap (AS-0.1 §8/§9).

Product module: ``rtl/fabric/vibe_fabric.sv``. Ports match tip
``1ce79bfe`` (product DUT after PR249 stage-45). Decision I
UNFROZEN (do not re-pin freeze). SPEC / CR-B names are
unchanged. Hierarchy wrap (``clk`` / ``rst_n`` /
``device_rst`` / 4b ``status_up`` / 4b ``default_bm`` /
``rt_wr_en`` / 16b ``rt_wr_idx`` / 32b ``rt_wr_data`` /
unpacked 512b ``nw_fab_data[0:3]`` / 4b ``nw_fab_vld`` /
4b ``nw_fab_ready`` / unpacked 512b ``fab_nw_data[0:3]`` /
4b ``fab_nw_vld`` / 4b ``fab_nw_ready`` / 4b ``len_err`` /
``drop_g1`` / 32b ``rt_shortest_unimpl`` / 32b
``drop_down_cnt`` / 4b ``deadlock_drop`` / ``irq_rt`` /
16b ``cna`` / ``cna_written`` / 4b ``fab_mgmt_cfg6_hit`` /
unpacked 512b ``fab_mgmt_cfg6_data[0:3]``). Parameter
``ROUTE_TABLE_DEPTH`` default 256 (passed to ``u_rt`` /
``g_rt[gi].u_rti``). First fabric-hierarchy wrap after
stage-33 ``vibe_xbar`` and stage-45 ``vibe_mgmt``.
Instantiates stock children: 4× ``vibe_saf_ing
#(.DEPTH(VIBE_SAF_PKT_DEPTH)) g_saf[gi].u_saf``,
``vibe_route_lu #(.DEPTH(...)) u_rt``, ``vibe_port_sel
u_ps``, 3× ``vibe_route_lu g_rt[gi].u_rti`` +
``vibe_port_sel g_rt[gi].u_psi`` (ports 1..3),
``vibe_xbar u_xbar``, 4× ``vibe_voq_egr
#(.DEPTH(VIBE_VOQ_DEPTH)) g_egr[gi].u_voq``, 4×
``vibe_vl_rr g_egr[gi].u_rr``, 4× ``vibe_fecn_mark
#(.FECN_WM(VIBE_FECN_WM)) g_egr[gi].u_fecn``. Children
already have pyCircuit wraps (stages 27–33). Wrap-local
stock glue (CFG6 terminate / G1 counters / local queues)
stays in the hand-finished body — preserve
byte-identical; do not invent CFG6 packing, Appendix D,
or opcode 0x10. Do not rewrite F1 ``ovf_l`` (lives under
``vibe_port``; fabric must not ECO it).

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own in the frontend.
Product RTL keeps **async active-low** ``rst_n`` on the
children. Landed SV is hand-finished so the stock
hierarchy (ports / generate loops / instances ``g_saf`` /
``u_rt`` / ``u_ps`` / ``g_rt`` / ``u_xbar`` / ``g_egr`` /
local wires / CFG6 / G1) stays byte-identical in the
module body.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
CNA_W = 16
DATA_W = 512
RT_IDX_W = 16
RT_DATA_W = 32
CNT_W = 32
# Stock default; product SV parameter on u_rt / g_rt[*].u_rti.
ROUTE_TABLE_DEPTH = 256
# rtl/common/vibe_ub_params.vh — product depths / watermark.
VIBE_SAF_PKT_DEPTH = 128
VIBE_VOQ_DEPTH = 32
VIBE_FECN_WM = 24


def _saf(gi: int):
    return {
        "module": "vibe_saf_ing",
        "inst": f"g_saf[{gi}].u_saf",
        "params": {"DEPTH": "VIBE_SAF_PKT_DEPTH"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "in_data": f"nw_fab_data[{gi}]",
            "in_vld": f"nw_fab_vld[{gi}]",
            "in_ready": f"nw_fab_ready[{gi}]",
            "pkt_data": f"saf_d[{gi}]",
            "pkt_vld": f"saf_v[{gi}]",
            "pkt_ready": f"saf_r[{gi}]",
            "pkt_sop": f"saf_sop[{gi}]",
            "pkt_eop": f"saf_eop[{gi}]",
            "pkt_bytes": f"saf_b[{gi}]",
            "len_err": f"len_err[{gi}]",
        },
    }


def _rti(gi: int):
    return {
        "module": "vibe_route_lu",
        "inst": f"g_rt[{gi}].u_rti",
        "params": {"DEPTH": "ROUTE_TABLE_DEPTH"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "device_rst": "device_rst",
            "wr_en": "rt_wr_en",
            "wr_idx": "rt_wr_idx",
            "wr_data": "rt_wr_data",
            "dest": f"vibe_nth_dcna(hdr[{gi}])",
            "rt": f"vibe_lph_rt(hdr[{gi}])",
            "lu_vld": f"saf_v[{gi}]",
            "bitmap": f"bm_p[{gi}]",
            "drop_g1": f"g1_p[{gi}]",
        },
    }


def _psi(gi: int):
    return {
        "module": "vibe_port_sel",
        "inst": f"g_rt[{gi}].u_psi",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "bitmap": f"bm_p[{gi}]",
            "status_up": "status_up",
            "default_bm": "default_bm",
            "rt": f"vibe_lph_rt(hdr[{gi}])",
            "drop_g1": f"g1_p[{gi}]",
            "sel_vld": f"saf_v[{gi}]",
            "cfg": f"vibe_lph_cfg(hdr[{gi}])",
            "src": f"vibe_nth_scna(hdr[{gi}])",
            "dest": f"vibe_nth_dcna(hdr[{gi}])",
            "vl": f"vibe_lph_vl(hdr[{gi}])",
            "egr": f"egr[{gi}]",
            "drop": f"pdrop[{gi}]",
            "drop_down_cnt": "",
        },
    }


def _voq(gi: int):
    return {
        "module": "vibe_voq_egr",
        "inst": f"g_egr[{gi}].u_voq",
        "params": {"DEPTH": "VIBE_VOQ_DEPTH"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "wr_vl": (
                f"xb_sop[{gi}] ? vibe_lph_vl(vibe_nw512_flit0(xb_d[{gi}]))"
                f" : xb_vl_q[{gi}]"
            ),
            "wr_en": f"xb_v[{gi}]",
            "wr_data": f"xb_d[{gi}]",
            "wr_sop": f"xb_sop[{gi}]",
            "wr_eop": f"xb_eop[{gi}]",
            "wr_ready": f"xb_r[{gi}]",
            "rd_vl": f"vl_sel[{gi}]",
            "rd_en": f"fab_nw_ready[{gi}] && vl_ok[{gi}]",
            "rd_data": f"fab_nw_data[{gi}]",
            "rd_sop": f"egr_sop[{gi}]",
            "rd_eop": "",
            "nonempty": f"ne[{gi}]",
            "occ_vl0": f"occ0[{gi}]",
            "deadlock_drop": f"deadlock_drop[{gi}]",
            "deadlock_cnt": "",
        },
    }


def _rr(gi: int):
    return {
        "module": "vibe_vl_rr",
        "inst": f"g_egr[{gi}].u_rr",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "nonempty": f"ne[{gi}]",
            "grant": f"fab_nw_ready[{gi}] && vl_ok[{gi}]",
            "vl_sel": f"vl_sel[{gi}]",
            "valid": f"vl_ok[{gi}]",
        },
    }


def _fecn(gi: int):
    return {
        "module": "vibe_fecn_mark",
        "inst": f"g_egr[{gi}].u_fecn",
        "params": {"FECN_WM": "VIBE_FECN_WM"},
        "connects": {
            "cci_in": (
                f"vibe_nth_cci(egr_sop[{gi}] ? vibe_nw512_flit0(fab_nw_data[{gi}])"
                f" : egr_hdr_q[{gi}])"
            ),
            "voq_occ": f"occ0[{gi}]",
            "cci_out": f"cci_m[{gi}]",
            "marked": "",
        },
    }


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
CHILDREN = (
    _saf(0),
    _saf(1),
    _saf(2),
    _saf(3),
    {
        "module": "vibe_route_lu",
        "inst": "u_rt",
        "params": {"DEPTH": "ROUTE_TABLE_DEPTH"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "device_rst": "device_rst",
            "wr_en": "rt_wr_en",
            "wr_idx": "rt_wr_idx",
            "wr_data": "rt_wr_data",
            "dest": "dst0",
            "rt": "rt0",
            "lu_vld": "saf_v[0]",
            "bitmap": "bm",
            "drop_g1": "g1",
        },
    },
    {
        "module": "vibe_port_sel",
        "inst": "u_ps",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "bitmap": "bm",
            "status_up": "status_up",
            "default_bm": "default_bm",
            "rt": "rt0",
            "drop_g1": "g1",
            "sel_vld": "saf_v[0]",
            "cfg": "cfg0",
            "src": "src0",
            "dest": "dst0",
            "vl": "vl0",
            "egr": "egr[0]",
            "drop": "pdrop[0]",
            "drop_down_cnt": "drop_down_cnt",
        },
    },
    _rti(1),
    _psi(1),
    _rti(2),
    _psi(2),
    _rti(3),
    _psi(3),
    {
        "module": "vibe_xbar",
        "inst": "u_xbar",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "status_up": "status_up",
            "in_data": "saf_d",
            "in_vld": "x_in_v",
            "in_sop": "saf_sop",
            "in_eop": "saf_eop",
            "in_dst": "egr",
            "in_ready": "xb_in_r",
            "out_data": "xb_d",
            "out_vld": "xb_v",
            "out_sop": "xb_sop",
            "out_eop": "xb_eop",
            "out_ready": "xb_r",
        },
    },
    _voq(0),
    _rr(0),
    _fecn(0),
    _voq(1),
    _rr(1),
    _fecn(1),
    _voq(2),
    _rr(2),
    _fecn(2),
    _voq(3),
    _rr(3),
    _fecn(3),
)


@module(name="vibe_fabric")
def build(m: Circuit) -> None:
    """Fabric hierarchy wrap: SAF / route / port_sel / xbar / VOQ / VL / FECN.

    Product ports (hand-finished SV)::

        clk, rst_n, device_rst, status_up[3:0], default_bm[3:0],
        rt_wr_en, rt_wr_idx[15:0], rt_wr_data[31:0],
        nw_fab_data[511:0][0:3], nw_fab_vld[3:0], nw_fab_ready[3:0],
        fab_nw_data[511:0][0:3], fab_nw_vld[3:0], fab_nw_ready[3:0],
        len_err[3:0], drop_g1, rt_shortest_unimpl[31:0],
        drop_down_cnt[31:0], deadlock_drop[3:0], irq_rt,
        cna[15:0], cna_written, fab_mgmt_cfg6_hit[3:0],
        fab_mgmt_cfg6_data[511:0][0:3]

    Parameter ``ROUTE_TABLE_DEPTH`` default 256 (``u_rt`` /
    ``g_rt[*].u_rti``). pyCircuit clock is ``clk``. Reset
    here is ``rst`` (active-high). Children keep async-low
    ``rst_n`` in the product SV. Unpacked product arrays are
    flattened here (``nw_fab_data_0..3``, ``fab_nw_data_0..3``,
    ``fab_mgmt_cfg6_data_0..3``). Frontend parks child-driven
    outputs at 0 (same pattern as stage-45 ``vibe_mgmt``).
    Product SV instantiates ``CHILDREN``. CFG6 terminate
    glue / G1 counters stay stock — do not invent packing.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    device_rst = m.input("device_rst", width=1)
    status_up = m.input("status_up", width=PORT_N)
    default_bm = m.input("default_bm", width=PORT_N)
    rt_wr_en = m.input("rt_wr_en", width=1)
    rt_wr_idx = m.input("rt_wr_idx", width=RT_IDX_W)
    rt_wr_data = m.input("rt_wr_data", width=RT_DATA_W)
    nw_fab_data = [
        m.input(f"nw_fab_data_{p}", width=DATA_W) for p in range(PORT_N)
    ]
    nw_fab_vld = m.input("nw_fab_vld", width=PORT_N)
    fab_nw_ready = m.input("fab_nw_ready", width=PORT_N)
    cna = m.input("cna", width=CNA_W)
    cna_written = m.input("cna_written", width=1)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        device_rst
        | rt_wr_en
        | cna_written
        | (status_up == 0)
        | (default_bm == 0)
        | (rt_wr_idx == 0)
        | (rt_wr_data == 0)
        | (nw_fab_vld == 0)
        | (fab_nw_ready == 0)
        | (cna == 0)
        | (nw_fab_data[0] == 0)
        | (nw_fab_data[1] == 0)
        | (nw_fab_data[2] == 0)
        | (nw_fab_data[3] == 0)
    )
    _ = (
        clk,
        rst,
        _keep,
        CHILDREN,
        ROUTE_TABLE_DEPTH,
        VIBE_SAF_PKT_DEPTH,
        VIBE_VOQ_DEPTH,
        VIBE_FECN_WM,
        PORT_N,
    )

    m.output("nw_fab_ready", u(PORT_N, 0))
    m.output("fab_nw_data_0", u(DATA_W, 0))
    m.output("fab_nw_data_1", u(DATA_W, 0))
    m.output("fab_nw_data_2", u(DATA_W, 0))
    m.output("fab_nw_data_3", u(DATA_W, 0))
    m.output("fab_nw_vld", u(PORT_N, 0))
    m.output("len_err", u(PORT_N, 0))
    m.output("drop_g1", u(1, 0))
    m.output("rt_shortest_unimpl", u(CNT_W, 0))
    m.output("drop_down_cnt", u(CNT_W, 0))
    m.output("deadlock_drop", u(PORT_N, 0))
    m.output("irq_rt", u(1, 0))
    m.output("fab_mgmt_cfg6_hit", u(PORT_N, 0))
    m.output("fab_mgmt_cfg6_data_0", u(DATA_W, 0))
    m.output("fab_mgmt_cfg6_data_1", u(DATA_W, 0))
    m.output("fab_mgmt_cfg6_data_2", u(DATA_W, 0))
    m.output("fab_mgmt_cfg6_data_3", u(DATA_W, 0))


build.__pycircuit_name__ = "vibe_fabric"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_fabric").emit_mlir())
