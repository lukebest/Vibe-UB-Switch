// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL BCRC CRC30 (AS-0.1 §12): init all-1, no invert.
// bit31 reserved, bit30 ERROR_FLAG. Clock from entry_unit (2 ns).
// Instance u_u matches Decision-I leaf wrappers.
// ovf_l (F1) is not in this module. This is not vibe_dll / vibe_dll_tx /
// vibe_dll_credit / vibe_dll_sm / vibe_dll_rx / vibe_icrc.
// CHILDREN: none.
`timescale 1ns/1ps

module vibe_bcrc_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [159:0] in_flit,
  input  logic         last,
  input  logic         error_flag,
  output logic [31:0]  crc_word,
  output logic         done
);
  vibe_bcrc u_u (
    .clk(clk), .rst_n(rst_n), .start(start),
    .in_vld(in_vld), .in_flit(in_flit), .last(last),
    .error_flag(error_flag), .crc_word(crc_word), .done(done)
  );
endmodule
