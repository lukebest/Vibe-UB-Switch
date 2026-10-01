"""vibe_ub_switch — chip-top structural wrap (AS-0.1.2 §4/§17).

Product module: ``rtl/top/vibe_ub_switch.sv``. Ports match tip
``cb644804`` / product body ``260dc6db``. Decision I UNFROZEN
(do not re-pin freeze). SPEC / CR-B names are unchanged.
Hierarchy wrap (``clk_fab`` / ``rst_n`` / ``txclk_0..3`` /
``rxclk_0..3`` / 512b ``pcs_pma_txdata_0..3`` /
``pma_pcs_rxdata_0..3`` / ``cfg_wr_vld`` / ``cfg_wr_ready`` /
4b ``cfg_wr_cmd`` / 16b ``cfg_wr_idx`` / 32b ``cfg_wr_data`` /
``irq_logic``). Parameter ``ROUTE_TABLE_DEPTH`` default 256
(passed to ``u_fab`` / ``u_mgmt``). First chip-top structural
wrap after stage-43 ``vibe_port``. Instantiates stock children:
4× ``vibe_port g_port[gi].u_port``, ``vibe_fabric
#(.ROUTE_TABLE_DEPTH(...)) u_fab``, ``vibe_mgmt
#(.ROUTE_TABLE_DEPTH(...)) u_mgmt``, 4× ``vibe_mgmt_byp
g_byp[gi].u_byp``. ``vibe_fabric`` / ``vibe_mgmt`` are stock
SV (no pyCircuit wrap yet) — listed in CHILDREN, not
migrated here. Wrap-local: packed ``txclk`` / ``rxclk`` /
``pma_pcs_rxdata`` / ``pcs_pma_txdata`` pin maps. Do not
rewrite F1 ``ovf_l`` (lives under ``vibe_port``; top must
not ECO it). Do not invent Appendix D / CFG opcode 0x10
packing.

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own. Product RTL keeps
**async active-low** ``rst_n`` on the children. Landed SV is
hand-finished so the stock hierarchy (ports / generate
loops / instances ``g_port`` / ``u_fab`` / ``u_mgmt`` /
``g_byp`` / nets) stays byte-identical in the module body.
Leave ``vibe_mgmt`` / ``vibe_fabric`` wraps for later stages.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

PMA_W = 512
N_PORT = 4
CFG_CMD_W = 4
CFG_IDX_W = 16
CFG_DATA_W = 32
# Stock default; product SV parameter on u_fab / u_mgmt.
ROUTE_TABLE_DEPTH = 256


def _port(gi: int):
    return {
        "module": "vibe_port",
        "inst": f"g_port[{gi}].u_port",
        "params": {},
        "connects": {
            "clk_fab": "clk_fab",
            "rst_n": "rst_n",
            "port_rst": f"port_rst[{gi}]",
            "device_rst": "device_rst",
            "lmsm_go": f"lmsm_go[{gi}]",
            "txclk": f"txclk[{gi}]",
            "rxclk": f"rxclk[{gi}]",
            "pcs_pma_txdata": f"pcs_pma_txdata[{gi}]",
            "pma_pcs_rxdata": f"pma_pcs_rxdata[{gi}]",
            "fab_nw_data": f"fab_nw_data[{gi}]",
            "fab_nw_vld": f"fab_nw_vld[{gi}]",
            "fab_nw_ready": f"fab_nw_ready[{gi}]",
            "nw_fab_data": f"nw_fab_data[{gi}]",
            "nw_fab_vld": f"nw_fab_vld[{gi}]",
            "nw_fab_ready": f"nw_fab_ready[{gi}]",
            "mgmt_nw_data": f"mgmt_nw_data[{gi}]",
            "mgmt_nw_vld": f"mgmt_nw_vld[{gi}]",
            "mgmt_nw_ready": f"mgmt_nw_ready[{gi}]",
            "status_up": f"status_up[{gi}]",
            "disabled": f"disabled[{gi}]",
            "retry_error": f"retry_error[{gi}]",
            "proto_err": f"proto_err[{gi}]",
            "fc_ovf": f"fc_ovf[{gi}]",
            "rx_ovf": f"rx_ovf[{gi}]",
            "afifo_ovf": f"afifo_ovf[{gi}]",
            "cfg0_hit": "",
            "cfg0_data": "",
        },
    }


def _byp(gi: int):
    return {
        "module": "vibe_mgmt_byp",
        "inst": f"g_byp[{gi}].u_byp",
        "params": {},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "in_data": f"mgmt_nw_push[{gi}]",
            "in_vld": f"mgmt_nw_push_vld[{gi}]",
            "in_ready": f"mgmt_nw_push_ready[{gi}]",
            "out_data": f"mgmt_nw_data[{gi}]",
            "out_vld": f"mgmt_nw_vld[{gi}]",
            "out_ready": f"mgmt_nw_ready[{gi}]",
        },
    }


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
# vibe_fabric / vibe_mgmt are stock SV (no wrap yet) — HOLD.
CHILDREN = (
    _port(0),
    _port(1),
    _port(2),
    _port(3),
    {
        "module": "vibe_fabric",
        "inst": "u_fab",
        "params": {"ROUTE_TABLE_DEPTH": "ROUTE_TABLE_DEPTH"},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
            "device_rst": "device_rst",
            "status_up": "status_up",
            "default_bm": "default_bm",
            "rt_wr_en": "rt_wr_en",
            "rt_wr_idx": "rt_wr_idx",
            "rt_wr_data": "rt_wr_data",
            "nw_fab_data": "nw_fab_data",
            "nw_fab_vld": "nw_fab_vld",
            "nw_fab_ready": "nw_fab_ready",
            "fab_nw_data": "fab_nw_data",
            "fab_nw_vld": "fab_nw_vld",
            "fab_nw_ready": "fab_nw_ready",
            "len_err": "len_err",
            "drop_g1": "drop_g1",
            "rt_shortest_unimpl": "rt_shortest_unimpl",
            "drop_down_cnt": "drop_down",
            "deadlock_drop": "deadlock_drop",
            "irq_rt": "",
            "cna": "cna",
            "cna_written": "cna_written",
            "fab_mgmt_cfg6_hit": "fab_mgmt_cfg6_hit",
            "fab_mgmt_cfg6_data": "fab_mgmt_cfg6_data",
        },
    },
    {
        "module": "vibe_mgmt",
        "inst": "u_mgmt",
        "params": {"ROUTE_TABLE_DEPTH": "ROUTE_TABLE_DEPTH"},
        "connects": {
            "clk": "clk_fab",
            "rst_n": "rst_n",
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
            "port_rst": "port_rst",
            "device_rst": "device_rst",
            "lmsm_go": "lmsm_go",
            "fab_mgmt_cfg6_hit": "fab_mgmt_cfg6_hit",
            "fab_mgmt_cfg6_data": "fab_mgmt_cfg6_data",
            "mgmt_fab_cfg6_consume": "mgmt_fab_cfg6_consume",
            "mgmt_nw_data": "mgmt_nw_push",
            "mgmt_nw_vld": "mgmt_nw_push_vld",
            "mgmt_nw_ready": "mgmt_nw_push_ready",
            "rx_ovf": "rx_ovf",
            "fc_ovf": "fc_ovf",
            "proto_err": "proto_err",
            "retry_error": "retry_error",
            "len_err": "len_err",
            "deadlock_drop": "deadlock_drop",
            "drop_g1": "drop_g1",
            "afifo_ovf": "afifo_ovf",
            "irq_logic": "irq_logic",
        },
    },
    _byp(0),
    _byp(1),
    _byp(2),
    _byp(3),
)


@module(name="vibe_ub_switch")
def build(m: Circuit) -> None:
    """Chip-top hierarchy wrap: 4× port / fabric / mgmt / 4× byp.

    Product ports (hand-finished SV)::

        clk_fab, rst_n, txclk_0..3, rxclk_0..3,
        pcs_pma_txdata_0..3[511:0], pma_pcs_rxdata_0..3[511:0],
        cfg_wr_vld, cfg_wr_ready, cfg_wr_cmd[3:0],
        cfg_wr_idx[15:0], cfg_wr_data[31:0], irq_logic

    Parameter ``ROUTE_TABLE_DEPTH`` default 256 (``u_fab`` /
    ``u_mgmt``). pyCircuit clock is ``clk_fab`` plus the
    eight PMA clocks. Reset here is ``rst`` (active-high).
    Children keep async-low ``rst_n`` in the product SV.
    Frontend parks child-driven outputs at 0 (same pattern
    as stage-43 ``vibe_port``). Product SV instantiates
    ``CHILDREN``. ``vibe_fabric`` / ``vibe_mgmt`` wraps
    remain HOLD (stock SV only).
    """
    clk_fab = m.clock("clk_fab")
    txclk_0 = m.clock("txclk_0")
    txclk_1 = m.clock("txclk_1")
    txclk_2 = m.clock("txclk_2")
    txclk_3 = m.clock("txclk_3")
    rxclk_0 = m.clock("rxclk_0")
    rxclk_1 = m.clock("rxclk_1")
    rxclk_2 = m.clock("rxclk_2")
    rxclk_3 = m.clock("rxclk_3")
    rst = m.reset("rst")
    pma_pcs_rxdata_0 = m.input("pma_pcs_rxdata_0", width=PMA_W)
    pma_pcs_rxdata_1 = m.input("pma_pcs_rxdata_1", width=PMA_W)
    pma_pcs_rxdata_2 = m.input("pma_pcs_rxdata_2", width=PMA_W)
    pma_pcs_rxdata_3 = m.input("pma_pcs_rxdata_3", width=PMA_W)
    cfg_wr_vld = m.input("cfg_wr_vld", width=1)
    cfg_wr_cmd = m.input("cfg_wr_cmd", width=CFG_CMD_W)
    cfg_wr_idx = m.input("cfg_wr_idx", width=CFG_IDX_W)
    cfg_wr_data = m.input("cfg_wr_data", width=CFG_DATA_W)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        cfg_wr_vld
        | (cfg_wr_cmd == 0)
        | (cfg_wr_idx == 0)
        | (cfg_wr_data == 0)
        | (pma_pcs_rxdata_0 == 0)
        | (pma_pcs_rxdata_1 == 0)
        | (pma_pcs_rxdata_2 == 0)
        | (pma_pcs_rxdata_3 == 0)
    )
    _ = (
        clk_fab,
        txclk_0,
        txclk_1,
        txclk_2,
        txclk_3,
        rxclk_0,
        rxclk_1,
        rxclk_2,
        rxclk_3,
        rst,
        _keep,
        CHILDREN,
        ROUTE_TABLE_DEPTH,
        N_PORT,
    )

    m.output("pcs_pma_txdata_0", u(PMA_W, 0))
    m.output("pcs_pma_txdata_1", u(PMA_W, 0))
    m.output("pcs_pma_txdata_2", u(PMA_W, 0))
    m.output("pcs_pma_txdata_3", u(PMA_W, 0))
    m.output("cfg_wr_ready", u(1, 0))
    m.output("irq_logic", u(1, 0))


build.__pycircuit_name__ = "vibe_ub_switch"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_ub_switch").emit_mlir())
