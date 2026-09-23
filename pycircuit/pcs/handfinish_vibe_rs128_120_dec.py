"""Emit the product SystemVerilog for vibe_rs128_120_dec (hand-finished).

Keeps tip ports, async-low ``rst_n``, ``include "vibe_ub_fn.vh"``,
combo next-syndromes (last symbol included before ``fec_fail``),
``msg[0:119]`` pack into 960b ``data_out``, and the 128-symbol
syndrome-check decode. Reset of ``msg`` is unrolled NBA
(same zeros as the stock reset ``for``; Icarus-legal and
Verilator 5.020 ``BLKLOOPINIT`` / ``BLKSEQ`` clean). pycc
netlists are a prototype only; this file is what lands in
``rtl/pcs/vibe_rs128_120_dec.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_rs128_120_dec.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 984e3b9 / freeze 302ac943.
// msg reset is unrolled NBA (same zeros as stock for-loop; lint-safe).
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_rs128_120_dec
//
"""

BODY = """\
// AS-0.1 §6: RS(128,120) syndrome check. Nonzero syndrome → fec_fail (Go-Back-N).
module vibe_rs128_120_dec (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_sym,
  output logic         in_ready,
  output logic         done,
  output logic         fec_fail,
  output logic [959:0] data_out
);
  `include "vibe_ub_fn.vh"

  logic [7:0]   s0, s1, s2, s3, s4, s5, s6, s7;
  logic [7:0]   cnt;
  logic         busy;
  logic [7:0]   msg [0:119];

  assign in_ready = busy && (cnt < 8'd128);

  function automatic [7:0] gf_mul2;
    input [7:0] a;
    begin
      gf_mul2 = a[7] ? {a[6:0], 1'b0} ^ 8'h1D : {a[6:0], 1'b0};
    end
  endfunction

  // Next syndromes (combo) so the last symbol is included before fec_fail.
  wire [7:0] ns0 = s0 ^ in_sym;
  wire [7:0] ns1 = gf_mul2(s1) ^ in_sym;
  wire [7:0] ns2 = vibe_gf256_mul(s2, 8'd4) ^ in_sym;
  wire [7:0] ns3 = vibe_gf256_mul(s3, 8'd8) ^ in_sym;
  wire [7:0] ns4 = vibe_gf256_mul(s4, 8'd16) ^ in_sym;
  wire [7:0] ns5 = vibe_gf256_mul(s5, 8'd32) ^ in_sym;
  wire [7:0] ns6 = vibe_gf256_mul(s6, 8'd64) ^ in_sym;
  wire [7:0] ns7 = vibe_gf256_mul(s7, 8'd128) ^ in_sym;

  integer i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
      s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
      cnt      <= 8'd0;
      busy     <= 1'b0;
      done     <= 1'b0;
      fec_fail <= 1'b0;
      data_out <= 960'd0;
__MSG_RESET__
    end else begin
      done     <= 1'b0;
      fec_fail <= 1'b0;
      if (start) begin
        s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
        s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
        cnt      <= 8'd0;
        busy     <= 1'b1;
        fec_fail <= 1'b0;
      end else if (busy && in_vld && in_ready) begin
        s0 <= ns0;
        s1 <= ns1;
        s2 <= ns2;
        s3 <= ns3;
        s4 <= ns4;
        s5 <= ns5;
        s6 <= ns6;
        s7 <= ns7;
        if (cnt < 8'd120)
          msg[cnt] <= in_sym;
        if (cnt == 8'd127) begin
          busy     <= 1'b0;
          done     <= 1'b1;
          fec_fail <= |{ns0, ns1, ns2, ns3, ns4, ns5, ns6, ns7};
          // pack msg[0] as first symbol (MSB of data_out)
          for (i = 0; i < 120; i = i + 1)
            data_out[959-8*i -: 8] <= msg[i];
        end else begin
          cnt <= cnt + 8'd1;
        end
      end
    end
  end
endmodule
"""


def _msg_reset_nbas() -> str:
    """Unrolled ``msg[i] <= 8'd0`` (stock reset for-loop, lint-safe)."""
    lines = []
    for row in range(0, 120, 8):
        parts = [f"msg[{i}] <= 8'd0;" for i in range(row, row + 8)]
        lines.append("      " + " ".join(parts))
    return "\n".join(lines)


def render() -> str:
    return HEADER + BODY.replace("__MSG_RESET__", _msg_reset_nbas())


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "pcs" / "vibe_rs128_120_dec.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
