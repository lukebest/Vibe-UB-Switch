"""RTL file lists and TC → (toplevel, sources, module) mapping."""

from __future__ import annotations

from pathlib import Path

from catalog_more import UNIT_MORE
from catalog_pcs import UNIT_PCS, _no_input_default

ROOT = Path(__file__).resolve().parents[3]
RTL = ROOT / "rtl"
PY = Path(__file__).resolve().parent
TBV = ROOT / "tb" / "vibe"

INC = [str(RTL / "common"), str(TBV / "common")]


def _w(*parts):
    return str(RTL.joinpath(*parts))


FAB_RTL = [
    _w("fabric", "vibe_saf_ing.sv"),
    _w("fabric", "vibe_route_lu.sv"),
    _w("fabric", "vibe_port_sel.sv"),
    _w("fabric", "vibe_xbar.sv"),
    _w("fabric", "vibe_voq_egr.sv"),
    _w("fabric", "vibe_vl_rr.sv"),
    _w("fabric", "vibe_fecn_mark.sv"),
    _w("fabric", "vibe_fabric.sv"),
    _w("mgmt", "vibe_cfg_space.sv"),
    _w("mgmt", "vibe_cna_ep.sv"),
    _w("mgmt", "vibe_irq_agg.sv"),
    _w("mgmt", "vibe_rst_ctl.sv"),
    _w("mgmt", "vibe_mgmt.sv"),
]

PORT_RTL = [
    _w("cdc", "vibe_sync2.sv"),
    _w("cdc", "vibe_afifo.sv"),
    _w("cdc", "vibe_rst_sync.sv"),
    _w("cdc", "vibe_gear_160_128.sv"),
    _w("cdc", "vibe_gear_128_160.sv"),
    _w("pma", "vibe_pma_bnd.sv"),
    _w("pcs", "vibe_pcs_tx.sv"),
    _w("pcs", "vibe_pcs_tx_g1.sv"),
    _w("pcs", "vibe_pcs_tx_fec.sv"),
    _w("pcs", "vibe_rs128_120_enc.sv"),
    _w("pcs", "vibe_pcs_tx_cw2beat.sv"),
    _w("pcs", "vibe_pcs_tx_pack.sv"),
    _w("pcs", "vibe_pcs_tx_amctl.sv"),
    _w("pcs", "vibe_ebch16.sv"),
    _w("pcs", "vibe_pcs_scramble.sv"),
    _no_input_default("pcs", "vibe_pcs_rx.sv"),
    _w("pcs", "vibe_pcs_rx_amctl_lock.sv"),
    _w("pcs", "vibe_pcs_rx_deskew.sv"),
    _no_input_default("pcs", "vibe_pcs_rx_unpack.sv"),
    _no_input_default("pcs", "vibe_pcs_rx_fec.sv"),
    _w("pcs", "vibe_rs128_120_dec.sv"),
    _w("lmsm", "vibe_lmsm.sv"),
    _w("dll", "vibe_dll.sv"),
    _w("dll", "vibe_dll_sm.sv"),
    _w("dll", "vibe_dll_credit.sv"),
    _w("dll", "vibe_dll_retry_buf.sv"),
    _w("dll", "vibe_dll_retry_req_sm.sv"),
    _w("dll", "vibe_dll_retry_ack_sm.sv"),
    _w("dll", "vibe_dll_tx.sv"),
    _w("dll", "vibe_dll_rx.sv"),
    _w("dll", "vibe_bcrc.sv"),
    _w("nw", "vibe_nw_adapt.sv"),
    _w("port", "vibe_port.sv"),
]

TOP_RTL = PORT_RTL + FAB_RTL + [
    _w("mgmt", "vibe_mgmt_byp.sv"),
    _w("top", "vibe_ub_switch.sv"),
]

FAB_TOP = str(PY / "tb" / "vibe_fab_cocotb_top.sv")
PORT_TOP = str(PY / "tb" / "vibe_port_cocotb_top.sv")
SWITCH_TOP = str(PY / "tb" / "vibe_switch_cocotb_top.sv")

