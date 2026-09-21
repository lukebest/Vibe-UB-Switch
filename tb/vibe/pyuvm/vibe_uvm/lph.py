"""AS-0.1 / FS-0.2.7 Overlay B LPH helpers. Mirrors rtl/common/vibe_ub_fn.vh
and tb/vibe/common/vibe_tb_defs.svh. Do not invent packing.
"""

CMD_CNA = 0
CMD_ROUTE = 1
CMD_DEFAULT = 2
CMD_PORTRST = 3
CMD_DEVRST = 4
CMD_LMSMGO = 5
CMD_NOPCLR = 7
PORTRST_W1C = 1
PORTRST_NOP = 0

GUID_TYPE = 0x03
CLASS_CODE = 0x0300
PORT_BASIC = 0x00040402
PORT_CAP = 0x00000104
N_PORT = 4
PKT_LEN_MIN = 16
PKT_LEN_MAX = 4300
CREDIT_THRESH = 1024
US_CYC = 1250


def plen_nflit(n: int) -> int:
    lastn = 1 if n < 1 else n
    if lastn > 32:
        lastn = 32
    return ((lastn - 1) & 0x1F) << 5


def plen_4300() -> int:
    return (6 << 10) | (22 << 5)


def plen_oversize() -> int:
    return (6 << 10) | (31 << 5)


def plen_min_try() -> int:
    return 0


def decl_flits(plen: int) -> int:
    nblk = ((plen >> 10) & 0xF) + 1
    lastn = ((plen >> 5) & 0x1F) + 1
    n = (nblk - 1) * 32 + lastn
    if n < 1:
        n = 1
    if n > 512:
        n = 512
    return n


def decl_beats(plen: int) -> int:
    bytes_ = decl_flits(plen) * 20
    n = (bytes_ + 63) >> 6
    return 1 if n < 1 else n


def mk_flit(cfg=0, rt=0, vl=0, scna=0, dcna=0, plen=0, cci=0, lbf=0, nlp=0, opc=0) -> int:
    f = 0
    f |= (cfg & 0xF) << 8
    f |= (rt & 0x3) << 22
    f |= (vl & 0x1)
    f |= ((vl >> 1) & 0x7) << 13
    f |= ((plen >> 8) & 0x3F) << 16
    f |= (plen & 0xFF) << 24
    f |= (scna & 0xFFFF) << 32
    f |= (dcna & 0xFFFF) << 48
    f |= (cci & 0xFFFF) << 64
    f |= (lbf & 0xFF) << 80
    f |= (nlp & 0x7) << 93
    f |= (opc & 0xFF) << 96
    return f


def mk_beat(flit0: int, payload_lo: int = 0) -> int:
    return ((flit0 & ((1 << 160) - 1)) << 352) | (payload_lo & ((1 << 352) - 1))


def nw512_flit0(beat: int) -> int:
    return (beat >> 352) & ((1 << 160) - 1)


def lph_cfg(flit: int) -> int:
    return (flit >> 8) & 0xF


def lph_rt(flit: int) -> int:
    return (flit >> 22) & 0x3


def lph_vl(flit: int) -> int:
    return (((flit >> 13) & 0x7) << 1) | (flit & 0x1)


def nth_scna(flit: int) -> int:
    return (flit >> 32) & 0xFFFF


def nth_dcna(flit: int) -> int:
    return (flit >> 48) & 0xFFFF


def nth_cci(flit: int) -> int:
    return (flit >> 64) & 0xFFFF


def nth_lbf(flit: int) -> int:
    return (flit >> 80) & 0xFF


def nth_nlp(flit: int) -> int:
    return (flit >> 93) & 0x7


def lph_plength(flit: int) -> int:
    return (((flit >> 16) & 0x3F) << 8) | ((flit >> 24) & 0xFF)


def nth_opc(flit: int) -> int:
    return (flit >> 96) & 0xFF


def cfg6_should_term(cna_written: bool, cna: int, flit: int) -> bool:
    dcna = nth_dcna(flit)
    nlp = nth_nlp(flit)
    opc = nth_opc(flit)
    us = bool(cna_written) and (dcna == (cna & 0xFFFF))
    return us or (nlp == 1) or (opc == 0x10 and us)


def nw512_plen4() -> int:
    return (3 << 5)


def nw512_sop(cfg=3, rt=0, scna=0, dcna=0, plen=None) -> int:
    if plen is None:
        plen = nw512_plen4()
    return mk_flit(cfg=cfg, rt=rt, scna=scna, dcna=dcna, plen=plen)


def mk_pcs_beat(flit0: int, payload_lo: int = 0) -> int:
    """640b DLL↔PCS beat: flit0 in [639:480]."""
    return ((flit0 & ((1 << 160) - 1)) << 480) | (payload_lo & ((1 << 480) - 1))


def nw512_golden_rx() -> int:
    pld = int("3C3CC3C30F0FF0F0010101010202020203030303040404040505050506060606070707070808080809090A0A", 16)
    return mk_beat(nw512_sop(3, 0, 0xC33C, 0xD44D, nw512_plen4()), pld)


def nw512_golden_tx() -> int:
    pld = int("A5A55A5A0123456789ABCDEFFEDCBA98765432101111222233334444555566667777888899AABBCCDDEEFF00", 16)
    return mk_beat(nw512_sop(3, 0, 0xA11A, 0xB22B, nw512_plen4()), pld)


def nw512_golden_tx_b2() -> int:
    return (0xB2B2C3C3D4D4E5E5 << 384)


def nw512_golden_tx_n(n: int) -> int:
    if n == 0:
        return nw512_golden_tx()
    k = n & 0xFFFFFFFF
    words = [
        0xA5A55A5A ^ k,
        (0x01234567 + k) & 0xFFFFFFFF,
        0x89ABCDEF ^ ((k & 0xFF) * 0x01010101),
        (0xFEDCBA98 + ((k << 8) & 0xFFFFFFFF)) & 0xFFFFFFFF,
        0x76543210 ^ ((k * 0x00010001) & 0xFFFFFFFF),
        (0x11112222 + k) & 0xFFFFFFFF,
        0x33334444 ^ k,
        (0x55556666 + ((k << 16) & 0xFFFFFFFF)) & 0xFFFFFFFF,
        0x77778888 ^ (k & 0xFFFF),
        (0x99AABBCC + k) & 0xFFFFFFFF,
        (0x00000100 + k) & 0xFFFFFFFF,
    ]
    pld = 0
    for w in words:
        pld = (pld << 32) | (w & 0xFFFFFFFF)
    return mk_beat(nw512_sop(3, 0, 0xA11A, 0xB22B, nw512_plen4()), pld)
