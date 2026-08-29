// AS-0.1 §12: DLL SM. Disabled when LinkUp==0. Entity reset must not force Disabled.
module vibe_dll_sm (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       port_rst,
  input  logic       link_up,
  input  logic       param_ok,
  input  logic       credit_ok,
  input  logic       dll_error,
  output logic [1:0] state,
  output logic       status_up,
  output logic       disabled
);
  localparam logic [1:0] ST_DIS  = 2'd0;
  localparam logic [1:0] ST_PARM = 2'd1;
  localparam logic [1:0] ST_CRD  = 2'd2;
  localparam logic [1:0] ST_NRM  = 2'd3;

  logic [1:0] st;

  assign state     = st;
  assign disabled  = (st == ST_DIS);
  assign status_up = (st == ST_NRM);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      st <= ST_DIS;
    end else if (port_rst) begin
      st <= ST_DIS;
    end else if (!link_up) begin
      st <= ST_DIS;
    end else if (dll_error) begin
      st <= ST_DIS;
    end else begin
      case (st)
        ST_DIS:  if (link_up) st <= ST_PARM;
        ST_PARM: if (param_ok) st <= ST_CRD;
        ST_CRD:  if (credit_ok) st <= ST_NRM;
        default: st <= ST_NRM;
      endcase
    end
  end
endmodule
