from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import cocotb

# Reset vector location
RESET_VECTOR_LO = 0xFFFC
RESET_VECTOR_HI = 0xFFFD

# Status register bits
SR_C = 0  # Carry
SR_Z = 1  # Zero
SR_I = 2  # Interrupt disable
SR_D = 3  # Decimal
SR_B = 4  # Break
SR_V = 6  # Overflow
SR_N = 7  # Negative

# Opcodes
LDA_IMM = 0xA9
STA_ABS = 0x8D
NOP = 0xEA
JMP_ABS = 0x4C
INX = 0xE8
CLV = 0xB8

def lo(addr):
    return addr & 0xFF

def hi(addr):
    return (addr >> 8) & 0xFF

def get_acc(dut):
    return int(dut.cpu_6502.register_acc.value)

def get_x(dut):
    return int(dut.cpu_6502.register_x.value)

def get_y(dut):
    return int(dut.cpu_6502.register_y.value)

def get_sp(dut):
    return int(dut.cpu_6502.register_sp.value)

def get_pc(dut):
    return int(dut.cpu_6502.program_counter.value)

def get_sr(dut):
    n = int(dut.cpu_6502.status_negative.value)
    v = int(dut.cpu_6502.status_overflow.value)
    d = int(dut.cpu_6502.status_decimal.value)
    i = int(dut.cpu_6502.status_interrupt.value)
    z = int(dut.cpu_6502.status_zero.value)
    c = int(dut.cpu_6502.status_carry.value)
    return (n << 7) | (v << 6) | (1 << 5) | (0 << 4) | (d << 3) | (i << 2) | (z << 1) | c

def assert_acc(dut, expected):
    actual = get_acc(dut)
    assert actual == expected, f"ACC: expected {expected:#04x}, got {actual:#04x}"

def assert_x(dut, expected):
    actual = get_x(dut)
    assert actual == expected, f"X: expected {expected:#04x}, got {actual:#04x}"

def assert_pc(dut, expected):
    actual = get_pc(dut)
    assert actual == expected, f"PC: expected {expected:#06x}, got {actual:#06x}"

def assert_flag(dut, bit, expected, name=""):
    sr = get_sr(dut)
    actual = (sr >> bit) & 1
    assert actual == expected, \
        f"Flag {name}(bit {bit}): expected {expected}, got {actual} (SR={sr:#04x})"


async def setup_reset_test(dut, reset_vector, program, data=None, cycles=50):
    """
    Setup test with reset vector pointing to program location.

    Args:
        dut: Device under test
        reset_vector: 16-bit address to store in reset vector (0xFFFC/0xFFFD)
        program: List of bytes to write at reset_vector address
        data: Optional dict of addr->value for additional memory setup
        cycles: Number of cycles to run after init
    """
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1
    dut.i_so_n.value = 1

    # Hold reset low for 2 cycles
    await ClockCycles(dut.i_clk, 2)

    # Write reset vector
    dut.ram.mem[RESET_VECTOR_LO].value = lo(reset_vector)
    dut.ram.mem[RESET_VECTOR_HI].value = hi(reset_vector)

    # Write program at reset vector address
    for i, b in enumerate(program):
        dut.ram.mem[reset_vector + i].value = b

    # Write additional data if provided
    if data:
        for addr, val in data.items():
            dut.ram.mem[addr].value = val

    # Release reset
    dut.i_reset_n.value = 1

    # Wait for init sequence (6 cycles) + reset vector read (2 cycles)
    await ClockCycles(dut.i_clk, 8)

    # Run program
    await ClockCycles(dut.i_clk, cycles)


