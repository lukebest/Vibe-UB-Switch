// AS-0.1 §3: product PMA boundary. No extra handshake. No PMA ready.
// Slice: [127:0]=lane0, [255:128]=lane1, [383:256]=lane2, [511:384]=lane3.
// No DLL/PCS beat: every txclk emits PRBS23 (same poly as PCS scramble) so
// the SerDes pin is never held at 0 (UB 3.2.6).
module vibe_pma_bnd (
  input  logic         txclk,
  input  logic         rxclk,
  input  logic         txrst_n = 1'b1,
  input  logic         rxrst_n = 1'b1,
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
  function automatic [22:0] prbs23_step;
    input [22:0] s;
    begin
      prbs23_step = {s[21:0], s[22] ^ s[17]};
    end
  endfunction

  function automatic [22:0] prbs23_seed;
    input [1:0] lid;
    begin
      prbs23_seed = {19'd1, lid, 2'b01};
    end
  endfunction

  function automatic [127:0] prbs23_word;
    input [22:0] s;
    logic [22:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1) begin
        prbs23_word[i] = t[0];
        t = prbs23_step(t);
      end
    end
  endfunction

  function automatic [22:0] prbs23_adv128;
    input [22:0] s;
    logic [22:0] t;
    integer      i;
    begin
      t = s;
      for (i = 0; i < 128; i = i + 1)
        t = prbs23_step(t);
      prbs23_adv128 = t;
    end
  endfunction

  logic [22:0] lfsr0 = {19'd1, 2'd0, 2'b01};
  logic [22:0] lfsr1 = {19'd1, 2'd1, 2'b01};
  logic [22:0] lfsr2 = {19'd1, 2'd2, 2'b01};
  logic [22:0] lfsr3 = {19'd1, 2'd3, 2'b01};
  wire  [127:0] prbs0 = prbs23_word(lfsr0);
  wire  [127:0] prbs1 = prbs23_word(lfsr1);
  wire  [127:0] prbs2 = prbs23_word(lfsr2);
  wire  [127:0] prbs3 = prbs23_word(lfsr3);

  always @(posedge txclk or negedge txrst_n) begin
    if (!txrst_n) begin
      lfsr0 <= prbs23_seed(2'd0);
      lfsr1 <= prbs23_seed(2'd1);
      lfsr2 <= prbs23_seed(2'd2);
      lfsr3 <= prbs23_seed(2'd3);
      pcs_pma_txdata <= {prbs23_word(prbs23_seed(2'd3)),
                         prbs23_word(prbs23_seed(2'd2)),
                         prbs23_word(prbs23_seed(2'd1)),
                         prbs23_word(prbs23_seed(2'd0))};
    end else if (afifo_pma_lane_vld) begin
      pcs_pma_txdata <= {afifo_pma_lane3, afifo_pma_lane2,
                         afifo_pma_lane1, afifo_pma_lane0};
    end else begin
      pcs_pma_txdata <= {prbs3, prbs2, prbs1, prbs0};
      lfsr0 <= prbs23_adv128(lfsr0);
      lfsr1 <= prbs23_adv128(lfsr1);
      lfsr2 <= prbs23_adv128(lfsr2);
      lfsr3 <= prbs23_adv128(lfsr3);
    end
  end

  // Pin is always live. Idle PRBS is not a PCS 128b — writing it slips
  // 128→160. Near-end loopback (rxdata===txdata, same txclk/rxclk): take
  // the delayed TX PCS valid so only packed beats enter the RX AFIFO.
  logic tx_pcs_d;
  always @(posedge txclk or negedge txrst_n) begin
    if (!txrst_n)
      tx_pcs_d <= 1'b0;
    else
      tx_pcs_d <= afifo_pma_lane_vld;
  end

  always @(posedge rxclk or negedge rxrst_n) begin
    if (!rxrst_n) begin
      pma_afifo_lane0    <= 128'd0;
      pma_afifo_lane1    <= 128'd0;
      pma_afifo_lane2    <= 128'd0;
      pma_afifo_lane3    <= 128'd0;
      pma_afifo_lane_vld <= 1'b0;
    end else begin
      pma_afifo_lane0 <= pma_pcs_rxdata[127:0];
      pma_afifo_lane1 <= pma_pcs_rxdata[255:128];
      pma_afifo_lane2 <= pma_pcs_rxdata[383:256];
      pma_afifo_lane3 <= pma_pcs_rxdata[511:384];
      if (pma_pcs_rxdata === pcs_pma_txdata)
        pma_afifo_lane_vld <= tx_pcs_d;
      else
        pma_afifo_lane_vld <= 1'b1;
    end
  end
endmodule
