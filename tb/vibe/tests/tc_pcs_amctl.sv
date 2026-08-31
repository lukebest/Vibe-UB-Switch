// AMCTL 40-symbol eBCH-16 insert path (after FEC, before G2).
`timescale 1ns/1ps
module tc_pcs_amctl;
  logic clk, rst_n, link_up, sdf_period, req, ack;
  logic [1:0] lane_id;
  logic [319:0] amctl_40B;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_pcs_tx_amctl u_a (
    .clk(clk), .rst_n(rst_n), .link_up(link_up), .sdf_period(sdf_period),
    .lane_id(lane_id), .req(req), .ack(ack), .amctl_40B(amctl_40B)
  );
  initial begin
    fail = 0;
    rst_n = 0; link_up = 1; sdf_period = 1; lane_id = 0; req = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    req = 1;
    repeat (4) @(posedge clk);
    if (amctl_40B === 320'd0) begin
      $display("FAIL tc_pcs_amctl");
      $display("  stimulus : link_up sdf_period lane0 req");
      $display("  expected : nonzero 40-symbol AMCTL (eBCH-16)");
      $display("  actual   : 0");
      $display("  hier     : u_a.amctl_40B / u_a.cw21");
      fail = 1;
    end
    // Hit every lane_id arm (combo LUT)
    lane_id = 2'd1; #1;
    lane_id = 2'd2; #1;
    lane_id = 2'd3; #1;
    if (amctl_40B === 320'd0) begin
      $display("FAIL tc_pcs_amctl");
      $display("  stimulus : lane_id=3");
      $display("  expected : nonzero AMCTL");
      $display("  actual   : 0");
      fail = 1;
    end
    link_up = 0; #1;
    if (ack) begin
      $display("FAIL tc_pcs_amctl");
      $display("  stimulus : req=1 link_up=0");
      $display("  expected : ack=0");
      $display("  actual   : 1");
      fail = 1;
    end
    if (!fail) $display("PASS tc_pcs_amctl");
    $finish;
  end
endmodule
