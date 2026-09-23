// Thin cocotb wrapper. DUT RTL never edited.
// Product 2-FF dest-domain reset sync: async assert / sync deassert.
// Clock comes from entry_unit.
`timescale 1ns/1ps

module vibe_rst_sync_cocotb_top (
  input  logic clk,
  input  logic rst_n_in,
  output logic rst_n_out
);
  vibe_rst_sync u_rst_sync (
    .clk(clk), .rst_n_in(rst_n_in), .rst_n_out(rst_n_out)
  );
endmodule
