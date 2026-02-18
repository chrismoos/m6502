include board.mk

DESIGN = top
TOP    = top

VERILOG_SYN_FILES = top.sv $(shell find ../../rtl -name "*.sv")

YOSYS     ?= yosys
NEXTPNR   ?= nextpnr-ice40
ICEPACK   ?= icepack

BUILDDIR = build

SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

QUIET = @

# If a container engine is used, each tool is executed in a separated container
ifdef CONTAINER_ENGINE
include ../../container.mk
endif

# Default target: run all required targets to build the DFU image.
all: $(BUILDDIR)/$(DESIGN).dfu
	$(QUIET) echo "Built '$(DESIGN)' for Fomu $(FOMU_REV)"

.DEFAULT: all

# Use *Yosys* to generate the synthesized netlist.
# This is called the **synthesis** and **tech mapping** step.
$(BUILDDIR)/$(DESIGN).json: $(VERILOG_SYN_FILES)
	mkdir -p $(BUILDDIR)
	$(QUIET) $(YOSYS) -w 'with list of registers' -w 'tri-state' -e '.*' $(YOSYSFLAGS) \
		-p  \
		"read_verilog -sv $(VERILOG_SYN_FILES); \
		synth_ice40 \
		-top $(TOP) \
		-json $@" 2>&1 | tee $(BUILDDIR)/yosys-report.txt

include PnR_Prog.mk

.PHONY: load

# Cleanup the generated files.
clean:
	rm -rf $(BUILDDIR)

.PHONY: clean
