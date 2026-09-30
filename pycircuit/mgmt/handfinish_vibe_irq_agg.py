"""Emit the product SystemVerilog for vibe_irq_agg (hand-finished).

Keeps tip ports, async-low ``rst_n``, and the sticky OR body
(AS-0.1 §10/§15: irq_logic of observable errors, including G1
RT=10/11). pycc netlists are a prototype only; this file is
what lands in ``rtl/mgmt/vibe_irq_agg.sv``.
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/mgmt/vibe_irq_agg.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip 7dbac272. Decision I UNFROZEN. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_irq_agg
"""

BODY = """\
// FS-0.2.3 + AS-0.1 §10/§15: irq_logic sticky OR of observable errors (includes G1 RT=10/11).
// Clear on static write or reset. Single bit; no extra product IRQ pins.
module vibe_irq_agg (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       irq_clr,
  input  logic [3:0] rx_ovf,
  input  logic [3:0] fc_ovf,
  input  logic [3:0] proto_err,
  input  logic [3:0] retry_error,
  input  logic       icrc_fail,
  input  logic [3:0] len_err,
  input  logic [3:0] deadlock_drop,
  input  logic       drop_g1,
  input  logic [3:0] afifo_ovf,
  output logic       irq_logic
);
  logic sticky;

  assign irq_logic = sticky;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sticky <= 1'b0;
    end else if (irq_clr) begin
      sticky <= 1'b0;
    end else if (|rx_ovf || |fc_ovf || |proto_err || |retry_error || icrc_fail ||
                 |len_err || |deadlock_drop || drop_g1 || |afifo_ovf) begin
      sticky <= 1'b1;
    end
  end
endmodule
"""


def render() -> str:
    return HEADER + BODY + FOOTER


def write_rtl(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return dest


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    dest = repo / "rtl" / "mgmt" / "vibe_irq_agg.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
