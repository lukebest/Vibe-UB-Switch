// Coverage bind target for vibe_* (Verilator --coverage collects line/toggle).
// FSM coverage is whatever the tool emits; we do not invent numbers.
`ifndef VIBE_COV_SV
`define VIBE_COV_SV
module vibe_cov_stub;
  // Intentionally empty — Verilator coverage is compile-flag based.
endmodule
`endif
