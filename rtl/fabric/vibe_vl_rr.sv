// GENERATED/HAND-FINISHED from pycircuit/fabric/vibe_vl_rr.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 450ed1c2 / freeze 302ac943. Path B hold.
// AS-0.1 §8: VL scheduling RR among non-empty VOQs of an egress; FCFS within VL. No SL.
module vibe_vl_rr (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [15:0] nonempty,
  input  logic        grant,
  output logic [3:0]  vl_sel,
  output logic        valid
);
  logic [3:0] rr;
  logic [3:0] pick;
  integer     n;
  logic [3:0] p;

  always @* begin
    valid = |nonempty;
    pick  = rr;
    p     = rr;
    for (n = 0; n < 16; n = n + 1) begin
      if (nonempty[p]) begin
        pick = p;
        n = 16;
      end else
        p = p + 4'd1;
    end
    vl_sel = pick;
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) rr <= 4'd0;
    else if (grant && valid) rr <= vl_sel + 4'd1;
  end
endmodule
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_vl_rr
