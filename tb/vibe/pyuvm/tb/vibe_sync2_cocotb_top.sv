// Thin cocotb wrapper. DUT RTL never edited.
// Product 2-FF dest-domain sync: W=5. Clock comes from entry_unit.
`timescale 1ns/1ps

module vibe_sync2_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic [4:0] d,
  output logic [4:0] q
);
  vibe_sync2 #(.W(5)) u_sync2 (
    .clk(clk), .rst_n(rst_n), .d(d), .q(q)
  );
endmodule
