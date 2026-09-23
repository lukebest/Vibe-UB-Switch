// Thin cocotb wrapper. DUT RTL never edited.
// Product DLL retry_buf (AS-0.1 §12): depth 256 FS-must.
// Null and Retry blocks do not enter. NumFreeBuf+ReleaseSize>256
// → DL Protocol Error. Instantiated by vibe_dll u_rbuf.
// Clock from entry_unit (2 ns).
`timescale 1ns/1ps

module vibe_dll_retry_buf_cocotb_top (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         port_rst,
  input  logic         link_up,
  input  logic         wr_en,
  input  logic         is_null,
  input  logic         is_retry,
  input  logic [159:0] wr_flit,
  input  logic [7:0]   send_size,
  input  logic         ack_rel,
  input  logic [7:0]   rel_size,
  input  logic [7:0]   rd_ptr_i,
  output logic [159:0] rd_flit,
  output logic [7:0]   wr_ptr,
  output logic [7:0]   tail_ptr,
  output logic [7:0]   rcv_ptr,
  output logic [8:0]   num_free,
  output logic         proto_err,
  output logic         can_send
);
  vibe_dll_retry_buf u_u (
    .clk(clk), .rst_n(rst_n), .port_rst(port_rst), .link_up(link_up),
    .wr_en(wr_en), .is_null(is_null), .is_retry(is_retry),
    .wr_flit(wr_flit), .send_size(send_size),
    .ack_rel(ack_rel), .rel_size(rel_size), .rd_ptr_i(rd_ptr_i),
    .rd_flit(rd_flit), .wr_ptr(wr_ptr), .tail_ptr(tail_ptr),
    .rcv_ptr(rcv_ptr), .num_free(num_free),
    .proto_err(proto_err), .can_send(can_send)
  );
endmodule
