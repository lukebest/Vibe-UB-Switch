// FS-0.2.3 + AS-0.1 §10/§15: irq_logic sticky OR of observable errors (includes G1 RT=10/11).
// Clear on static write or reset. Single bit; no extra product IRQ pins.
module vibe_irq_agg (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       irq_clr,
  input  logic [3:0] rx_ovf,
  input  logic [3:0] fc_ovf,
  input  logic [3:0] proto_err,
  input  logic [3:0] retry_error,
  input  logic       icrc_fail,
  input  logic [3:0] len_err,
  input  logic [3:0] deadlock_drop,
  input  logic       drop_g1,
  input  logic [3:0] afifo_ovf,
  output logic       irq_logic
);
  logic sticky;

  assign irq_logic = sticky;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      sticky <= 1'b0;
    end else if (irq_clr) begin
      sticky <= 1'b0;
    end else if (|rx_ovf || |fc_ovf || |proto_err || |retry_error || icrc_fail ||
                 |len_err || |deadlock_drop || drop_g1 || |afifo_ovf) begin
      sticky <= 1'b1;
    end
  end
endmodule
