"""Emit the product SystemVerilog for vibe_cna_ep (hand-finished).

Keeps tip ports, combo ``always @*`` body, and the CFG6
terminate / echo (AS-0.1.2 §9/§13: DCNA==mgmt CNA AND CNA
written, OR NLP=1, OR opcode 0x10). pycc netlists are a
prototype only; this file is what lands in
``rtl/mgmt/vibe_cna_ep.sv``. Official opcode 0x10 /
Appendix D packing is 未知 — do not invent. Echo only.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/mgmt/vibe_cna_ep.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip cf64951b. Decision I UNFROZEN. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_cna_ep
"""

BODY = """\
// AS-0.1.2 §9/§13: CFG6 terminate if DCNA==mgmt CNA AND CNA written, OR NLP=1, OR opcode 0x10.
// ICRC only as sender/receiver. Transit has no ICRC unit.
// Power-on CNA UNKNOWN: do not match until static write.
// CFG6 R/W of named subset (incl. Table D-103 Port Reset): official opcode
// 0x10 payload packing / Appendix D offsets are 未知 — do not invent.
// This module echos the request; it does not assemble a CFG6 CSR read.
module vibe_cna_ep (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [15:0]  cna,
  input  logic         cna_written,
  input  logic [3:0]   fab_mgmt_cfg6_hit,
  input  logic [511:0] fab_mgmt_cfg6_data [0:3],
  output logic [3:0]   mgmt_fab_cfg6_consume,
  output logic [511:0] mgmt_nw_data [0:3],
  output logic [3:0]   mgmt_nw_vld,
  input  logic [3:0]   mgmt_nw_ready,
  output logic         icrc_fail
);
  `include "vibe_ub_fn.vh"

  integer p;
  logic [159:0] flit;
  logic [3:0]  cfg;
  logic [15:0] dcna;
  logic [2:0]  nlp;
  logic [7:0]  opc;
  logic        us, term;

  always @* begin
    mgmt_fab_cfg6_consume = 4'd0;
    icrc_fail = 1'b0;
    flit      = 160'd0;
    cfg       = 4'd0;
    dcna      = 16'd0;
    nlp       = 3'd0;
    opc       = 8'd0;
    us        = 1'b0;
    term      = 1'b0;
    for (p = 0; p < 4; p = p + 1) begin
      mgmt_nw_data[p] = 512'd0;
      mgmt_nw_vld[p]  = 1'b0;
      if (fab_mgmt_cfg6_hit[p]) begin
        flit = vibe_nw512_flit0(fab_mgmt_cfg6_data[p]);
        cfg  = vibe_lph_cfg(flit);
        dcna = vibe_nth_dcna(flit);
        nlp  = vibe_nth_nlp(flit);
        opc  = flit[103:96]; // opcode in first assembled flit
        us   = cna_written && (dcna == cna);
        term = us || (nlp == 3'd1) || (opc == 8'h10 && us);
        if (term) begin
          mgmt_fab_cfg6_consume[p] = 1'b1;
          mgmt_nw_vld[p]           = 1'b1;
          mgmt_nw_data[p]          = fab_mgmt_cfg6_data[p]; // echo; cna_ep generates CFG6 reply
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
    dest = repo / "rtl" / "mgmt" / "vibe_cna_ep.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
