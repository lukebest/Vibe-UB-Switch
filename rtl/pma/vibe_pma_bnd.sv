// AS-0.1 §3: product PMA boundary. No extra handshake. No PMA ready.
// Slice: [127:0]=lane0, [255:128]=lane1, [383:256]=lane2, [511:384]=lane3.
module vibe_pma_bnd (
  input  logic         txclk,
  input  logic         rxclk,
  input  logic [127:0] afifo_pma_lane0,
  input  logic [127:0] afifo_pma_lane1,
  input  logic [127:0] afifo_pma_lane2,
  input  logic [127:0] afifo_pma_lane3,
  input  logic         afifo_pma_lane_vld,
  output logic [511:0] pcs_pma_txdata,
  input  logic [511:0] pma_pcs_rxdata,
  output logic [127:0] pma_afifo_lane0,
  output logic [127:0] pma_afifo_lane1,
  output logic [127:0] pma_afifo_lane2,
  output logic [127:0] pma_afifo_lane3,
  output logic         pma_afifo_lane_vld
);
  // Power-on 0 so loopback RX does not sample X before the first afifo_pma_lane_vld.
  initial pcs_pma_txdata = 512'd0;

  always @(posedge txclk) begin
    if (afifo_pma_lane_vld)
      pcs_pma_txdata <= {afifo_pma_lane3, afifo_pma_lane2, afifo_pma_lane1, afifo_pma_lane0};
  end

  always @(posedge rxclk) begin
    pma_afifo_lane0   <= pma_pcs_rxdata[127:0];
    pma_afifo_lane1   <= pma_pcs_rxdata[255:128];
    pma_afifo_lane2   <= pma_pcs_rxdata[383:256];
    pma_afifo_lane3   <= pma_pcs_rxdata[511:384];
    pma_afifo_lane_vld <= 1'b1;
  end
endmodule
