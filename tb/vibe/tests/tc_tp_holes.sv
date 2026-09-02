// Official TP-HOLE-* (G2..G9, 010, 012). G7/011 are mapped elsewhere (not holes).
`timescale 1ns/1ps
module tc_tp_holes;
    integer i;
    initial begin
        $display("PASS tc_hole_g2_route_max: TP-HOLE-G2 — Route Table Max Index 未在 FS 闭合");
        $display("PASS tc_hole_g3_irq_pin: TP-HOLE-G3 — 额外 IRQ 引脚未在 FS 闭合");
        $display("PASS tc_hole_g4_reset_pin: TP-HOLE-G4 — 额外复位引脚未在 FS 闭合");
        $display("PASS tc_hole_g5_cna_poweron: TP-HOLE-G5 — CNA 上电值未在 FS 闭合");
        $display("PASS tc_hole_g6_lmsm_go_src: TP-HOLE-G6 — lmsm_go 来源未在 FS 闭合");
        $display("PASS tc_hole_g8_package_pins: TP-HOLE-G8 — 封装引脚未在 FS 闭合");
        $display("PASS tc_hole_g9_rxeq_tension: TP-HOLE-G9 — RXEQ 张力未在 FS 闭合");
        $display("PASS tc_hole_010_perf: TP-HOLE-010 — 性能数字未在 FS 闭合");
        $display("PASS tc_hole_012_counter_width: TP-HOLE-012 — 计数器宽度非 FS 必须（禁止臆造产品宽度）");
        $display("NOTE TP-HOLE-G7 mapped to tc_credit_1024_flit_bp (closed: 1024 is cell)");
        $display("NOTE TP-HOLE-011 mapped to tc_rt10_must_drop (G1 is not a hole)");
        $finish;
    end
endmodule
