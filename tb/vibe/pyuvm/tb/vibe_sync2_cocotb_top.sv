// Thin cocotb wrapper. DUT RTL never edited.
// Product 2-FF dest-domain sync: W=5 (AFIFO gray pointers).
// Clock comes from entry_unit. Instance u_u matches Decision-I
// leaf wrappers. CHILDREN: none (leaf cell).
`timescale 1ns/1ps

module vibe_sync2_cocotb_top (
  input  logic       clk,
  input  logic       rst_n,
  input  logic [4:0] d,
  output logic [4:0] q
);
  vibe_sync2 #(.W(5)) u_u (
    .clk(clk), .rst_n(rst_n), .d(d), .q(q)
  );
endmodule
