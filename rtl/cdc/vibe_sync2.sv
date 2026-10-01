// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_sync2.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 00647c9e. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_sync2
//
// AS-0.1 §7: 2-FF synchronizer for gray pointers.
module vibe_sync2 #(
  parameter int W = 5
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [W-1:0] d,
  output logic [W-1:0] q
);
  logic [W-1:0] q1;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      q1 <= '0;
      q  <= '0;
    end else begin
      q1 <= d;
      q  <= q1;
    end
  end
endmodule
