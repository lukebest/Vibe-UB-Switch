// AS-0.1 §12 / FS-0.2.6: credit consume ceil(DLLDP_flits/n), n default 8.
// Pending-to-return is a cell count. Pending >= 1024 cell → backpressure NW
// and force Crd_Ack (VIBE_CREDIT_THRESH stays 1024; not 1024×n flits).
// Timeout 1us → DL Protocol Error. CFG0 DLLCB does not consume credit.
// No credit underflow code.
module vibe_dll_credit (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        port_rst,
  input  logic        link_up,
  input  logic [7:0]  grain_n,     // 1,2,4,...,128 default 8
  input  logic        consume_vld,
  input  logic [9:0]  consume_flits,
  input  logic        is_cfg0,
  input  logic        credit_ret,
  input  logic [15:0] credit_ret_n,
  output logic [15:0] pending,
  output logic        credit_low,
  output logic        force_crd_ack,
  output logic        bp_nw,
  output logic        proto_err,
  output logic        fc_ovf
);
  `include "vibe_ub_params.vh"

  logic [15:0] cells;
  logic [15:0] pend;
  logic [10:0] to;

  // flits → cells. n=0 → 0. Same grain for consume and pending-to-return.
  function automatic [15:0] ceil_div;
    input [15:0] flits;
    input [7:0]  n;
    begin
      if (n == 8'd0) ceil_div = 16'd0;
      else ceil_div = ({1'b0, flits} + {9'd0, n} - 17'd1) / {9'd0, n};
    end
  endfunction

  assign pending       = pend;
  assign force_crd_ack = (pend >= VIBE_CREDIT_THRESH[15:0]) || (!consume_vld && pend != 0);
  assign bp_nw         = (pend >= VIBE_CREDIT_THRESH[15:0]);
  assign credit_low    = (cells == 16'd0);

  // 17-bit sum so Flow Control Overflow is reachable (16-bit CMPCONST never fired).
  wire [15:0] consume_cells = ceil_div({6'd0, consume_flits}, grain_n);
  wire [16:0] cells_sum     = {1'b0, cells} + {1'b0, consume_cells};
  // pend is cells. Sent/received flits use the same ceil(flits/n) as consume.
  // Crd_Ack grain (credit_ret_n) is already cells — do not treat it as raw flits.
  wire [16:0] pend_sum = {1'b0, pend}
                       + (credit_ret ? {1'b0, credit_ret_n} : 17'd0)
                       + ((consume_vld && !is_cfg0) ? {1'b0, consume_cells} : 17'd0);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cells     <= 16'd0;
      pend      <= 16'd0;
      to        <= 11'd0;
      proto_err <= 1'b0;
      fc_ovf    <= 1'b0;
    end else if (port_rst || !link_up) begin
      cells     <= 16'd0;
      pend      <= 16'd0;
      to        <= 11'd0;
    end else begin
      if (consume_vld && !is_cfg0) begin
        if (cells_sum > 17'd65535) begin
          fc_ovf <= 1'b1;
          cells  <= 16'd65535;
        end else
          cells  <= cells_sum[15:0];
      end
      pend <= pend_sum[15:0];
      if (credit_ret || (consume_vld && !is_cfg0 && consume_cells != 16'd0))
        to <= VIBE_US_CYC[10:0];
      else if (pend != 0) begin
        if (to == 0) proto_err <= 1'b1;
        else         to <= to - 11'd1;
      end
    end
  end
endmodule
