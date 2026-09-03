# RTL file lists for the impl flow. Paths are relative to VIBE_ROOT.
# Keep in sync with the compile list in the top-level README.
# Do not add tb/ sources. Do not list .vh files (they are `include`d).

RTL := $(VIBE_ROOT)/rtl

VIBE_INC_DIR := $(RTL)/common

# Small sequential leaf used by synth-smoke (no `include`, no children).
VIBE_SMOKE_TOP ?= vibe_sync2
VIBE_SMOKE_SV  := $(RTL)/cdc/vibe_sync2.sv

# Full-chip list (same modules as README "Compile (syntax check)").
VIBE_TOP_SV := \
  $(wildcard $(RTL)/cdc/*.sv) \
  $(wildcard $(RTL)/pma/*.sv) \
  $(wildcard $(RTL)/pcs/*.sv) \
  $(wildcard $(RTL)/lmsm/*.sv) \
  $(wildcard $(RTL)/dll/*.sv) \
  $(wildcard $(RTL)/nw/*.sv) \
  $(wildcard $(RTL)/fabric/*.sv) \
  $(wildcard $(RTL)/mgmt/*.sv) \
  $(wildcard $(RTL)/port/*.sv) \
  $(RTL)/top/vibe_ub_switch.sv
