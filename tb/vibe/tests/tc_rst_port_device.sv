// Port Reset pulse vs device reset hold. Device rst must not be a DLL_Disabled pin.
`timescale 1ns/1ps
module tc_rst_port_device;
  logic clk, rst_n, device_rst_pulse, device_rst;
  logic [3:0] port_rst_pulse, port_rst;
  integer fail;
  initial clk = 0;
  always #1 clk = ~clk;
  vibe_rst_ctl u_r (
    .clk(clk), .rst_n(rst_n),
    .device_rst_pulse(device_rst_pulse), .port_rst_pulse(port_rst_pulse),
    .device_rst(device_rst), .port_rst(port_rst)
  );
  initial begin
    fail = 0;
    rst_n = 0; device_rst_pulse = 0; port_rst_pulse = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(negedge clk);
    port_rst_pulse = 4'b0100;
    @(posedge clk);
    @(negedge clk);
    port_rst_pulse = 0;
    @(posedge clk);
    if (port_rst[2] !== 1'b1 || port_rst[0] !== 1'b0) begin
      $display("FAIL tc_rst_port_device");
      $display("  stimulus : port_rst_pulse[2]");
      $display("  expected : port_rst[2]=1 others 0");
      $display("  actual   : %04b", port_rst);
      fail = 1;
    end
    @(negedge clk);
    device_rst_pulse = 1;
    @(posedge clk);
    @(negedge clk);
    device_rst_pulse = 0;
    @(posedge clk);
    if (!device_rst) begin
      $display("FAIL tc_rst_port_device");
      $display("  stimulus : device_rst_pulse");
      $display("  expected : device_rst hold");
      $display("  actual   : 0");
      fail = 1;
    end
    if (!fail) $display("PASS tc_rst_port_device");
    $finish;
  end
endmodule
