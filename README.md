# m6502

A compact MOS 6502 CPU implementation in SystemVerilog, designed for FPGA and ASIC deployment with a focus on minimal gate count.

## Overview

m6502 is a cycle-accurate 6502 CPU core that can be used standalone or integrated into larger systems. The core is optimized for resource-constrained environments, making it suitable for small FPGAs like the Lattice iCE40 (Fomu) and projects with limited I/O like Tiny Tapeout.

An optional MCU wrapper is provided as a practical way to experiment with the core, offering peripheral integration (GPIO, SK6812 LED controller) and simplified memory interfacing. However, the CPU core itself is fully standalone and can be integrated into any design.

## Key Features

### CPU Core
- **Cycle-accurate 6502 implementation** - Full NMOS 6502 instruction set with all addressing modes
- **Microcode-driven architecture** - Vertical microcode for minimal gate count (~950 LUTs)
- **Standalone usage** - Standard 6502 bus interface for integration into any design
- **Flexible memory support** - Works with block RAM, external memory, or custom memory controllers

### Optional MCU Wrapper
- **Peripheral integration** - GPIO and SK6812 RGBW LED controller for experimentation
- **Bus multiplexing** - Reduces pin count for I/O-constrained platforms
- **FPGA-proven targets** - Working implementations for Fomu (iCE40) and ULX3S (ECP5)

## Architecture

### CPU Core

The [CPU core](docs/architecture.md) is a fully synthesizable implementation of the MOS 6502 processor. Key architectural decisions:

- **Microcode-based execution**: Instructions are broken down into microinstructions executed by a state machine, allowing for precise cycle timing and reduced logic complexity
- **Vertical microcode organization**: Compact microcode format optimized for internal ROM rather than external lookup tables
- **Single-cycle ALU**: Dedicated arithmetic logic unit with support for binary and BCD modes
- **Standard 6502 bus interface**: 16-bit address bus, 8-bit data bus, read/write control signals

### MCU Module

The MCU wrapper provides a complete microcontroller platform:

- Integrates the CPU core with peripheral controllers
- Memory-mapped I/O at standard base addresses
- Clock domain management for CPU and peripherals
- Internal bus multiplexing to route data between CPU, peripherals, and external memory

### Memory Options

The design supports two primary memory configurations:

1. **Block RAM (BRAM)**: Internal FPGA memory for program and data storage. Ideal for standalone applications where the entire program fits in on-chip RAM.

2. **External Bus**: Traditional 6502-style external memory interface with full 16-bit address and 8-bit data buses. Allows connection to external ROM, RAM, and memory-mapped peripherals like a real 6502 system.

### Bus Multiplexing

For pin-constrained applications (such as Tiny Tapeout), an optional [bus multiplexer](docs/bus-multiplexer.md) reduces the required I/O pins from 24 (16 address + 8 data) to just 8 shared pins plus control signals.

The multiplexer operates in four phases:
1. Output address low byte
2. Output address high byte
3. Read data input (for read operations)
4. Write data output (for write operations)

An [RP2040 PIO implementation](rpi-flash-emulator/) provides external RAM/ROM using this multiplexed interface.

**Note**: Bus multiplexing is only necessary for platforms with limited pin count. Designs with sufficient I/O can use the full parallel bus interface directly.

## Peripherals

Current peripheral implementations:

- **[GPIO](docs/peripherals.md#gpio-peripheral)**: 8-bit general-purpose I/O with pin multiplexing
  - Base address: `0xA000`
  - Configurable direction, pin modes (UART, SK6812, etc.)

- **[SK6812 RGBW LED Controller](docs/peripherals.md#sk6812-rgbw-led-controller)**: Hardware driver for SK6812 addressable LEDs
  - Base address: `0xA010`
  - Configurable timing and color control

- **[Timer](docs/peripherals.md#timer-peripheral)**: 16-bit timer with prescaler and interrupts
  - Base address: `0xA020`
  - Configurable prescaler, auto-reload, interrupt on overflow

- **[Clock Control](docs/peripherals.md#clock-control)**: CPU clock frequency management
  - Base address: `0xA030`
  - Software-configurable CPU clock divider (1MHz default on targets)

- **[UART](docs/peripherals.md#uart-peripheral)**: Serial communication controller
  - Base address: `0xA040`
  - Configurable baud rate, TX/RX FIFOs, interrupt support

See [docs/peripherals.md](docs/peripherals.md) for detailed peripheral documentation.

## Targets

### Fomu (Lattice iCE40)
Minimal implementation targeting the Fomu USB board with iCE40UP5K FPGA. Demonstrates the design running in ~1000 LUTs with block RAM for program storage.

### ULX3S (Lattice ECP5)
Development platform with more resources, used for testing and validation with external peripherals.

See [docs/targets.md](docs/targets.md) for build instructions and target-specific details.

## Documentation

- [Architecture Details](docs/architecture.md) - In-depth CPU microarchitecture and design decisions
- [Peripherals](docs/peripherals.md) - Peripheral registers and programming guide
- [Bus Multiplexer](docs/bus-multiplexer.md) - Pin-reduction bus multiplexing system
- [Memory Systems](docs/memory.md) - Block RAM vs. external memory configurations
- [Targets](docs/targets.md) - Platform-specific build and deployment
- [Testing Guide](TESTING.md) - Running tests and verification
- [RP2040 Flash Emulator](rpi-flash-emulator/) - External memory controller implementation

## Getting Started

1. Clone the repository
2. Choose your target platform (`fomu` or `ulx3s`)
3. Build an example:
   ```bash
   cd examples
   make
   cd ../targets/fomu  # or ulx3s
   make
   ```

## Design Goals

This implementation prioritizes:

1. **Minimal gate count** - Careful optimization for small FPGA targets and ASIC tapeouts
2. **Cycle accuracy** - Matches original 6502 timing for compatibility
3. **Flexibility** - Supports both integrated block RAM and external memory bus configurations
4. **Modularity** - Clean separation between CPU core, MCU wrapper, and peripherals

## License

MIT
