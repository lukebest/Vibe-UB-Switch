"""Emit the product SystemVerilog for vibe_rs128_120_enc (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_fn.vh"``,
``vibe_gf256_mul`` LFSR step, combo ``in_ready`` / ``parity``, and
the 120-symbol systematic encode. pycc netlists are a prototype
only; this file is what lands in ``rtl/pcs/vibe_rs128_120_enc.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_rs128_120_enc.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 984e3b9 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_rs128_120_enc
//
"""

BODY = """\
// AS-0.1 §5 T3 / UB 2.0 §3.2.2: systematic RS(128,120) encoder, GF(256).
// Generator coefficients Table 3-2. T=2 encoding produces the same 8 parity symbols.
module vibe_rs128_120_enc (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        start,
  input  logic        in_vld,
  input  logic [7:0]  in_sym,
  output logic        in_ready,
  output logic        done,
  output logic [63:0] parity // p7..p0, p7 = p[63:56]
);
  `include "vibe_ub_fn.vh"

  localparam logic [7:0] G0 = 8'd24;
  localparam logic [7:0] G1 = 8'd200;
  localparam logic [7:0] G2 = 8'd173;
  localparam logic [7:0] G3 = 8'd239;
  localparam logic [7:0] G4 = 8'd54;
  localparam logic [7:0] G5 = 8'd81;
  localparam logic [7:0] G6 = 8'd11;
  localparam logic [7:0] G7 = 8'd255;

  logic [7:0] r0, r1, r2, r3, r4, r5, r6, r7;
  logic [7:0] cnt;
  logic       busy;

  assign in_ready = busy && (cnt < 8'd120);
  assign parity   = {r7, r6, r5, r4, r3, r2, r1, r0};

  wire [7:0] fb = in_sym ^ r7;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      r0 <= 8'd0; r1 <= 8'd0; r2 <= 8'd0; r3 <= 8'd0;
      r4 <= 8'd0; r5 <= 8'd0; r6 <= 8'd0; r7 <= 8'd0;
      cnt  <= 8'd0;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (start) begin
        r0 <= 8'd0; r1 <= 8'd0; r2 <= 8'd0; r3 <= 8'd0;
        r4 <= 8'd0; r5 <= 8'd0; r6 <= 8'd0; r7 <= 8'd0;
        cnt  <= 8'd0;
        busy <= 1'b1;
      end else if (busy && in_vld && in_ready) begin
        r0 <= vibe_gf256_mul(fb, G0);
        r1 <= r0 ^ vibe_gf256_mul(fb, G1);
        r2 <= r1 ^ vibe_gf256_mul(fb, G2);
        r3 <= r2 ^ vibe_gf256_mul(fb, G3);
        r4 <= r3 ^ vibe_gf256_mul(fb, G4);
        r5 <= r4 ^ vibe_gf256_mul(fb, G5);
        r6 <= r5 ^ vibe_gf256_mul(fb, G6);
        r7 <= r6 ^ vibe_gf256_mul(fb, G7);
        cnt <= cnt + 8'd1;
        if (cnt == 8'd119) begin
          busy <= 1'b0;
          done <= 1'b1;
        end
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
    dest = repo / "rtl" / "pcs" / "vibe_rs128_120_enc.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
