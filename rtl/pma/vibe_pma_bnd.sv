// AS-0.1 §3: product PMA boundary. No extra handshake. No PMA ready.
// Slice: [127:0]=lane0, [255:128]=lane1, [383:256]=lane2, [511:384]=lane3.
module vibe_pma_bnd (
  input  logic         txclk,
  input  logic         rxclk,
  input  logic [127:0] tx_lane0,
  input  logic [127:0] tx_lane1,
  input  logic [127:0] tx_lane2,
  input  logic [127:0] tx_lane3,
  input  logic         tx_lane_vld,
  output logic [511:0] txdata,
  input  logic [511:0] rxdata,
  output logic [127:0] rx_lane0,
  output logic [127:0] rx_lane1,
  output logic [127:0] rx_lane2,
  output logic [127:0] rx_lane3,
  output logic         rx_lane_vld
);
  // Power-on 0 so loopback RX does not sample X before the first tx_lane_vld.
  initial txdata = 512'd0;

  always @(posedge txclk) begin
    if (tx_lane_vld)
      txdata <= {tx_lane3, tx_lane2, tx_lane1, tx_lane0};
  end

  always @(posedge rxclk) begin
    rx_lane0   <= rxdata[127:0];
    rx_lane1   <= rxdata[255:128];
    rx_lane2   <= rxdata[383:256];
    rx_lane3   <= rxdata[511:384];
    rx_lane_vld <= 1'b1;
  end
endmodule
