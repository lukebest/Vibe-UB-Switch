// PASS/FAIL lines kept so tb/vibe/scripts/summarize.sh still greps the gate.
task automatic vibe_uvm_pass(input string name);
  $display("PASS %0s", name);
endtask

task automatic vibe_uvm_fail(
    input string name,
    input string stimulus,
    input string expected,
    input string actual,
    input string hier);
  begin
    $display("FAIL %0s", name);
    $display("  stimulus : %0s", stimulus);
    $display("  expected : %0s", expected);
    $display("  actual   : %0s", actual);
    $display("  hier     : %0s", hier);
    $display("  reproduce: make -C tb/vibe TC=%0s", name);
    `uvm_error(name, actual)
  end
endtask
