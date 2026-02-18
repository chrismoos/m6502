PCF_PATH   ?= .

ifeq ($(FOMU_REV),pvt)
YOSYSFLAGS ?= -D PVT=1
PNRFLAGS   ?= --up5k --package uwg30
PCF        ?= fomu-pvt.pcf
else
$(error Unrecognized FOMU_REV value. must be "pvt")
endif