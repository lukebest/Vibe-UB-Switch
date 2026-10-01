"""vibe_mgmt — chip mgmt hierarchy wrap (AS-0.1.2 §4/§10).

Product module: ``rtl/mgmt/vibe_mgmt.sv``. Ports match tip
``72e53573`` / product body ``7924cf44``. Decision I UNFROZEN
(do not re-pin freeze). SPEC / CR-B names are unchanged.
Hierarchy wrap (``clk`` / ``rst_n`` / ``cfg_wr_vld`` /
``cfg_wr_ready`` / 4b ``cfg_wr_cmd`` / 16b ``cfg_wr_idx`` /
32b ``cfg_wr_data`` / 16b ``cna`` / ``cna_written`` /
4b ``default_bm`` / ``rt_wr_en`` / 16b ``rt_wr_idx`` /
32b ``rt_wr_data`` / 4b ``port_rst`` / ``device_rst`` /
4b ``lmsm_go`` / 4b ``fab_mgmt_cfg6_hit`` / unpacked
512b ``fab_mgmt_cfg6_data[0:3]`` / 4b
``mgmt_fab_cfg6_consume`` / unpacked 512b
``mgmt_nw_data[0:3]`` / 4b ``mgmt_nw_vld`` / 4b
``mgmt_nw_ready`` / 4b ``rx_ovf`` / 4b ``fc_ovf`` /
4b ``proto_err`` / 4b ``retry_error`` / 4b ``len_err`` /
4b ``deadlock_drop`` / ``drop_g1`` / 4b ``afifo_ovf`` /
``irq_logic``). Parameter ``ROUTE_TABLE_DEPTH`` default
256 (passed to ``u_cfg``). First mgmt-hierarchy wrap after
stage-42 ``vibe_cfg_space`` and stage-44 ``vibe_ub_switch``.
Instantiates stock children: ``vibe_cfg_space
#(.ROUTE_TABLE_DEPTH(...)) u_cfg``, ``vibe_rst_ctl u_rst``,
``vibe_cna_ep u_cna``, ``vibe_irq_agg u_irq``. Children
already have pyCircuit wraps (stages 38–42). Wrap-local:
``port_rst = port_rst_hold | port_rst_rw1c``. Do not
rewrite F1 ``ovf_l`` (lives under ``vibe_port``; mgmt
must not ECO it). Do not invent Appendix D / CFG opcode
0x10 packing. ``vibe_fabric`` wrap stays HOLD.

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own. Product RTL keeps
**async active-low** ``rst_n`` on the children. Landed SV is
hand-finished so the stock hierarchy (ports / instances
``u_cfg`` / ``u_rst`` / ``u_cna`` / ``u_irq`` / local
wires / ``port_rst`` OR) stays byte-identical in the
module body. Leave ``vibe_fabric`` for a later stage.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PORT_N = 4
CFG_CMD_W = 4
CFG_IDX_W = 16
CFG_DATA_W = 32
CNA_W = 16
DATA_W = 512
# Stock default; product SV parameter on u_cfg.
ROUTE_TABLE_DEPTH = 256


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
CHILDREN = (
    {
        "module": "vibe_cfg_space",
        "inst": "u_cfg",
        "params": {"ROUTE_TABLE_DEPTH": "ROUTE_TABLE_DEPTH"},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "device_rst": "device_rst",
            "cfg_wr_vld": "cfg_wr_vld",
            "cfg_wr_ready": "cfg_wr_ready",
            "cfg_wr_cmd": "cfg_wr_cmd",
            "cfg_wr_idx": "cfg_wr_idx",
            "cfg_wr_data": "cfg_wr_data",
            "cna": "cna",
            "cna_written": "cna_written",
            "default_bm": "default_bm",
            "rt_wr_en": "rt_wr_en",
            "rt_wr_idx": "rt_wr_idx",
            "rt_wr_data": "rt_wr_data",
            "port_rst_pulse": "port_rst_pulse",
            "port_rst_hold": "port_rst_hold",
            "port_rst_rw1c": "port_rst_rw1c",
            "device_rst_pulse": "device_rst_pulse",
            "lmsm_go_pulse": "lmsm_go",
            "irq_clr": "irq_clr",
            "guid0": "",
            "class_code": "",
            "port_basic": "",
            "port_cap": "",
        },
    },
    {
        "module": "vibe_rst_ctl",
        "inst": "u_rst",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "device_rst_pulse": "device_rst_pulse",
            "port_rst_pulse": "port_rst_pulse",
            "device_rst": "device_rst",
            "port_rst": "port_rst_hold",
        },
    },
    {
        "module": "vibe_cna_ep",
        "inst": "u_cna",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "cna": "cna",
            "cna_written": "cna_written",
            "fab_mgmt_cfg6_hit": "fab_mgmt_cfg6_hit",
            "fab_mgmt_cfg6_data": "fab_mgmt_cfg6_data",
            "mgmt_fab_cfg6_consume": "mgmt_fab_cfg6_consume",
            "mgmt_nw_data": "mgmt_nw_data",
            "mgmt_nw_vld": "mgmt_nw_vld",
            "mgmt_nw_ready": "mgmt_nw_ready",
            "icrc_fail": "icrc_fail",
        },
    },
    {
        "module": "vibe_irq_agg",
        "inst": "u_irq",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "irq_clr": "irq_clr | device_rst",
            "rx_ovf": "rx_ovf",
            "fc_ovf": "fc_ovf",
            "proto_err": "proto_err",
            "retry_error": "retry_error",
            "icrc_fail": "icrc_fail",
            "len_err": "len_err",
            "deadlock_drop": "deadlock_drop",
            "drop_g1": "drop_g1",
            "afifo_ovf": "afifo_ovf",
            "irq_logic": "irq_logic",
        },
    },
)


@module(name="vibe_mgmt")
def build(m: Circuit) -> None:
    """Mgmt hierarchy wrap: cfg_space / rst_ctl / cna_ep / irq_agg.

    Product ports (hand-finished SV)::

        clk, rst_n, cfg_wr_vld, cfg_wr_ready, cfg_wr_cmd[3:0],
        cfg_wr_idx[15:0], cfg_wr_data[31:0], cna[15:0],
        cna_written, default_bm[3:0], rt_wr_en, rt_wr_idx[15:0],
        rt_wr_data[31:0], port_rst[3:0], device_rst, lmsm_go[3:0],
        fab_mgmt_cfg6_hit[3:0], fab_mgmt_cfg6_data[511:0][0:3],
        mgmt_fab_cfg6_consume[3:0], mgmt_nw_data[511:0][0:3],
        mgmt_nw_vld[3:0], mgmt_nw_ready[3:0], rx_ovf[3:0],
        fc_ovf[3:0], proto_err[3:0], retry_error[3:0],
        len_err[3:0], deadlock_drop[3:0], drop_g1,
        afifo_ovf[3:0], irq_logic

    Parameter ``ROUTE_TABLE_DEPTH`` default 256 (``u_cfg``).
    pyCircuit clock is ``clk``. Reset here is ``rst``
    (active-high). Children keep async-low ``rst_n`` in the
    product SV. Unpacked product arrays are flattened here
    (``fab_mgmt_cfg6_data_0..3``, ``mgmt_nw_data_0..3``).
    Frontend parks child-driven outputs at 0 (same pattern
    as stage-44 ``vibe_ub_switch``). Product SV instantiates
    ``CHILDREN``. ``vibe_fabric`` wrap remains HOLD.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    cfg_wr_vld = m.input("cfg_wr_vld", width=1)
    cfg_wr_cmd = m.input("cfg_wr_cmd", width=CFG_CMD_W)
    cfg_wr_idx = m.input("cfg_wr_idx", width=CFG_IDX_W)
    cfg_wr_data = m.input("cfg_wr_data", width=CFG_DATA_W)
    fab_mgmt_cfg6_hit = m.input("fab_mgmt_cfg6_hit", width=PORT_N)
    fab_mgmt_cfg6_data = [
        m.input(f"fab_mgmt_cfg6_data_{p}", width=DATA_W) for p in range(PORT_N)
    ]
    mgmt_nw_ready = m.input("mgmt_nw_ready", width=PORT_N)
    rx_ovf = m.input("rx_ovf", width=PORT_N)
    fc_ovf = m.input("fc_ovf", width=PORT_N)
    proto_err = m.input("proto_err", width=PORT_N)
    retry_error = m.input("retry_error", width=PORT_N)
    len_err = m.input("len_err", width=PORT_N)
    deadlock_drop = m.input("deadlock_drop", width=PORT_N)
    drop_g1 = m.input("drop_g1", width=1)
    afifo_ovf = m.input("afifo_ovf", width=PORT_N)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        cfg_wr_vld
        | drop_g1
        | (cfg_wr_cmd == 0)
        | (cfg_wr_idx == 0)
        | (cfg_wr_data == 0)
        | (fab_mgmt_cfg6_hit == 0)
        | (mgmt_nw_ready == 0)
        | (rx_ovf == 0)
        | (fc_ovf == 0)
        | (proto_err == 0)
        | (retry_error == 0)
        | (len_err == 0)
        | (deadlock_drop == 0)
        | (afifo_ovf == 0)
        | (fab_mgmt_cfg6_data[0] == 0)
        | (fab_mgmt_cfg6_data[1] == 0)
        | (fab_mgmt_cfg6_data[2] == 0)
        | (fab_mgmt_cfg6_data[3] == 0)
    )
    _ = (clk, rst, _keep, CHILDREN, ROUTE_TABLE_DEPTH, PORT_N)

    m.output("cfg_wr_ready", u(1, 0))
    m.output("cna", u(CNA_W, 0))
    m.output("cna_written", u(1, 0))
    m.output("default_bm", u(PORT_N, 0))
    m.output("rt_wr_en", u(1, 0))
    m.output("rt_wr_idx", u(CFG_IDX_W, 0))
    m.output("rt_wr_data", u(CFG_DATA_W, 0))
    m.output("port_rst", u(PORT_N, 0))
    m.output("device_rst", u(1, 0))
    m.output("lmsm_go", u(PORT_N, 0))
    m.output("mgmt_fab_cfg6_consume", u(PORT_N, 0))
    m.output("mgmt_nw_data_0", u(DATA_W, 0))
    m.output("mgmt_nw_data_1", u(DATA_W, 0))
    m.output("mgmt_nw_data_2", u(DATA_W, 0))
    m.output("mgmt_nw_data_3", u(DATA_W, 0))
    m.output("mgmt_nw_vld", u(PORT_N, 0))
    m.output("irq_logic", u(1, 0))


build.__pycircuit_name__ = "vibe_mgmt"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_mgmt").emit_mlir())
