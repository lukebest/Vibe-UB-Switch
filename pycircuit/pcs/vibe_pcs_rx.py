"""vibe_pcs_rx — PCS RX hierarchy wrap (AS-0.1 §6).

Product module: ``rtl/pcs/vibe_pcs_rx.sv``. Ports match tip
``3365182d`` (product DUT after PR253 stage-47). Decision I
UNFROZEN (do not re-pin freeze). SPEC / CR-B names are
unchanged. Hierarchy wrap (``clk`` / ``rst_n`` / ``link_up`` /
3b ``fec_mode`` / 160b ``afifo_pcs_lane0`` /
``afifo_pcs_lane1`` / ``afifo_pcs_lane2`` /
``afifo_pcs_lane3`` / ``afifo_pcs_lane_vld`` / 640b
``pcs_dll_data`` / ``pcs_dll_vld`` / ``pcs_dll_ready`` /
``fec_fail`` / 4b ``am_locked`` / ``lid_bad`` /
``deskew_ok``). First PCS-RX hierarchy wrap after
stage-47 ``vibe_pcs_tx`` and stage-18 ``vibe_pcs_rx_fec``.
Instantiates stock children: 4× ``vibe_pcs_rx_amctl_lock
u_l0`` / ``u_l1`` / ``u_l2`` / ``u_l3``, 4×
``vibe_pcs_scramble u_d0`` / ``u_d1`` / ``u_d2`` /
``u_d3``, ``vibe_pcs_rx_deskew u_dsk``,
``vibe_pcs_rx_unpack u_un``, ``vibe_pcs_rx_fec u_fec``.
Children already have pyCircuit wraps (stages 7 / 13–15 /
18). Wrap-local stock glue (``lid_seeded``, scramble seed
wires ``sl0``..``sl3``, AM delay, ``lid_bad``, deskew,
unpack/fec ``pair_rst``, Inverse T2 always block,
``flit_null``) stays in the hand-finished body — preserve
byte-identical; do not invent CFG6 packing, Appendix D, or
opcode 0x10. Do not rewrite F1 ``ovf_l`` (lives under
``vibe_port``). Leave ``vibe_lmsm`` for a later stage.

pyCircuit registers are dest-domain **synchronous active-high** reset.
This wrap has no sequential of its own in the frontend.
Product RTL keeps **async active-low** ``rst_n`` on the
children. Landed SV is hand-finished so the stock
hierarchy (ports / instances ``u_l0``..``u_l3`` /
``u_d0``..``u_d3`` / ``u_dsk`` / ``u_un`` / ``u_fec`` /
local wires / ``lid_seeded`` / seed wires / Inverse T2)
stays byte-identical in the module body.
"""

from __future__ import annotations

from pycircuit import Circuit, module, u

DLL_W = 640
LANE_W = 160
FEC_MODE_W = 3
LANE_ID_W = 2
AM_LOCKED_W = 4


def _amctl_lock(lane: int, sdf: str):
    return {
        "module": "vibe_pcs_rx_amctl_lock",
        "inst": f"u_l{lane}",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "in_vld": "afifo_pcs_lane_vld",
            "in_data": f"afifo_pcs_lane{lane}",
            "locked": f"am_locked[{lane}]",
            "lid": f"lid{lane}",
            "lid_bad": f"bad{lane}",
            "is_amctl": f"am{lane}",
            "sdf": sdf,
            "edf": f"edf{lane}",
        },
    }


def _descramble(lane: int, out_vld: str):
    return {
        "module": "vibe_pcs_scramble",
        "inst": f"u_d{lane}",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "lane_id": f"2'd{lane}",
            "seed_load": f"sl{lane}",
            "en": f"afifo_pcs_lane_vld && !am{lane}",
            "in_vld": "afifo_pcs_lane_vld",
            "in_data": f"afifo_pcs_lane{lane}",
            "out_vld": out_vld,
            "out_data": f"d{lane}",
        },
    }


