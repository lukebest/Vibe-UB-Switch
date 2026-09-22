"""Fabric / DLL / mgmt / NW / LMSM unit TCs. Same RTL lists as run_units.sh."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PY = Path(__file__).resolve().parent
def _wrap(name):
    return str(PY / "tb" / f"{name}.sv")


def _w(*p):
    return str(ROOT.joinpath("rtl", *p))


FAB = [
    _w("fabric", "vibe_saf_ing.sv"),
    _w("fabric", "vibe_route_lu.sv"),
    _w("fabric", "vibe_port_sel.sv"),
    _w("fabric", "vibe_xbar.sv"),
    _w("fabric", "vibe_voq_egr.sv"),
    _w("fabric", "vibe_vl_rr.sv"),
    _w("fabric", "vibe_fecn_mark.sv"),
    _w("fabric", "vibe_fabric.sv"),
]
MGMT = [
    _w("mgmt", "vibe_mgmt.sv"),
    _w("mgmt", "vibe_cfg_space.sv"),
    _w("mgmt", "vibe_cna_ep.sv"),
    _w("mgmt", "vibe_irq_agg.sv"),
    _w("mgmt", "vibe_rst_ctl.sv"),
]
DLL_RX = [_w("dll", "vibe_dll_rx.sv")]
RETRY_REQ = [_w("dll", "vibe_dll_retry_req_sm.sv")]

UNIT_MORE = [
    ("tc_irq_agg", "vibe_irq_agg", [_w("mgmt", "vibe_irq_agg.sv")], "entry_unit"),
    ("tc_rst_port_device", "vibe_rst_ctl", [_w("mgmt", "vibe_rst_ctl.sv")], "entry_unit"),
    ("tc_fecn_mark", "vibe_fecn_mark", [_w("fabric", "vibe_fecn_mark.sv")], "entry_unit"),
    ("tc_credit_grain_n", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_credit_no_underflow", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_nw_adapt_linkready", "vibe_nw_adapt", [_w("nw", "vibe_nw_adapt.sv")], "entry_unit"),
    ("tc_phy_nw_dll_512b", "vibe_nw_adapt", [_w("nw", "vibe_nw_adapt.sv")], "entry_unit"),
    ("tc_saf_ing", "vibe_saf_ing", [_w("fabric", "vibe_saf_ing.sv")], "entry_unit"),
    ("tc_voq_rd", "vibe_voq_egr", [_w("fabric", "vibe_voq_egr.sv")], "entry_unit"),
    ("tc_dll_sm_states", "vibe_dll_sm", [_w("dll", "vibe_dll_sm.sv")], "entry_unit"),
    ("tc_mgmt_byp", "vibe_mgmt_byp", [_w("mgmt", "vibe_mgmt_byp.sv")], "entry_unit"),
    ("tc_xbar_unit", "vibe_xbar_cocotb_top",
     [_wrap("vibe_xbar_cocotb_top"), _w("fabric", "vibe_xbar.sv")], "entry_unit"),
    ("tc_cna_ep", "vibe_cna_ep_cocotb_top",
     [_wrap("vibe_cna_ep_cocotb_top"), _w("mgmt", "vibe_cna_ep.sv")], "entry_unit"),
    ("tc_credit_timeout_1us", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_deadlock_timeout_1us", "vibe_voq_egr", [_w("fabric", "vibe_voq_egr.sv")], "entry_unit"),
    ("tc_retry_buf_256", "vibe_dll_retry_buf", [_w("dll", "vibe_dll_retry_buf.sv")], "entry_unit"),
    ("tc_retry_req_gbn", "vibe_retry_req_cocotb_top",
     [_wrap("vibe_retry_req_cocotb_top")] + RETRY_REQ, "entry_unit"),
    ("tc_retry_ack_replay", "vibe_dll_retry_ack_sm",
     [_w("dll", "vibe_dll_retry_ack_sm.sv")], "entry_unit"),
    ("tc_retry_wait_retrain", "vibe_retry_req_cocotb_top",
     [_wrap("vibe_retry_req_cocotb_top")] + RETRY_REQ, "entry_unit"),
    ("tc_icrc_txrx_vs_transit", "vibe_icrc", [_w("nw", "vibe_icrc.sv")], "entry_unit"),
    ("tc_pma_512b_slice", "vibe_pma_bnd", [_w("pma", "vibe_pma_bnd.sv")], "entry_unit"),
    ("tc_afifo_afull10", "vibe_afifo",
     [_w("cdc", "vibe_afifo.sv"), _w("cdc", "vibe_sync2.sv")], "entry_unit"),
    ("tc_vibe_afifo", "vibe_afifo_cocotb_top",
     [_wrap("vibe_afifo_cocotb_top"),
      _w("cdc", "vibe_afifo.sv"), _w("cdc", "vibe_sync2.sv")], "entry_unit"),
    ("tc_lmsm_walk", "vibe_lmsm", [_w("lmsm", "vibe_lmsm.sv")], "entry_unit"),
    ("tc_lmsm_vlock", "vibe_lmsm", [_w("lmsm", "vibe_lmsm.sv")], "entry_unit"),
    ("tc_lmsm_cc", "vibe_lmsm", [_w("lmsm", "vibe_lmsm.sv")], "entry_unit"),
    ("tc_cfg0_term_not_fabric", "vibe_dll_rx_cocotb_top",
     [_wrap("vibe_dll_rx_cocotb_top")] + DLL_RX, "entry_unit"),
    ("tc_dll_rx_errflag", "vibe_dll_rx_cocotb_top",
     [_wrap("vibe_dll_rx_cocotb_top")] + DLL_RX, "entry_unit"),
    ("tc_fec_fail_gbn", "vibe_dll_rx_cocotb_top",
     [_wrap("vibe_dll_rx_cocotb_top")] + DLL_RX, "entry_unit"),
    ("tc_rt_g1_official", "vibe_rt_g1_cocotb_top",
     [_wrap("vibe_rt_g1_cocotb_top"), _w("fabric", "vibe_route_lu.sv"),
      _w("fabric", "vibe_port_sel.sv")],
     "entry_unit"),
    ("tc_dll_tx_cfg0", "vibe_dll_tx_cfg0_cocotb_top",
     [_wrap("vibe_dll_tx_cfg0_cocotb_top"), _w("dll", "vibe_dll_tx.sv"),
      _w("dll", "vibe_bcrc.sv"), _w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_mgmt", "vibe_mgmt", MGMT, "entry_unit"),
    ("tc_timers_indep", "vibe_timers_indep_cocotb_top",
     [_wrap("vibe_timers_indep_cocotb_top"),
      _w("dll", "vibe_dll_credit.sv"), _w("fabric", "vibe_voq_egr.sv")],
     "entry_unit"),
]
