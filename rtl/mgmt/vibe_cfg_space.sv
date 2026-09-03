// AS-0.1.2 §10 / UB Table D-103: static write cfg_wr_*.
// cfg_wr_cmd is 4 bits: 0=CNA, 1=route entry, 2=Default bitmap,
// 3=Port Reset (RW1C per port), 4=device reset, 5=pulse lmsm_go;
// 6–15 ignore (irq_clr still pulses on any accepted write).
// GUID Type 0x3, Class 0x03/0x00, CFG0_PORT_BASIC/CAP,
// ROUTE_TABLE + Default, CNA static write only.
//
// Port Reset (cmd=3): Table D-103 field Port Reset bit 0, RW1C_DE0_EO.
// Four stored bits (port_rst_rw1c), one per port. Read 0=normal, 1=reset.
// Port = cfg_wr_idx[1:0]. Write data[0]==1 is W1C: start that port's
// Port Reset sequence and keep the bit 1 while rst_ctl holds; HW
// returns the bit to 0 when the hold ends. data[0]==0 does not start
// Port Reset (not the old WO pulse). RSVD data[31:1] ignored (RO).
// Bits live in these mgmt flops — no product cfg_rd_* pin (AS §18).
// CFG6 R/W of this bit: AS names CFG6 for the subset. Official opcode
// 0x10 payload packing / Appendix D offsets are 未知 — do not invent.
// vibe_cna_ep still echos the CFG6 request.
module vibe_cfg_space #(
  parameter int ROUTE_TABLE_DEPTH = 256
) (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        device_rst,
  input  logic        cfg_wr_vld,
  output logic        cfg_wr_ready,
  input  logic [3:0]  cfg_wr_cmd,
  input  logic [15:0] cfg_wr_idx,
  input  logic [31:0] cfg_wr_data,
  output logic [15:0] cna,
  output logic        cna_written,
  output logic [3:0]  default_bm,
  output logic        rt_wr_en,
  output logic [15:0] rt_wr_idx,
  output logic [31:0] rt_wr_data,
  output logic [3:0]  port_rst_pulse,
  input  logic [3:0]  port_rst_hold,
  output logic [3:0]  port_rst_rw1c,
  output logic        device_rst_pulse,
  output logic [3:0]  lmsm_go_pulse,
  output logic        irq_clr,
  output logic [31:0] guid0,
  output logic [31:0] class_code,
  output logic [31:0] port_basic,
  output logic [31:0] port_cap
);
  `include "vibe_ub_params.vh"

  // Readable inside mgmt. Not a top-level pin (AS §18: no cfg_rd_*).
  logic [3:0] port_rst_hold_d;
  integer     i;
  logic       wr_acc;
  logic [1:0] wr_port;
  logic       wr_port_rst_w1c;

  assign cfg_wr_ready = 1'b1;
  assign guid0        = {24'd0, VIBE_GUID_TYPE};
  assign class_code   = {16'd0, VIBE_CLASS_CODE};
  assign port_basic   = VIBE_PORT_BASIC;
  assign port_cap     = VIBE_PORT_CAP;

  assign wr_acc          = cfg_wr_vld && cfg_wr_ready;
  assign wr_port         = cfg_wr_idx[1:0];
  assign wr_port_rst_w1c = wr_acc && (cfg_wr_cmd == 4'd3) && cfg_wr_data[0];

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
      port_rst_rw1c    <= 4'd0;
      port_rst_hold_d  <= 4'd0;
    end else begin
      rt_wr_en         <= 1'b0;
      port_rst_pulse   <= 4'd0;
      device_rst_pulse <= 1'b0;
      lmsm_go_pulse    <= 4'd0;
      irq_clr          <= 1'b0;
      port_rst_hold_d  <= port_rst_hold;
      // HW clear when rst_ctl hold ends (bit 1 → 0 = normal). Same-cycle
      // W1C write-1 retriggers and keeps the bit set.
      for (i = 0; i < 4; i = i + 1) begin
        if (port_rst_hold_d[i] && !port_rst_hold[i] &&
            !(wr_port_rst_w1c && (wr_port == i[1:0])))
          port_rst_rw1c[i] <= 1'b0;
      end
      if (wr_acc) begin
        irq_clr <= 1'b1; // AS-0.1.2 §10: sticky clear on any accepted write
        case (cfg_wr_cmd)
          4'd0: begin
            cna         <= cfg_wr_data[15:0];
            cna_written <= 1'b1;
          end
          4'd1: begin
            rt_wr_en   <= 1'b1;
            rt_wr_idx  <= cfg_wr_idx;
            rt_wr_data <= cfg_wr_data;
          end
          4'd2: default_bm <= cfg_wr_data[3:0];
          4'd3: begin
            if (cfg_wr_data[0]) begin
              port_rst_rw1c[wr_port]  <= 1'b1;
              port_rst_pulse[wr_port] <= 1'b1;
            end
          end
          4'd4: device_rst_pulse <= 1'b1;
          4'd5: lmsm_go_pulse[wr_port] <= 1'b1;
          default: ; // 4'd6–4'd15 ignore; irq_clr already pulsed
        endcase
      end
    end
  end
endmodule
