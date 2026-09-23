// Thin cocotb wrapper. DUT RTL never edited.
// Product fabric egress VOQ (AS-0.1 §8/§14). 32 flit/VL, 16 VLs.
// Combo wr_ready / rd_* / nonempty / occ_vl0; async-low rst_n clears
// deadlock_* + wptr/rptr (mem/sop/eop/age not cleared). Deadlock
// timeout VIBE_US_CYC (1250) from enqueue. Instantiated by
// vibe_fabric g_egr.u_voq. Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_voq_egr_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [3:0]   wr_vl,
  input  logic         wr_en,
  input  logic [511:0] wr_data,
  input  logic         wr_sop,
  input  logic         wr_eop,
  output logic         wr_ready,
  input  logic [3:0]   rd_vl,
  input  logic         rd_en,
  output logic [511:0] rd_data,
  output logic         rd_sop,
  output logic         rd_eop,
  output logic [15:0]  nonempty,
  output logic [5:0]   occ_vl0,
  output logic         deadlock_drop,
  output logic [31:0]  deadlock_cnt
);
  vibe_voq_egr #(.DEPTH(32)) u_u (
    .clk(clk), .rst_n(rst_n),
    .wr_vl(wr_vl), .wr_en(wr_en), .wr_data(wr_data),
    .wr_sop(wr_sop), .wr_eop(wr_eop), .wr_ready(wr_ready),
    .rd_vl(rd_vl), .rd_en(rd_en),
    .rd_data(rd_data), .rd_sop(rd_sop), .rd_eop(rd_eop),
    .nonempty(nonempty), .occ_vl0(occ_vl0),
    .deadlock_drop(deadlock_drop), .deadlock_cnt(deadlock_cnt)
  );
endmodule
