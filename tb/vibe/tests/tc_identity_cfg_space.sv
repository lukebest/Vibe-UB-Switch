// GUID Type 0x3, Class 0x03/0x00, PORT_BASIC/CAP via vibe_cfg_space (AS-0.1 §10).
`timescale 1ns/1ps

module tc_identity_cfg_space;
  `include "vibe_ub_params.vh"

  logic        clk, rst_n, device_rst;
  logic        cfg_wr_vld, cfg_wr_ready, cna_written, rt_wr_en, irq_clr;
  logic        device_rst_pulse;
  logic [3:0]  cfg_wr_cmd;
  logic [15:0] cfg_wr_idx, cna, rt_wr_idx;
  logic [31:0] cfg_wr_data, rt_wr_data;
  logic [3:0]  default_bm, port_rst_pulse, port_rst_hold, port_rst_rw1c, lmsm_go_pulse;
  logic [31:0] guid0, class_code, port_basic, port_cap;
  integer      fail;

  initial clk = 0;
  always #1 clk = ~clk;

  vibe_cfg_space u_cfg (
    .clk(clk), .rst_n(rst_n), .device_rst(device_rst),
    .cfg_wr_vld(cfg_wr_vld), .cfg_wr_ready(cfg_wr_ready),
    .cfg_wr_cmd(cfg_wr_cmd), .cfg_wr_idx(cfg_wr_idx), .cfg_wr_data(cfg_wr_data),
    .cna(cna), .cna_written(cna_written), .default_bm(default_bm),
    .rt_wr_en(rt_wr_en), .rt_wr_idx(rt_wr_idx), .rt_wr_data(rt_wr_data),
    .port_rst_pulse(port_rst_pulse), .port_rst_hold(port_rst_hold),
    .port_rst_rw1c(port_rst_rw1c), .device_rst_pulse(device_rst_pulse),
    .lmsm_go_pulse(lmsm_go_pulse), .irq_clr(irq_clr),
    .guid0(guid0), .class_code(class_code),
    .port_basic(port_basic), .port_cap(port_cap)
  );

  initial begin
    fail = 0;
    rst_n = 0; device_rst = 0; cfg_wr_vld = 0;
    cfg_wr_cmd = 0; cfg_wr_idx = 0; cfg_wr_data = 0;
    port_rst_hold = 4'd0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    repeat (2) @(posedge clk);
    if (guid0[7:0] !== 8'h03 || class_code[15:0] !== 16'h0300) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : reset (constants; AS has no cfg_wr read map)");
      $display("  expected : GUID Type 0x3, Class 0x0300");
      $display("  actual   : guid0=%h class=%h", guid0, class_code);
      $display("  hier     : u_cfg.guid0 / class_code");
      fail = 1;
    end
    if (port_basic !== VIBE_PORT_BASIC || port_cap !== VIBE_PORT_CAP) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : reset");
      $display("  expected : PORT_BASIC/CAP constants");
      $display("  actual   : basic=%h cap=%h", port_basic, port_cap);
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_cmd = 4'd0; cfg_wr_data = 32'h0000_BEEF; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cfg_wr_vld = 0;
    repeat (2) @(posedge clk);
    if (cna !== 16'hBEEF || !cna_written) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=0 data=BEEF");
      $display("  expected : cna=BEEF cna_written=1");
      $display("  actual   : cna=%h written=%0b", cna, cna_written);
      fail = 1;
    end
    // cmd=1 route write — sample at negedge after NBA
    @(negedge clk);
    cfg_wr_cmd = 4'd1; cfg_wr_idx = 16'h0003; cfg_wr_data = 32'h0000_000F; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!rt_wr_en || rt_wr_idx !== 16'h0003 || rt_wr_data !== 32'h0000_000F) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=1 idx=3 data=F");
      $display("  expected : rt_wr_en pulse idx=3 data=F");
      $display("  actual   : en=%0b idx=%h data=%h", rt_wr_en, rt_wr_idx, rt_wr_data);
      fail = 1;
    end
    // cmd=2 default bitmap
    @(negedge clk);
    cfg_wr_cmd = 4'd2; cfg_wr_data = 32'h0000_0005; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    cfg_wr_vld = 0;
    @(posedge clk);
    if (default_bm !== 4'b0101) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=2 data=5");
      $display("  expected : default_bm=0101");
      $display("  actual   : %04b", default_bm);
      fail = 1;
    end
    // cmd=3 data[0]==0 must not start Port Reset
    @(negedge clk);
    cfg_wr_cmd = 4'd3; cfg_wr_idx = 16'd2; cfg_wr_data = 32'd0; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (port_rst_pulse[2] !== 1'b0 || port_rst_rw1c[2] !== 1'b0) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=4'h3 idx=2 data[0]=0");
      $display("  expected : pulse=0 rw1c=0 (DUT must not reset)");
      $display("  actual   : pulse=%04b rw1c=%04b", port_rst_pulse, port_rst_rw1c);
      $display("  hier     : u_cfg.port_rst_pulse / port_rst_rw1c");
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_vld = 0;
    // cmd=3 data[0]==1 W1C starts that port
    @(negedge clk);
    cfg_wr_cmd = 4'd3; cfg_wr_idx = 16'd2; cfg_wr_data = 32'd1; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (port_rst_pulse[2] !== 1'b1 || port_rst_rw1c[2] !== 1'b1) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=4'h3 idx=2 data[0]=1");
      $display("  expected : port_rst_pulse[2]=1 rw1c[2]=1 (no cfg_rd_*)");
      $display("  actual   : pulse=%04b rw1c=%04b", port_rst_pulse, port_rst_rw1c);
      $display("  hier     : u_cfg.port_rst_pulse / port_rst_rw1c");
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_vld = 0;
    // cmd=4 device rst pulse
    @(negedge clk);
    cfg_wr_cmd = 4'd4; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!device_rst_pulse) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=4");
      $display("  expected : device_rst_pulse=1");
      $display("  actual   : 0");
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_vld = 0;
    // cmd=5 lmsm_go
    @(negedge clk);
    cfg_wr_cmd = 4'd5; cfg_wr_idx = 16'd1; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (lmsm_go_pulse[1] !== 1'b1) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=5 idx=1");
      $display("  expected : lmsm_go_pulse[1]=1");
      $display("  actual   : %04b", lmsm_go_pulse);
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_vld = 0;
    // default cmd (7) still irq_clr
    @(negedge clk);
    cfg_wr_cmd = 4'd7; cfg_wr_vld = 1;
    @(posedge clk);
    @(negedge clk);
    if (!irq_clr) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : cfg_wr_cmd=7 (ignored opcode)");
      $display("  expected : irq_clr=1 (any static write)");
      $display("  actual   : 0");
      fail = 1;
    end
    @(negedge clk);
    cfg_wr_vld = 0;
    // device_rst pin clears CNA
    @(negedge clk);
    device_rst = 1;
    @(posedge clk);
    @(negedge clk);
    device_rst = 0;
    @(posedge clk);
    if (cna_written !== 1'b0) begin
      $display("FAIL tc_identity_cfg_space");
      $display("  stimulus : device_rst");
      $display("  expected : cna_written=0");
      $display("  actual   : 1");
      fail = 1;
    end
    if (!fail) $display("PASS tc_identity_cfg_space");
    $finish;
  end
endmodule
