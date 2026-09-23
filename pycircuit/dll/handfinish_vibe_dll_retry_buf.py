"""Emit the product SystemVerilog for vibe_dll_retry_buf (hand-finished).

Keeps tip ports, async-low ``rst_n``, depth-256 RETRY buffer
(Null/Retry skip; ``NumFree+ReleaseSize>256`` → proto_err).
pycc netlists are a prototype only; this file is what lands in
``rtl/dll/vibe_dll_retry_buf.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/dll/vibe_dll_retry_buf.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip fc7c0151 / freeze 302ac943. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_dll_retry_buf
"""

BODY = """\
// AS-0.1 §12: retry_buf depth 256 FS-must. Null and Retry blocks do not enter.
// NumFreeBuf+ReleaseSize>256 → DL Protocol Error.
module vibe_dll_retry_buf (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         link_up,
  input  logic         wr_en,
  input  logic         is_null,
  input  logic         is_retry,
  input  logic [159:0] wr_flit,
  input  logic [7:0]   send_size,
  input  logic         ack_rel,
  input  logic [7:0]   rel_size,
  input  logic [7:0]   rd_ptr_i,
  output logic [159:0] rd_flit,
  output logic [7:0]   wr_ptr,
  output logic [7:0]   tail_ptr,
  output logic [7:0]   rcv_ptr,
  output logic [8:0]   num_free,
  output logic         proto_err,
  output logic         can_send
);
  `include "vibe_ub_params.vh"

  logic [159:0] mem [0:255];
  logic [7:0]   wrp, tail, rcv;
  logic [8:0]   freeb;

  assign wr_ptr   = wrp;
  assign tail_ptr = tail;
  assign rcv_ptr  = rcv;
  assign num_free = freeb;
  assign can_send = (freeb >= {1'b0, send_size});
  assign rd_flit  = mem[rd_ptr_i];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wrp       <= 8'd0;
      tail      <= 8'd0;
      rcv       <= 8'd0;
      freeb     <= 9'd256;
      proto_err <= 1'b0;
    end else if (port_rst || !link_up) begin
      wrp       <= 8'd0;
      tail      <= 8'd0;
      rcv       <= 8'd0;
      freeb     <= 9'd256;
    end else begin
      if (wr_en && !is_null && !is_retry && can_send) begin
        mem[wrp] <= wr_flit;
        wrp      <= wrp + 8'd1;
        freeb    <= freeb - 9'd1;
      end
      if (ack_rel) begin
        if (freeb + {1'b0, rel_size} > 9'd256)
          proto_err <= 1'b1;
        else begin
          freeb <= freeb + {1'b0, rel_size};
          tail  <= tail + rel_size;
          rcv   <= rcv + rel_size;
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
    dest = repo / "rtl" / "dll" / "vibe_dll_retry_buf.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