@cocotb.test()
async def test_reset_vector_basic(dut):
    """Reset vector: PC loads from 0xFFFC/0xFFFD after reset."""
    reset_addr = 0x8000
    prog = [
        LDA_IMM, 0x42,  # LDA #$42
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    # Verify PC is at reset_addr + program length
    assert_pc(dut, reset_addr + len(prog))
    # Verify instruction executed
    assert_acc(dut, 0x42)


@cocotb.test()
async def test_reset_vector_low_address(dut):
    """Reset vector: PC loads correctly for low address (0x0200)."""
    reset_addr = 0x0200
    prog = [
        LDA_IMM, 0xAB,  # LDA #$AB
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    assert_pc(dut, reset_addr + len(prog))
    assert_acc(dut, 0xAB)


@cocotb.test()
async def test_reset_vector_high_address(dut):
    """Reset vector: PC loads correctly for high address (0xF000)."""
    reset_addr = 0xF000
    prog = [
        LDA_IMM, 0xCD,  # LDA #$CD
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    assert_pc(dut, reset_addr + len(prog))
    assert_acc(dut, 0xCD)


@cocotb.test()
async def test_reset_vector_interrupt_flag_set(dut):
    """Reset: Interrupt disable flag (I) is set after reset."""
    reset_addr = 0x8000
    prog = [NOP, NOP]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    # I flag should be set after reset
    assert_flag(dut, SR_I, 1, "I")


@cocotb.test()
async def test_reset_vector_flags_cleared(dut):
    """Reset: N, V, D, Z, C flags are cleared after reset."""
    reset_addr = 0x8000
    prog = [NOP, NOP]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_D, 0, "D")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 0, "C")


@cocotb.test()
async def test_reset_vector_execution_continues(dut):
    """Reset vector: Execution continues normally after reset."""
    reset_addr = 0x8000
    prog = [
        LDA_IMM, 0x10,  # LDA #$10
        LDA_IMM, 0x20,  # LDA #$20 (overwrites)
        LDA_IMM, 0x30,  # LDA #$30 (overwrites)
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=8)

    assert_pc(dut, reset_addr + len(prog))
    assert_acc(dut, 0x30)


@cocotb.test()
async def test_reset_vector_with_store(dut):
    """Reset vector: Store operations work after reset."""
    reset_addr = 0x8000
    store_addr = 0x0300
    prog = [
        LDA_IMM, 0x55,           # LDA #$55
        STA_ABS, lo(store_addr), hi(store_addr),  # STA $0300
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=8)

    # Verify store worked
    stored = int(dut.ram.mem[store_addr].value)
    assert stored == 0x55, f"Memory at {store_addr:#06x}: expected 0x55, got {stored:#04x}"


@cocotb.test()
async def test_reset_vector_with_jump(dut):
    """Reset vector: JMP works correctly after reset."""
    reset_addr = 0x8000
    jump_target = 0x9000

    # Program at reset vector jumps to another location
    prog = [
        JMP_ABS, lo(jump_target), hi(jump_target),  # JMP $9000
    ]

    # Program at jump target
    target_prog = [
        LDA_IMM, 0x77,  # LDA #$77
        NOP,
    ]

    data = {}
    for i, b in enumerate(target_prog):
        data[jump_target + i] = b

    await setup_reset_test(dut, reset_addr, prog, data=data, cycles=8)

    # Verify we jumped and executed at new location
    assert_pc(dut, jump_target + len(target_prog))
    assert_acc(dut, 0x77)


@cocotb.test()
async def test_reset_vector_registers_zeroed(dut):
    """Reset: Registers A, X, Y are zeroed after reset."""
    reset_addr = 0x8000
    prog = [NOP, NOP]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    assert_acc(dut, 0x00)
    assert_x(dut, 0x00)
    assert get_y(dut) == 0x00, f"Y: expected 0x00, got {get_y(dut):#04x}"


@cocotb.test()
async def test_reset_vector_page_boundary(dut):
    """Reset vector: PC loads correctly when address crosses page boundary."""
    # Reset vector points to 0x10FF - instruction spans pages
    reset_addr = 0x10FF
    prog = [
        LDA_IMM, 0xEE,  # Opcode at 0x10FF, operand at 0x1100
        NOP,
    ]
    await setup_reset_test(dut, reset_addr, prog, cycles=4)

    assert_pc(dut, reset_addr + len(prog))
    assert_acc(dut, 0xEE)


@cocotb.test()
async def test_so_pin_sets_overflow_flag(dut):
    """SO pin: Falling edge on SO sets the V (overflow) flag."""
    reset_addr = 0x8000
    prog = [
        NOP,  # NOP - wait for SO trigger
        NOP,  # NOP - V flag should be set now
        CLV,  # CLV - clear overflow flag
        NOP,  # NOP - V flag should be clear now
    ]

    # Start with SO high
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1
    dut.i_so_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    # Write reset vector and program
    dut.ram.mem[RESET_VECTOR_LO].value = lo(reset_addr)
    dut.ram.mem[RESET_VECTOR_HI].value = hi(reset_addr)
    for i, b in enumerate(prog):
        dut.ram.mem[reset_addr + i].value = b

    # Release reset
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)  # Reset sequence

    # V flag should be clear initially
    assert_flag(dut, SR_V, 0, "V (before SO)")

    # Execute first NOP
    await ClockCycles(dut.i_clk, 2)

    # Trigger SO (falling edge: 1 -> 0)
    dut.i_so_n.value = 0
    await ClockCycles(dut.i_clk, 1)

    # Execute second NOP - V flag should now be set
    await ClockCycles(dut.i_clk, 2)
    assert_flag(dut, SR_V, 1, "V (after SO)")

    # Keep SO low - should not re-trigger (edge-triggered, not level)
    await ClockCycles(dut.i_clk, 1)
    assert_flag(dut, SR_V, 1, "V (SO held low)")

    # Execute CLV - clears V flag
    await ClockCycles(dut.i_clk, 2)
    assert_flag(dut, SR_V, 0, "V (after CLV)")

    # Execute final NOP - V should still be clear
    await ClockCycles(dut.i_clk, 2)
    assert_flag(dut, SR_V, 0, "V (final)")

    # Release SO back to high
    dut.i_so_n.value = 1
    await ClockCycles(dut.i_clk, 2)


@cocotb.test()
async def test_so_pin_edge_triggered(dut):
    """SO pin: Only falling edge triggers, not level."""
    reset_addr = 0x8000
    prog = [
        CLV,  # CLV - ensure V is clear
        NOP,  # NOP
        NOP,  # NOP
        NOP,  # NOP
    ]

    # Start with SO already low
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1
    dut.i_so_n.value = 0  # Start LOW (no edge yet)

    await ClockCycles(dut.i_clk, 2)

    # Write reset vector and program
    dut.ram.mem[RESET_VECTOR_LO].value = lo(reset_addr)
    dut.ram.mem[RESET_VECTOR_HI].value = hi(reset_addr)
    for i, b in enumerate(prog):
        dut.ram.mem[reset_addr + i].value = b

    # Release reset (SO still low)
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)  # Reset sequence

    # Execute CLV
    await ClockCycles(dut.i_clk, 2)

    # V should be clear - SO being low doesn't set it (no edge)
    assert_flag(dut, SR_V, 0, "V (SO held low, no edge)")

    # Execute NOPs - V should stay clear
    await ClockCycles(dut.i_clk, 4)
    assert_flag(dut, SR_V, 0, "V (still low)")

    # Now create a falling edge: high -> low
    dut.i_so_n.value = 1
    await ClockCycles(dut.i_clk, 2)
    dut.i_so_n.value = 0  # Falling edge
    await ClockCycles(dut.i_clk, 2)

    # NOW V should be set (edge detected)
    assert_flag(dut, SR_V, 1, "V (after falling edge)")
