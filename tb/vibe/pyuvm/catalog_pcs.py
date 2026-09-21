"""PCS / PHY / gear unit TCs. Same RTL lists as tb/vibe/scripts/run_units.sh."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PY = Path(__file__).resolve().parent


def _w(*p):
    return str(ROOT.joinpath("rtl", *p))


PHY_U26_TOP = str(PY / "tb" / "vibe_phy_u26_chain_cocotb_top.sv")

FEC_TX = [_w("pcs", "vibe_pcs_tx_fec.sv"), _w("pcs", "vibe_rs128_120_enc.sv")]
AMCTL_TX = [_w("pcs", "vibe_pcs_tx_amctl.sv"), _w("pcs", "vibe_ebch16.sv")]

# (name, toplevel, [verilog sources], entry module)
UNIT_PCS = [
    ("tc_pcs_tx_g1_window", "vibe_pcs_tx_g1",
     [_w("pcs", "vibe_pcs_tx_g1.sv")], "entry_unit"),
    ("tc_pcs_fec_bypass", "vibe_pcs_tx_fec", FEC_TX, "entry_unit"),
    ("tc_pcs_fec_dual_enc", "vibe_pcs_tx_fec", FEC_TX, "entry_unit"),
    ("tc_pcs_fec_t2", "vibe_pcs_tx_fec", FEC_TX, "entry_unit"),
    ("tc_pcs_cw2beat", "vibe_pcs_tx_cw2beat",
     [_w("pcs", "vibe_pcs_tx_cw2beat.sv")], "entry_unit"),
    ("tc_pcs_amctl", "vibe_pcs_tx_amctl", AMCTL_TX, "entry_unit"),
    ("tc_pcs_scramble", "vibe_pcs_scramble",
     [_w("pcs", "vibe_pcs_scramble.sv")], "entry_unit"),
    ("tc_ebch16_lut", "vibe_ebch16",
     [_w("pcs", "vibe_ebch16.sv")], "entry_unit"),
    ("tc_pcs_fec_emitb", "vibe_pcs_tx_fec", FEC_TX, "entry_unit"),
    ("tc_pcs_rx_amctl", "vibe_pcs_rx_amctl_lock",
     [_w("pcs", "vibe_pcs_rx_amctl_lock.sv"), _w("pcs", "vibe_ebch16.sv")],
     "entry_unit"),
    ("tc_pcs_rx_deskew", "vibe_pcs_rx_deskew",
     [_w("pcs", "vibe_pcs_rx_deskew.sv")], "entry_unit"),
    ("tc_pcs_rx_unpack", "vibe_pcs_rx_unpack",
     [_w("pcs", "vibe_pcs_rx_unpack.sv")], "entry_unit"),
    ("tc_pcs_rx_fec", "vibe_pcs_rx_fec",
     [_w("pcs", "vibe_pcs_rx_fec.sv"), _w("pcs", "vibe_rs128_120_dec.sv")],
     "entry_unit"),
    ("tc_pcs_tx_pack", "vibe_pcs_tx_pack",
     [_w("pcs", "vibe_pcs_tx_pack.sv"),
      _w("pcs", "vibe_pcs_tx_amctl.sv"),
      _w("pcs", "vibe_ebch16.sv")], "entry_unit"),
    ("tc_rs_dec_syndrome", "vibe_rs128_120_dec",
     [_w("pcs", "vibe_rs128_120_dec.sv")], "entry_unit"),
    ("tc_gear_160_128", "vibe_gear_160_128",
     [_w("cdc", "vibe_gear_160_128.sv")], "entry_unit"),
    ("tc_gear_128_160", "vibe_gear_128_160",
     [_w("cdc", "vibe_gear_128_160.sv")], "entry_unit"),
    ("tc_pma_922mhz", "vibe_pma_bnd",
     [_w("pma", "vibe_pma_bnd.sv")], "entry_unit"),
    ("tc_phy_u26_chain", "vibe_phy_u26_chain_cocotb_top",
     [PHY_U26_TOP,
      _w("cdc", "vibe_gear_160_128.sv"),
      _w("cdc", "vibe_gear_128_160.sv"),
      _w("pma", "vibe_pma_bnd.sv")], "entry_unit"),
]
