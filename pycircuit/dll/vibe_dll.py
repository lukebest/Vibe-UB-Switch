"""vibe_dll — DLL structural top (AS-0.1 §12).

Product module: ``rtl/dll/vibe_dll.sv``. Ports match tip
``5b071097`` / freeze ``302ac943``. SPEC / CR-B names are unchanged.
Hierarchy wrap (``clk`` / ``rst_n`` / ``port_rst`` / ``device_rst`` /
``link_up`` / ``fec_fail`` / 512b ``nw_dll_data`` / ``nw_dll_vld`` /
``nw_dll_ready`` / 512b ``dll_nw_data`` / ``dll_nw_vld`` /
``dll_nw_ready`` / 640b ``dll_pcs_data`` / ``dll_pcs_vld`` /
``dll_pcs_ready`` / 640b ``pcs_dll_data`` / ``pcs_dll_vld`` /
``pcs_dll_ready`` / ``status_up`` / ``disabled`` / ``retrain_req`` /
``retry_error`` / ``proto_err`` / ``fc_ovf`` / ``rx_ovf`` /
``cfg0_hit`` / 640b ``cfg0_data``). Parameter
``RETRY_WAIT_CYC`` default 12500 (passed to ``u_req``). First
DLL structural top after the eight DLL leaves (``vibe_bcrc`` /
``vibe_dll_credit`` / ``vibe_dll_sm`` / ``vibe_dll_rx`` /
``vibe_dll_retry_ack_sm`` / ``vibe_dll_retry_buf`` /
``vibe_dll_retry_req_sm`` / ``vibe_dll_tx``). Instantiates
already-migrated children: ``vibe_dll_sm u_sm``,
``vibe_dll_credit u_crd``, ``vibe_dll_retry_buf u_rbuf``,
``vibe_dll_retry_req_sm #(.RETRY_WAIT_CYC(...)) u_req``,
``vibe_dll_retry_ack_sm u_ack``, ``vibe_dll_tx u_tx``,
``vibe_dll_rx u_rx``. Wrap-local combo:
``proto_err = crd_proto | buf_proto``, ``fc_ovf = crd_ovf``.
Instantiated by ``vibe_port`` (later).

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own. Product RTL keeps
**async active-low** ``rst_n`` on the children. Landed SV is
hand-finished so the stock hierarchy (instances / nets /
ties) stays byte-identical in the module body. Leave PCS
tx / rx tops and ``vibe_fabric`` top for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

NW_W = 512
PCS_W = 640
FLIT_W = 160
SM_W = 2
PTR_W = 8
FREE_W = 9
PEND_W = 16
CONS_W = 10
RTY_W = 3
# Stock default; product SV parameter on u_req.
RETRY_WAIT_CYC = 12500

# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
CHILDREN = (
    {
        "module": "vibe_dll_sm",
        "inst": "u_sm",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "link_up": "link_up",
            "param_ok": "1'b1",
            "credit_ok": "1'b1",
            "dll_error": "retry_error || proto_err",
            "state": "sm_st",
            "status_up": "status_up",
            "disabled": "disabled",
        },
    },
    {
        "module": "vibe_dll_credit",
        "inst": "u_crd",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "link_up": "link_up",
            "grain_n": "8'd8",
            "consume_vld": "cons_vld",
            "consume_flits": "cons_flits",
            "is_cfg0": "cons_cfg0",
            "credit_ret": "force_ack",
            "credit_ret_n": "16'd1",
            "pending": "pending",
            "credit_low": "credit_low",
            "force_crd_ack": "force_ack",
            "bp_nw": "bp_nw",
            "proto_err": "crd_proto",
            "fc_ovf": "crd_ovf",
        },
    },
    {
        "module": "vibe_dll_retry_buf",
        "inst": "u_rbuf",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "link_up": "link_up",
            "wr_en": "wr_en",
            "is_null": "is_null",
            "is_retry": "is_retry",
            "wr_flit": "wr_flit",
            "send_size": "8'd4",
            "ack_rel": "1'b0",
            "rel_size": "8'd0",
            "rd_ptr_i": "rd_ptr",
            "rd_flit": "rd_flit",
            "wr_ptr": "wr_ptr",
            "tail_ptr": "tail_ptr",
            "rcv_ptr": "rcv_ptr",
            "num_free": "nfree",
            "proto_err": "buf_proto",
            "can_send": "can_send",
        },
    },
    {
        "module": "vibe_dll_retry_req_sm",
        "inst": "u_req",
        "params": {"RETRY_WAIT_CYC": "RETRY_WAIT_CYC"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "device_rst": "device_rst",
            "start_retry": "start_retry",
            "phy_retrain": "1'b0",
            "wait_done_ack": "1'b0",
            "state": "req_st",
            "drop_data": "drop_data",
            "retrain_req": "retrain_req",
            "retry_error": "retry_error",
            "send_idle": "send_idle",
            "send_req": "send_req",
            "send_cnt": "",
        },
    },
    {
        "module": "vibe_dll_retry_ack_sm",
        "inst": "u_ack",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "start_ack": "start_ack",
            "wr_ptr": "wr_ptr",
            "rcv_ptr": "rcv_ptr",
            "state": "ack_st",
            "send_idle": "",
            "send_ack": "send_ack",
            "replay": "replay",
            "rd_ptr": "rd_ptr",
        },
    },
    {
        "module": "vibe_dll_tx",
        "inst": "u_tx",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "link_up": "link_up",
            "status_up": "status_up",
            "credit_low": "credit_low",
            "bp_pending": "bp_nw",
            "drop_data": "drop_data",
            "can_send": "can_send",
            "replay": "replay",
            "replay_flit": "rd_flit",
            "send_idle": "send_idle",
            "send_req": "send_req",
            "send_ack": "send_ack",
            "nw_dll_data": "nw_dll_data",
            "nw_dll_vld": "nw_dll_vld",
            "nw_dll_ready": "nw_dll_ready",
            "dll_pcs_data": "dll_pcs_data",
            "dll_pcs_vld": "dll_pcs_vld",
            "dll_pcs_ready": "dll_pcs_ready",
            "wr_en": "wr_en",
            "wr_flit": "wr_flit",
            "is_null": "is_null",
            "is_retry": "is_retry",
            "consume_flits": "cons_flits",
            "consume_vld": "cons_vld",
            "consume_cfg0": "cons_cfg0",
        },
    },
    {
        "module": "vibe_dll_rx",
        "inst": "u_rx",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "port_rst": "port_rst",
            "link_up": "link_up",
            "fec_fail": "fec_fail",
            "pcs_dll_data": "pcs_dll_data",
            "pcs_dll_vld": "pcs_dll_vld",
            "pcs_dll_ready": "pcs_dll_ready",
            "dll_nw_data": "dll_nw_data",
            "dll_nw_vld": "dll_nw_vld",
            "dll_nw_ready": "dll_nw_ready",
            "cfg0_hit": "cfg0_hit",
            "cfg0_data": "cfg0_data",
            "bcrc_fail": "bcrc_fail",
            "start_retry": "start_retry",
            "rx_ovf": "rx_ovf",
            "start_ack": "start_ack",
        },
    },
)


@module(name="vibe_dll")
def build(m: Circuit) -> None:
    """DLL hierarchy wrap: seven children + proto/fc combo.

    Product ports (hand-finished SV)::

        clk, rst_n, port_rst, device_rst, link_up, fec_fail,
        nw_dll_data[511:0], nw_dll_vld, nw_dll_ready,
        dll_nw_data[511:0], dll_nw_vld, dll_nw_ready,
        dll_pcs_data[639:0], dll_pcs_vld, dll_pcs_ready,
        pcs_dll_data[639:0], pcs_dll_vld, pcs_dll_ready,
        status_up, disabled, retrain_req, retry_error,
        proto_err, fc_ovf, rx_ovf, cfg0_hit, cfg0_data[639:0]

    Parameter ``RETRY_WAIT_CYC`` default 12500 (``u_req``).
    pyCircuit clock is ``clk``. Reset here is ``rst``
    (active-high). Children keep async-low ``rst_n`` in the
    product SV. Frontend parks child-driven outputs at 0
    (same pattern as stage-16 ``vibe_pcs_tx_pack`` AM words).
    Wrap-local combo stays: ``proto_err = crd_proto | buf_proto``,
    ``fc_ovf = crd_ovf``. Product SV instantiates ``CHILDREN``.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    port_rst = m.input("port_rst", width=1)
    device_rst = m.input("device_rst", width=1)
    link_up = m.input("link_up", width=1)
    fec_fail = m.input("fec_fail", width=1)
    nw_dll_data = m.input("nw_dll_data", width=NW_W)
    nw_dll_vld = m.input("nw_dll_vld", width=1)
    dll_nw_ready = m.input("dll_nw_ready", width=1)
    dll_pcs_ready = m.input("dll_pcs_ready", width=1)
    pcs_dll_data = m.input("pcs_dll_data", width=PCS_W)
    pcs_dll_vld = m.input("pcs_dll_vld", width=1)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        port_rst
        | device_rst
        | link_up
        | fec_fail
        | nw_dll_vld
        | dll_nw_ready
        | dll_pcs_ready
        | pcs_dll_vld
        | (nw_dll_data == 0)
        | (pcs_dll_data == 0)
    )
    _ = (clk, rst, _keep, CHILDREN, RETRY_WAIT_CYC)

    # Child-driven nets parked at 0. Product SV wires u_crd /
    # u_rbuf proto + ovf into the wrap assigns below.
    crd_proto = u(1, 0)
    buf_proto = u(1, 0)
    crd_ovf = u(1, 0)
    proto_err = crd_proto | buf_proto
    fc_ovf = crd_ovf

    m.output("nw_dll_ready", u(1, 0))
    m.output("dll_nw_data", u(NW_W, 0))
    m.output("dll_nw_vld", u(1, 0))
    m.output("dll_pcs_data", u(PCS_W, 0))
    m.output("dll_pcs_vld", u(1, 0))
    m.output("pcs_dll_ready", u(1, 0))
    m.output("status_up", u(1, 0))
    m.output("disabled", u(1, 0))
    m.output("retrain_req", u(1, 0))
    m.output("retry_error", u(1, 0))
    m.output("proto_err", proto_err)
    m.output("fc_ovf", fc_ovf)
    m.output("rx_ovf", u(1, 0))
    m.output("cfg0_hit", u(1, 0))
    m.output("cfg0_data", u(PCS_W, 0))


build.__pycircuit_name__ = "vibe_dll"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_dll").emit_mlir())
