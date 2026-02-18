# CPU Architecture

## Overview

m6502 is a cycle-accurate implementation of the classic NMOS 6502 microprocessor, designed for efficient implementation in FPGAs and ASICs. It maintains full compatibility with the original 6502 instruction set and timing characteristics while optimizing for minimal gate count.

## Design Philosophy

### Microcode Architecture

The CPU uses a microcode-driven approach where each 6502 instruction is decomposed into a sequence of smaller operations. This architecture was chosen to minimize logic resources while maintaining cycle-accurate timing.

**Microcode advantages:**
- **Compact design**: Shared execution paths reduce gate count
- **Simplified timing**: Predictable cycle-by-cycle execution
- **Easy verification**: Clear mapping between operations and cycles
- **Flexibility**: Simplified instruction decoder logic

The implementation uses vertical microcode with narrow operation encodings, making it well-suited for resource-constrained designs.

## Instruction Execution

Each 6502 instruction executes as a sequence of microoperations:
- Instruction fetch
- Operand address calculation
- Memory access
- ALU operation
- Register/flag updates

### Example: LDA Immediate

The `LDA #$nn` instruction executes in 2 cycles:
1. Fetch opcode, increment PC
2. Read immediate operand, load accumulator, set flags

### Example: LDA Absolute,X

The `LDA $nnnn,X` instruction executes in 4-5 cycles:
1. Fetch opcode
2. Read address low byte
3. Read address high byte, add X index
4. [Optional] Fix high byte if page boundary crossed
5. Read data, load accumulator, set flags

Page crossing adds an extra cycle, matching original 6502 behavior.

## Clock Architecture

### Two-Phase Clocking

The CPU uses a two-phase clock architecture matching the original 6502:

- **PHI1** (first half-cycle): Internal operations, address calculation
- **PHI2** (second half-cycle): Bus operations, data sampling

This ensures proper setup and hold timing for external memory and peripherals, allowing direct interfacing with classic 6502 peripherals.

## Arithmetic Logic Unit (ALU)

### Supported Operations

- **ADC/SBC**: Add/subtract with carry (binary and BCD modes)
- **AND/ORA/EOR**: Logical operations
- **ASL/LSR**: Shift left/right
- **ROL/ROR**: Rotate through carry
- **CMP/CPX/CPY**: Comparisons (subtraction without storing result)

### Binary Coded Decimal (BCD) Mode

The CPU supports BCD arithmetic in decimal mode (D flag set). BCD operations perform nibble-wise decimal arithmetic with automatic correction:
- Each nibble represents 0-9
- Values above 9 trigger +6 adjustment
- Matches NMOS 6502 BCD behavior exactly

## Instruction Decoding

The CPU decodes instructions using the standard 6502 opcode encoding pattern:

```
Opcode format: aaabbbcc

cc = 01: ALU group (ORA, AND, EOR, ADC, STA, LDA, CMP, SBC)
cc = 10: RMW group (ASL, ROL, LSR, ROR, STX, LDX, DEC, INC)
cc = 00: Control group (BIT, JMP, STY, LDY, CPY, CPX, branches)

bbb: Addressing mode (varies by group)
aaa: Operation variant
```

This regular pattern enables compact decoding logic.

## Interrupts and Reset

### Reset Sequence

On reset, the CPU:
1. Performs initialization (6 cycles)
2. Reads reset vector from `0xFFFC-0xFFFD`
3. Begins execution at reset vector address

### IRQ Handling

Maskable interrupts (IRQ):
1. Checked between instructions when interrupt disable flag is clear
2. Pushes PC and status register to stack (7 cycles total)
3. Sets interrupt disable flag
4. Jumps to IRQ vector at `0xFFFE-0xFFFF`

### NMI Handling

Non-maskable interrupts (NMI):
1. Edge-triggered on falling edge of NMI input
2. Similar sequence to IRQ but uses NMI vector at `0xFFFA-0xFFFB`
3. Cannot be disabled by interrupt flag (always serviced)

