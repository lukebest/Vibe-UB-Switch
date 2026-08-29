// AS-0.1 §12 RETRY_ACK_SM: NORMAL, ACK (1 Idle + 32 Ack then replay RdPtr=RcvPtr until WrPtr).
module vibe_dll_retry_ack_sm (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       start_ack,
  input  logic [7:0] wr_ptr,
  input  logic [7:0] rcv_ptr,
  output logic [2:0] state,
  output logic       send_idle,
  output logic       send_ack,
  output logic       replay,
  output logic [7:0] rd_ptr
);
  localparam logic [2:0] ST_N = 3'd0;
  localparam logic [2:0] ST_A = 3'd1;
  localparam logic [2:0] ST_P = 3'd2;

  logic [2:0] st;
  logic [5:0] burst;
  logic [7:0] rp;

  assign state     = st;
  assign send_idle = (st == ST_A) && (burst == 6'd0);
  assign send_ack  = (st == ST_A) && (burst != 6'd0);
  assign replay    = (st == ST_P);
  assign rd_ptr    = rp;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st    <= ST_N;
      burst <= 6'd0;
      rp    <= 8'd0;
    end else if (port_rst) begin
      st    <= ST_N;
      burst <= 6'd0;
      rp    <= 8'd0;
    end else begin
      case (st)
        ST_N: if (start_ack) begin
          st    <= ST_A;
          burst <= 6'd0;
        end
        ST_A: begin
          if (burst == 6'd32) begin
            st <= ST_P;
            rp <= rcv_ptr;
          end else
            burst <= burst + 6'd1;
        end
        ST_P: begin
          if (rp == wr_ptr)
            st <= ST_N;
          else
            rp <= rp + 8'd1;
        end
        default: st <= ST_N;
      endcase
    end
  end
endmodule
