// Thin cocotb wrapper. DUT RTL never edited.
// Product mgmt CFG6 terminate / echo (AS-0.1.2 §9/§13): combo
// leaf. Terminate if DCNA==written CNA, OR NLP=1, OR
// (opc==8'h10 && us). Echo fab_mgmt_cfg6_data — do not assemble
// a CFG6 CSR read. Official opcode 0x10 / Appendix D packing
// is 未知; this wrapper does not invent it. icrc_fail is tied 0
// (no ICRC unit in this leaf). clk / rst_n / mgmt_nw_ready are
// unused in the combo body (wrap still wires them). Instantiated
// by vibe_mgmt u_cna. Clock from entry_unit (2 ns). Flattened
// fab_mgmt_cfg6_data_* / mgmt_nw_data_* — cocotb cannot drive
// unpacked array ports. Instance u_u matches Decision-I leaf
// wrappers (wrap-style tc_cna_ep still uses flattened ports).
// Icarus 12 VPI leaves 512-bit packed mgmt_nw_data_* X; packed
// consume / mgmt_nw_vld / icrc_fail remain the Icarus scorers.
`timescale 1ns/1ps

module vibe_cna_ep_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         cna_written,
  input  logic [15:0]  cna,
  input  logic [3:0]   fab_mgmt_cfg6_hit,
  input  logic [3:0]   mgmt_nw_ready,
  input  logic [511:0] fab_mgmt_cfg6_data_0,
  input  logic [511:0] fab_mgmt_cfg6_data_1,
  input  logic [511:0] fab_mgmt_cfg6_data_2,
  input  logic [511:0] fab_mgmt_cfg6_data_3,
  output logic [3:0]   consume,
  output logic [3:0]   mgmt_nw_vld,
  output logic [511:0] mgmt_nw_data_0,
  output logic [511:0] mgmt_nw_data_1,
  output logic [511:0] mgmt_nw_data_2,
  output logic [511:0] mgmt_nw_data_3,
  output logic         icrc_fail
);
  logic [511:0] fab_mgmt_cfg6_data [0:3];
  logic [511:0] mgmt_nw_data [0:3];
  assign fab_mgmt_cfg6_data[0] = fab_mgmt_cfg6_data_0;
  assign fab_mgmt_cfg6_data[1] = fab_mgmt_cfg6_data_1;
  assign fab_mgmt_cfg6_data[2] = fab_mgmt_cfg6_data_2;
  assign fab_mgmt_cfg6_data[3] = fab_mgmt_cfg6_data_3;
  assign mgmt_nw_data_0 = mgmt_nw_data[0];
  assign mgmt_nw_data_1 = mgmt_nw_data[1];
  assign mgmt_nw_data_2 = mgmt_nw_data[2];
  assign mgmt_nw_data_3 = mgmt_nw_data[3];
  vibe_cna_ep u_u (
    .clk(clk), .rst_n(rst_n), .cna(cna), .cna_written(cna_written),
    .fab_mgmt_cfg6_hit(fab_mgmt_cfg6_hit),
    .fab_mgmt_cfg6_data(fab_mgmt_cfg6_data),
    .mgmt_fab_cfg6_consume(consume),
    .mgmt_nw_data(mgmt_nw_data),
    .mgmt_nw_vld(mgmt_nw_vld),
    .mgmt_nw_ready(mgmt_nw_ready),
    .icrc_fail(icrc_fail)
  );
endmodule
