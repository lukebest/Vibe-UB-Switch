// AS-0.1 §12: credit consume ceil(DLLDP_flits/n), n default 8.
// Pending >= 1024 → backpressure NW and force Crd_Ack. Timeout 1us → DL Protocol Error.
// CFG0 DLLCB does not consume credit. No credit underflow code.
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

  function automatic [15:0] ceil_div;
    input [9:0] flits;
    input [7:0] n;
    begin
      if (n == 8'd0) ceil_div = 16'd0;
      else ceil_div = ({6'd0, flits} + {8'd0, n} - 16'd1) / {8'd0, n};
    end
  endfunction

  assign pending       = pend;
  assign force_crd_ack = (pend >= VIBE_CREDIT_THRESH[15:0]) || (!consume_vld && pend != 0);
  assign bp_nw         = (pend >= VIBE_CREDIT_THRESH[15:0]);
  assign credit_low    = (cells == 16'd0);

  // 17-bit sum so Flow Control Overflow is reachable (16-bit CMPCONST never fired).
  wire [16:0] cells_sum = {1'b0, cells} + {1'b0, ceil_div(consume_flits, grain_n)};

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
      if (credit_ret) begin
        pend <= pend + credit_ret_n;
        to   <= VIBE_US_CYC[10:0];
      end else if (pend != 0) begin
        if (to == 0) proto_err <= 1'b1;
        else         to <= to - 11'd1;
      end
    end
  end
endmodule
