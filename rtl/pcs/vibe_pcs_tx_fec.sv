// AS-0.1 §5 T3: two RS(128,120) interleaved. T=4 default / T=2 / bypass.
// Bypass skips encoder, still 6-flit align.
module vibe_pcs_tx_fec (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [2:0]   fec_mode,
  input  logic [959:0] win_data,
  input  logic         win_vld,
  output logic         win_ready,
  output logic [1023:0] cw_data,
  output logic         cw_vld,
  input  logic         cw_ready
);
  `include "vibe_ub_params.vh"

  logic [959:0] w0, w1;
  logic         have0, have1;
  logic [7:0]   sym_cnt;
  logic         enc_go;
  logic         enc_a_start, enc_b_start;
  logic         enc_a_vld, enc_b_vld;
  logic [7:0]   enc_a_sym, enc_b_sym;
  logic         enc_a_rdy, enc_b_rdy;
  logic         enc_a_done, enc_b_done;
  logic [63:0]  par_a, par_b;
  logic [1023:0] cwa, cwb;
  logic          pair_done;
  logic          emit_b;

  vibe_rs128_120_enc u_enc_a (
    .clk(clk), .rst_n(rst_n), .start(enc_a_start),
    .in_vld(enc_a_vld), .in_sym(enc_a_sym), .in_ready(enc_a_rdy),
    .done(enc_a_done), .parity(par_a)
  );
  vibe_rs128_120_enc u_enc_b (
    .clk(clk), .rst_n(rst_n), .start(enc_b_start),
    .in_vld(enc_b_vld), .in_sym(enc_b_sym), .in_ready(enc_b_rdy),
    .done(enc_b_done), .parity(par_b)
  );

  assign win_ready = !have0 || (!have1 && !(win_vld && have0));

  wire bypass = (fec_mode == VIBE_FEC_BYPASS);

  // Serial stream of 240 symbols = w0 then w1, even→A odd→B
  wire [1919:0] serial = {w0, w1};
  wire [7:0]    even_sym = serial[1919-16*sym_cnt -: 8];
  wire [7:0]    odd_sym  = serial[1911-16*sym_cnt -: 8];

  assign enc_a_sym = even_sym;
  assign enc_b_sym = odd_sym;
  assign enc_a_vld = enc_go;
  assign enc_b_vld = enc_go;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      w0 <= 960'd0; w1 <= 960'd0;
      have0 <= 1'b0; have1 <= 1'b0;
      sym_cnt <= 8'd0;
      enc_go <= 1'b0;
      enc_a_start <= 1'b0;
      enc_b_start <= 1'b0;
      cw_data <= 1024'd0;
      cw_vld  <= 1'b0;
      pair_done <= 1'b0;
      emit_b <= 1'b0;
      cwa <= 1024'd0;
      cwb <= 1024'd0;
    end else begin
      enc_a_start <= 1'b0;
      enc_b_start <= 1'b0;
      if (cw_vld && cw_ready)
        cw_vld <= 1'b0;

      if (win_vld && !have0) begin
        w0    <= win_data;
        have0 <= 1'b1;
      end else if (win_vld && have0 && !have1) begin
        w1    <= win_data;
        have1 <= 1'b1;
        if (bypass) begin
          cwa <= {win_data, 64'd0}; // second window later
        end else begin
          enc_a_start <= 1'b1;
          enc_b_start <= 1'b1;
          enc_go      <= 1'b1;
          sym_cnt     <= 8'd0;
        end
      end

      if (have0 && have1 && bypass && !cw_vld) begin
        if (!emit_b) begin
          cw_data <= {w0, 64'd0};
          cw_vld  <= 1'b1;
          emit_b  <= 1'b1;
        end else begin
          cw_data <= {w1, 64'd0};
          cw_vld  <= 1'b1;
          emit_b  <= 1'b0;
          have0   <= 1'b0;
          have1   <= 1'b0;
        end
      end

      if (enc_go && enc_a_rdy && enc_b_rdy) begin
        if (sym_cnt == 8'd119)
          enc_go <= 1'b0;
        else
          sym_cnt <= sym_cnt + 8'd1;
      end

      if (enc_a_done)
        cwa <= { /* message even symbols reconstructed */ {120{8'd0}}, par_a};
      if (enc_b_done)
        cwb <= {{120{8'd0}}, par_b};

      if (enc_a_done && enc_b_done) begin
        // Rebuild codewords: even/odd merge of 240 data + two parities
        cwa <= {w0[959:0], par_a}; // 960+64=1024 (per-encoder message is 120B)
        cwb <= {w1[959:0], par_b};
        pair_done <= 1'b1;
      end

      if (pair_done && !cw_vld) begin
        if (!emit_b) begin
          cw_data <= cwa;
          cw_vld  <= 1'b1;
          emit_b  <= 1'b1;
        end else begin
          cw_data <= cwb;
          cw_vld  <= 1'b1;
          emit_b  <= 1'b0;
          pair_done <= 1'b0;
          have0 <= 1'b0;
          have1 <= 1'b0;
        end
      end
    end
  end
endmodule
