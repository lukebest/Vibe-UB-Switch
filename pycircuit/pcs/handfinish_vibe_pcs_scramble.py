"""Emit the product SystemVerilog for vibe_pcs_scramble (hand-finished).

Keeps tip ports, async-low ``rst_n``, combo 160b ``xmask``, pass-through
when ``en=0`` (AMCTL/EEIB; LFSR does not advance), and seed
``{19'd1, lane_id, 2'b01}``. pycc netlists are a prototype only;
this file is what lands in ``rtl/pcs/vibe_pcs_scramble.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_pcs_scramble.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 5087843 / freeze 302ac943.
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_pcs_scramble
//
"""

BODY = """\
// AS-0.1 §5 / UB 3.2.2.4: scramble LTB and DLL data; not AMCTL/EEIB.
// Seed from AMCTL.LID (lane_id). Reset seed on AMCTL+EDF when LMSM is not
// Send_NullBlock/Link_Active; do not reset on SDF in those states.
module vibe_pcs_scramble (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [1:0]   lane_id,   // AMCTL.LID (physical=logical this rev)
  input  logic         seed_load,
  input  logic         en,       // 0 = pass-through (AMCTL/EEIB)
  input  logic         in_vld,
  input  logic [159:0] in_data,
  output logic         out_vld,
  output logic [159:0] out_data
);
  `include "vibe_ub_params.vh"

  logic [22:0] lfsr;
  logic [159:0] xmask;
  integer i;

  function automatic [22:0] step;
    input [22:0] s;
    begin
      step = {s[21:0], s[22] ^ s[17]};
    end
  endfunction

  always @* begin
    xmask = 160'd0;
    begin : gen_mask
      logic [22:0] t;
      t = lfsr;
      for (i = 0; i < 160; i = i + 1) begin
        xmask[i] = t[0];
        t = step(t);
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      lfsr     <= {21'd0, 2'b01};
      out_vld  <= 1'b0;
      out_data <= 160'd0;
    end else begin
      if (seed_load)
        lfsr <= {19'd1, lane_id, 2'b01};
      out_vld <= in_vld;
      if (in_vld) begin
        out_data <= en ? (in_data ^ xmask) : in_data;
        if (en) begin
          begin : adv
            logic [22:0] t;
            t = lfsr;
            for (i = 0; i < 160; i = i + 1) t = step(t);
            lfsr <= t;
          end
        end
      end
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "pcs" / "vibe_pcs_scramble.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
