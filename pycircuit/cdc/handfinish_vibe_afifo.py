"""Emit the product SystemVerilog for vibe_afifo (hand-finished).

Keeps freeze ``302ac943`` ports, async-low reset, combo RAM (no mem reset),
``vibe_sync2``, and ``vibe_ub_fn.vh`` gray helpers. pycc netlists are a
prototype only; this file is what lands in ``rtl/cdc/vibe_afifo.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_afifo.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match freeze 302ac943. SPEC / CR-B names unchanged.
// Do not substitute pyc.async_fifo. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_afifo
//
// AS-0.1 §7: per-lane gray-pointer AFIFO, depth 16, ptr 5 bits.
// Write-domain almost_full at occupancy >= 10. Independent of prior-revision ready formulas.
"""

BODY = """\
module vibe_afifo #(
  parameter int W     = 160,
  parameter int DEPTH = 16
) (
  input  logic         wclk,
  input  logic         wrst_n,
  input  logic         wen,
  input  logic [W-1:0] wdata,
  output logic         wfull,
  output logic         almost_full,
  output logic [4:0]   wocc,
  input  logic         rclk,
  input  logic         rrst_n,
  input  logic         ren,
  output logic [W-1:0] rdata,
  output logic         rempty
);
  `include "vibe_ub_params.vh"
  `include "vibe_ub_fn.vh"

  localparam int AW = 4; // 16 deep

  logic [W-1:0] mem [0:DEPTH-1];
  logic [4:0] wbin, rbin;
  logic [4:0] wgray, rgray;
  logic [4:0] wgray_s, rgray_s;
  logic [4:0] rbin_w, wbin_r;

  assign wgray = vibe_bin2gray5(wbin);
  assign rgray = vibe_bin2gray5(rbin);

  vibe_sync2 #(.W(5)) u_r2w (
    .clk(wclk), .rst_n(wrst_n), .d(rgray), .q(rgray_s)
  );
  vibe_sync2 #(.W(5)) u_w2r (
    .clk(rclk), .rst_n(rrst_n), .d(wgray), .q(wgray_s)
  );

  assign rbin_w = vibe_gray2bin5(rgray_s);
  assign wbin_r = vibe_gray2bin5(wgray_s);
  assign wocc   = wbin - rbin_w;
  assign wfull  = (wocc == DEPTH[4:0]);
  assign almost_full = (wocc >= VIBE_AFIFO_AFULL_OCC[4:0]);
  assign rempty = (rbin == wbin_r);

  always @(posedge wclk) begin
    if (wen && !wfull)
      mem[wbin[AW-1:0]] <= wdata;
  end

  always @(posedge wclk or negedge wrst_n) begin
    if (!wrst_n) wbin <= 5'd0;
    else if (wen && !wfull) wbin <= wbin + 5'd1;
  end

  always @(posedge rclk or negedge rrst_n) begin
    if (!rrst_n) rbin <= 5'd0;
    else if (ren && !rempty) rbin <= rbin + 5'd1;
  end

  assign rdata = mem[rbin[AW-1:0]];
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
    dest = repo / "rtl" / "cdc" / "vibe_afifo.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
