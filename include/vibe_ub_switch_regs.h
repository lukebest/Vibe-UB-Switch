#ifndef VIBE_UB_SWITCH_REGS_H
#define VIBE_UB_SWITCH_REGS_H

/*
 * Vibe-UB-Switch management command map (matches docs/rdl/vibe_ub_switch_mgmt.rdl).
 *
 * This is not MMIO. There is no address decode, APB, AXI, I2C, or JTAG in
 * rtl/mgmt. Bare-metal firmware drives the top-level static-write pins:
 *
 *   cfg_wr_vld, cfg_wr_ready (tied 1), cfg_wr_cmd[2:0],
 *   cfg_wr_idx[15:0], cfg_wr_data[31:0], pin irq_logic
 *
 * Firmware "address" is cfg_wr_cmd (3-bit RTL). Do not invent cmd 8-15.
 * Every accepted write, including ignored cmd 6/7, pulses irq_clr.
 */

#include <stdint.h>

/* -------------------------------------------------------------------------- */
/* Handshake pin widths (not MMIO)                                            */
/* -------------------------------------------------------------------------- */

#define VIBE_CFG_WR_CMD_WIDTH   3u
#define VIBE_CFG_WR_IDX_WIDTH   16u
#define VIBE_CFG_WR_DATA_WIDTH  32u
#define VIBE_CFG_WR_READY_TIED  1u

/* -------------------------------------------------------------------------- */
/* Command encodings — firmware address = cfg_wr_cmd, not a hex MMIO offset   */
/* -------------------------------------------------------------------------- */

#define VIBE_CMD_CNA            0u
#define VIBE_CMD_ROUTE_TABLE    1u
#define VIBE_CMD_DEFAULT_BM     2u
#define VIBE_CMD_PORT_RST       3u
#define VIBE_CMD_DEVICE_RST     4u
#define VIBE_CMD_LMSM_GO        5u
/* cmd 6 and 7 are ignored encodings; they still pulse irq_clr. */

/* -------------------------------------------------------------------------- */
/* CMD_CNA (addr=0): CNA[15:0] on cfg_wr_data. access=WO. reset=16'h0.        */
/* RTL reset 0 is not a product CNA. DCNA match is gated by cna_written.      */
/* Product CNA power-on default: 未知.                                        */
/* -------------------------------------------------------------------------- */

#define VIBE_CNA_SHIFT          0u
#define VIBE_CNA_WIDTH          16u
#define VIBE_CNA_MASK           ((uint32_t)0x0000FFFFu)

/* -------------------------------------------------------------------------- */
/* CMD_ROUTE_TABLE (addr=1): RT_BM[3:0] on cfg_wr_data. access=WO. reset=0.   */
/* cfg_wr_idx[15:0] (RT_IDX) is captured; fabric RAM uses [7:0], DEPTH=256.   */
/* DEPTH=256 is the architecture default, not product Max Index (未知).       */
/* Route table RAM is in fabric, not mgmt.                                    */
/* -------------------------------------------------------------------------- */

#define VIBE_RT_BM_SHIFT        0u
#define VIBE_RT_BM_WIDTH        4u
#define VIBE_RT_BM_MASK         ((uint32_t)0x0000000Fu)

#define VIBE_RT_IDX_SHIFT       0u
#define VIBE_RT_IDX_WIDTH       16u
#define VIBE_RT_IDX_MASK        ((uint32_t)0x0000FFFFu)
#define VIBE_RT_RAM_IDX_MASK    ((uint32_t)0x000000FFu)

/* -------------------------------------------------------------------------- */
/* CMD_DEFAULT_BM (addr=2): default_bm[3:0] on cfg_wr_data. WO. reset=4'h0.   */
/* -------------------------------------------------------------------------- */

#define VIBE_DEFAULT_BM_SHIFT   0u
#define VIBE_DEFAULT_BM_WIDTH   4u
#define VIBE_DEFAULT_BM_MASK    ((uint32_t)0x0000000Fu)

/* -------------------------------------------------------------------------- */
/* CMD_PORT_RST (addr=3) / CMD_LMSM_GO (addr=5): PORT[1:0] on cfg_wr_idx.     */
/* access=WO pulse. Not a stored RW1C bit. cfg_wr_data unused.                */
/* -------------------------------------------------------------------------- */

#define VIBE_PORT_SHIFT         0u
#define VIBE_PORT_WIDTH         2u
#define VIBE_PORT_MASK          ((uint32_t)0x00000003u)

/* CMD_DEVICE_RST (addr=4): WO pulse. idx and data unused. Not RW1C. */

/* -------------------------------------------------------------------------- */
/* Identity constants (vibe_cfg_space combo). Tied off in vibe_mgmt.          */
/* access=not readable this RTL. Not on pins. CFG6 echos the request.         */
/* PORT_BASIC / PORT_CAP bit packing: 未知.                                   */
/* -------------------------------------------------------------------------- */

#define VIBE_GUID0              ((uint32_t)0x00000003u)
#define VIBE_CLASS_CODE         ((uint32_t)0x00000300u)
#define VIBE_PORT_BASIC         ((uint32_t)0x00040402u)
#define VIBE_PORT_CAP           ((uint32_t)0x00000104u)

/* -------------------------------------------------------------------------- */
/* irq_logic is a pin, not a register address. Firmware reads the pin only.   */
/* 1-bit sticky OR. No per-cause status CSR.                                  */
/* Clear: any accepted cfg_wr, rst_n, or device_rst.                          */
/* Port Reset pulse (port_rst) does not clear irq.                            */
/* Product IRQ pin name / polarity / vector count: 未知.                      */
/* -------------------------------------------------------------------------- */

#define VIBE_IRQ_LOGIC_WIDTH    1u
#define VIBE_IRQ_LOGIC_MASK     ((uint32_t)0x00000001u)

/* icrc_fail from cna_ep is hardwired 0 in this RTL. */

/* Pack helpers: result goes on cfg_wr_data or cfg_wr_idx as noted. */

#define VIBE_PACK_CNA(cna) \
    ((((uint32_t)(cna)) << VIBE_CNA_SHIFT) & VIBE_CNA_MASK)

#define VIBE_PACK_RT_BM(bm) \
    ((((uint32_t)(bm)) << VIBE_RT_BM_SHIFT) & VIBE_RT_BM_MASK)

#define VIBE_PACK_RT_IDX(idx) \
    ((((uint32_t)(idx)) << VIBE_RT_IDX_SHIFT) & VIBE_RT_IDX_MASK)

#define VIBE_PACK_DEFAULT_BM(bm) \
    ((((uint32_t)(bm)) << VIBE_DEFAULT_BM_SHIFT) & VIBE_DEFAULT_BM_MASK)

#define VIBE_PACK_PORT(port) \
    ((((uint32_t)(port)) << VIBE_PORT_SHIFT) & VIBE_PORT_MASK)

#endif /* VIBE_UB_SWITCH_REGS_H */
