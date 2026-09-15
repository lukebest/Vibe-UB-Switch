class vibe_cfg_write_seq extends uvm_sequence #(vibe_cfg_item);
  `uvm_object_utils(vibe_cfg_write_seq)
  bit [3:0]  cmd;
  bit [15:0] idx;
  bit [31:0] data;
  function new(string name = "vibe_cfg_write_seq");
    super.new(name);
  endfunction
  task body();
    vibe_cfg_item t;
    t = vibe_cfg_item::type_id::create("t");
    start_item(t);
    t.cmd  = cmd;
    t.idx  = idx;
    t.data = data;
    finish_item(t);
  endtask
endclass

class vibe_pkt_seq extends uvm_sequence #(vibe_pkt_item);
  `uvm_object_utils(vibe_pkt_seq)
  vibe_pkt_item tmpl;
  function new(string name = "vibe_pkt_seq");
    super.new(name);
    tmpl = vibe_pkt_item::type_id::create("tmpl");
  endfunction
  task body();
    vibe_pkt_item t;
    t = vibe_pkt_item::type_id::create("t");
    t.copy(tmpl);
    start_item(t);
    finish_item(t);
  endtask
endclass