## Register Implementation

### CPU Registers

- **A** (Accumulator): 8-bit general-purpose accumulator
- **X, Y** (Index registers): 8-bit indexing and counter registers
- **PC** (Program Counter): 16-bit instruction pointer
- **SP** (Stack Pointer): 8-bit stack pointer (full address is `0x01SP`)
- **P** (Status Register): 7 flags (NV-BDIZC)

Status flags:
- **N** (Negative): Bit 7 of result
- **V** (Overflow): Signed arithmetic overflow
- **B** (Break): Distinguishes BRK from IRQ (software flag)
- **D** (Decimal): BCD mode enable
- **I** (Interrupt Disable): Masks IRQ
- **Z** (Zero): Result equals zero
- **C** (Carry): Carry out or borrow

### Register Update Timing

Registers update during instruction execution, ensuring values are stable before the next instruction fetch begins.

## Cycle Accuracy

The implementation is cycle-accurate to the original NMOS 6502:

- All instructions take the correct number of cycles
- Page boundary crossings add penalty cycles where appropriate
- Dummy reads occur on the same cycles as hardware
- Bus timing matches original waveforms (important for cycle-sensitive peripherals)

## Resource Optimization

Techniques used to minimize logic resources:

1. **Shared datapaths**: ALU used for both arithmetic and address calculation
2. **Compact microcode**: Efficient operation encoding
3. **Pattern-based decoding**: Leverages regular 6502 opcode structure
4. **Registered outputs**: Reduces combinational logic depth

## Performance

- **Clock speed**: Up to 48 MHz on iCE40, faster on larger FPGAs
- **IPC**: 0.125 - 0.5 (matching original 6502 multi-cycle execution)

## Debug Port

The CPU exposes an 8-bit debug output port for real-time inspection of internal state without requiring a full debug interface or simulator.

### Interface

```systemverilog
input  [2:0] i_debug_sel,   // selects which internal signal to observe
output [7:0] o_debug_data   // current value of selected signal
```

The output is combinational — it updates every clock cycle with no latency.

### Selector Map

| `i_debug_sel` | Signal | Width | Description |
|---------------|--------|-------|-------------|
| `3'd0` | `active_microinstruction` | 6-bit | Current microinstruction being executed |
| `3'd1` | `next_active_microinstruction` | 6-bit | Next microinstruction (lookahead) |
| `3'd2` | `opcode` | 8-bit | Currently executing 6502 opcode byte |
| `3'd3` | `operation` | 4-bit | Execution sub-state (memory access phase) |
| `3'd4` | `program_counter[15:8]` | 8-bit | PC high byte |
| `3'd5` | `program_counter[7:0]` | 8-bit | PC low byte |
| `3'd6` | `register_acc` | 8-bit | Accumulator register |
| `3'd7` | Status register | 8-bit | `NV11DIZC` — standard 6502 status flags |

Narrower values (microinstruction, operation) are zero-extended to 8 bits.

### Status Register Encoding (sel=7)

| Bit | Flag | Description |
|-----|------|-------------|
| 7 | N | Negative |
| 6 | V | Overflow |
| 5 | 1 | (always 1) |
| 4 | 1 | (always 1) |
| 3 | D | Decimal mode |
| 2 | I | Interrupt disable |
| 1 | Z | Zero |
| 0 | C | Carry |

### Usage

Connect `o_debug_data` to logic analyser probes, GPIO pins, or an on-board LED bank to observe CPU internals in hardware without modifying the design.

The `mcu` wrapper passes the debug port through unchanged; instantiate with:

```systemverilog
mcu mcu (
    ...
    .i_debug_sel(my_sel),
    .o_debug_data(debug_out)
);
```

See the ULX3S target for an example wiring debug output to GPIO header pins with button-controlled selector cycling.

