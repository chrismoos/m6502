DESIGN = toplevel
TOP    = top

DEVICE   ?= 85k
PIN_DEF  ?= ulx3s_v20.lpf

VERILOG_SYN_FILES = top.sv $(shell find ../../rtl -name "*.sv")

YOSYS    ?= yosys
NEXTPNR  ?= nextpnr-ecp5
ECPPACK  ?= ecppack

BUILDDIR = bin

SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

QUIET = @

all: $(BUILDDIR)/$(DESIGN).bit
	$(QUIET) echo "Built '$(DESIGN)' for ULX3S $(DEVICE)"

$(BUILDDIR)/$(DESIGN).json: $(VERILOG_SYN_FILES)
	mkdir -p $(BUILDDIR)
	$(QUIET) $(YOSYS) -w 'with list of registers' -w 'tri-state' -e '.*' \
		-p "$(foreach f,$^,read_verilog -sv -defer $(f);) synth_ecp5 -abc9 -top $(TOP) -json $@"

$(BUILDDIR)/$(DESIGN).config: $(PIN_DEF) $(BUILDDIR)/$(DESIGN).json
	$(QUIET) $(NEXTPNR) --$(DEVICE) --package CABGA381 --freq 50 \
		--textcfg $@ --json $(filter-out $<,$^) --top $(TOP) --lpf $<

$(BUILDDIR)/$(DESIGN).bit: $(BUILDDIR)/$(DESIGN).config
	$(QUIET) $(ECPPACK) --compress $^ $@

prog: $(BUILDDIR)/$(DESIGN).bit
	fujprog $^

clean:
	rm -rf $(BUILDDIR)

.SECONDARY:
.PHONY: all clean prog
