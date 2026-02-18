# Target Platforms

This document covers the supported FPGA platforms and build instructions for each target.

## Supported Targets

### Fomu (Lattice iCE40UP5K)

The Fomu is a tiny FPGA board in a USB-A form factor, featuring a Lattice iCE40UP5K FPGA with 5280 LUTs, 120Kbit (15KB) of embedded block RAM (EBR), and 1Mbit (128KB) of SPRAM.

**Key Specifications**:
- FPGA: iCE40UP5K-SG48
- LUTs: 5280
- Block RAM: 120Kbit (15KB) EBR; 1Mbit (128KB) SPRAM
- Clock: 48 MHz oscillator
- I/O: Limited (USB pins, RGB LED, 4 touch pads)
- Form factor: USB Type-A

**Resources Used**:
- Block RAM: ~8-16KB (for program/data)
- Clock: 24-48 MHz

#### Building for Fomu

```bash
cd targets/fomu

# Compile example program (default: fomu_touch_led)
cd ../../examples
make fomu_touch_led.hex

# Build FPGA bitstream
cd ../targets/fomu
make FOMU_REV=pvt

# Program Fomu (plug in, Fomu boots into DFU mode by default)
dfu-util -D build/top.bit
```

#### Fomu Configuration

The Fomu target uses:
- System clock: 48 MHz (internal oscillator)
- CPU clock: 1 MHz (software divided, `/48`)
- RGB LED connected via GPIO pins 0-2 (active-low)
- Minimal GPIO (touch pads on pins 4-7)
- Pure BRAM configuration (no external memory)

**Clock Architecture**:
- Software clock divider generates 1 MHz CPU clock from 48 MHz system clock
- Peripherals run at 48 MHz system clock for accurate timing (UART, Timer)
- CPU clock configurable via Clock Control peripheral (`0xA030`)
- PHI2 output matches CPU clock frequency exactly

#### Memory Map (Fomu)

**8KB BRAM Configuration** (mirrored throughout 64KB address space):

```
0x0000-0x1FFF: 8KB BRAM (mirrored every 8KB)
  0x0000-0x00FF: Zero Page
  0x0100-0x01FF: Stack
  0x0200-0x1FFF: RAM/ROM (from hex file)
0x2000-0x3FFF: Mirror of 0x0000-0x1FFF
0x4000-0x5FFF: Mirror of 0x0000-0x1FFF
0x6000-0x7FFF: Mirror of 0x0000-0x1FFF
0x8000-0x9FFF: Mirror of 0x0000-0x1FFF
0xA000-0xBFFF: Mirror + Peripherals (0xA000-0xA0FF)
  0xA000-0xA00B: GPIO (RGB LED on pins 0-2, touch pads on pins 4-7)
  0xA010-0xA017: SK6812 LED controller (not used on Fomu)
  0xA020-0xA027: Timer
  0xA030-0xA033: Clock control
  0xA040-0xA047: UART
0xC000-0xDFFF: Mirror of 0x0000-0x1FFF
0xE000-0xFFFF: Mirror of 0x0000-0x1FFF
  0xFFFA-0xFFFB: NMI Vector (mirrors 0x1FFA-0x1FFB)
  0xFFFC-0xFFFD: RESET Vector (mirrors 0x1FFC-0x1FFD)
  0xFFFE-0xFFFF: IRQ Vector (mirrors 0x1FFE-0x1FFF)
```

**Note**: The 8KB BRAM uses only the lower 13 address bits, causing it to repeat (mirror) every 8KB across the full 64KB address space.

#### Constraints

- Limited I/O: Only USB pins and internal resources available
- No external memory: Must fit in block RAM
- Power budget: USB-powered, minimal consumption
- Package size: Small QFN48 package

### ULX3S (Lattice ECP5)

The ULX3S is a feature-rich development board with a Lattice ECP5 FPGA, abundant I/O, and expansion options.

**Key Specifications**:
- FPGA: ECP5-12F/25F/45F/85F (various sizes)
- LUTs: 12K - 85K
- Block RAM: 208KB - 3.7MB
- Clock: 25 MHz oscillator (PLL capable)
- I/O: GPIO headers, HDMI, audio, SD card
- Form factor: Development board

**Resources Used**:
- Block RAM: Configurable (plenty available)
- Clock: 25 MHz base, configurable with PLL

#### Building for ULX3S

```bash
cd targets/ulx3s

# Compile example program
cd ../../examples
make

# Build FPGA bitstream
cd ../targets/ulx3s
make

# Program ULX3S (via openFPGALoader)
make prog
```

#### ULX3S Configuration

The ULX3S target demonstrates:
- System clock: 50 MHz (25 MHz base with PLL)
- CPU clock: 1 MHz (software divided, `/50`)
- 5 onboard LEDs connected to GPIO pins 0-4
- UART TX on GPIO pin 5 (header pin gp26)
- UART RX on GPIO pin 6 (header pin gn27)
- GPIO pin 7 available on external header (gn26)
- External bus capability via GPIO headers with multiplexer
- External RAM/ROM via bus multiplexer (RP2040/ESP32 companion)
- Debug port output on GPIO header pins gn16–gp19

#### Debug Port (ULX3S)

