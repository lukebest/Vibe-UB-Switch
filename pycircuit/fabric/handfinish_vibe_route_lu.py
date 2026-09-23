"""Emit the product SystemVerilog for vibe_route_lu (hand-finished).

Keeps tip ports, async-low ``rst_n``, DEPTH=256 CFG0_ROUTE_TABLE
dest → 4-bit egress bitmap, and RT=10/11 DROP (pulse
``drop_g1``). No Dijkstra, no treat-as-RT=00, no RT rewrite
(AS-0.1 §2/§8 + FS-0.2.3 G1). pycc netlists are a prototype
only; this file is what lands in ``rtl/fabric/vibe_route_lu.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/fabric/vibe_route_lu.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 2841888e / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_route_lu
"""

BODY = """\
// AS-0.1 §2/§8 + FS-0.2.3 G1: CFG0_ROUTE_TABLE dest → 4-bit egress bitmap.
// RT=10/11: DROP (pulse drop_g1). No Dijkstra, no treat-as-RT=00, no RT rewrite.
// Fabric saturates rt_shortest_unimpl and irq_agg sticks irq_logic.
module vibe_route_lu #(
  parameter int DEPTH = 256
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        device_rst,
  input  logic        wr_en,
  input  logic [15:0] wr_idx,
  input  logic [31:0] wr_data,
  input  logic [15:0] dest,
  input  logic [1:0]  rt,
  input  logic        lu_vld,
  output logic [3:0]  bitmap,
  output logic        drop_g1
);
  logic [31:0] tbl [0:DEPTH-1];
  integer i;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n || device_rst) begin
      for (i = 0; i < DEPTH; i = i + 1)
        tbl[i] <= 32'd0;
      bitmap              <= 4'd0;
      drop_g1             <= 1'b0;
    end else begin
      drop_g1 <= 1'b0;
      if (wr_en)
        tbl[wr_idx[7:0]] <= wr_data;
      if (lu_vld) begin
        if (rt == 2'b10 || rt == 2'b11) begin
          // FS-0.2.3 + AS-0.1 G1: drop only; count/irq aggregated in fabric
          drop_g1            <= 1'b1;
          bitmap             <= 4'd0;
        end else begin
          bitmap <= tbl[dest[7:0]][3:0];
        end
      end
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY + FOOTER


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "fabric" / "vibe_route_lu.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
