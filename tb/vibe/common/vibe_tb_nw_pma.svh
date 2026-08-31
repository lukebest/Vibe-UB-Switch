// Known NW packet for PMA TX / loopback checkers (AS-0.1 LPH, RT=00, legal 1-beat).
// Included per-module (no guard). Requires vibe_tb_defs.svh already included.

function automatic [639:0] vibe_tb_nw_pma_pkt;
  reg [159:0] f0;
  begin
    f0 = vibe_tb_mk_flit(
        4'd3, 2'b00, 4'd0, 16'hA11A, 16'hB22B, vibe_tb_plen_nflit(1),
        16'hC33C, 8'h5A, 3'd0, 8'd0);
    // Unique payload flits so PMA/RX compare is not header-only.
    vibe_tb_nw_pma_pkt = {f0,
        160'h0123_4567_89AB_CDEF_FEDC_BA98_7654_3210,
        160'h1111_2222_3333_4444_5555_6666_7777_8888,
        160'hDEAD_BEEF_CAFE_F00D_0123_4567_89AB_CDEF};
  end
endfunction

function automatic vibe_tb_nw_pma_lph_ok;
  input [639:0] beat;
  reg [159:0] f;
  begin
    f = beat[639:480];
    vibe_tb_nw_pma_lph_ok =
        (vibe_lph_cfg(f) == 4'd3) &&
        (vibe_lph_rt(f)  == 2'b00) &&
        (vibe_nth_scna(f) == 16'hA11A) &&
        (vibe_nth_dcna(f) == 16'hB22B);
  end
endfunction
