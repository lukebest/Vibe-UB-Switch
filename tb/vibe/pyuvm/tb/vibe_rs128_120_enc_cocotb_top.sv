// Thin cocotb wrapper. DUT RTL never edited.
// Product systematic RS(128,120) encoder, GF(256) (AS-0.1 §5 T3).
// Clock comes from entry_unit. Instance u_u matches Decision-I
// leaf wrappers. CHILDREN: none (leaf cell).
// ovf_l (F1) is not in this module. This is not vibe_pcs_tx / rx.
`timescale 1ns/1ps

module vibe_rs128_120_enc_cocotb_top (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        start,
  input  logic        in_vld,
  input  logic [7:0]  in_sym,
  output logic        in_ready,
  output logic        done,
  output logic [63:0] parity
);
  vibe_rs128_120_enc u_u (
    .clk(clk), .rst_n(rst_n), .start(start),
    .in_vld(in_vld), .in_sym(in_sym), .in_ready(in_ready),
    .done(done), .parity(parity)
  );
endmodule
