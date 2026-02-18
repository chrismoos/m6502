# Memory Systems

m6502 supports multiple memory configurations, from fully self-contained block RAM systems to traditional external memory bus architectures.

## Overview

The 6502 architecture provides a unified 64KB address space that can be populated with:

- **Block RAM (BRAM)**: On-chip FPGA memory
- **External RAM/ROM**: Off-chip memory via parallel or multiplexed bus
- **Memory-mapped peripherals**: Internal or external I/O devices
- **Hybrid combinations**: Mix of internal and external memory

## Block RAM (BRAM) Configuration

### Description

Block RAM uses the FPGA's internal memory blocks to provide fast, zero-wait-state memory directly connected to the CPU core.

### Advantages

- **Zero latency**: Single-cycle read/write access
- **No external components**: Fully self-contained
- **Simplified routing**: No I/O pin constraints
- **Higher performance**: Direct connection to CPU
- **Lower power**: On-chip access uses less power

### Limitations

- **Size constraints**: Limited by FPGA resources
  - iCE40UP5K (Fomu): 120Kbit (15KB) EBR available for inferred BRAM; 1Mbit (128KB) SPRAM requires special primitives
  - ECP5 (ULX3S): Several hundred KB available
- **Fixed at synthesis**: Cannot be modified without rebuilding bitstream
- **No external expansion**: Isolated from external devices

### Characteristics

Block RAM provides:
- Single-cycle read/write access
- Configurable size (limited by FPGA resources)
- Optional initialization from file
- Direct connection to CPU (no bus latency)

### Memory Initialization

Block RAM can be pre-loaded with program code during FPGA configuration:

1. Compile 6502 program to binary format
2. Convert binary to memory initialization format (.hex or .mem)
3. Configure BRAM with initialization file
4. Program loads automatically when FPGA is configured

This allows instant program execution on power-up without external programming.

### Typical Memory Map (Block RAM)

```
0x0000-0x00FF: Zero Page (fast access)
0x0100-0x01FF: Stack
0x0200-0x03FF: General purpose RAM
0x0400-0x7FFF: Program RAM (if sufficient BRAM)
0x8000-0xFFFF: Program ROM (initialized from hex file)
0xA000-0xAFFF: Memory-mapped I/O (internal peripherals)
0xFFFA-0xFFFF: Interrupt vectors
```

## External Memory Bus Configuration

### Description

Traditional 6502 architecture with separate address and data buses connected to external ROM and RAM chips.

### Advantages

- **Large capacity**: Up to 64KB without banking, expandable beyond
- **Flexibility**: Mix ROM, RAM, EEPROM, flash
- **Replaceability**: Update program by swapping ROM chip
- **Peripheral expansion**: Standard bus for I/O devices
- **Authentic experience**: Matches original 6502 systems

### Limitations

- **Pin count**: Requires 24+ I/O pins (16 address + 8 data + control)
- **External components**: ROM/RAM chips needed
- **PCB complexity**: More routing, larger board
- **Slower access**: Multi-cycle external memory access
- **Power consumption**: External chips draw more power

### Standard Bus Interface

The CPU provides a standard 6502 bus:

```systemverilog
output [15:0] o_bus_addr,    // 16-bit address bus
inout [7:0] io_bus_data,     // 8-bit bidirectional data bus
output o_rw,                 // Read/Write control (1=read, 0=write)
output o_phi2,               // Clock phase 2 (bus timing reference)
output o_sync,               // Opcode fetch indicator
```

### External Memory Types

#### ROM (Read-Only Memory)

- Program storage
- Typically 28C64 (8KB) to 28C256 (32KB) EEPROM
- Address decode to upper memory region (0x8000-0xFFFF)

#### RAM (Random Access Memory)

- Data and stack storage
- Typically 62256 (32KB) SRAM
- Address decode to lower memory region (0x0000-0x7FFF)

#### Hybrid ROM/RAM

- Flash with RAM-like interface (e.g., SST39SF)
- Allows in-system programming
- Trade-off: Slower write cycles

### Address Decoding

External glue logic or CPLD decodes addresses to chip selects:

```
Address Range    | Chip Select | Device
-----------------+-------------+------------------
0x0000-0x7FFF      | /RAM_CS     | 32KB SRAM
0x8000-0x9FFF      | /ROM_CS     | 8KB EEPROM
0xA000-0xAFFF      | /IO_CS      | Peripheral I/O
0xB000-0xFFFF      | /ROM_CS     | EEPROM (continued)
```

Simple 74-series logic or a CPLD can implement this decode.

### Example External Memory Circuit

```
[m6502 FPGA]
    |
    +-- A[15:0] ----+---- [74HC138 Decoder]
    |               |         |
    +-- D[7:0] -----+----+----+----+
    |               |    |    |    |
    +-- R/W --------+   RAM  ROM  I/O
    +-- PHI2 -------+
```

## Multiplexed External Bus

See [bus-multiplexer.md](bus-multiplexer.md) for details on pin-reduced external memory access using time-multiplexed address/data.

### Quick Summary

- Reduces 24 pins to 8 shared pins + control
- Requires smart external controller (e.g., RP2040 PIO)
- No speed penalty — all mux phases complete within one CPU cycle
- Ideal for Tiny Tapeout or pin-constrained designs

