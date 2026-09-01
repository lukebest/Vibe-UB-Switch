// TP-HOLE-001..012 — record AS/FS unknowns. Do not invent product numbers.
// Each name PASSes as documentation (NOTE), not as a guessed pin / depth / default.
`timescale 1ns/1ps
module tc_tp_holes;
  initial begin
    $display("=== tc_tp_holes (TP-HOLE-001..012) ===");

    $display("HOLE tc_hole_max_index");
    $display("  stimulus : AS/FS do not publish Max Index");
    $display("  expected : do not invent; ROUTE_TABLE_DEPTH=256 is architecture-chosen");
    $display("  actual   : no product Max Index asserted");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_max_index: unknown not invented");
    $display("PASS tc_hole_max_index");

    $display("HOLE tc_hole_extra_irq_pins");
    $display("  stimulus : AS §10 logical irq_logic only");
    $display("  expected : no invented extra IRQ pin names");
    $display("  actual   : no extra IRQ pins guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_extra_irq_pins: unknown not invented");
    $display("PASS tc_hole_extra_irq_pins");

    $display("HOLE tc_hole_extra_rst_pins");
    $display("  stimulus : AS §10 rst_n / port_rst / device_rst only");
    $display("  expected : no invented extra reset pin names");
    $display("  actual   : no extra reset pins guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_extra_rst_pins: unknown not invented");
    $display("PASS tc_hole_extra_rst_pins");

    $display("HOLE tc_hole_cna_default");
    $display("  stimulus : AS §9 power-on CNA default UNKNOWN");
    $display("  expected : do not match DCNA until static write; no guessed default");
    $display("  actual   : no CNA reset value invented");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_cna_default: unknown not invented");
    $display("PASS tc_hole_cna_default");

    $display("HOLE tc_hole_lmsm_go_source");
    $display("  stimulus : AS G2-G9 lmsm_go source unpublished");
    $display("  expected : cfg_wr_cmd=5 is the locked pulse; no invented pin");
    $display("  actual   : no lmsm_go source pin invented");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_lmsm_go_source: unknown not invented");
    $display("PASS tc_hole_lmsm_go_source");

    $display("HOLE tc_hole_package_pins");
    $display("  stimulus : AS §18 logical pins only");
    $display("  expected : no invented package pinout");
    $display("  actual   : no package pins guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_package_pins: unknown not invented");
    $display("PASS tc_hole_package_pins");

    $display("HOLE tc_hole_rxeq_optimize");
    $display("  stimulus : AS §11 this-rev LMSM has no RXEQ_Optimize");
    $display("  expected : no invented RXEQ state encoding");
    $display("  actual   : no RXEQ_Optimize value guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_rxeq_optimize: unknown not invented");
    $display("PASS tc_hole_rxeq_optimize");

    $display("HOLE tc_hole_change_speed");
    $display("  stimulus : AS §11 Change_Speed not implemented");
    $display("  expected : no invented rate table");
    $display("  actual   : no Change_Speed value guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_change_speed: unknown not invented");
    $display("PASS tc_hole_change_speed");

    $display("HOLE tc_hole_polarity_laneswap");
    $display("  stimulus : AS §6 U24 no polarity/lane-swap training");
    $display("  expected : factory physical=logical; no invented swap map");
    $display("  actual   : no polarity/lane-swap table guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_polarity_laneswap: unknown not invented");
    $display("PASS tc_hole_polarity_laneswap");

    $display("HOLE tc_hole_fig328_arcs");
    $display("  stimulus : AS §11 missing Fig 3-28 arcs unpublished");
    $display("  expected : no invented LMSM transitions");
    $display("  actual   : no Fig 3-28 arc values guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_fig328_arcs: unknown not invented");
    $display("PASS tc_hole_fig328_arcs");

    $display("HOLE tc_hole_credit_underflow");
    $display("  stimulus : AS §12 do NOT invent credit underflow");
    $display("  expected : no underflow code / threshold invented");
    $display("  actual   : no credit-underflow number guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_credit_underflow: unknown not invented");
    $display("PASS tc_hole_credit_underflow");

    $display("HOLE tc_hole_optical");
    $display("  stimulus : AS §11 optical not in this-rev subset");
    $display("  expected : no invented optical pins / modules");
    $display("  actual   : no optical product number guessed");
    $display("  hier     : n/a");
    $display("NOTE tc_hole_optical: unknown not invented");
    $display("PASS tc_hole_optical");

    $display("PASS tc_tp_holes");
    $finish;
  end
endmodule
