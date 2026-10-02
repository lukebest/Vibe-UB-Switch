// Thin cocotb wrapper. DUT RTL never edited.
// Product NW ICRC CRC32 (AS-0.1 §13): init all-1, per-byte bit reverse
// then reverse+invert. Clock from entry_unit (2 ns).
// Decision-I wrap leaf `tc_vibe_icrc` / make icrc / make tc_vibe_icrc
// uses this top. Instance u_u matches Decision-I leaf wrappers
// (product instantiator is Unit TB / cna_ep u_icrc; not leftover
// u_icrc on this wrap). First NW leaf after stage-77 DLL wrap.
// ovf_l (F1) is not in this module. This is not vibe_dll /
// vibe_bcrc / vibe_dll_tx / vibe_dll_credit / vibe_dll_sm /
// vibe_dll_rx / vibe_nw_adapt / vibe_port.
// CHILDREN: none.
`timescale 1ns/1ps

module vibe_icrc_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_byte,
  input  logic         last,
  output logic [31:0]  crc_out,
  output logic         done
);
  vibe_icrc u_u (
    .clk(clk), .rst_n(rst_n), .start(start),
    .in_vld(in_vld), .in_byte(in_byte), .last(last),
    .crc_out(crc_out), .done(done)
  );
endmodule
