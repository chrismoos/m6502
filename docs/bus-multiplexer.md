# Bus Multiplexer

## Overview

The bus multiplexer is an optional component that reduces the I/O pin requirements for external memory access from 24 pins (16 address + 8 data) down to 8 shared pins plus a few control signals. All multiplexer phases complete within a single CPU cycle — there is **no speed penalty** compared to a parallel bus.

The external controller (e.g., RP2040 PIO) drives the `MUX_SEL` lines to sequence through address and data phases, tracking the CPU's PHI2 clock and conforming to standard 6502 bus timing.

## Timing

![Bus Multiplexer Timing Diagram](timing_1mhz.png)

The multiplexer phases fit entirely within one CPU bus cycle. The 6502 bus timing:

- **negedge PHI2**: CPU sets address and R/W signals; samples read data
- **posedge PHI2**: CPU write data becomes valid

Within one cycle (negedge to negedge), the external controller waits for the CPU address to stabilize (tADS), then sequences through the mux phases:

| Phase | When | MUX_SEL | What happens |
|-------|------|---------|-------------|
| WAIT | PHI1, first 150 ns (tADS) | — | Mux idle; CPU address stabilizing |
| ADDR_HI | PHI1, after tADS, first half | `01` | MCU outputs `addr[15:8]` on shared pins; external latches it |
| ADDR_LO | PHI1, after tADS, second half | `00` | MCU outputs `addr[7:0]` on shared pins; external latches it |
| DATA | PHI2 (PHI2 high) | `10` / `11` | Read: external drives data, MCU tri-states (`10`). Write: MCU drives data (`11`) |

ADDR_HI is sent first to allow the external controller to begin address decoding earlier. Both address phases have equal duration.

### Timing Budget at 1 MHz

At 1 MHz (1000 ns/cycle, 500 ns per half), the 6502 datasheet timing parameters and mux propagation delay determine the available windows:

| Parameter | Symbol | Value | Description |
|-----------|--------|-------|-------------|
| Address Delay | tADS | 150 ns typ | Address valid after negedge PHI2 |
| Address Hold | tHA | 30 ns min | Address held after next negedge PHI2 |
| R/W Delay | tRWS | 150 ns typ | R/W valid after negedge PHI2 |
| R/W Hold | tHRW | 30 ns min | R/W held after next negedge PHI2 |
| Memory Access | tACC | 575 ns max | From posedge PHI2 to data valid |
| Data Setup | tDSU | 100 ns min | Read data valid before negedge PHI2 |
| Write Data Setup | tMDS | 200 ns typ | Write data valid before negedge PHI2 |
| Data Hold (Read) | tHR | 10 ns min | Read data held after negedge PHI2 |
| Data Hold (Write) | tHW | 30 ns min | Write data held after negedge PHI2 |
| Mux Propagation | tMUX | 10 ns | Mux output valid after select change |

**Address phase timing** (PHI1 = 500 ns):
- Wait for tADS: 150 ns (mux idle, CPU address stabilizing)
- Available for address phases: 500 - 150 = 350 ns
- Each address phase: 175 ns (equal width for ADDR_HI and ADDR_LO)
- Mux output valid after tMUX (10 ns) within each phase: 165 ns of valid data per phase

**Data phase timing** (PHI2 = 500 ns):
- Full PHI2 high period available for data transfer, well within tACC

To generate timing diagrams at other frequencies:

```bash
uv run docs/timing_diagram.py --freq 1.0 --output docs/timing_1mhz.png
uv run docs/timing_diagram.py --freq 2.0 --output docs/timing_2mhz.png
```

## Architecture

### Signal Interface

The bus multiplexer uses these signals:

**Control Input**:
- `MUX_SEL[1:0]`: Phase select (driven by external controller)

**CPU Interface**:
- `CPU_DATA[7:0]`: Write data from CPU
- `CPU_ADDR[15:0]`: Address from CPU

**Multiplexed I/O**:
- `MUX_DATA[7:0]`: Shared bidirectional data bus
- `MUX_DATA_OE`: Output enable control

The multiplexer operates combinationally, instantly routing signals based on the `MUX_SEL` value with no added latency.

### Multiplexing Phases

| i_sel | Phase | OE | Data on Pins |
|-------|-------|----|-------------|
| `01` | ADDRESS_HI | 1 (driving) | `addr[15:8]` |
| `00` | ADDRESS_LO | 1 (driving) | `addr[7:0]` |
| `10` | DATA_IN | 0 (hi-z) | External drives read data |
| `11` | DATA_OUT | 1 (driving) | CPU write data |

## External Controller Implementation

### RP2040 PIO

An RP2040 can provide external RAM/ROM using its Programmable I/O (PIO) subsystem:

- Monitors PHI2 to track bus cycle phases
- Controls `MUX_SEL` to sequence through address and data phases
- Latches address bytes during PHI1
- Provides read data or captures write data during PHI2
- Operates at high speed (125+ MHz) — all phases complete within one 6502 cycle

A complete implementation is available in [rpi-flash-emulator](../rpi-flash-emulator/) with build instructions and usage examples.

### Required External Signals

In addition to the 8 shared data pins, the external controller needs:

- **PHI2**: CPU clock (to track cycle phases)
- **R/W**: Read/write direction (determines DATA_IN vs DATA_OUT)
- **MUX_SEL[1:0]**: Phase selection (driven by external controller)

Optional signals:
- **SYNC**: Instruction fetch indicator
- **READY**: Stall signal (active low, if needed for slow memory)

## Tiny Tapeout Integration

### Available I/O

Tiny Tapeout provides 24 pins total: 8 input, 8 output, 8 bidirectional.

### Why Multiplex on Tiny Tapeout?

A full parallel bus would need 16 address + 8 data = 24 pins — consuming every pin with nothing left for R/W, clock, reset, or any peripherals. The multiplexer frees up pins:

- **Multiplexed bus**: 8 pins for address/data, freeing 16 pins for control, peripherals, debug, and expansion

### Recommended Pin Assignment (Multiplexed)

**Input Pins [7:0]**:
- MUX_DATA read (when external device drives data)
- RESET_N
- READY (wait state control)
- Reserved for future use

**Output Pins [7:0]**:
- R/W
- SYNC
- MUX_SEL[1:0]
- PHI2 (forward CPU clock to external controller)
- DEBUG[2:0] (CPU state indicators)

**Bidirectional Pins [7:0]**:
- MUX_DATA bidirectional bus

This configuration maintains full memory bus capability while leaving pins for status outputs, debug signals, and peripheral expansion.

### RP2040 on Tiny Tapeout Test Board

The Tiny Tapeout test board includes an RP2040 that serves as the external memory controller:

1. Monitors PHI2 and controls MUX_SEL timing
2. Sequences through address capture and data phases within each cycle
3. Provides RAM/ROM contents from RP2040 flash or SRAM
4. Operates at 125 MHz — provides plenty of timing margin for 1 MHz 6502 operation

See [rpi-flash-emulator](../rpi-flash-emulator/) for a complete implementation that can be used with any RP2040 board.