SUITE_TESTS = [
    "tc_suite_all",
    "tc_rt00_per_flow_rr_fwd",
    "tc_rt01_per_packet_rr_fwd",
    "tc_rt10_must_drop",
    "tc_rt11_must_drop",
    "tc_rt_shortest_unimpl_count",
    "tc_rt_shortest_irq_logic",
    "tc_rt_irq_logic_sticky",
    "tc_rt_no_rewrite",
    "tc_rt10_not_as_rt00",
    "tc_rt_counter_32b_sat",
    "tc_cfg_identity_guid_class",
    "tc_default_rt_all0_port0",
    "tc_pkt_len_err_drop",
    "tc_cfg6_term_vs_fwd",
    "tc_saf_full_pkt",
    "tc_icrc_transit_no_recompute",
    "tc_cfg3_fwd",
    "tc_cfg4_fwd",
    "tc_cfg5_fwd",
    "tc_cfg7_fwd",
    "tc_cfg9_fwd",
    "tc_cfg0_fabric_no_special",
    "tc_cfg_reserved_fwd",
    "tc_cfg_fwd_class",
    "tc_port_rst_via_cfg",
    "tc_device_rst_via_cfg",
    "tc_pkt_len_legal_16_4300",
    "tc_cfg9_no_icrc",
]

# (name, toplevel, extra sources, entry module)
UNIT_SIM = [
    ("tc_vl_rr", "vibe_vl_rr", [_w("fabric", "vibe_vl_rr.sv")], "entry_unit"),
    ("tc_vl_rr_0_15", "vibe_vl_rr", [_w("fabric", "vibe_vl_rr.sv")], "entry_unit"),
    ("tc_lmsm_idle_discovery", "vibe_lmsm", [_w("lmsm", "vibe_lmsm.sv")], "entry_unit"),
    ("tc_neg_absent_features", "vibe_lmsm", [_w("lmsm", "vibe_lmsm.sv")], "entry_unit"),
    ("tc_bcrc_crc30", "vibe_bcrc", [_w("dll", "vibe_bcrc.sv")], "entry_unit"),
    ("tc_rst_sync", "vibe_rst_sync", [_w("cdc", "vibe_rst_sync.sv")], "entry_unit"),
    ("tc_p0_down_drop", "vibe_port_sel", [_w("fabric", "vibe_port_sel.sv")], "entry_unit"),
    ("tc_route_lu", "vibe_route_lu", [_w("fabric", "vibe_route_lu.sv")], "entry_unit"),
    ("tc_cfg0_no_credit", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_credit_1024_flit_bp", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_credit_1024_hole", "vibe_dll_credit", [_w("dll", "vibe_dll_credit.sv")], "entry_unit"),
    ("tc_identity_cfg_space", "vibe_cfg_space", [_w("mgmt", "vibe_cfg_space.sv")], "entry_unit"),
    ("tc_cna_16bit", "vibe_cfg_space", [_w("mgmt", "vibe_cfg_space.sv")], "entry_unit"),
] + UNIT_MORE + UNIT_PCS

PORT_TESTS = [
    ("tc_port_smoke", "vibe_port_cocotb_top", [PORT_TOP] + PORT_RTL, "entry_port"),
    ("tc_nw_pkt_to_pma_tx", "vibe_port_cocotb_top", [PORT_TOP] + PORT_RTL, "entry_port"),
    ("tc_nw_pkt_pma_loopback", "vibe_port_cocotb_top", [PORT_TOP] + PORT_RTL, "entry_port"),
]

