// GENERATED/HAND-FINISHED from pycircuit/cdc/vibe_rst_sync.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 31647057. Decision I UNFROZEN (freeze 302ac943 VOID). Path B hold.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_rst_sync
//
// AS-0.1 §3: async assert, sync deassert into a destination clock.
module vibe_rst_sync (
  input  logic clk,
  input  logic rst_n_in,
  output logic rst_n_out
);
  logic r1;
  always @(posedge clk or negedge rst_n_in) begin
    if (!rst_n_in) begin
      r1        <= 1'b0;
      rst_n_out <= 1'b0;
    end else begin
      r1        <= 1'b1;
      rst_n_out <= r1;
    end
  end
endmodule
