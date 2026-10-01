"""vibe_port — per-port structural wrap (AS-0.1 §4).

Product module: ``rtl/port/vibe_port.sv``. Ports match tip
``4cff3a53`` (product DUT after PR259 TB-only; RTL same as
``cd71b1d0`` / PR258 stage-49). Decision I UNFROZEN (do
not re-pin freeze). SPEC / CR-B names are unchanged.
Hierarchy wrap
(``clk_fab`` / ``rst_n`` / ``port_rst`` / ``device_rst`` /
``lmsm_go`` / ``txclk`` / ``rxclk`` / 512b
``pcs_pma_txdata`` / ``pma_pcs_rxdata`` / 512b
``fab_nw_data`` / ``fab_nw_vld`` / ``fab_nw_ready`` /
512b ``nw_fab_data`` / ``nw_fab_vld`` / ``nw_fab_ready`` /
512b ``mgmt_nw_data`` / ``mgmt_nw_vld`` / ``mgmt_nw_ready`` /
``status_up`` / ``disabled`` / ``retry_error`` / ``proto_err`` /
``fc_ovf`` / ``rx_ovf`` / ``afifo_ovf`` / ``cfg0_hit`` /
640b ``cfg0_data``). First port structural top. Instantiates
stock children: ``vibe_rst_sync u_txrst`` / ``u_rxrst``,
``vibe_lmsm u_lmsm``, ``vibe_nw_adapt u_nw``,
``vibe_dll u_dll``, ``vibe_pcs_tx u_ptx``,
``vibe_pcs_rx u_prx``, 4× TX ``vibe_afifo u_at*`` +
``vibe_gear_160_128 u_g*``, ``vibe_pma_bnd u_pma``,
4× RX ``vibe_afifo u_ar*`` + ``vibe_gear_128_160 u_rg*``.
``vibe_pcs_tx`` / ``vibe_pcs_rx`` / ``vibe_lmsm`` now have
pyCircuit wraps (stages 47–49) — listed in CHILDREN, not
re-migrated here. Wrap-local: ``fec_mode = VIBE_FEC_T4``,
TX/RX gear hold, RX change-detect, F1 ``ovf_l`` CDC sync.
Do not rewrite ``ovf_l`` (CDC F1). Instantiated by
``vibe_ub_switch``. ``vibe_ub_switch`` wrap stays HOLD.
CDC leaf banners still cite void freeze ``302ac943`` —
leave those for a later leaf.

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap's sequential (``ovf_l`` / change-detect / CDC sync)
stays in the hand-finished product SV. Product RTL keeps
**async active-low** ``rst_n`` on the children. Landed SV is
hand-finished so the stock hierarchy (ports / instances /
nets / AFIFO / gear / PMA / ``ovf_l``) stays byte-identical
in the module body. Do not invent CFG6 packing, Appendix D,
or opcode 0x10.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

NW_W = 512
PMA_W = 512
PCS_W = 640
LANE_FAB_W = 160
LANE_PMA_W = 128
N_LANE = 4
# rtl/common/vibe_ub_params.vh — product AFIFO depth on u_at* / u_ar*.
VIBE_AFIFO_DEPTH = 16


def _lane_afifo_tx(inst: str, wdata: str, almost: str, ren: str, rdata: str, rempty: str):
    return {
        "module": "vibe_afifo",
        "inst": inst,
        "params": {"W": "160", "DEPTH": "VIBE_AFIFO_DEPTH"},
        "connects": {
            "wclk": "clk_fab",
            "wrst_n": "rst_n",
            "wen": "pcs_afifo_lane_vld",
            "wdata": wdata,
            "wfull": "",
            "almost_full": almost,
            "wocc": "",
            "rclk": "txclk",
            "rrst_n": "txrst_n",
            "ren": ren,
            "rdata": rdata,
            "rempty": rempty,
        },
    }


def _lane_gear_tx(inst: str, te: str, ready: str, tq: str, gv: str, out: str):
    return {
        "module": "vibe_gear_160_128",
        "inst": inst,
        "params": {},
        "connects": {
            "clk": "txclk",
            "rst_n": "txrst_n",
            "in_vld": f"!{te} && !tx_hold_wait",
            "in_ready": ready,
            "in_data": tq,
            "out_vld": gv,
            "out_ready": "afifo_pma_lane_vld",
            "out_data": out,
        },
    }


def _lane_afifo_rx(inst: str, wen: str, wdata: str, wfull: str, almost: str, ren: str, rdata: str, rempty: str):
    return {
        "module": "vibe_afifo",
        "inst": inst,
        "params": {"W": "128", "DEPTH": "VIBE_AFIFO_DEPTH"},
        "connects": {
            "wclk": "rxclk",
            "wrst_n": "rxrst_n",
            "wen": wen,
            "wdata": wdata,
            "wfull": wfull,
            "almost_full": almost,
            "wocc": "",
            "rclk": "clk_fab",
            "rrst_n": "rst_n",
            "ren": ren,
            "rdata": rdata,
            "rempty": rempty,
        },
    }


def _lane_gear_rx(inst: str, re: str, ready: str, rq: str, afrv: str, out: str):
    return {
        "module": "vibe_gear_128_160",
        "inst": inst,
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "in_vld": f"!{re} && !rx_hold_wait",
            "in_ready": ready,
            "in_data": rq,
            "out_vld": afrv,
            "out_ready": "afifo_pcs_lane_vld",
            "out_data": out,
        },
    }


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
# vibe_pcs_tx / vibe_pcs_rx / vibe_lmsm now have pyCircuit wraps
# (stages 47–49); listed here, not re-migrated.
CHILDREN = (
    {
        "module": "vibe_rst_sync",
        "inst": "u_txrst",
        "params": {},
        "connects": {
            "clk": "txclk",
            "rst_n_in": "rst_n && !port_rst",
            "rst_n_out": "txrst_n",
        },
    },
    {
        "module": "vibe_rst_sync",
        "inst": "u_rxrst",
        "params": {},
        "connects": {
            "clk": "rxclk",
            "rst_n_in": "rst_n && !port_rst",
            "rst_n_out": "rxrst_n",
        },
    },
    {
        "module": "vibe_lmsm",
        "inst": "u_lmsm",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "lmsm_go": "lmsm_go",
            "am_locked": "am_locked",
            "lid_bad": "lid_bad",
            "lane0_fail": "1'b0",
            "eq_negotiated": "1'b0",
            "retrain_req": "retrain_req",
            "link_up": "link_up",
            "link_ready": "link_ready",
            "sdf_period": "sdf_period",
            "state": "lmsm_st",
            "width_fail": "width_fail",
        },
    },
    {
        "module": "vibe_nw_adapt",
        "inst": "u_nw",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "link_ready": "link_ready",
            "fab_nw_data": "fab_nw_data",
            "fab_nw_vld": "fab_nw_vld",
            "fab_nw_ready": "fab_nw_ready",
            "mgmt_nw_data": "mgmt_nw_data",
            "mgmt_nw_vld": "mgmt_nw_vld",
            "mgmt_nw_ready": "mgmt_nw_ready",
            "nw_dll_data": "nw_dll_data",
            "nw_dll_vld": "nw_dll_vld",
            "nw_dll_ready": "nw_dll_ready",
            "dll_nw_data": "dll_nw_data",
            "dll_nw_vld": "dll_nw_vld",
            "dll_nw_ready": "dll_nw_ready",
            "nw_fab_data": "nw_fab_data",
            "nw_fab_vld": "nw_fab_vld",
            "nw_fab_ready": "nw_fab_ready",
        },
    },
    {
        "module": "vibe_dll",
        "inst": "u_dll",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "device_rst": "device_rst",
            "link_up": "link_up",
            "fec_fail": "fec_fail",
            "nw_dll_data": "nw_dll_data",
            "nw_dll_vld": "nw_dll_vld",
            "nw_dll_ready": "nw_dll_ready",
            "dll_nw_data": "dll_nw_data",
            "dll_nw_vld": "dll_nw_vld",
            "dll_nw_ready": "dll_nw_ready",
            "dll_pcs_data": "dll_pcs_data",
            "dll_pcs_vld": "dll_pcs_vld",
            "dll_pcs_ready": "dll_pcs_ready",
            "pcs_dll_data": "pcs_dll_data",
            "pcs_dll_vld": "pcs_dll_vld",
            "pcs_dll_ready": "pcs_dll_ready",
            "status_up": "status_up",
            "disabled": "disabled",
            "retrain_req": "retrain_req",
            "retry_error": "retry_error",
            "proto_err": "proto_err",
            "fc_ovf": "fc_ovf",
            "rx_ovf": "rx_ovf",
            "cfg0_hit": "cfg0_hit",
            "cfg0_data": "cfg0_data",
        },
    },
    {
        "module": "vibe_pcs_tx",
        "inst": "u_ptx",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "link_up": "link_up",
            "sdf_period": "sdf_period",
            "fec_mode": "fec_mode",
            "afifo_afull": "|af_tx",
            "dll_pcs_data": "dll_pcs_data",
            "dll_pcs_vld": "dll_pcs_vld",
            "dll_pcs_ready": "dll_pcs_ready",
            "pcs_afifo_lane0": "pcs_afifo_lane0",
            "pcs_afifo_lane1": "pcs_afifo_lane1",
            "pcs_afifo_lane2": "pcs_afifo_lane2",
            "pcs_afifo_lane3": "pcs_afifo_lane3",
            "pcs_afifo_lane_vld": "pcs_afifo_lane_vld",
        },
    },
    {
        "module": "vibe_pcs_rx",
        "inst": "u_prx",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "link_up": "link_up",
            "fec_mode": "fec_mode",
            "afifo_pcs_lane0": "afifo_pcs_lane0",
            "afifo_pcs_lane1": "afifo_pcs_lane1",
            "afifo_pcs_lane2": "afifo_pcs_lane2",
            "afifo_pcs_lane3": "afifo_pcs_lane3",
            "afifo_pcs_lane_vld": "afifo_pcs_lane_vld",
            "pcs_dll_data": "pcs_dll_data",
            "pcs_dll_vld": "pcs_dll_vld",
            "pcs_dll_ready": "pcs_dll_ready",
            "fec_fail": "fec_fail",
            "am_locked": "am_locked",
            "lid_bad": "lid_bad",
            "deskew_ok": "deskew_ok",
        },
    },
    _lane_afifo_tx("u_at0", "pcs_afifo_lane0", "af_tx[0]", "tren0", "tq0", "te0"),
    _lane_afifo_tx("u_at1", "pcs_afifo_lane1", "af_tx[1]", "tren1", "tq1", "te1"),
    _lane_afifo_tx("u_at2", "pcs_afifo_lane2", "af_tx[2]", "tren2", "tq2", "te2"),
    _lane_afifo_tx("u_at3", "pcs_afifo_lane3", "af_tx[3]", "tren3", "tq3", "te3"),
    _lane_gear_tx("u_g0", "te0", "g0r", "tq0", "gv0", "afifo_pma_lane0"),
    _lane_gear_tx("u_g1", "te1", "g1r", "tq1", "gv1", "afifo_pma_lane1"),
    _lane_gear_tx("u_g2", "te2", "g2r", "tq2", "gv2", "afifo_pma_lane2"),
    _lane_gear_tx("u_g3", "te3", "g3r", "tq3", "gv3", "afifo_pma_lane3"),
    {
        "module": "vibe_pma_bnd",
        "inst": "u_pma",
        "params": {},
        "connects": {
            "txclk": "txclk",
            "rxclk": "rxclk",
            "txrst_n": "txrst_n",
            "rxrst_n": "rxrst_n",
            "afifo_pma_lane0": "afifo_pma_lane0",
            "afifo_pma_lane1": "afifo_pma_lane1",
            "afifo_pma_lane2": "afifo_pma_lane2",
            "afifo_pma_lane3": "afifo_pma_lane3",
            "afifo_pma_lane_vld": "afifo_pma_lane_vld",
            "pcs_pma_txdata": "pcs_pma_txdata",
            "pma_pcs_rxdata": "pma_pcs_rxdata",
            "pma_afifo_lane0": "pma_afifo_lane0",
            "pma_afifo_lane1": "pma_afifo_lane1",
            "pma_afifo_lane2": "pma_afifo_lane2",
            "pma_afifo_lane3": "pma_afifo_lane3",
            "pma_afifo_lane_vld": "pma_afifo_lane_vld",
        },
    },
    _lane_afifo_rx("u_ar0", "wr0", "pma_afifo_lane0", "wf0", "af_rx[0]", "rren0", "rq0", "re0"),
    _lane_afifo_rx("u_ar1", "wr1", "pma_afifo_lane1", "wf1", "af_rx[1]", "rren1", "rq1", "re1"),
    _lane_afifo_rx("u_ar2", "wr2", "pma_afifo_lane2", "wf2", "af_rx[2]", "rren2", "rq2", "re2"),
    _lane_afifo_rx("u_ar3", "wr3", "pma_afifo_lane3", "wf3", "af_rx[3]", "rren3", "rq3", "re3"),
    _lane_gear_rx("u_rg0", "re0", "gr0", "rq0", "afrv0", "afifo_pcs_lane0"),
    _lane_gear_rx("u_rg1", "re1", "gr1", "rq1", "afrv1", "afifo_pcs_lane1"),
    _lane_gear_rx("u_rg2", "re2", "gr2", "rq2", "afrv2", "afifo_pcs_lane2"),
    _lane_gear_rx("u_rg3", "re3", "gr3", "rq3", "afrv3", "afifo_pcs_lane3"),
)


@module(name="vibe_port")
def build(m: Circuit) -> None:
    """Port hierarchy wrap: rst_sync / lmsm / nw / dll / pcs / afifo / gear / pma.

    Product ports (hand-finished SV)::

        clk_fab, rst_n, port_rst, device_rst, lmsm_go, txclk, rxclk,
        pcs_pma_txdata[511:0], pma_pcs_rxdata[511:0],
        fab_nw_data[511:0], fab_nw_vld, fab_nw_ready,
        nw_fab_data[511:0], nw_fab_vld, nw_fab_ready,
        mgmt_nw_data[511:0], mgmt_nw_vld, mgmt_nw_ready,
        status_up, disabled, retry_error, proto_err, fc_ovf,
        rx_ovf, afifo_ovf, cfg0_hit, cfg0_data[639:0]

    pyCircuit clocks are ``clk_fab`` / ``txclk`` / ``rxclk``.
    Reset here is ``rst`` (active-high). Children keep
    async-low ``rst_n`` in the product SV. Frontend parks
    child-driven outputs at 0 (same pattern as stage-35
    ``vibe_dll``). F1 ``ovf_l`` / gear hold / change-detect
    stay in the hand-finished body — do not rewrite.
    Product SV instantiates ``CHILDREN``.
    """
    clk_fab = m.clock("clk_fab")
    txclk = m.clock("txclk")
    rxclk = m.clock("rxclk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    device_rst = m.input("device_rst", width=1)
    lmsm_go = m.input("lmsm_go", width=1)
    pma_pcs_rxdata = m.input("pma_pcs_rxdata", width=PMA_W)
    fab_nw_data = m.input("fab_nw_data", width=NW_W)
    fab_nw_vld = m.input("fab_nw_vld", width=1)
    nw_fab_ready = m.input("nw_fab_ready", width=1)
    mgmt_nw_data = m.input("mgmt_nw_data", width=NW_W)
    mgmt_nw_vld = m.input("mgmt_nw_vld", width=1)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        port_rst
        | device_rst
        | lmsm_go
        | fab_nw_vld
        | nw_fab_ready
        | mgmt_nw_vld
        | (pma_pcs_rxdata == 0)
        | (fab_nw_data == 0)
        | (mgmt_nw_data == 0)
    )
    _ = (clk_fab, txclk, rxclk, rst, _keep, CHILDREN, VIBE_AFIFO_DEPTH, N_LANE)

    m.output("pcs_pma_txdata", u(PMA_W, 0))
    m.output("fab_nw_ready", u(1, 0))
    m.output("nw_fab_data", u(NW_W, 0))
    m.output("nw_fab_vld", u(1, 0))
    m.output("mgmt_nw_ready", u(1, 0))
    m.output("status_up", u(1, 0))
    m.output("disabled", u(1, 0))
    m.output("retry_error", u(1, 0))
    m.output("proto_err", u(1, 0))
    m.output("fc_ovf", u(1, 0))
    m.output("rx_ovf", u(1, 0))
    m.output("afifo_ovf", u(1, 0))
    m.output("cfg0_hit", u(1, 0))
    m.output("cfg0_data", u(PCS_W, 0))


build.__pycircuit_name__ = "vibe_port"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_port").emit_mlir())
