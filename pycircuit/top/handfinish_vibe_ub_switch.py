"""Emit the product SystemVerilog for vibe_ub_switch (hand-finished).

Keeps tip ports, ``ROUTE_TABLE_DEPTH`` default 256, the stock
children (4× ``g_port[gi].u_port``, ``u_fab``, ``u_mgmt``,
4× ``g_byp[gi].u_byp``), interconnect nets, and generate
loops (AS-0.1.2 §4/§17). ``vibe_fabric`` / ``vibe_mgmt`` stay
stock SV (no pyCircuit wrap yet). pycc netlists are a
prototype only; this file is what lands in
``rtl/top/vibe_ub_switch.sv``. Do not rewrite F1 ``ovf_l``
(lives under ``vibe_port``).
"""

from __future__ import annotations

from pathlib import Path

HEADER = """\
// GENERATED/HAND-FINISHED from pycircuit/top/vibe_ub_switch.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
// Product ports match tip cb644804 / 260dc6db. Decision I UNFROZEN. Path B hold.
"""

FOOTER = """\
// pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// SPEC / CR-B names unchanged. F1 ovf_l stays stock (lives in vibe_port; do not rewrite).
// Regenerate: make -C pycircuit vibe_ub_switch
"""

BODY = """\
// FS-0.2.3 + AS-0.1.2 §4/§17: top — 4-port PMA + clk_fab + rst_n + cfg_wr_* + irq_logic.
// cfg_wr_cmd is 4 bits (opcodes 0–5; 6–15 ignore). No cfg_rd_* pin.
// G1 named signals: rt_shortest_unimpl (32-bit saturating), sticky irq_logic. No extra IRQ pins.
module vibe_ub_switch #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic         clk_fab,
  input  logic         rst_n,
  input  logic         txclk_0,
  input  logic         txclk_1,
  input  logic         txclk_2,
  input  logic         txclk_3,
  input  logic         rxclk_0,
  input  logic         rxclk_1,
  input  logic         rxclk_2,
  input  logic         rxclk_3,
  output logic [511:0] pcs_pma_txdata_0,
  output logic [511:0] pcs_pma_txdata_1,
  output logic [511:0] pcs_pma_txdata_2,
  output logic [511:0] pcs_pma_txdata_3,
  input  logic [511:0] pma_pcs_rxdata_0,
  input  logic [511:0] pma_pcs_rxdata_1,
  input  logic [511:0] pma_pcs_rxdata_2,
  input  logic [511:0] pma_pcs_rxdata_3,
  input  logic         cfg_wr_vld,
  output logic         cfg_wr_ready,
  input  logic [3:0]   cfg_wr_cmd,
  input  logic [15:0]  cfg_wr_idx,
  input  logic [31:0]  cfg_wr_data,
  output logic         irq_logic
);
  logic [3:0]   status_up, disabled;
  logic [3:0]   retry_error, proto_err, fc_ovf, rx_ovf, afifo_ovf;
  logic [3:0]   port_rst, lmsm_go;
  logic         device_rst;
  logic [3:0]   default_bm;
  logic         rt_wr_en;
  logic [15:0]  rt_wr_idx;
  logic [31:0]  rt_wr_data;
  logic [15:0]  cna;
  logic         cna_written;
  logic [511:0] fab_nw_data [0:3];
  logic [3:0]   fab_nw_vld, fab_nw_ready;
  logic [511:0] nw_fab_data [0:3];
  logic [3:0]   nw_fab_vld, nw_fab_ready;
  logic [511:0] mgmt_nw_data [0:3];
  logic [3:0]   mgmt_nw_vld, mgmt_nw_ready;
  logic [3:0]   len_err, deadlock_drop, fab_mgmt_cfg6_hit, mgmt_fab_cfg6_consume;
  logic         drop_g1;
  logic [31:0]  rt_shortest_unimpl, drop_down;
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  logic [511:0] mgmt_nw_push [0:3];
  logic [3:0]   mgmt_nw_push_vld, mgmt_nw_push_ready;
  logic [511:0] pcs_pma_txdata [0:3];
  logic [511:0] pma_pcs_rxdata [0:3];
  logic [3:0]   txclk, rxclk;

  assign txclk = {txclk_3, txclk_2, txclk_1, txclk_0};
  assign rxclk = {rxclk_3, rxclk_2, rxclk_1, rxclk_0};
  assign pma_pcs_rxdata[0] = pma_pcs_rxdata_0;
  assign pma_pcs_rxdata[1] = pma_pcs_rxdata_1;
  assign pma_pcs_rxdata[2] = pma_pcs_rxdata_2;
  assign pma_pcs_rxdata[3] = pma_pcs_rxdata_3;
  assign pcs_pma_txdata_0 = pcs_pma_txdata[0];
  assign pcs_pma_txdata_1 = pcs_pma_txdata[1];
  assign pcs_pma_txdata_2 = pcs_pma_txdata[2];
  assign pcs_pma_txdata_3 = pcs_pma_txdata[3];

  genvar gi;
  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_port
      vibe_port u_port (
        .clk_fab(clk_fab), .rst_n(rst_n),
        .port_rst(port_rst[gi]), .device_rst(device_rst),
        .lmsm_go(lmsm_go[gi]),
        .txclk(txclk[gi]), .rxclk(rxclk[gi]),
        .pcs_pma_txdata(pcs_pma_txdata[gi]), .pma_pcs_rxdata(pma_pcs_rxdata[gi]),
        .fab_nw_data(fab_nw_data[gi]), .fab_nw_vld(fab_nw_vld[gi]), .fab_nw_ready(fab_nw_ready[gi]),
        .nw_fab_data(nw_fab_data[gi]), .nw_fab_vld(nw_fab_vld[gi]), .nw_fab_ready(nw_fab_ready[gi]),
        .mgmt_nw_data(mgmt_nw_data[gi]), .mgmt_nw_vld(mgmt_nw_vld[gi]), .mgmt_nw_ready(mgmt_nw_ready[gi]),
        .status_up(status_up[gi]), .disabled(disabled[gi]),
        .retry_error(retry_error[gi]), .proto_err(proto_err[gi]),
        .fc_ovf(fc_ovf[gi]), .rx_ovf(rx_ovf[gi]), .afifo_ovf(afifo_ovf[gi]),
        .cfg0_hit(), .cfg0_data()
      );
    end
  endgenerate

  vibe_fabric #(.ROUTE_TABLE_DEPTH(ROUTE_TABLE_DEPTH)) u_fab (
    .clk(clk_fab), .rst_n(rst_n), .device_rst(device_rst),
    .status_up(status_up), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .nw_fab_data(nw_fab_data), .nw_fab_vld(nw_fab_vld), .nw_fab_ready(nw_fab_ready),
    .fab_nw_data(fab_nw_data), .fab_nw_vld(fab_nw_vld), .fab_nw_ready(fab_nw_ready),
    .len_err(len_err), .drop_g1(drop_g1),
    .rt_shortest_unimpl(rt_shortest_unimpl), .drop_down_cnt(drop_down),
    .deadlock_drop(deadlock_drop), .irq_rt(),
    .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data)
  );

  vibe_mgmt #(.ROUTE_TABLE_DEPTH(ROUTE_TABLE_DEPTH)) u_mgmt (
    .clk(clk_fab), .rst_n(rst_n),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst(port_rst), .device_rst(device_rst), .lmsm_go(lmsm_go),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit), .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data),
    .mgmt_fab_cfg6_consume(mgmt_fab_cfg6_consume),
    .mgmt_nw_data(mgmt_nw_push), .mgmt_nw_vld(mgmt_nw_push_vld), .mgmt_nw_ready(mgmt_nw_push_ready),
    .rx_ovf(rx_ovf), .fc_ovf(fc_ovf), .proto_err(proto_err),
    .retry_error(retry_error), .len_err(len_err),
    .deadlock_drop(deadlock_drop), .drop_g1(drop_g1),
    .afifo_ovf(afifo_ovf), .irq_logic(irq_logic)
  );

  generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : g_byp
      vibe_mgmt_byp u_byp (
        .clk(clk_fab), .rst_n(rst_n),
        .in_data(mgmt_nw_push[gi]), .in_vld(mgmt_nw_push_vld[gi]), .in_ready(mgmt_nw_push_ready[gi]),
        .out_data(mgmt_nw_data[gi]), .out_vld(mgmt_nw_vld[gi]), .out_ready(mgmt_nw_ready[gi])
      );
    end
  endgenerate
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
    dest = repo / "rtl" / "top" / "vibe_ub_switch.sv"
    write_rtl(dest)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
