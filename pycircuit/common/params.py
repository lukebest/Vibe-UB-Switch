"""Architecture-chosen AFIFO constants from ``rtl/common/vibe_ub_params.vh``.

These are not product interface names. Changing them needs a CR.
"""

# AS-0.1 §14 / vibe_ub_params.vh
VIBE_LANE_FAB_W = 160
VIBE_AFIFO_DEPTH = 16
VIBE_AFIFO_AFULL_OCC = 10
VIBE_AFIFO_PTR_W = 5  # depth 16 → 5-bit gray pointers
