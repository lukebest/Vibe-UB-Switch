// Thin cocotb wrapper. DUT RTL never edited.
// Dual-clock product TX config: W=160, DEPTH=16. Clocks come from entry_unit.
`timescale 1ns/1ps

module vibe_afifo_cocotb_top (
  input  logic         wclk,
  input  logic         wrst_n,
  input  logic         wen,
  input  logic [159:0] wdata,
  output logic         wfull,
  output logic         almost_full,
  output logic [4:0]   wocc,
  input  logic         rclk,
  input  logic         rrst_n,
  input  logic         ren,
  output logic [159:0] rdata,
  output logic         rempty
);
  vibe_afifo #(.W(160), .DEPTH(16)) u_afifo (
    .wclk(wclk), .wrst_n(wrst_n), .wen(wen), .wdata(wdata),
    .wfull(wfull), .almost_full(almost_full), .wocc(wocc),
    .rclk(rclk), .rrst_n(rrst_n), .ren(ren), .rdata(rdata),
    .rempty(rempty)
  );
endmodule
