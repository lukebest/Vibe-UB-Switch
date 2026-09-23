"""Emit the product SystemVerilog for vibe_gear_128_160 (hand-finished).

Keeps tip ports, async-low ``rst_n``, combo ``in_ready``, and the
5-beat dual-residue body (``res_a`` / ``res_b`` / ``phase`` 0..4).
pycc netlists are a prototype only; this file is what lands in
``rtl/cdc/vibe_gear_128_160.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_gear_128_160.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 195d380 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_gear_128_160
//
"""

BODY = """\
// AS-0.1 §6/§7: RX 128→160 dual-residue gearbox. 5×128 = 4×160.
module vibe_gear_128_160 (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         in_vld,
  output logic         in_ready,
  input  logic [127:0] in_data,
  output logic         out_vld,
  input  logic         out_ready,
  output logic [159:0] out_data
);
  logic [127:0] res_a;
  logic [127:0] res_b;
  logic [2:0]   phase; // 0..4 inputs in a 5-beat group
  logic [159:0] hold;
  logic         hold_vld;

  assign out_vld  = hold_vld;
  assign out_data = hold;
  assign in_ready = !hold_vld || out_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      res_a    <= 128'd0;
      res_b    <= 128'd0;
      phase    <= 3'd0;
      hold     <= 160'd0;
      hold_vld <= 1'b0;
    end else begin
      if (hold_vld && out_ready)
        hold_vld <= 1'b0;
      if (in_vld && in_ready) begin
        case (phase)
          3'd0: begin
            res_a <= in_data;
            phase <= 3'd1;
          end
          3'd1: begin
            hold     <= {in_data[31:0], res_a};
            res_b    <= {32'd0, in_data[127:32]};
            hold_vld <= 1'b1;
            phase    <= 3'd2;
          end
          3'd2: begin
            hold     <= {in_data[63:0], res_b[95:0]};
            res_a    <= {64'd0, in_data[127:64]};
            hold_vld <= 1'b1;
            phase    <= 3'd3;
          end
          3'd3: begin
            hold     <= {in_data[95:0], res_a[63:0]};
            res_b    <= {96'd0, in_data[127:96]};
            hold_vld <= 1'b1;
            phase    <= 3'd4;
          end
          default: begin
            hold     <= {in_data, res_b[31:0]};
            hold_vld <= 1'b1;
            res_a    <= 128'd0;
            res_b    <= 128'd0;
            phase    <= 3'd0;
          end
        endcase
      end
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
    dest = repo / "rtl" / "cdc" / "vibe_gear_128_160.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
