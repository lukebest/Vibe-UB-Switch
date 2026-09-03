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
  input  logic [3:0]   cfg6_hit,
  input  logic [511:0] cfg6_data [0:3],
  output logic [3:0]   consume,
  output logic [511:0] reply_data [0:3],
  output logic [3:0]   reply_vld,
  input  logic [3:0]   reply_ready,
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
    consume   = 4'd0;
    icrc_fail = 1'b0;
    flit      = 160'd0;
    for (p = 0; p < 4; p = p + 1) begin
      reply_data[p] = 512'd0;
      reply_vld[p]  = 1'b0;
      if (cfg6_hit[p]) begin
        flit = vibe_nw512_flit0(cfg6_data[p]);
        cfg  = vibe_lph_cfg(flit);
        dcna = vibe_nth_dcna(flit);
        nlp  = vibe_nth_nlp(flit);
        opc  = flit[103:96]; // opcode in first assembled flit
        us   = cna_written && (dcna == cna);
        term = us || (nlp == 3'd1) || (opc == 8'h10 && us);
        if (term) begin
          consume[p]    = 1'b1;
          reply_vld[p]  = 1'b1;
          reply_data[p] = cfg6_data[p]; // echo; cna_ep generates CFG6 reply
        end
      end
    end
  end
endmodule