The ULX3S target wires the CPU debug port to 8 GPIO header pins for logic analyser or oscilloscope observation. See [Debug Port](architecture.md#debug-port) for the full signal table.

**Debug output pins** (bit 7 → bit 0):

| Debug bit | Header pin |
|-----------|-----------|
| 7 (MSB) | gp19 |
| 6 | gn19 |
| 5 | gp18 |
| 4 | gn18 |
| 3 | gp17 |
| 2 | gn17 |
| 1 | gp16 |
| 0 (LSB) | gn16 |

**Button controls** for the debug selector:

| Button | Action |
|--------|--------|
| UP (`btn[3]`) | Increment selector (wraps 7→0) |
| DOWN (`btn[4]`) | Decrement selector (wraps 0→7) |
| LEFT (`btn[5]`) | Reset selector to 0 |

All three buttons use a 3-stage synchroniser to prevent metastability and edge-detect on press (active-high, PULLMODE=DOWN). The selector resets to 0 (`active_microinstruction`) on power-on reset.

**Clock Architecture**:
- Software clock divider generates CPU clock from 50 MHz system clock
- System clock runs peripherals at full speed
- CPU clock configurable via Clock Control peripheral (`0xA030`)
- PHI2 output matches CPU clock frequency exactly

#### Memory Map (ULX3S)

**External Memory Configuration** (current default):

ULX3S uses external memory via GPIO headers with bus multiplexer:

```
0x0000-0xFFFF: External Memory (64KB addressable)
  - Accessed via GPIO pins (gp7-gp4, gn7-gn4 for data bus)
  - Bus multiplexer for address/data
  - Control signals: gp9 (phi2), gn9 (r/w), gp8/gn8 (bus_sel)

0xA000-0xA0FF: Internal Peripherals (FPGA-based)
  0xA000-0xA00B: GPIO (pins 0-4: LEDs, pin 5: UART TX/gp26, pin 6: UART RX/gn27, pin 7: gn26)
  0xA010-0xA017: SK6812 LED controller (available via GPIO pin mux mode 0x03)
  0xA020-0xA027: Timer
  0xA030-0xA033: Clock control
  0xA040-0xA047: UART (115200 baud example at examples/ulx3s_uart_echo.s)
```

**Note**: Internal BRAM is **not used** on ULX3S (but can be enabled). All program/data memory must be provided externally via the GPIO bus multiplexer interface. Typical setup uses an external microcontroller (e.g., RP2040, ESP32) to emulate RAM/ROM.

#### Expansion Options

The ULX3S provides multiple expansion routes:
- GPIO headers: Connect external memory/peripherals
- PMOD connectors: Standard interface for modules
- ESP32 module: WiFi/Bluetooth co-processor
- SD card: Mass storage
- HDMI: Video output potential

## Tiny Tapeout (ASIC)

### Overview

Tiny Tapeout is a program that makes ASIC manufacturing accessible by sharing die space among multiple tiny designs. It's ideal for educational projects and small digital circuits.

**Platform Specifications**:
- **I/O Pins**: 24 total (8 input, 8 output, 8 bidirectional)
- **Process**: Skywater 130nm
- **Clock**: External, provided by test board
- **Memory**: External (no on-chip RAM/ROM available)

### m6502 for Tiny Tapeout

m6502 can be configured for Tiny Tapeout submission with these characteristics:

**Configuration**:
- **External memory required**: All program and data storage is external
- **Bus multiplexing**: Reduces I/O requirements from 24 to 8 pins
- **Minimal peripherals**: Core CPU + GPIO only
- **RP2040 companion**: Test board provides external RAM

**Resource Usage**:
- Clock speed: Target >10 MHz (process dependent)

### External Memory Interface

The Tiny Tapeout test board includes an RP2040 that provides external memory via its PIO (Programmable I/O) subsystem, offering high-speed memory emulation for the 6502.

## Adding a New Target

To add a new FPGA platform, you'll need:

1. **Target directory structure** with board-specific configuration
2. **Pin assignments** mapping MCU signals to board I/O
3. **Clock generation** appropriate for the platform (PLL, divider, etc.)
4. **Memory configuration** (BRAM initialization, external bus setup)
5. **Build scripts** for synthesis and programming

Refer to existing targets (Fomu, ULX3S) as examples for new platform ports.

## Performance Results

### Clock Speed by Platform

| Platform | System Clock | CPU Clock (Default) | Notes |
|----------|-------------|---------------------|-------|
| Fomu (iCE40UP5K) | 48 MHz | 1 MHz | Configurable via CPU_DIV register |
| ULX3S (ECP5-12F) | 50 MHz | 1 MHz | Configurable via CPU_DIV register |
| ULX3S (ECP5-85F) | 50 MHz | 1 MHz | Configurable via CPU_DIV register |
| Tiny Tapeout (ASIC) | TBD | TBD | Depends on process, likely >50 MHz |

**Notes**:
- System clock drives peripherals (UART, LED controllers) at full speed
- CPU clock is software-divided from system clock via Clock Control peripheral
- CPU frequency = sysclk / (CPU_DIV + 1), configurable at runtime
- PHI2 output frequency matches CPU clock exactly
- System clock can run much faster than CPU clock for peripheral accuracy

### Resource Utilization

Resource utilization numbers will be updated after re-synthesis. The design is intentionally compact, leaving room for peripherals and application logic on all supported platforms.

## Future Targets

Potential future platforms:

- **iCEBreaker**: Popular iCE40 development board
- **OrangeCrab**: ECP5 in Feather form factor
- **Other Tiny Tapeout shuttles**: Future ASIC submissions
