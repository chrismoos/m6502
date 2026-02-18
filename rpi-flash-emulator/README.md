# RP2040 Family Flash Emulator

## Overview

This is an RP2040-based external memory controller that provides RAM/ROM to the m6502 using the [bus multiplexing protocol](../docs/bus-multiplexer.md). The RP2040 runs at 125+ MHz and uses its Programmable I/O (PIO) subsystem to handle the multiplexed bus protocol, providing full 64KB memory emulation from flash or SRAM with zero CPU performance impact.

This implementation is particularly useful when interfacing with the 6502 core on limited pin count devices like Tiny Tapeout ASICs. By using the bus multiplexing protocol, the 6502's 24-pin memory bus (16 address + 8 data) is reduced to just 8 shared pins plus a few control signals, freeing up precious I/O for other peripherals and functionality. The RP2040's high-speed PIO state machines handle all the multiplexing timing automatically, allowing the 6502 to run at full speed without wait states.

A key aspect of this design is the use of RP2040 DMA channels to handle all data movement between PIO FIFOs and memory. Address bytes, read data, and write data all flow through dedicated DMA channels with zero RP2040 CPU involvement — the ARM core remains completely idle during 6502 bus cycles, available for other tasks such as USB communication or dynamic ROM patching. This zero-overhead architecture means memory latency is determined solely by PIO and DMA timing, not by software interrupt response time.

## Hardware Requirements

### Supported Boards
- Adafruit Feather RP2350 (tested)
- Raspberry Pi Pico / Pico 2
- Any RP2040 family board with sufficient GPIO pins

### Pin Connections

The implementation expects the following GPIO connections to the m6502:

| RP2040 GPIO | Signal | Direction | Description |
|-------------|--------|-----------|-------------|
| 0-7 | MUX_DATA[7:0] | Bidirectional | Multiplexed address/data bus |
| 8-9 | MUX_SEL[1:0] | Output | Mux phase select (driven by RP2040) |
| 10 | R/W | Input | Read/write control from CPU |
| 26 | PHI2 | Input | CPU clock |

Optional connections:
- SYNC: Instruction fetch indicator
- RESET: CPU reset control

## Building

### Prerequisites
- [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk) (version 2.2.0 or later)
- CMake 3.12+
- ARM GCC toolchain

### Build Steps

1. Set up the Pico SDK environment:
```bash
export PICO_SDK_PATH=/path/to/pico-sdk
```

2. Build the project:
```bash
cd rpi-flash-emulator
mkdir build
cd build
cmake ..
make
```

3. Flash to your board:
- Hold BOOTSEL button while connecting USB
- Copy `rpi_flash_emulator.uf2` to the mounted drive

## Loading 6502 Programs

The emulator serves ROM data from a header file (`rom.h`) that must be generated from your 6502 binary:

```bash
./bin2header.py your_program.bin > rom.h
```

Then rebuild the RP2040 firmware with the new ROM data.

## Operation

### Startup Sequence

1. The RP2040 initializes the PIO state machines on boot
2. The PIO continuously monitors PHI2 and handles memory requests
3. The 6502 CPU can immediately access the emulated memory

### Bus Multiplexing Protocol

The RP2040 implements the bus multiplexing protocol described in [docs/bus-multiplexer.md](../docs/bus-multiplexer.md):

1. **Address Capture**: On PHI1, the RP2040 switches `MUX_SEL` to capture the high and low address bytes
2. **Data Transfer**: On PHI2, the RP2040 either provides read data or captures write data
3. **Zero CPU Overhead**: All phases complete within one 6502 bus cycle with no wait states

At 1 MHz CPU clock (tested configuration), the RP2040 running at 125 MHz has 125 clock cycles per 6502 bus cycle, providing ample timing margin. Higher CPU speeds may be achievable with timing adjustments (testing TBD).

## Timing Configuration

**Tested Configuration**: 1MHz CPU clock with RP2040 at 125MHz

The PIO program includes timing constants in `flash.pio`:
```
.define RW_ADDR_SETUP_TIME_1 6
.define MUX_SETUP_TIME 16
```

These constants account for the 6502's address setup time (tADS) and mux propagation delays.

**Higher Speeds**: The implementation can likely support faster CPU clock speeds (2MHz+) depending on the RP2040 system clock frequency. The timing constants would need adjustment for higher frequencies. Testing at higher speeds is TBD.

## Memory Configuration

The current implementation provides:
- **ROM**: Served from RP2040 flash memory via the `rom.h` include
- **RAM**: Can be implemented in RP2040 SRAM (the full 6502 64KB address space fits easily; RP2040 has 264KB total SRAM)

The high address bits are set during initialization (`mov y, osr` in the PIO program) to point to the ROM base address.

## Technical Details

### PIO Program

The implementation uses `flash.pio`, which provides a complete memory controller in a single PIO state machine, handling address capture and data transfer.

### DMA Architecture

The RP2040 uses DMA channels to move data between the PIO FIFOs and memory with zero CPU involvement:
- Address bytes flow from PIO → RAM address pointer
- Read data flows from ROM/RAM → PIO TX FIFO
- Write data flows from PIO RX FIFO → RAM

This allows the RP2040 CPU to remain idle or perform other tasks while serving memory requests.

## Integration with m6502

To use this with your m6502 FPGA design:

1. Enable bus multiplexing in your MCU configuration
2. Connect the multiplexed signals to the RP2040 as shown in the pin table
3. Build and flash this firmware to the RP2040
4. Load your 6502 program via `rom.h`
5. Power on both devices

The 6502 will boot and execute code from the RP2040-provided memory.

## Future Enhancements

Potential improvements:
- USB serial interface for dynamic ROM loading
- RAM/ROM banking support for >64KB total memory
- Cycle-accurate timing debug output
- Integration with debuggers (GDB stub, etc.)

## References

- [Bus Multiplexer Documentation](../docs/bus-multiplexer.md) - Complete protocol specification and timing diagrams
- [m6502 Main README](../README.md) - Overall project documentation
- [RP2040 Datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) - Hardware reference
