// GENERATED/HAND-FINISHED from pycircuit/pcs/vibe_rs128_120_dec.py
// pyCircuit: lukebest/pyCircuit @ 43cc5918e3d09ecc0c814cabef6c1384cb9980ae
//            pyc4.0 / pycircuit-hisi 0.1.0 (pycc → Verilog when LLVM 19 is present)
// Product ports and behavior match tip 984e3b9 / freeze 302ac943.
// msg reset is unrolled NBA (same zeros as stock for-loop; lint-safe).
// SPEC / CR-B names unchanged. Do not touch F1 ovf_l (lives in vibe_port).
// Regenerate: make -C pycircuit vibe_rs128_120_dec
//
// AS-0.1 §6: RS(128,120) syndrome check. Nonzero syndrome → fec_fail (Go-Back-N).
module vibe_rs128_120_dec (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         start,
  input  logic         in_vld,
  input  logic [7:0]   in_sym,
  output logic         in_ready,
  output logic         done,
  output logic         fec_fail,
  output logic [959:0] data_out
);
  `include "vibe_ub_fn.vh"

  logic [7:0]   s0, s1, s2, s3, s4, s5, s6, s7;
  logic [7:0]   cnt;
  logic         busy;
  logic [7:0]   msg [0:119];

  assign in_ready = busy && (cnt < 8'd128);

  function automatic [7:0] gf_mul2;
    input [7:0] a;
    begin
      gf_mul2 = a[7] ? {a[6:0], 1'b0} ^ 8'h1D : {a[6:0], 1'b0};
    end
  endfunction

  // Next syndromes (combo) so the last symbol is included before fec_fail.
  wire [7:0] ns0 = s0 ^ in_sym;
  wire [7:0] ns1 = gf_mul2(s1) ^ in_sym;
  wire [7:0] ns2 = vibe_gf256_mul(s2, 8'd4) ^ in_sym;
  wire [7:0] ns3 = vibe_gf256_mul(s3, 8'd8) ^ in_sym;
  wire [7:0] ns4 = vibe_gf256_mul(s4, 8'd16) ^ in_sym;
  wire [7:0] ns5 = vibe_gf256_mul(s5, 8'd32) ^ in_sym;
  wire [7:0] ns6 = vibe_gf256_mul(s6, 8'd64) ^ in_sym;
  wire [7:0] ns7 = vibe_gf256_mul(s7, 8'd128) ^ in_sym;

  integer i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
      s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
      cnt      <= 8'd0;
      busy     <= 1'b0;
      done     <= 1'b0;
      fec_fail <= 1'b0;
      data_out <= 960'd0;
      msg[0] <= 8'd0; msg[1] <= 8'd0; msg[2] <= 8'd0; msg[3] <= 8'd0; msg[4] <= 8'd0; msg[5] <= 8'd0; msg[6] <= 8'd0; msg[7] <= 8'd0;
      msg[8] <= 8'd0; msg[9] <= 8'd0; msg[10] <= 8'd0; msg[11] <= 8'd0; msg[12] <= 8'd0; msg[13] <= 8'd0; msg[14] <= 8'd0; msg[15] <= 8'd0;
      msg[16] <= 8'd0; msg[17] <= 8'd0; msg[18] <= 8'd0; msg[19] <= 8'd0; msg[20] <= 8'd0; msg[21] <= 8'd0; msg[22] <= 8'd0; msg[23] <= 8'd0;
      msg[24] <= 8'd0; msg[25] <= 8'd0; msg[26] <= 8'd0; msg[27] <= 8'd0; msg[28] <= 8'd0; msg[29] <= 8'd0; msg[30] <= 8'd0; msg[31] <= 8'd0;
      msg[32] <= 8'd0; msg[33] <= 8'd0; msg[34] <= 8'd0; msg[35] <= 8'd0; msg[36] <= 8'd0; msg[37] <= 8'd0; msg[38] <= 8'd0; msg[39] <= 8'd0;
      msg[40] <= 8'd0; msg[41] <= 8'd0; msg[42] <= 8'd0; msg[43] <= 8'd0; msg[44] <= 8'd0; msg[45] <= 8'd0; msg[46] <= 8'd0; msg[47] <= 8'd0;
      msg[48] <= 8'd0; msg[49] <= 8'd0; msg[50] <= 8'd0; msg[51] <= 8'd0; msg[52] <= 8'd0; msg[53] <= 8'd0; msg[54] <= 8'd0; msg[55] <= 8'd0;
      msg[56] <= 8'd0; msg[57] <= 8'd0; msg[58] <= 8'd0; msg[59] <= 8'd0; msg[60] <= 8'd0; msg[61] <= 8'd0; msg[62] <= 8'd0; msg[63] <= 8'd0;
      msg[64] <= 8'd0; msg[65] <= 8'd0; msg[66] <= 8'd0; msg[67] <= 8'd0; msg[68] <= 8'd0; msg[69] <= 8'd0; msg[70] <= 8'd0; msg[71] <= 8'd0;
      msg[72] <= 8'd0; msg[73] <= 8'd0; msg[74] <= 8'd0; msg[75] <= 8'd0; msg[76] <= 8'd0; msg[77] <= 8'd0; msg[78] <= 8'd0; msg[79] <= 8'd0;
      msg[80] <= 8'd0; msg[81] <= 8'd0; msg[82] <= 8'd0; msg[83] <= 8'd0; msg[84] <= 8'd0; msg[85] <= 8'd0; msg[86] <= 8'd0; msg[87] <= 8'd0;
      msg[88] <= 8'd0; msg[89] <= 8'd0; msg[90] <= 8'd0; msg[91] <= 8'd0; msg[92] <= 8'd0; msg[93] <= 8'd0; msg[94] <= 8'd0; msg[95] <= 8'd0;
      msg[96] <= 8'd0; msg[97] <= 8'd0; msg[98] <= 8'd0; msg[99] <= 8'd0; msg[100] <= 8'd0; msg[101] <= 8'd0; msg[102] <= 8'd0; msg[103] <= 8'd0;
      msg[104] <= 8'd0; msg[105] <= 8'd0; msg[106] <= 8'd0; msg[107] <= 8'd0; msg[108] <= 8'd0; msg[109] <= 8'd0; msg[110] <= 8'd0; msg[111] <= 8'd0;
      msg[112] <= 8'd0; msg[113] <= 8'd0; msg[114] <= 8'd0; msg[115] <= 8'd0; msg[116] <= 8'd0; msg[117] <= 8'd0; msg[118] <= 8'd0; msg[119] <= 8'd0;
    end else begin
      done     <= 1'b0;
      fec_fail <= 1'b0;
      if (start) begin
        s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0;
        s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0;
        cnt      <= 8'd0;
        busy     <= 1'b1;
        fec_fail <= 1'b0;
      end else if (busy && in_vld && in_ready) begin
        s0 <= ns0;
        s1 <= ns1;
        s2 <= ns2;
        s3 <= ns3;
        s4 <= ns4;
        s5 <= ns5;
        s6 <= ns6;
        s7 <= ns7;
        if (cnt < 8'd120)
          msg[cnt] <= in_sym;
        if (cnt == 8'd127) begin
          busy     <= 1'b0;
          done     <= 1'b1;
          fec_fail <= |{ns0, ns1, ns2, ns3, ns4, ns5, ns6, ns7};
          // pack msg[0] as first symbol (MSB of data_out)
          for (i = 0; i < 120; i = i + 1)
            data_out[959-8*i -: 8] <= msg[i];
        end else begin
          cnt <= cnt + 8'd1;
        end
      end
    end
  end
endmodule
