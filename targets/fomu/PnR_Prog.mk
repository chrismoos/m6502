COPY ?= cp -a

# Use **nextpnr** to generate the FPGA configuration.
# This is called the **place** and **route** step.
$(BUILDDIR)/$(DESIGN).asc: $(BUILDDIR)/$(DESIGN).json $(PCF)
	$(QUIET) $(NEXTPNR) \
		$(PNRFLAGS) \
		--pre-pack clocks.py \
		--pcf $(PCF) \
		--json $(BUILDDIR)/$(DESIGN).json \
		--asc $@

# Use icepack to convert the FPGA configuration into a "bitstream" loadable onto the FPGA.
# This is called the bitstream generation step.
$(BUILDDIR)/$(DESIGN).bit: $(BUILDDIR)/$(DESIGN).asc
	$(QUIET) $(ICEPACK) $< $@

# Use dfu-suffix to generate the DFU image from the FPGA bitstream.
$(BUILDDIR)/$(DESIGN).dfu: $(BUILDDIR)/$(DESIGN).bit
	$(QUIET) $(COPY) $< $@
	$(QUIET) dfu-suffix -v 1209 -p 70b1 -a $@

# Use df-util to load the DFU image onto the Fomu.
load: $(BUILDDIR)/$(DESIGN).dfu
	dfu-util -D $<
