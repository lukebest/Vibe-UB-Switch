// AS-0.1 §12 RETRY_REQ_SM: NORMAL, REQ, WAIT, RETRAIN, ERROR.
module vibe_dll_retry_req_sm #(
  parameter int RETRY_WAIT_CYC = 12500
) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       device_rst,
  input  logic       start_retry,   // FEC/BCRC fail Go-Back-N
  input  logic       phy_retrain,
  input  logic       wait_done_ack,
  output logic [2:0] state,
  output logic       drop_data,     // REQ|WAIT drop data
  output logic       retrain_req,
  output logic       retry_error,
  output logic       send_idle,
  output logic       send_req,
  output logic [4:0] send_cnt
);
  `include "vibe_ub_params.vh"

  localparam logic [2:0] ST_N = 3'd0;
  localparam logic [2:0] ST_Q = 3'd1;
  localparam logic [2:0] ST_W = 3'd2;
  localparam logic [2:0] ST_R = 3'd3;
  localparam logic [2:0] ST_E = 3'd4;

  logic [2:0]  st;
  logic [3:0]  num_retry;
  logic [2:0]  num_phy;
  logic [23:0] wtmr;
  logic [5:0]  burst;

  assign state       = st;
  assign drop_data   = (st == ST_Q) || (st == ST_W);
  assign retrain_req = (st == ST_R);
  assign retry_error = (st == ST_E);
  assign send_idle   = (st == ST_Q) && (burst == 6'd0);
  assign send_req    = (st == ST_Q) && (burst != 6'd0);
  assign send_cnt    = burst[4:0];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st        <= ST_N;
      num_retry <= 4'd0;
      num_phy   <= 3'd0;
      wtmr      <= 24'd0;
      burst     <= 6'd0;
    end else if (port_rst || device_rst) begin
      st        <= ST_N;
      num_retry <= 4'd0;
      num_phy   <= 3'd0;
      burst     <= 6'd0;
    end else begin
      case (st)
        ST_N: if (start_retry) begin
          st    <= ST_Q;
          burst <= 6'd0;
        end
        ST_Q: begin
          if (burst == 6'd32) begin
            num_retry <= num_retry + 4'd1;
            if ((num_retry + 4'd1) == VIBE_NUM_RETRY[3:0] || phy_retrain)
              st <= ST_R;
            else begin
              st   <= ST_W;
              wtmr <= RETRY_WAIT_CYC[23:0];
            end
          end else
            burst <= burst + 6'd1;
        end
        ST_W: begin
          if (wait_done_ack) st <= ST_N;
          else if (wtmr == 0) begin
            st    <= ST_Q;
            burst <= 6'd0;
          end else
            wtmr <= wtmr - 24'd1;
        end
        ST_R: begin
          num_phy <= num_phy + 3'd1;
          if ((num_phy + 3'd1) == VIBE_NUM_PHY_REINIT[2:0])
            st <= ST_E;
          else
            st <= ST_N;
        end
        ST_E: begin
          // wait Port/device reset → NORMAL
        end
        default: st <= ST_N;
      endcase
    end
  end
endmodule
