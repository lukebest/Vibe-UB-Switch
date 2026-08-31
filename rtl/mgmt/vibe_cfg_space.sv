// AS-0.1 §10: static write cfg_wr_*. GUID Type 0x3, Class 0x03/0x00,
// CFG0_PORT_BASIC/CAP, ROUTE_TABLE + Default, CNA static write only.
module vibe_cfg_space #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        device_rst,
  input  logic        cfg_wr_vld,
  output logic        cfg_wr_ready,
  input  logic [2:0]  cfg_wr_cmd,
  input  logic [15:0] cfg_wr_idx,
  input  logic [31:0] cfg_wr_data,
  output logic [15:0] cna,
  output logic        cna_written,
  output logic [3:0]  default_bm,
  output logic        rt_wr_en,
  output logic [15:0] rt_wr_idx,
  output logic [31:0] rt_wr_data,
  output logic [3:0]  port_rst_pulse,
  output logic        device_rst_pulse,
  output logic [3:0]  lmsm_go_pulse,
  output logic        irq_clr,
  output logic [31:0] guid0,
  output logic [31:0] class_code,
  output logic [31:0] port_basic,
  output logic [31:0] port_cap
);
  `include "vibe_ub_params.vh"

  assign cfg_wr_ready = 1'b1;
  assign guid0        = {24'd0, VIBE_GUID_TYPE};
  assign class_code   = {16'd0, VIBE_CLASS_CODE};
  assign port_basic   = VIBE_PORT_BASIC;
  assign port_cap     = VIBE_PORT_CAP;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n || device_rst) begin
      cna              <= 16'd0;
      cna_written      <= 1'b0;
      default_bm       <= 4'd0;
      rt_wr_en         <= 1'b0;
      rt_wr_idx        <= 16'd0;
      rt_wr_data       <= 32'd0;
      port_rst_pulse   <= 4'd0;
      device_rst_pulse <= 1'b0;
      lmsm_go_pulse    <= 4'd0;
      irq_clr          <= 1'b0;
    end else begin
      rt_wr_en         <= 1'b0;
      port_rst_pulse   <= 4'd0;
      device_rst_pulse <= 1'b0;
      lmsm_go_pulse    <= 4'd0;
      irq_clr          <= 1'b0;
      if (cfg_wr_vld && cfg_wr_ready) begin
        irq_clr <= 1'b1; // AS-0.1 §10: sticky clear on static write
        case (cfg_wr_cmd)
          3'd0: begin
            cna         <= cfg_wr_data[15:0];
            cna_written <= 1'b1;
          end
          3'd1: begin
            rt_wr_en   <= 1'b1;
            rt_wr_idx  <= cfg_wr_idx;
            rt_wr_data <= cfg_wr_data;
          end
          3'd2: default_bm <= cfg_wr_data[3:0];
          3'd3: port_rst_pulse[cfg_wr_idx[1:0]] <= 1'b1;
          3'd4: device_rst_pulse <= 1'b1;
          3'd5: lmsm_go_pulse[cfg_wr_idx[1:0]] <= 1'b1;
          default: ;
        endcase
      end
    end
  end
endmodule
