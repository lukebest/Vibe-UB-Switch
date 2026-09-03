#ifndef VIBE_UB_SWITCH_REGS_H
#define VIBE_UB_SWITCH_REGS_H

/*
 * Vibe-UB-Switch management command map (matches docs/rdl/vibe_ub_switch_mgmt.rdl).
 *
 * Firmware contract is the architecture spec (AS-0.1 + AS-0.1.2 cmd width),
 * not a snapshot of rtl/mgmt. A 3-bit RTL cmd bus is void for firmware.
 *
 * This is not MMIO. No APB, AXI, I2C, or JTAG. Bare-metal firmware drives
 * the AS static-write pins:
 *
 *   cfg_wr_vld, cfg_wr_ready, cfg_wr_cmd[3:0],
 *   cfg_wr_idx[15:0], cfg_wr_data[31:0], pin irq_logic
 *
 * Firmware "address" is cfg_wr_cmd (4-bit). Encodings 0-5 used;
 * 6-15 reserved/ignored. AS names no cfg_rd_* pins.
 */

#include <stdint.h>

/* -------------------------------------------------------------------------- */
/* Handshake pin widths (not MMIO). AS §10 static write, AS-0.1.2 cmd[3:0].   */
/* -------------------------------------------------------------------------- */

#define VIBE_CFG_WR_CMD_WIDTH   4u
#define VIBE_CFG_WR_CMD_MASK    ((uint32_t)0x0000000Fu)
#define VIBE_CFG_WR_IDX_WIDTH   16u
#define VIBE_CFG_WR_DATA_WIDTH  32u

/* -------------------------------------------------------------------------- */
/* Command encodings — firmware address = cfg_wr_cmd[3:0], not hex MMIO       */
/* -------------------------------------------------------------------------- */

#define VIBE_CMD_CNA            0u
#define VIBE_CMD_ROUTE_TABLE    1u
#define VIBE_CMD_DEFAULT_BM     2u
#define VIBE_CMD_PORT_RST       3u
#define VIBE_CMD_DEVICE_RST     4u
#define VIBE_CMD_LMSM_GO        5u
/* cmd 6..15 reserved/ignored (4-bit encoding). */

/* -------------------------------------------------------------------------- */
/* CMD_CNA (addr=0): CNA[15:0] on cfg_wr_data. access=WO (static write only). */
/* Product CNA power-on default: 未知. Do not treat 0 as a valid CNA.         */
/* DCNA match only after a static CNA write (AS §9).                          */
/* -------------------------------------------------------------------------- */

#define VIBE_CNA_SHIFT          0u
#define VIBE_CNA_WIDTH          16u
#define VIBE_CNA_MASK           ((uint32_t)0x0000FFFFu)

/* -------------------------------------------------------------------------- */
/* CMD_ROUTE_TABLE (addr=1): RT_BM[3:0] on cfg_wr_data. access=WO. reset=0.   */
/* cfg_wr_idx = dest index. AS: entries 32-bit, only [3:0] meaningful.        */
/* ROUTE_TABLE_DEPTH default 256 is architecture-chosen, not product Max Index*/
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
/* CMD_PORT_RST (addr=3): Port Reset is RW1C per port (AS §10), reset=0.      */
/* cmd=3 writes 1 to the selected port bit (idx[1:0]). Firmware observes the  */
/* bit until write-1-clears. No MMIO address.                                 */
/* AS names no cfg_rd_*: RW1C read-data path is 未知. Do not invent cfg_rd_*. */
/* -------------------------------------------------------------------------- */

#define VIBE_PORT_SHIFT         0u
#define VIBE_PORT_WIDTH         2u
#define VIBE_PORT_MASK          ((uint32_t)0x00000003u)

#define VIBE_PORT_RST_SHIFT     0u
#define VIBE_PORT_RST_WIDTH     1u
#define VIBE_PORT_RST_MASK      ((uint32_t)0x00000001u)
#define VIBE_PORT_RST_RESET     0u
#define VIBE_PORT_RST_VEC_WIDTH 4u
#define VIBE_PORT_RST_VEC_MASK  ((uint32_t)0x0000000Fu)
#define VIBE_PORT_RST_VEC_RESET 0u

/* cmd=3 write-1 to selected bit (set / W1C). PORT_RST[p] reset 0. */
#define VIBE_PACK_PORT_RST_BIT  VIBE_PORT_RST_MASK

/* CMD_LMSM_GO (addr=5): PORT[1:0] on cfg_wr_idx. access=WO pulse.            */
/* CMD_DEVICE_RST (addr=4): WO pulse. idx and data unused. Not RW1C.          */

/* -------------------------------------------------------------------------- */
/* Identity constants (AS §10 GUID Type 0x3, Class 0x03/0x00, PORT_BASIC/CAP).*/
/* Compile-time only: AS does not name a GUID / identity read on cfg_wr_*.    */
/* PORT_BASIC / PORT_CAP official bit packing: 未知.                          */
/* -------------------------------------------------------------------------- */

#define VIBE_GUID0              ((uint32_t)0x00000003u)
#define VIBE_CLASS_CODE         ((uint32_t)0x00000300u)
#define VIBE_PORT_BASIC         ((uint32_t)0x00040402u)
#define VIBE_PORT_CAP           ((uint32_t)0x00000104u)

/* -------------------------------------------------------------------------- */
/* irq_logic is a pin, not a register address. Firmware reads the pin only.   */
/* 1-bit sticky OR (AS §10/§15). No per-cause status CSR.                     */
/* Clear: static write or reset (AS §10).                                     */
/* Product IRQ pin name / polarity / vector count: 未知.                      */
/* -------------------------------------------------------------------------- */

#define VIBE_IRQ_LOGIC_WIDTH    1u
#define VIBE_IRQ_LOGIC_MASK     ((uint32_t)0x00000001u)

/* Pack helpers: result goes on cfg_wr_data or cfg_wr_idx as noted. */

#define VIBE_PACK_CMD(cmd) \
    ((((uint32_t)(cmd)) ) & VIBE_CFG_WR_CMD_MASK)

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

#define VIBE_PACK_PORT_RST(w1) \
    ((((uint32_t)(w1)) << VIBE_PORT_RST_SHIFT) & VIBE_PORT_RST_MASK)

#define VIBE_PORT_RST_BIT(port) \
    ((uint32_t)(VIBE_PORT_RST_MASK << (((uint32_t)(port)) & VIBE_PORT_MASK)))

#endif /* VIBE_UB_SWITCH_REGS_H */
