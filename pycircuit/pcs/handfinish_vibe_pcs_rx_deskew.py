"""Emit the product SystemVerilog for vibe_pcs_rx_deskew (hand-finished).

Keeps tip ports, async-low ``rst_n``, combo ``aligned`` / ``out_vld`` /
pass-through ``out0``..``out3``, first-AMCTL lock pointers, and hunt
FIFOs whose contents are not reset. Factory physical=logical (U24):
no lane swap and no delay once aligned. pycc netlists are a prototype
only; this file is what lands in ``rtl/pcs/vibe_pcs_rx_deskew.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_pcs_rx_deskew.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip ebd1671 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_rx_deskew
//
"""

BODY = """\
// AS-0.1 §6: deskew on AMCTL. Factory physical=logical; no lane swap (U24).
module vibe_pcs_rx_deskew (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [159:0] in0,
  input  logic [159:0] in1,
  input  logic [159:0] in2,
  input  logic [159:0] in3,
  input  logic         in_vld,
  input  logic         am0,
  input  logic         am1,
  input  logic         am2,
  input  logic         am3,
  output logic [159:0] out0,
  output logic [159:0] out1,
  output logic [159:0] out2,
  output logic [159:0] out3,
  output logic         out_vld,
  output logic         aligned
);
  logic [159:0] f0[0:7];
  logic [159:0] f1[0:7];
  logic [159:0] f2[0:7];
  logic [159:0] f3[0:7];
  logic [2:0]   wptr;
  logic [2:0]   a0, a1, a2, a3;
  logic         saw0, saw1, saw2, saw3;
  logic         am0_r, am1_r, am2_r, am3_r;

  assign aligned = saw0 & saw1 & saw2 & saw3;
  // Factory physical=logical: pass data during hunt (lock/aligned come later).
  // AMCTL is still dropped so unpack sees a gap between 4×640 groups.
  assign out_vld = in_vld && !(am0|am1|am2|am3);
  // Factory physical=logical (U24): no delay once aligned. FIFO pointers
  // only record first-AMCTL lock; feeding them as out would leak the second
  // AMCTL 160b into the 512b stream after each marker.
  assign out0 = in0;
  assign out1 = in1;
  assign out2 = in2;
  assign out3 = in3;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 3'd0;
      a0 <= 3'd0; a1 <= 3'd0; a2 <= 3'd0; a3 <= 3'd0;
      saw0 <= 1'b0; saw1 <= 1'b0; saw2 <= 1'b0; saw3 <= 1'b0;
      am0_r <= 1'b0; am1_r <= 1'b0; am2_r <= 1'b0; am3_r <= 1'b0;
    end else if (in_vld) begin
      f0[wptr] <= in0;
      f1[wptr] <= in1;
      f2[wptr] <= in2;
      f3[wptr] <= in3;
      // Latch delay on the first AMCTL 160b only. The second word would
      // shift the pointer so the next data beat reads AMCTL out of the FIFO.
      if (am0 && !am0_r) begin a0 <= wptr; saw0 <= 1'b1; end
      if (am1 && !am1_r) begin a1 <= wptr; saw1 <= 1'b1; end
      if (am2 && !am2_r) begin a2 <= wptr; saw2 <= 1'b1; end
      if (am3 && !am3_r) begin a3 <= wptr; saw3 <= 1'b1; end
      am0_r <= am0; am1_r <= am1; am2_r <= am2; am3_r <= am3;
      wptr <= wptr + 3'd1;
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "pcs" / "vibe_pcs_rx_deskew.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
