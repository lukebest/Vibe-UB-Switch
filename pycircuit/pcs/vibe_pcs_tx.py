"""vibe_pcs_tx — PCS TX hierarchy wrap (AS-0.1 §5).

Product module: ``rtl/pcs/vibe_pcs_tx.sv``. Ports match tip
``deef6adc`` (product DUT after PR251 stage-46). Decision I
UNFROZEN (do not re-pin freeze). SPEC / CR-B names are
unchanged. Hierarchy wrap (``clk`` / ``rst_n`` / ``link_up`` /
``sdf_period`` / 3b ``fec_mode`` / ``afifo_afull`` / 640b
``dll_pcs_data`` / ``dll_pcs_vld`` / ``dll_pcs_ready`` /
160b ``pcs_afifo_lane0`` / ``pcs_afifo_lane1`` /
``pcs_afifo_lane2`` / ``pcs_afifo_lane3`` /
``pcs_afifo_lane_vld``). First PCS-TX hierarchy wrap after
stage-19 ``vibe_pcs_tx_g1`` and stage-46 ``vibe_fabric``.
Instantiates stock children: ``vibe_pcs_tx_g1 u_g1``,
``vibe_pcs_tx_fec u_fec``, ``vibe_pcs_tx_cw2beat u_cw``,
``vibe_pcs_tx_pack u_pack``, 4× ``vibe_pcs_scramble u_s0``
/ ``u_s1`` / ``u_s2`` / ``u_s3``. Children already have
pyCircuit wraps (stages 7 / 16–19). Wrap-local stock glue
(``p_rdy = 1'b1`` / lane assigns) stays in the
hand-finished body — preserve byte-identical; do not invent
CFG6 packing, Appendix D, or opcode 0x10. Do not rewrite
F1 ``ovf_l`` (lives under ``vibe_port``). Leave
``vibe_pcs_rx`` and ``vibe_lmsm`` for later stages.

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own in the frontend.
Product RTL keeps **async active-low** ``rst_n`` on the
children. Landed SV is hand-finished so the stock
hierarchy (ports / instances ``u_g1`` / ``u_fec`` /
``u_cw`` / ``u_pack`` / ``u_s0``..``u_s3`` / local wires
/ ``p_rdy`` / lane assigns) stays byte-identical in the
module body.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DLL_W = 640
LANE_W = 160
FEC_MODE_W = 3
LANE_ID_W = 2


def _scramble(lane: int, out_vld: str):
    return {
        "module": "vibe_pcs_scramble",
        "inst": f"u_s{lane}",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "lane_id": f"2'd{lane}",
            "seed_load": "!link_up",
            "en": "!am_word",
            "in_vld": "p_vld",
            "in_data": f"p{lane}",
            "out_vld": out_vld,
            "out_data": f"s{lane}",
        },
    }


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
CHILDREN = (
    {
        "module": "vibe_pcs_tx_g1",
        "inst": "u_g1",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "link_up": "link_up",
            "in_data": "dll_pcs_data",
            "in_vld": "dll_pcs_vld",
            "in_ready": "dll_pcs_ready",
            "win_data": "win",
            "win_vld": "win_vld",
            "win_ready": "win_rdy",
        },
    },
    {
        "module": "vibe_pcs_tx_fec",
        "inst": "u_fec",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "fec_mode": "fec_mode",
            "win_data": "win",
            "win_vld": "win_vld",
            "win_ready": "win_rdy",
            "cw_data": "cw",
            "cw_vld": "cw_vld",
            "cw_ready": "cw_rdy",
        },
    },
    {
        "module": "vibe_pcs_tx_cw2beat",
        "inst": "u_cw",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "cw_data": "cw",
            "cw_vld": "cw_vld",
            "cw_ready": "cw_rdy",
            "beat_data": "beat",
            "beat_vld": "beat_vld",
            "beat_ready": "beat_rdy",
        },
    },
    {
        "module": "vibe_pcs_tx_pack",
        "inst": "u_pack",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "sdf_period": "sdf_period",
            "afifo_afull": "afifo_afull",
            "beat_data": "beat",
            "beat_vld": "beat_vld",
            "beat_ready": "beat_rdy",
            "lane0": "p0",
            "lane1": "p1",
            "lane2": "p2",
            "lane3": "p3",
            "lane_vld": "p_vld",
            "lane_ready": "p_rdy",
            "am_word": "am_word",
        },
    },
    _scramble(0, "s_vld"),
    _scramble(1, ""),
    _scramble(2, ""),
    _scramble(3, ""),
)


@module(name="vibe_pcs_tx")
def build(m: Circuit) -> None:
    """PCS TX hierarchy wrap: G1 / FEC / cw2beat / pack / scramble×4.

    Product ports (hand-finished SV)::

        clk, rst_n, link_up, sdf_period, fec_mode[2:0],
        afifo_afull, dll_pcs_data[639:0], dll_pcs_vld,
        dll_pcs_ready, pcs_afifo_lane0[159:0],
        pcs_afifo_lane1[159:0], pcs_afifo_lane2[159:0],
        pcs_afifo_lane3[159:0], pcs_afifo_lane_vld

    pyCircuit clock is ``clk``. Reset here is ``rst``
    (active-high). Children keep async-low ``rst_n`` in the
    product SV. Frontend parks child-driven outputs at 0
    (same pattern as stage-45 ``vibe_mgmt`` / stage-46
    ``vibe_fabric``). Product SV instantiates ``CHILDREN``.
    Wrap-local ``p_rdy = 1'b1`` / lane assigns stay stock —
    do not invent packing. ``vibe_pcs_rx`` / ``vibe_lmsm``
    remain HOLD.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    link_up = m.input("link_up", width=1)
    sdf_period = m.input("sdf_period", width=1)
    fec_mode = m.input("fec_mode", width=FEC_MODE_W)
    afifo_afull = m.input("afifo_afull", width=1)
    dll_pcs_data = m.input("dll_pcs_data", width=DLL_W)
    dll_pcs_vld = m.input("dll_pcs_vld", width=1)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        link_up
        | sdf_period
        | afifo_afull
        | dll_pcs_vld
        | (fec_mode == 0)
        | (dll_pcs_data == 0)
    )
    _ = (clk, rst, _keep, CHILDREN, LANE_W, LANE_ID_W)

    m.output("dll_pcs_ready", u(1, 0))
    m.output("pcs_afifo_lane0", u(LANE_W, 0))
    m.output("pcs_afifo_lane1", u(LANE_W, 0))
    m.output("pcs_afifo_lane2", u(LANE_W, 0))
    m.output("pcs_afifo_lane3", u(LANE_W, 0))
    m.output("pcs_afifo_lane_vld", u(1, 0))


build.__pycircuit_name__ = "vibe_pcs_tx"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_tx").emit_mlir())