# Product instances + connects (hand-finished SV). pycc prototype
# does not emit hierarchy; CHILDREN is the wrap contract.
CHILDREN = (
    _amctl_lock(0, "sdf0"),
    _amctl_lock(1, ""),
    _amctl_lock(2, ""),
    _amctl_lock(3, ""),
    _descramble(0, "dv"),
    _descramble(1, ""),
    _descramble(2, ""),
    _descramble(3, ""),
    {
        "module": "vibe_pcs_rx_deskew",
        "inst": "u_dsk",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "in0": "d0",
            "in1": "d1",
            "in2": "d2",
            "in3": "d3",
            "in_vld": "dv",
            "am0": "am0_d",
            "am1": "am1_d",
            "am2": "am2_d",
            "am3": "am3_d",
            "out0": "u0",
            "out1": "u1",
            "out2": "u2",
            "out3": "u3",
            "out_vld": "uv",
            "aligned": "aligned",
        },
    },
    {
        "module": "vibe_pcs_rx_unpack",
        "inst": "u_un",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "lane0": "u0",
            "lane1": "u1",
            "lane2": "u2",
            "lane3": "u3",
            "lane_vld": "uv",
            "am0": "1'b0",
            "am1": "1'b0",
            "am2": "1'b0",
            "am3": "1'b0",
            "am_gap": "pair_rst",
            "beat_data": "beat",
            "beat_vld": "bv",
            "beat_ready": "br",
        },
    },
    {
        "module": "vibe_pcs_rx_fec",
        "inst": "u_fec",
        "params": {},
        "connects": {
            "clk": "clk",
            "rst_n": "rst_n",
            "fec_mode": "fec_mode",
            "beat_data": "beat",
            "beat_vld": "bv",
            "beat_ready": "br",
            "win_data": "win",
            "win_vld": "wv",
            "win_ready": "wr",
            "am_gap": "pair_rst",
            "fec_fail": "fec_fail",
        },
    },
)


@module(name="vibe_pcs_rx")
def build(m: Circuit) -> None:
    """PCS RX hierarchy wrap: amctl_lock×4 / scramble×4 / deskew / unpack / fec.

    Product ports (hand-finished SV)::

        clk, rst_n, link_up, fec_mode[2:0],
        afifo_pcs_lane0[159:0], afifo_pcs_lane1[159:0],
        afifo_pcs_lane2[159:0], afifo_pcs_lane3[159:0],
        afifo_pcs_lane_vld, pcs_dll_data[639:0], pcs_dll_vld,
        pcs_dll_ready, fec_fail, am_locked[3:0], lid_bad,
        deskew_ok

    pyCircuit clock is ``clk``. Reset here is ``rst``
    (active-high). Children keep async-low ``rst_n`` in the
    product SV. Frontend parks child-driven outputs at 0
    (same pattern as stage-45 ``vibe_mgmt`` / stage-46
    ``vibe_fabric`` / stage-47 ``vibe_pcs_tx``). Product SV
    instantiates ``CHILDREN``. Wrap-local ``lid_seeded`` /
    seed wires / deskew / unpack/fec ``pair_rst`` / Inverse
    T2 / ``flit_null`` stay stock — do not invent packing.
    ``vibe_lmsm`` remains HOLD.
    """
    clk = m.clock("clk")
    rst = m.reset("rst")
    link_up = m.input("link_up", width=1)
    fec_mode = m.input("fec_mode", width=FEC_MODE_W)
    afifo_pcs_lane0 = m.input("afifo_pcs_lane0", width=LANE_W)
    afifo_pcs_lane1 = m.input("afifo_pcs_lane1", width=LANE_W)
    afifo_pcs_lane2 = m.input("afifo_pcs_lane2", width=LANE_W)
    afifo_pcs_lane3 = m.input("afifo_pcs_lane3", width=LANE_W)
    afifo_pcs_lane_vld = m.input("afifo_pcs_lane_vld", width=1)
    pcs_dll_ready = m.input("pcs_dll_ready", width=1)

    # Keep wrap inputs in the frontend graph. Product SV fans
    # them into CHILDREN; this prototype does not instantiate.
    _keep = (
        link_up
        | afifo_pcs_lane_vld
        | pcs_dll_ready
        | (fec_mode == 0)
        | (afifo_pcs_lane0 == 0)
        | (afifo_pcs_lane1 == 0)
        | (afifo_pcs_lane2 == 0)
        | (afifo_pcs_lane3 == 0)
    )
    _ = (clk, rst, _keep, CHILDREN, LANE_ID_W)

    m.output("pcs_dll_data", u(DLL_W, 0))
    m.output("pcs_dll_vld", u(1, 0))
    m.output("fec_fail", u(1, 0))
    m.output("am_locked", u(AM_LOCKED_W, 0))
    m.output("lid_bad", u(1, 0))
    m.output("deskew_ok", u(1, 0))


build.__pycircuit_name__ = "vibe_pcs_rx"


if __name__ == "__main__":
    from pycircuit import compile as pyc_compile

    print(pyc_compile(build, name="vibe_pcs_rx").emit_mlir())