# Old Icarus name → new uvm-python test (same identifier when possible).
NAME_MAP = {
    "make suite / vibe_suite tasks": "tc_suite_all + per-TC UVM_TESTNAME (entry_fab)",
    "make units / run_units.sh": "make units (static + UNIT_SIM + port)",
    "make afifo / tc_vibe_afifo": "tc_vibe_afifo (vibe_afifo_cocotb_top, module-level)",
    "make sync2 / tc_vibe_sync2": "tc_vibe_sync2 (vibe_sync2_cocotb_top, module-level)",
    "Icarus tc_dll (full stack)": "tc_dll (vibe_dll_cocotb_top; TP-DLL-004 split)",
    "make rst_sync / tc_vibe_rst_sync": "tc_vibe_rst_sync (vibe_rst_sync_cocotb_top, module-level)",
    "make gear_128_160 / tc_vibe_gear_128_160":
        "tc_vibe_gear_128_160 (vibe_gear_128_160_cocotb_top, module-level)",
    "make gear_160_128 / tc_vibe_gear_160_128":
        "tc_vibe_gear_160_128 (vibe_gear_160_128_cocotb_top, module-level)",
    "make pcs_scramble / tc_vibe_pcs_scramble":
        "tc_vibe_pcs_scramble (vibe_pcs_scramble_cocotb_top, module-level)",
    "make ebch16 / tc_vibe_ebch16":
        "tc_vibe_ebch16 (vibe_ebch16_cocotb_top, module-level)",
    "make cw2beat / tc_vibe_pcs_tx_cw2beat":
        "tc_vibe_pcs_tx_cw2beat (vibe_pcs_tx_cw2beat_cocotb_top, module-level)",
    "make amctl / tc_vibe_pcs_tx_amctl":
        "tc_vibe_pcs_tx_amctl (vibe_pcs_tx_amctl_cocotb_top, module-level)",
    "make rs128_120_enc / tc_vibe_rs128_120_enc":
        "tc_vibe_rs128_120_enc (vibe_rs128_120_enc_cocotb_top, module-level)",
    "make rs128_120_dec / tc_vibe_rs128_120_dec":
        "tc_vibe_rs128_120_dec (vibe_rs128_120_dec_cocotb_top, module-level)",
    "make deskew / tc_vibe_pcs_rx_deskew":
        "tc_vibe_pcs_rx_deskew (vibe_pcs_rx_deskew_cocotb_top, module-level)",
    "make amctl_lock / tc_vibe_pcs_rx_amctl_lock":
        "tc_vibe_pcs_rx_amctl_lock (vibe_pcs_rx_amctl_lock_cocotb_top, module-level)",
    "make unpack / tc_vibe_pcs_rx_unpack":
        "tc_vibe_pcs_rx_unpack (vibe_pcs_rx_unpack_cocotb_top, module-level)",
    "make pack / tc_vibe_pcs_tx_pack":
        "tc_vibe_pcs_tx_pack (vibe_pcs_tx_pack_cocotb_top, module-level)",
    "make tx_fec / tc_vibe_pcs_tx_fec":
        "tc_vibe_pcs_tx_fec (vibe_pcs_tx_fec_cocotb_top, module-level)",
    "make rx_fec / tc_vibe_pcs_rx_fec":
        "tc_vibe_pcs_rx_fec (vibe_pcs_rx_fec_cocotb_top, module-level)",
    "make g1 / tx_g1 / tc_vibe_pcs_tx_g1":
        "tc_vibe_pcs_tx_g1 (vibe_pcs_tx_g1_cocotb_top, module-level)",
    "make bcrc / tc_vibe_bcrc":
        "tc_vibe_bcrc (vibe_bcrc_cocotb_top, module-level)",
    "make credit / tc_vibe_dll_credit":
        "tc_vibe_dll_credit (vibe_dll_credit_cocotb_top, module-level)",
    "make dll_sm / sm / tc_vibe_dll_sm":
        "tc_vibe_dll_sm (vibe_dll_sm_cocotb_top, module-level)",
    "make dll_rx / rx / tc_vibe_dll_rx":
        "tc_vibe_dll_rx (vibe_dll_rx_cocotb_top, module-level)",
    "make retry_ack_sm / ack_sm / tc_vibe_dll_retry_ack_sm":
        "tc_vibe_dll_retry_ack_sm (vibe_dll_retry_ack_sm_cocotb_top, module-level)",
    "make retry_buf / buf / tc_vibe_dll_retry_buf":
        "tc_vibe_dll_retry_buf (vibe_dll_retry_buf_cocotb_top, module-level)",
    "make top / tc_top_smoke": "tc_top_smoke (entry_switch)",
    "make neg / scan_absent.sh": "python3 -m vibe_uvm.tests.static_tests + run_absent_scan",
    "SV UVM +UVM_TESTNAME": "same class name, Python UVM 1.2",
}
