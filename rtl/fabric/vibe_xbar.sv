// AS-0.1 §8: output queued, ingress RR on conflict, one full packet per grant.
// Down ports get no data DLLDP. Mgmt bypass does not enter xbar.
module vibe_xbar (
  input  logic         clk,
  input  logic         rst_n,
  input  logic [3:0]   status_up,
  input  logic [639:0] in_data [0:3],
  input  logic [3:0]   in_vld,
  input  logic [3:0]   in_sop,
  input  logic [3:0]   in_eop,
  input  logic [1:0]   in_dst [0:3],
  output logic [3:0]   in_ready,
  output logic [639:0] out_data [0:3],
  output logic [3:0]   out_vld,
  output logic [3:0]   out_sop,
  output logic [3:0]   out_eop,
  input  logic [3:0]   out_ready
);
  logic [1:0] lock [0:3];
  logic       locked [0:3];
  logic [1:0] rr [0:3];
  integer     e, i;
  logic [3:0] req;
  logic [1:0] win;

  always @* begin
    for (e = 0; e < 4; e = e + 1) begin
      in_ready[e] = 1'b0;
      out_data[e] = 640'd0;
      out_vld[e]  = 1'b0;
      out_sop[e]  = 1'b0;
      out_eop[e]  = 1'b0;
    end
    for (e = 0; e < 4; e = e + 1) begin
      if (!status_up[e]) begin
        // Down ports get no data DLLDP
      end else if (locked[e]) begin
        if (in_vld[lock[e]] && in_dst[lock[e]] == e[1:0] && out_ready[e]) begin
          out_data[e]           = in_data[lock[e]];
          out_vld[e]            = 1'b1;
          out_sop[e]            = in_sop[lock[e]];
          out_eop[e]            = in_eop[lock[e]];
          in_ready[lock[e]]     = 1'b1;
        end
      end else begin
        req = 4'd0;
        for (i = 0; i < 4; i = i + 1)
          if (in_vld[i] && in_dst[i] == e[1:0]) req[i] = 1'b1;
        win = rr[e];
        for (i = 0; i < 4; i = i + 1) begin
          if (req[win] && out_ready[e]) begin
            out_data[e]   = in_data[win];
            out_vld[e]    = 1'b1;
            out_sop[e]    = in_sop[win];
            out_eop[e]    = in_eop[win];
            in_ready[win] = 1'b1;
            i = 4;
          end else
            win = win + 2'd1;
        end
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (e = 0; e < 4; e = e + 1) begin
        lock[e]   <= 2'd0;
        locked[e] <= 1'b0;
        rr[e]     <= 2'd0;
      end
    end else begin
      for (e = 0; e < 4; e = e + 1) begin
        if (out_vld[e] && out_ready[e] && out_sop[e]) begin
          locked[e] <= 1'b1;
          lock[e]   <= in_dst[0]; // set below
        end
        if (out_vld[e] && out_ready[e]) begin
          if (locked[e])
            lock[e] <= lock[e];
          else begin
            locked[e] <= 1'b1;
            // winner stored as who got in_ready
            for (i = 0; i < 4; i = i + 1)
              if (in_ready[i] && in_dst[i] == e[1:0])
                lock[e] <= i[1:0];
          end
          if (out_eop[e]) begin
            locked[e] <= 1'b0;
            rr[e]     <= lock[e] + 2'd1;
          end
        end
      end
    end
  end
endmodule
