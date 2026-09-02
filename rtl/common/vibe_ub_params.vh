// AS-0.1 §14/§17: shared parameters. Protocol constants unknown in AS stay parameters.
// Included per-module (no ifndef): localparam must be visible in every including scope.

// Widths (AS-0.1 §3 / FS-0.2.7 overlay B)
localparam int VIBE_FLIT_W      = 160;   // 20-byte flit
localparam int VIBE_NW_W        = 512;   // NW/fabric/cna packet body (byte stream)
localparam int VIBE_BEAT_W      = 640;   // DLL↔PCS only: 4 flits @ clk_fab
localparam int VIBE_FLITS_BEAT  = 4;
localparam int VIBE_NW_BYTES    = 64;
localparam int VIBE_FLIT_BYTES  = 20;
localparam int VIBE_LANE_FAB_W  = 160;
localparam int VIBE_LANE_PMA_W  = 128;
localparam int VIBE_PMA_W       = 512;
localparam int VIBE_N_LANE      = 4;
localparam int VIBE_N_PORT      = 4;
localparam int VIBE_N_VL        = 16;

// Architecture-chosen (AS-0.1 §14)
localparam int VIBE_AFIFO_DEPTH         = 16;
localparam int VIBE_AFIFO_AFULL_OCC     = 10;
localparam int VIBE_DLL_RXBUF_FLIT      = 1024;
localparam int VIBE_SAF_PKT_DEPTH       = 128;
localparam int VIBE_VOQ_DEPTH           = 32;
localparam int VIBE_MGMT_BYP_DEPTH      = 16;
localparam int VIBE_FECN_WM             = 24;
localparam int VIBE_AMCTL_CONFIRM_N     = 3;
localparam int VIBE_AMCTL_UNLOCK_N      = 3;
localparam int VIBE_ROUTE_TABLE_DEPTH   = 256;

// FS-must (AS-0.1 §14)
localparam int VIBE_RETRY_BUF_DEPTH     = 256;
localparam int VIBE_CREDIT_THRESH       = 1024;
localparam int VIBE_NUM_RETRY           = 15;
localparam int VIBE_NUM_PHY_REINIT      = 4;
localparam int VIBE_US_CYC              = 1250;      // 1 us @ 1.25 GHz
localparam int VIBE_RETRY_WAIT_CYC      = 12500;     // 10 us default

// Timers on clk_fab (AS-0.1 §11)
localparam int VIBE_T_10US              = 12500;
localparam int VIBE_T_2MS               = 2_500_000;
localparam int VIBE_T_22MS              = 27_500_000;
localparam int VIBE_T_24MS              = 30_000_000;
localparam int VIBE_T_48MS              = 60_000_000;
localparam int VIBE_T_64MS              = 80_000_000;

// Packet bounds (AS-0.1 §8)
localparam int VIBE_PKT_LEN_MIN         = 16;
localparam int VIBE_PKT_LEN_MAX         = 4300;

// FEC (AS-0.1 §5 T3)
localparam logic [2:0] VIBE_FEC_BYPASS  = 3'b000;
localparam logic [2:0] VIBE_FEC_T2      = 3'b001;
localparam logic [2:0] VIBE_FEC_T4      = 3'b010;

// GUID / Class (AS-0.1 §10)
localparam logic [7:0]  VIBE_GUID_TYPE  = 8'h03;
localparam logic [15:0] VIBE_CLASS_CODE = 16'h0300;

// CFG0_PORT_BASIC / CAP constants (AS-0.1 §10): 4 ports, x4, Mode-2 106.25G
localparam logic [31:0] VIBE_PORT_BASIC = 32'h0004_0402;
localparam logic [31:0] VIBE_PORT_CAP   = 32'h0000_0104;

// Header extracts from first flit (UB 2.0 LPH/NTH; bit positions parameterized)
localparam int VIBE_CFG_LSB             = 8;
localparam int VIBE_RT_LSB              = 22;
localparam int VIBE_SCNA_LSB            = 32;
localparam int VIBE_DCNA_LSB            = 48;
localparam int VIBE_CCI_LSB             = 64;
localparam int VIBE_LBF_LSB             = 80;
localparam int VIBE_PLEN_HI_LSB         = 18; // PLENGTH[13:10] in LPH byte2

// RS(128,120) GF(256) primitive x^8+x^4+x^3+x^2+1 (UB 2.0 §3.2.2)
localparam logic [8:0] VIBE_GF_PRIM     = 9'h11D;

// PRBS23 additive scramble (poly parameterized; seed from LID)
localparam logic [22:0] VIBE_SCR_POLY   = 23'h040001; // x^23+x^18+1 typical

// BCRC CRC30 (AS-0.1 §12)
// x^30+x^28+x^26+x^24+x^23+x^21+x^19+x^16+x^14+x^11+x^9+x^7+x^6+x^4+x^2+1
localparam logic [29:0] VIBE_BCRC_POLY  = 30'h15A9_4AD5;

// ICRC CRC32 (AS-0.1 §13)
localparam logic [31:0] VIBE_ICRC_POLY  = 32'h04C1_1DB7;
