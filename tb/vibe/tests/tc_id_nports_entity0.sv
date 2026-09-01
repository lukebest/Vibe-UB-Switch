// TP-ID-002 / TP-NEG-010: Entity 0, Port 0..3, N_PORTS=4. No fifth port.
`timescale 1ns/1ps
module tc_id_nports_entity0;
  `include "vibe_ub_params.vh"
  integer fail;
  initial begin
    fail = 0;
    if (VIBE_N_PORT !== 4) begin
      $display("FAIL tc_id_nports_entity0");
      $display("  stimulus : compile-time VIBE_N_PORT");
      $display("  expected : 4 (Entity 0 Port 0..3)");
      $display("  actual   : %0d", VIBE_N_PORT);
      $display("  hier     : vibe_ub_params.vh VIBE_N_PORT");
      $display("  reproduce: make -C tb/vibe units");
      fail = 1;
    end
    if (VIBE_PORT_BASIC[31:16] !== 16'd4) begin
      $display("FAIL tc_id_nports_entity0");
      $display("  stimulus : CFG0_PORT_BASIC nports field");
      $display("  expected : 4");
      $display("  actual   : %0d", VIBE_PORT_BASIC[31:16]);
      $display("  hier     : VIBE_PORT_BASIC");
      fail = 1;
    end
    if (!fail) begin
      $display("PASS tc_id_nports_entity0");
      $display("PASS tc_neg_no_fifth_port");
    end
    $finish;
  end
endmodule
