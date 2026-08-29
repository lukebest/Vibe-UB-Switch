// AS-0.1 §11: LMSM this-rev subset. No Probe, no RXEQ_Optimize, no Change_Speed, no QDLWS.
module vibe_lmsm (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        port_rst,
  input  logic        lmsm_go,
  input  logic [3:0]  am_locked,
  input  logic        lid_bad,
  input  logic        lane0_fail,
  input  logic        eq_negotiated,
  input  logic        retrain_req,
  output logic        link_up,
  output logic        link_ready,
  output logic        sdf_period,
  output logic [4:0]  state,
  output logic        width_fail
);
  `include "vibe_ub_params.vh"

  localparam logic [4:0] ST_IDLE     = 5'd0;
  localparam logic [4:0] ST_DISC_A   = 5'd1;
  localparam logic [4:0] ST_DISC_C   = 5'd2;
  localparam logic [4:0] ST_CFG_A    = 5'd3;
  localparam logic [4:0] ST_CFG_K    = 5'd4;
  localparam logic [4:0] ST_CFG_C    = 5'd5;
  localparam logic [4:0] ST_EQ_P     = 5'd6;
  localparam logic [4:0] ST_EQ_A     = 5'd7;
  localparam logic [4:0] ST_NULL     = 5'd8;
  localparam logic [4:0] ST_ACTIVE   = 5'd9;
  localparam logic [4:0] ST_RTR_A    = 5'd10;
  localparam logic [4:0] ST_RTR_C    = 5'd11;

  logic [4:0]  st, st_n;
  logic [26:0] tmr;
  logic [3:0]  null_cnt;
  logic        from_retrain_cfg;

  assign state      = st;
  assign link_up    = (st == ST_NULL) || (st == ST_ACTIVE);
  assign link_ready = (st == ST_ACTIVE);
  assign sdf_period = (st == ST_NULL) || (st == ST_ACTIVE);
  assign width_fail = 1'b0; // x4-only product; fail path in FSM

  wire all_lock = &am_locked;
  wire x4_ok    = all_lock && !lid_bad;

  always @* begin
    st_n = st;
    case (st)
      ST_IDLE: if (lmsm_go) st_n = ST_DISC_A;
      ST_DISC_A: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (all_lock) st_n = ST_DISC_C;
      end
      ST_DISC_C: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (x4_ok) st_n = ST_CFG_A;
        else if (lid_bad) st_n = ST_IDLE; // U24
      end
      ST_CFG_A: begin
        if (tmr == 0) st_n = ST_IDLE;
        else st_n = ST_CFG_K;
      end
      ST_CFG_K: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (!x4_ok) st_n = ST_IDLE;
        else st_n = ST_CFG_C;
      end
      ST_CFG_C: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (eq_negotiated) st_n = ST_EQ_P;
        else st_n = ST_NULL;
      end
      ST_EQ_P: if (tmr == 0) st_n = ST_EQ_A;
      ST_EQ_A: if (tmr == 0) st_n = ST_NULL;
      ST_NULL: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (null_cnt >= 4'd8) st_n = ST_ACTIVE;
      end
      ST_ACTIVE: begin
        if (retrain_req || lane0_fail) st_n = ST_RTR_A;
        else if (lid_bad) st_n = ST_RTR_A;
      end
      ST_RTR_A: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (all_lock) st_n = ST_RTR_C;
      end
      ST_RTR_C: begin
        if (tmr == 0) st_n = ST_IDLE;
        else if (x4_ok) st_n = ST_DISC_A;
      end
      default: st_n = ST_IDLE;
    endcase
  end

  function automatic [26:0] tmr_load;
    input [4:0] s;
    input       from_rc;
    begin
      case (s)
        ST_DISC_A: tmr_load = from_rc ? VIBE_T_10US[26:0] : VIBE_T_24MS[26:0];
        ST_DISC_C: tmr_load = VIBE_T_48MS[26:0];
        ST_CFG_A, ST_CFG_K, ST_CFG_C: tmr_load = VIBE_T_2MS[26:0];
        ST_NULL:   tmr_load = VIBE_T_2MS[26:0];
        ST_RTR_A:  tmr_load = VIBE_T_24MS[26:0];
        ST_RTR_C:  tmr_load = VIBE_T_48MS[26:0];
        ST_EQ_P:   tmr_load = VIBE_T_64MS[26:0];
        ST_EQ_A:   tmr_load = VIBE_T_24MS[26:0];
        default:   tmr_load = 27'd0;
      endcase
    end
  endfunction

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st <= ST_IDLE;
      tmr <= 27'd0;
      null_cnt <= 4'd0;
      from_retrain_cfg <= 1'b0;
    end else if (port_rst) begin
      st <= ST_IDLE;
      tmr <= 27'd0;
      null_cnt <= 4'd0;
    end else begin
      if (st_n != st) begin
        st  <= st_n;
        tmr <= tmr_load(st_n, from_retrain_cfg || (st == ST_RTR_C) || (st == ST_CFG_C));
        if (st_n == ST_NULL) null_cnt <= 4'd0;
        if (st == ST_RTR_C || st == ST_CFG_C) from_retrain_cfg <= 1'b1;
        if (st_n == ST_IDLE) from_retrain_cfg <= 1'b0;
      end else if (tmr != 0) begin
        tmr <= tmr - 27'd1;
      end
      if (st == ST_NULL)
        null_cnt <= (null_cnt < 4'd8) ? null_cnt + 4'd1 : null_cnt;
    end
  end
endmodule
