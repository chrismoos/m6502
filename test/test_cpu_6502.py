from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
import cocotb
import utils

# ============================================================
# Constants
# ============================================================

START_PC = 0x0400

# Status register bits
SR_C = 0  # Carry
SR_Z = 1  # Zero
SR_I = 2  # Interrupt disable
SR_D = 3  # Decimal
SR_B = 4  # Break
SR_V = 6  # Overflow
SR_N = 7  # Negative

# --- Load/Store ---
LDA_IMM = 0xA9
LDA_ZP  = 0xA5
LDA_ZPX = 0xB5
LDA_ABS = 0xAD
LDA_ABX = 0xBD
LDA_ABY = 0xB9
LDA_IZX = 0xA1
LDA_IZY = 0xB1

LDX_IMM = 0xA2
LDX_ZP  = 0xA6
LDX_ZPY = 0xB6
LDX_ABS = 0xAE
LDX_ABY = 0xBE

LDY_IMM = 0xA0
LDY_ZP  = 0xA4
LDY_ZPX = 0xB4
LDY_ABS = 0xAC
LDY_ABX = 0xBC

STA_ZP  = 0x85
STA_ZPX = 0x95
STA_ABS = 0x8D
STA_ABX = 0x9D
STA_ABY = 0x99
STA_IZX = 0x81
STA_IZY = 0x91

STX_ZP  = 0x86
STX_ZPY = 0x96
STX_ABS = 0x8E

STY_ZP  = 0x84
STY_ZPX = 0x94
STY_ABS = 0x8C

# --- Transfer ---
TAX = 0xAA
TAY = 0xA8
TXA = 0x8A
TYA = 0x98
TSX = 0xBA
TXS = 0x9A

# --- Stack ---
PHA = 0x48
PHP = 0x08
PLA = 0x68
PLP = 0x28

# --- Arithmetic ---
ADC_IMM = 0x69
ADC_ZP  = 0x65
ADC_ZPX = 0x75
ADC_ABS = 0x6D
ADC_ABX = 0x7D
ADC_ABY = 0x79
ADC_IZX = 0x61
ADC_IZY = 0x71

SBC_IMM = 0xE9
SBC_ZP  = 0xE5
SBC_ZPX = 0xF5
SBC_ABS = 0xED
SBC_ABX = 0xFD
SBC_ABY = 0xF9
SBC_IZX = 0xE1
SBC_IZY = 0xF1

# --- Logical ---
AND_IMM = 0x29
AND_ZP  = 0x25
AND_ZPX = 0x35
AND_ABS = 0x2D
AND_ABX = 0x3D
AND_ABY = 0x39
AND_IZX = 0x21
AND_IZY = 0x31

ORA_IMM = 0x09
ORA_ZP  = 0x05
ORA_ZPX = 0x15
ORA_ABS = 0x0D
ORA_ABX = 0x1D
ORA_ABY = 0x19
ORA_IZX = 0x01
ORA_IZY = 0x11

EOR_IMM = 0x49
EOR_ZP  = 0x45
EOR_ZPX = 0x55
EOR_ABS = 0x4D
EOR_ABX = 0x5D
EOR_ABY = 0x59
EOR_IZX = 0x41
EOR_IZY = 0x51

# --- Shift/Rotate ---
ASL_A   = 0x0A
ASL_ZP  = 0x06
ASL_ZPX = 0x16
ASL_ABS = 0x0E
ASL_ABX = 0x1E

LSR_A   = 0x4A
LSR_ZP  = 0x46
LSR_ZPX = 0x56
LSR_ABS = 0x4E
LSR_ABX = 0x5E

ROL_A   = 0x2A
ROL_ZP  = 0x26
ROL_ZPX = 0x36
ROL_ABS = 0x2E
ROL_ABX = 0x3E

ROR_A   = 0x6A
ROR_ZP  = 0x66
ROR_ZPX = 0x76
ROR_ABS = 0x6E
ROR_ABX = 0x7E

# --- Increment/Decrement ---
INC_ZP  = 0xE6
INC_ZPX = 0xF6
INC_ABS = 0xEE
INC_ABX = 0xFE

DEC_ZP  = 0xC6
DEC_ZPX = 0xD6
DEC_ABS = 0xCE
DEC_ABX = 0xDE

INX = 0xE8
INY = 0xC8
DEX = 0xCA
DEY = 0x88

# --- Compare ---
CMP_IMM = 0xC9
CMP_ZP  = 0xC5
CMP_ZPX = 0xD5
CMP_ABS = 0xCD
CMP_ABX = 0xDD
CMP_ABY = 0xD9
CMP_IZX = 0xC1
CMP_IZY = 0xD1

CPX_IMM = 0xE0
CPX_ZP  = 0xE4
CPX_ABS = 0xEC

CPY_IMM = 0xC0
CPY_ZP  = 0xC4
CPY_ABS = 0xCC

BIT_ZP  = 0x24
BIT_ABS = 0x2C

# --- Branch ---
BCC = 0x90
BCS = 0xB0
BEQ = 0xF0
BMI = 0x30
BNE = 0xD0
BPL = 0x10
BVC = 0x50
BVS = 0x70

# --- Jump ---
JMP_ABS = 0x4C
JMP_IND = 0x6C
JSR_ABS = 0x20
RTS_IMP = 0x60

# --- Flag ---
CLC = 0x18
SEC = 0x38
CLD = 0xD8
SED = 0xF8
CLI = 0x58
SEI = 0x78
CLV = 0xB8

# --- System ---
BRK = 0x00
RTI = 0x40
NOP = 0xEA

# ============================================================
# Instruction Test Plan
# ============================================================
# [x] ADC - Add with Carry (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] SBC - Subtract with Carry (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] AND - Logical AND (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] ORA - Logical OR (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] EOR - Exclusive OR (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] ASL - Arithmetic Shift Left (acc, zp, zpx, abs, abx)
# [x] LSR - Logical Shift Right (acc, zp, zpx, abs, abx)
# [x] ROL - Rotate Left (acc, zp, zpx, abs, abx)
# [x] ROR - Rotate Right (acc, zp, zpx, abs, abx)
# [x] LDA - Load Accumulator (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] LDX - Load X (imm, zp, zpy, abs, aby)
# [x] LDY - Load Y (imm, zp, zpx, abs, abx)
# [x] STA - Store Accumulator (zp, zpx, abs, abx, aby, izx, izy)
# [x] STX - Store X (zp, zpy, abs)
# [x] STY - Store Y (zp, zpx, abs)
# [x] TAX, TAY, TXA, TYA, TSX, TXS
# [x] PHA, PHP, PLA, PLP
# [x] INC - Increment Memory (zp, zpx, abs, abx)
# [x] DEC - Decrement Memory (zp, zpx, abs, abx)
# [x] INX, INY, DEX, DEY
# [x] CMP - Compare Accumulator (imm, zp, zpx, abs, abx, aby, izx, izy)
# [x] CPX - Compare X (imm, zp, abs)
# [x] CPY - Compare Y (imm, zp, abs)
# [x] BIT - Bit Test (zp, abs)
# [x] BCC, BCS, BEQ, BMI, BNE, BPL, BVC, BVS
# [x] JMP - Jump (abs, ind)
# [x] JSR - Jump to Subroutine (abs)
# [x] RTS - Return from Subroutine
# [x] CLC, SEC, CLD, SED, CLI, SEI, CLV
# [x] BRK - Break
# [x] RTI - Return from Interrupt
# [x] NOP - No Operation

# ============================================================
# Helpers
# ============================================================

def lo(addr):
    """Low byte of 16-bit address."""
    return addr & 0xFF

def hi(addr):
    """High byte of 16-bit address."""
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

def assert_y(dut, expected):
    actual = get_y(dut)
    assert actual == expected, f"Y: expected {expected:#04x}, got {actual:#04x}"

def assert_sp(dut, expected):
    actual = get_sp(dut)
    assert actual == expected, f"SP: expected {expected:#04x}, got {actual:#04x}"

def assert_pc(dut, expected):
    actual = get_pc(dut)
    assert actual == expected, f"PC: expected {expected:#06x}, got {actual:#06x}"

def assert_flag(dut, bit, expected, name=""):
    sr = get_sr(dut)
    actual = (sr >> bit) & 1
    assert actual == expected, \
        f"Flag {name}(bit {bit}): expected {expected}, got {actual} (SR={sr:#04x})"

def assert_nz(dut, value):
    """Assert N and Z flags match an 8-bit result value."""
    assert_flag(dut, SR_N, 1 if (value & 0x80) else 0, "N")
    assert_flag(dut, SR_Z, 1 if (value & 0xFF) == 0 else 0, "Z")

async def read_mem(dut, addr):
    return int(dut.ram.mem[addr].value)

async def setup_and_run(dut, program, zp_data=None, data=None, cycles=50):
    """
    Reset CPU, write program at START_PC, optionally write data to memory,
    release reset, run for N cycles.
    """
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    # hold reset low for 2 cycles
    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(program):
        dut.ram.mem[START_PC + i].value = b

    if zp_data:
        for addr, val in zp_data.items():
            dut.ram.mem[addr].value = val

    if data:
        for addr, val in data.items():
            dut.ram.mem[addr].value = val


    # wait for system init (6 cycles)
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 2)
    await ClockCycles(dut.i_clk, 6)

    await ClockCycles(dut.i_clk, cycles)


# ============================================================
# ADC - Add with Carry
# A = A + M + C
# Flags: N, V, Z, C
# ============================================================

# --- Immediate ---

@cocotb.test()
async def test_adc_imm_basic(dut):
    """ADC immediate: 0x10 + 0x20 = 0x30, no flags."""
    prog = [
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IMM, 0x20,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_adc_imm_zero(dut):
    """ADC immediate: 0x00 + 0x00 = 0x00, Z=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        ADC_IMM, 0x00,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_adc_imm_negative(dut):
    """ADC immediate: 0x00 + 0x80 = 0x80, N=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        ADC_IMM, 0x80,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x80)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_adc_imm_carry_out(dut):
    """ADC immediate: 0xFF + 0x01 = 0x00, C=1, Z=1."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        ADC_IMM, 0x01,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_adc_imm_carry_in(dut):
    """ADC immediate with carry in: 0x10 + 0x20 + C = 0x31."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IMM, 0x20,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x31)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_adc_imm_overflow_positive(dut):
    """ADC immediate signed overflow: 0x50 + 0x50 = 0xA0, V=1, N=1."""
    prog = [
        LDA_IMM, 0x50,      # 2 cycles
        ADC_IMM, 0x50,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xA0)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 1, "V")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_adc_imm_overflow_negative(dut):
    """ADC immediate signed overflow: 0xD0 + 0x90 = 0x60, V=1, C=1."""
    prog = [
        LDA_IMM, 0xD0,      # 2 cycles
        ADC_IMM, 0x90,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x60)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 1, "V")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_adc_imm_no_overflow(dut):
    """ADC immediate no overflow: 0x01 + 0xFF = 0x00, C=1, V=0, Z=1."""
    prog = [
        LDA_IMM, 0x01,      # 2 cycles
        ADC_IMM, 0xFF,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

# --- Zero Page ---

@cocotb.test()
async def test_adc_zp(dut):
    """ADC zero page: A + mem[0x10] = 0x10 + 0x20 = 0x30."""
    prog = [
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x20}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_zp_carry_out(dut):
    """ADC zero page with carry out: 0x80 + 0x90 = 0x10, C=1, V=1."""
    prog = [
        LDA_IMM, 0x80,      # 2 cycles
        ADC_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x90}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x10)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 1, "V")
    assert_nz(dut, 0x10)

# --- Zero Page,X ---

@cocotb.test()
async def test_adc_zpx(dut):
    """ADC zero page,X: A + mem[0x10 + X] where X=5, mem[0x15]=0x20."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x20}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_zpx_wrap(dut):
    """ADC zero page,X wraps within zero page: base=0xF0, X=0x20 -> addr=0x10."""
    prog = [
        LDX_IMM, 0x20,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ZPX, 0xF0,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x25}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x35)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x35)

# --- Absolute ---

@cocotb.test()
async def test_adc_abs(dut):
    """ADC absolute: A + mem[0x0300] = 0x10 + 0x20 = 0x30."""
    prog = [
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x20}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_abs_carry_out(dut):
    """ADC absolute with carry out."""
    prog = [
        LDA_IMM, 0xFE,      # 2 cycles
        ADC_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x03}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x01)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x01)

# --- Absolute,X ---

@cocotb.test()
async def test_adc_abx(dut):
    """ADC absolute,X: A + mem[0x0300 + X] where X=4."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ABX, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x20}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_abx_page_cross(dut):
    """ADC absolute,X crossing page boundary: base=0x02FE, X=5 -> 0x0303."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ABX, 0xFE, 0x02,  # 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x20}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x30)

# --- Absolute,Y ---

@cocotb.test()
async def test_adc_aby(dut):
    """ADC absolute,Y: A + mem[0x0300 + Y] where Y=3."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ABY, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x20}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_aby_page_cross(dut):
    """ADC absolute,Y crossing page boundary: base=0x02FF, Y=2 -> 0x0301."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_ABY, 0xFF, 0x02,  # 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0301: 0x20}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x30)

# --- (Indirect,X) ---

@cocotb.test()
async def test_adc_izx(dut):
    """ADC (indirect,X): pointer at zp[(0x50+X) mod 256], X=2 -> zp[0x52]=0x0300."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog,
        zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x20}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_izx_wrap(dut):
    """ADC (indirect,X) with zero page wrap: base=0xFF, X=1 -> ptr at zp[0x00]."""
    prog = [
        LDX_IMM, 0x01,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IZX, 0xFF,      # 6 cycles
    ]
    await setup_and_run(dut, prog,
        zp_data={0x00: 0x00, 0x01: 0x03}, data={0x0300: 0x20}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x30)

# --- (Indirect),Y ---

@cocotb.test()
async def test_adc_izy(dut):
    """ADC (indirect),Y: pointer at zp[0x50]=0x0300, Y=3 -> addr=0x0303."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog,
        zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x20}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x30)

@cocotb.test()
async def test_adc_izy_page_cross(dut):
    """ADC (indirect),Y crossing page: ptr=0x02FF, Y=2 -> addr=0x0301."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        ADC_IZY, 0x50,      # 6 cycles (page cross)
    ]
    await setup_and_run(dut, prog,
        zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0x20}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x30)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x30)


# ============================================================
# LDA - Load Accumulator
# A = M
# Flags: N, Z
# ============================================================

# --- Immediate ---

@cocotb.test()
async def test_lda_imm_basic(dut):
    """LDA immediate: A = 0x42."""
    prog = [LDA_IMM, 0x42]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_lda_imm_zero(dut):
    """LDA immediate: A = 0x00, Z=1."""
    prog = [LDA_IMM, 0x00]
    await setup_and_run(dut, prog, cycles=2)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_lda_imm_negative(dut):
    """LDA immediate: A = 0x80, N=1."""
    prog = [LDA_IMM, 0x80]
    await setup_and_run(dut, prog, cycles=2)
    assert_acc(dut, 0x80)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_lda_imm_ff(dut):
    """LDA immediate: A = 0xFF, N=1."""
    prog = [LDA_IMM, 0xFF]
    await setup_and_run(dut, prog, cycles=2)
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

# --- Zero Page ---

@cocotb.test()
async def test_lda_zp(dut):
    """LDA zero page: A = mem[0x10]."""
    prog = [LDA_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x37}, cycles=3)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x37)
    assert_nz(dut, 0x37)

@cocotb.test()
async def test_lda_zp_zero(dut):
    """LDA zero page: A = 0x00, Z=1."""
    prog = [LDA_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x00}, cycles=3)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_lda_zp_negative(dut):
    """LDA zero page: A = 0xFE, N=1."""
    prog = [LDA_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0xFE}, cycles=3)
    assert_acc(dut, 0xFE)
    assert_nz(dut, 0xFE)

# --- Zero Page,X ---

@cocotb.test()
async def test_lda_zpx(dut):
    """LDA zero page,X: A = mem[(0x10 + X) & 0xFF], X=5."""
    prog = [LDX_IMM, 0x05, LDA_ZPX, 0x10]
    await setup_and_run(dut, prog, zp_data={0x15: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_lda_zpx_wrap(dut):
    """LDA zero page,X wraps: base=0xF0, X=0x20 -> addr=0x10."""
    prog = [LDX_IMM, 0x20, LDA_ZPX, 0xF0]
    await setup_and_run(dut, prog, zp_data={0x10: 0x77}, cycles=6)
    assert_acc(dut, 0x77)
    assert_nz(dut, 0x77)

# --- Absolute ---

@cocotb.test()
async def test_lda_abs(dut):
    """LDA absolute: A = mem[0x0300]."""
    prog = [LDA_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x55}, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x55)
    assert_nz(dut, 0x55)

@cocotb.test()
async def test_lda_abs_zero(dut):
    """LDA absolute: A = 0x00, Z=1."""
    prog = [LDA_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x00}, cycles=4)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

# --- Absolute,X ---

@cocotb.test()
async def test_lda_abx(dut):
    """LDA absolute,X: A = mem[0x0300 + X], X=4."""
    prog = [LDX_IMM, 0x04, LDA_ABX, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0304: 0x66}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x66)
    assert_nz(dut, 0x66)

@cocotb.test()
async def test_lda_abx_page_cross(dut):
    """LDA absolute,X page cross: base=0x02FE, X=5 -> 0x0303, +1 cycle."""
    prog = [LDX_IMM, 0x05, LDA_ABX, 0xFE, 0x02]
    await setup_and_run(dut, prog, data={0x0303: 0x88}, cycles=7)
    assert_acc(dut, 0x88)
    assert_nz(dut, 0x88)

# --- Absolute,Y ---

@cocotb.test()
async def test_lda_aby(dut):
    """LDA absolute,Y: A = mem[0x0300 + Y], Y=3."""
    prog = [LDY_IMM, 0x03, LDA_ABY, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0303: 0x99}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x99)
    assert_nz(dut, 0x99)

@cocotb.test()
async def test_lda_aby_page_cross(dut):
    """LDA absolute,Y page cross: base=0x02FF, Y=2 -> 0x0301, +1 cycle."""
    prog = [LDY_IMM, 0x02, LDA_ABY, 0xFF, 0x02]
    await setup_and_run(dut, prog, data={0x0301: 0xAA}, cycles=7)
    assert_acc(dut, 0xAA)
    assert_nz(dut, 0xAA)

# --- (Indirect,X) ---

@cocotb.test()
async def test_lda_izx(dut):
    """LDA (indirect,X): ptr at zp[(0x50+X)&0xFF], X=2 -> zp[0x52]=0x0300."""
    prog = [LDX_IMM, 0x02, LDA_IZX, 0x50]
    await setup_and_run(dut, prog,
        zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0xBB}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xBB)
    assert_nz(dut, 0xBB)

@cocotb.test()
async def test_lda_izx_wrap(dut):
    """LDA (indirect,X) wrap: base=0xFF, X=1 -> ptr at zp[0x00]."""
    prog = [LDX_IMM, 0x01, LDA_IZX, 0xFF]
    await setup_and_run(dut, prog,
        zp_data={0x00: 0x00, 0x01: 0x03}, data={0x0300: 0xCC}, cycles=8)
    assert_acc(dut, 0xCC)
    assert_nz(dut, 0xCC)

# --- (Indirect),Y ---

@cocotb.test()
async def test_lda_izy(dut):
    """LDA (indirect),Y: ptr at zp[0x50]=0x0300, Y=3 -> addr=0x0303."""
    prog = [LDY_IMM, 0x03, LDA_IZY, 0x50]
    await setup_and_run(dut, prog,
        zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0xDD}, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xDD)
    assert_nz(dut, 0xDD)

@cocotb.test()
async def test_lda_izy_page_cross(dut):
    """LDA (indirect),Y page cross: ptr=0x02FF, Y=2 -> addr=0x0301, +1 cycle."""
    prog = [LDY_IMM, 0x02, LDA_IZY, 0x50]
    await setup_and_run(dut, prog,
        zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0xEE}, cycles=8)
    assert_acc(dut, 0xEE)
    assert_nz(dut, 0xEE)


# ============================================================
# LDX - Load X Register
# X = M
# Flags: N, Z
# ============================================================

# --- Immediate ---

@cocotb.test()
async def test_ldx_imm_basic(dut):
    """LDX immediate: X = 0x42."""
    prog = [LDX_IMM, 0x42]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_ldx_imm_zero(dut):
    """LDX immediate: X = 0x00, Z=1."""
    prog = [LDX_IMM, 0x00]
    await setup_and_run(dut, prog, cycles=2)
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_ldx_imm_negative(dut):
    """LDX immediate: X = 0x80, N=1."""
    prog = [LDX_IMM, 0x80]
    await setup_and_run(dut, prog, cycles=2)
    assert_x(dut, 0x80)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_ldx_imm_ff(dut):
    """LDX immediate: X = 0xFF, N=1."""
    prog = [LDX_IMM, 0xFF]
    await setup_and_run(dut, prog, cycles=2)
    assert_x(dut, 0xFF)
    assert_nz(dut, 0xFF)

# --- Zero Page ---

@cocotb.test()
async def test_ldx_zp(dut):
    """LDX zero page: X = mem[0x10]."""
    prog = [LDX_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x37}, cycles=3)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x37)
    assert_nz(dut, 0x37)

@cocotb.test()
async def test_ldx_zp_zero(dut):
    """LDX zero page: X = 0x00, Z=1."""
    prog = [LDX_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x00}, cycles=3)
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_ldx_zp_negative(dut):
    """LDX zero page: X = 0xFE, N=1."""
    prog = [LDX_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0xFE}, cycles=3)
    assert_x(dut, 0xFE)
    assert_nz(dut, 0xFE)

# --- Zero Page,Y ---

@cocotb.test()
async def test_ldx_zpy(dut):
    """LDX zero page,Y: X = mem[(0x10 + Y) & 0xFF], Y=5."""
    prog = [LDY_IMM, 0x05, LDX_ZPY, 0x10]
    await setup_and_run(dut, prog, zp_data={0x15: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_ldx_zpy_wrap(dut):
    """LDX zero page,Y wraps: base=0xF0, Y=0x20 -> addr=0x10."""
    prog = [LDY_IMM, 0x20, LDX_ZPY, 0xF0]
    await setup_and_run(dut, prog, zp_data={0x10: 0x77}, cycles=6)
    assert_x(dut, 0x77)
    assert_nz(dut, 0x77)

# --- Absolute ---

@cocotb.test()
async def test_ldx_abs(dut):
    """LDX absolute: X = mem[0x0300]."""
    prog = [LDX_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x55}, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x55)
    assert_nz(dut, 0x55)

@cocotb.test()
async def test_ldx_abs_zero(dut):
    """LDX absolute: X = 0x00, Z=1."""
    prog = [LDX_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x00}, cycles=4)
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

# --- Absolute,Y ---

@cocotb.test()
async def test_ldx_aby(dut):
    """LDX absolute,Y: X = mem[0x0300 + Y], Y=3."""
    prog = [LDY_IMM, 0x03, LDX_ABY, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0303: 0x99}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x99)
    assert_nz(dut, 0x99)

@cocotb.test()
async def test_ldx_aby_page_cross(dut):
    """LDX absolute,Y page cross: base=0x02FF, Y=2 -> 0x0301, +1 cycle."""
    prog = [LDY_IMM, 0x02, LDX_ABY, 0xFF, 0x02]
    await setup_and_run(dut, prog, data={0x0301: 0xAA}, cycles=7)
    assert_x(dut, 0xAA)
    assert_nz(dut, 0xAA)


# ============================================================
# LDY - Load Y Register
# Y = M
# Flags: N, Z
# ============================================================

# --- Immediate ---

@cocotb.test()
async def test_ldy_imm_basic(dut):
    """LDY immediate: Y = 0x42."""
    prog = [LDY_IMM, 0x42]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_ldy_imm_zero(dut):
    """LDY immediate: Y = 0x00, Z=1."""
    prog = [LDY_IMM, 0x00]
    await setup_and_run(dut, prog, cycles=2)
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_ldy_imm_clears_zero_flag(dut):
    """LDY immediate must clear Z flag when loading non-zero value.

    This tests the scenario from the functional test:
    DEX sets Z=1 (when X becomes 0), then LDY #5 should clear Z=0.

    Regression test: ensures flags are updated after bus data is valid
    (flags update on negedge, registers on posedge).
    """
    prog = [
        LDX_IMM, 0x01,       # 2 cycles - X=1, Z=0
        DEX,                  # 2 cycles - X=0, Z=1
        LDY_IMM, 0x05,       # 2 cycles - Y=5, Z should be 0
        BNE, 0x01,           # 3 cycles if taken (skip trap), 2 if not
        NOP,                  # trap - BNE should skip this
        NOP,                  # landing zone
    ]
    # LDX(2) + DEX(2) + LDY(2) + BNE_taken(3) + NOP(2) = 11 cycles
    await setup_and_run(dut, prog, cycles=11)
    assert_x(dut, 0x00)
    assert_y(dut, 0x05)
    assert_flag(dut, SR_Z, 0, "Z")  # Z must be cleared by LDY #5
    # PC should be at the second NOP (BNE skipped the first NOP)
    assert_pc(dut, START_PC + 8 + 1)

@cocotb.test()
async def test_ldy_imm_negative(dut):
    """LDY immediate: Y = 0x80, N=1."""
    prog = [LDY_IMM, 0x80]
    await setup_and_run(dut, prog, cycles=2)
    assert_y(dut, 0x80)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_ldy_imm_ff(dut):
    """LDY immediate: Y = 0xFF, N=1."""
    prog = [LDY_IMM, 0xFF]
    await setup_and_run(dut, prog, cycles=2)
    assert_y(dut, 0xFF)
    assert_nz(dut, 0xFF)

# --- Zero Page ---

@cocotb.test()
async def test_ldy_zp(dut):
    """LDY zero page: Y = mem[0x10]."""
    prog = [LDY_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x37}, cycles=3)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x37)
    assert_nz(dut, 0x37)

@cocotb.test()
async def test_ldy_zp_zero(dut):
    """LDY zero page: Y = 0x00, Z=1."""
    prog = [LDY_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0x00}, cycles=3)
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_ldy_zp_negative(dut):
    """LDY zero page: Y = 0xFE, N=1."""
    prog = [LDY_ZP, 0x10]
    await setup_and_run(dut, prog, zp_data={0x10: 0xFE}, cycles=3)
    assert_y(dut, 0xFE)
    assert_nz(dut, 0xFE)

# --- Zero Page,X ---

@cocotb.test()
async def test_ldy_zpx(dut):
    """LDY zero page,X: Y = mem[(0x10 + X) & 0xFF], X=5."""
    prog = [LDX_IMM, 0x05, LDY_ZPX, 0x10]
    await setup_and_run(dut, prog, zp_data={0x15: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_ldy_zpx_wrap(dut):
    """LDY zero page,X wraps: base=0xF0, X=0x20 -> addr=0x10."""
    prog = [LDX_IMM, 0x20, LDY_ZPX, 0xF0]
    await setup_and_run(dut, prog, zp_data={0x10: 0x77}, cycles=6)
    assert_y(dut, 0x77)
    assert_nz(dut, 0x77)

# --- Absolute ---

@cocotb.test()
async def test_ldy_abs(dut):
    """LDY absolute: Y = mem[0x0300]."""
    prog = [LDY_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x55}, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x55)
    assert_nz(dut, 0x55)

@cocotb.test()
async def test_ldy_abs_zero(dut):
    """LDY absolute: Y = 0x00, Z=1."""
    prog = [LDY_ABS, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0300: 0x00}, cycles=4)
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

# --- Absolute,X ---

@cocotb.test()
async def test_ldy_abx(dut):
    """LDY absolute,X: Y = mem[0x0300 + X], X=4."""
    prog = [LDX_IMM, 0x04, LDY_ABX, 0x00, 0x03]
    await setup_and_run(dut, prog, data={0x0304: 0x66}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x66)
    assert_nz(dut, 0x66)

@cocotb.test()
async def test_ldy_abx_page_cross(dut):
    """LDY absolute,X page cross: base=0x02FE, X=5 -> 0x0303, +1 cycle."""
    prog = [LDX_IMM, 0x05, LDY_ABX, 0xFE, 0x02]
    await setup_and_run(dut, prog, data={0x0303: 0x88}, cycles=7)
    assert_y(dut, 0x88)
    assert_nz(dut, 0x88)


# ── SBC Tests ────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_sbc_imm_basic(dut):
    """SBC immediate: SEC, A=$50 - $10 = $40, C=1, V=0, N=0, Z=0."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_IMM, 0x10,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_imm_zero(dut):
    """SBC immediate: SEC, A=$10 - $10 = $00, C=1, Z=1."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        SBC_IMM, 0x10,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_sbc_imm_borrow(dut):
    """SBC immediate: SEC, A=$10 - $20 = $F0, C=0, N=1."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x10,      # 2 cycles
        SBC_IMM, 0x20,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_sbc_imm_overflow(dut):
    """SBC immediate: SEC, A=$50 - $B0 = $A0, V=1, C=0, N=1."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_IMM, 0xB0,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xA0)
    assert_flag(dut, SR_V, 1, "V")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_sbc_zp(dut):
    """SBC zero page: SEC, A=$50 - mem[$10]=$10 = $40."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x10}, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_zpx(dut):
    """SBC zero page,X: LDX #$05, SEC, A=$50 - mem[$15]=$10 = $40."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x10}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_abs(dut):
    """SBC absolute: SEC, A=$50 - mem[$0300]=$10 = $40."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ABS, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x10}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_abx(dut):
    """SBC absolute,X: LDX #$04, SEC, A=$50 - mem[$0304]=$10 = $40."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ABX, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x10}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_abx_page_cross(dut):
    """SBC absolute,X with page crossing: LDX #$05, SEC, A=$50 - mem[$0303]=$10 = $40."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ABX, 0xFE, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x10}, cycles=11)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_aby(dut):
    """SBC absolute,Y: LDY #$03, SEC, A=$50 - mem[$0303]=$10 = $40."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ABY, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x10}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_aby_page_cross(dut):
    """SBC absolute,Y with page crossing: LDY #$02, SEC, A=$50 - mem[$0301]=$10 = $40."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_ABY, 0xFF, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0301: 0x10}, cycles=11)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_izx(dut):
    """SBC (indirect,X): LDX #$02, SEC, A=$50 - mem[$0300]=$10 = $40."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x10}, cycles=12)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_izy(dut):
    """SBC (indirect),Y: LDY #$03, SEC, A=$50 - mem[$0303]=$10 = $40."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x10}, cycles=11)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)

@cocotb.test()
async def test_sbc_izy_page_cross(dut):
    """SBC (indirect),Y with page crossing: LDY #$02, SEC, A=$50 - mem[$0301]=$10 = $40."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        SEC,                 # 2 cycles
        LDA_IMM, 0x50,      # 2 cycles
        SBC_IZY, 0x50,      # 6 cycles (page cross)
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0x10}, cycles=12)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x40)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_V, 0, "V")
    assert_nz(dut, 0x40)


# ── AND Tests ────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_and_imm_basic(dut):
    """AND immediate: A=$FF & $0F = $0F."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        AND_IMM, 0x0F,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_imm_zero(dut):
    """AND immediate: A=$F0 & $0F = $00, Z=1."""
    prog = [
        LDA_IMM, 0xF0,      # 2 cycles
        AND_IMM, 0x0F,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_and_imm_negative(dut):
    """AND immediate: A=$FF & $80 = $80, N=1."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        AND_IMM, 0x80,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x80)
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_and_zp(dut):
    """AND zero page: A=$FF & mem[$10]=$0F = $0F."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x0F}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_zpx(dut):
    """AND zero page,X: LDX #$05, A=$FF & mem[$15]=$0F = $0F."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_abs(dut):
    """AND absolute: A=$FF & mem[$0300]=$0F = $0F."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ABS, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x0F}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_abx(dut):
    """AND absolute,X: LDX #$04, A=$FF & mem[$0304]=$0F = $0F."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ABX, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_abx_page_cross(dut):
    """AND absolute,X with page crossing: LDX #$05, A=$FF & mem[$0303]=$0F = $0F."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ABX, 0xFE, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_aby(dut):
    """AND absolute,Y: LDY #$03, A=$FF & mem[$0303]=$0F = $0F."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ABY, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_aby_page_cross(dut):
    """AND absolute,Y with page crossing: LDY #$02, A=$FF & mem[$0301]=$0F = $0F."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_ABY, 0xFF, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0301: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_izx(dut):
    """AND (indirect,X): LDX #$02, A=$FF & mem[$0300]=$0F = $0F."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_izy(dut):
    """AND (indirect),Y: LDY #$03, A=$FF & mem[$0303]=$0F = $0F."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)

@cocotb.test()
async def test_and_izy_page_cross(dut):
    """AND (indirect),Y with page crossing: LDY #$02, A=$FF & mem[$0301]=$0F = $0F."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        AND_IZY, 0x50,      # 6 cycles (page cross)
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x0F)
    assert_nz(dut, 0x0F)


# ── ORA Tests ────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_ora_imm_basic(dut):
    """ORA immediate: A=$F0 | $0F = $FF, N=1."""
    prog = [
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_IMM, 0x0F,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_ora_imm_zero(dut):
    """ORA immediate: A=$00 | $00 = $00, Z=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        ORA_IMM, 0x00,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_ora_zp(dut):
    """ORA zero page: A=$F0 | mem[$10]=$0F = $FF."""
    prog = [
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x0F}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_zpx(dut):
    """ORA zero page,X: LDX #$05, A=$F0 | mem[$15]=$0F = $FF."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_abs(dut):
    """ORA absolute: A=$F0 | mem[$0300]=$0F = $FF."""
    prog = [
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ABS, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x0F}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_abx(dut):
    """ORA absolute,X: LDX #$04, A=$F0 | mem[$0304]=$0F = $FF."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ABX, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_abx_page_cross(dut):
    """ORA absolute,X with page crossing: LDX #$05, A=$F0 | mem[$0303]=$0F = $FF."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ABX, 0xFE, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_aby(dut):
    """ORA absolute,Y: LDY #$03, A=$F0 | mem[$0303]=$0F = $FF."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ABY, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_aby_page_cross(dut):
    """ORA absolute,Y with page crossing: LDY #$02, A=$F0 | mem[$0301]=$0F = $FF."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_ABY, 0xFF, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0301: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_izx(dut):
    """ORA (indirect,X): LDX #$02, A=$F0 | mem[$0300]=$0F = $FF."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_izy(dut):
    """ORA (indirect),Y: LDY #$03, A=$F0 | mem[$0303]=$0F = $FF."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)

@cocotb.test()
async def test_ora_izy_page_cross(dut):
    """ORA (indirect),Y with page crossing: LDY #$02, A=$F0 | mem[$0301]=$0F = $FF."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xF0,      # 2 cycles
        ORA_IZY, 0x50,      # 6 cycles (page cross)
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xFF)
    assert_nz(dut, 0xFF)


# ── EOR Tests ────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_eor_imm_basic(dut):
    """EOR immediate: A=$FF ^ $0F = $F0, N=1."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_IMM, 0x0F,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_eor_imm_zero(dut):
    """EOR immediate: A=$AA ^ $AA = $00, Z=1."""
    prog = [
        LDA_IMM, 0xAA,      # 2 cycles
        EOR_IMM, 0xAA,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_eor_zp(dut):
    """EOR zero page: A=$FF ^ mem[$10]=$0F = $F0."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x0F}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_zpx(dut):
    """EOR zero page,X: LDX #$05, A=$FF ^ mem[$15]=$0F = $F0."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_abs(dut):
    """EOR absolute: A=$FF ^ mem[$0300]=$0F = $F0."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ABS, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x0F}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_abx(dut):
    """EOR absolute,X: LDX #$04, A=$FF ^ mem[$0304]=$0F = $F0."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ABX, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_abx_page_cross(dut):
    """EOR absolute,X with page crossing: LDX #$05, A=$FF ^ mem[$0303]=$0F = $F0."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ABX, 0xFE, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_aby(dut):
    """EOR absolute,Y: LDY #$03, A=$FF ^ mem[$0303]=$0F = $F0."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ABY, 0x00, 0x03,# 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x0F}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_aby_page_cross(dut):
    """EOR absolute,Y with page crossing: LDY #$02, A=$FF ^ mem[$0301]=$0F = $F0."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_ABY, 0xFF, 0x02,# 5 cycles (page cross)
    ]
    await setup_and_run(dut, prog, data={0x0301: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_izx(dut):
    """EOR (indirect,X): LDX #$02, A=$FF ^ mem[$0300]=$0F = $F0."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_izy(dut):
    """EOR (indirect),Y: LDY #$03, A=$FF ^ mem[$0303]=$0F = $F0."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x0F}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)

@cocotb.test()
async def test_eor_izy_page_cross(dut):
    """EOR (indirect),Y with page crossing: LDY #$02, A=$FF ^ mem[$0301]=$0F = $F0."""
    prog = [
        LDY_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        EOR_IZY, 0x50,      # 6 cycles (page cross)
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0xFF, 0x51: 0x02}, data={0x0301: 0x0F}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xF0)
    assert_nz(dut, 0xF0)


# ============================================================================
# ASL - Arithmetic Shift Left
# ============================================================================

@cocotb.test()
async def test_asl_acc_basic(dut):
    """ASL accumulator: $01 << 1 = $02, C=0."""
    prog = [
        LDA_IMM, 0x01,      # 2 cycles
        ASL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x02)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_asl_acc_carry(dut):
    """ASL accumulator: $80 << 1 = $00, C=1, Z=1."""
    prog = [
        LDA_IMM, 0x80,      # 2 cycles
        ASL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")


@cocotb.test()
async def test_asl_acc_negative(dut):
    """ASL accumulator: $40 << 1 = $80, N=1, C=0."""
    prog = [
        LDA_IMM, 0x40,      # 2 cycles
        ASL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x80)
    assert_flag(dut, SR_N, 1, "N")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_asl_zp(dut):
    """ASL zero page: mem[$10] $01 << 1 = $02."""
    prog = [
        ASL_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x01}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x02, f"Expected mem[$10]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_asl_zpx(dut):
    """ASL zero page,X: mem[$15] $01 << 1 = $02."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        ASL_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x01}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x02, f"Expected mem[$15]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_asl_abs(dut):
    """ASL absolute: mem[$0300] $01 << 1 = $02."""
    prog = [
        ASL_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x01}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x02, f"Expected mem[$0300]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_asl_abx(dut):
    """ASL absolute,X: mem[$0304] $01 << 1 = $02."""
    prog = [
        LDX_IMM, 0x04,        # 2 cycles
        ASL_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x01}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x02, f"Expected mem[$0304]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


# ============================================================================
# LSR - Logical Shift Right
# ============================================================================

@cocotb.test()
async def test_lsr_acc_basic(dut):
    """LSR accumulator: $02 >> 1 = $01, C=0."""
    prog = [
        LDA_IMM, 0x02,      # 2 cycles
        LSR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x01)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_lsr_acc_carry(dut):
    """LSR accumulator: $01 >> 1 = $00, C=1, Z=1."""
    prog = [
        LDA_IMM, 0x01,      # 2 cycles
        LSR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")


@cocotb.test()
async def test_lsr_acc_no_negative(dut):
    """LSR accumulator: $FE >> 1 = $7F, N=0, C=0."""
    prog = [
        LDA_IMM, 0xFE,      # 2 cycles
        LSR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x7F)
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_lsr_zp(dut):
    """LSR zero page: mem[$10] $02 >> 1 = $01."""
    prog = [
        LSR_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x02}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x01, f"Expected mem[$10]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_lsr_zpx(dut):
    """LSR zero page,X: mem[$15] $02 >> 1 = $01."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LSR_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x02}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x01, f"Expected mem[$15]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_lsr_abs(dut):
    """LSR absolute: mem[$0300] $02 >> 1 = $01."""
    prog = [
        LSR_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x02}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x01, f"Expected mem[$0300]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_lsr_abx(dut):
    """LSR absolute,X: mem[$0304] $02 >> 1 = $01."""
    prog = [
        LDX_IMM, 0x04,        # 2 cycles
        LSR_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x02}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x01, f"Expected mem[$0304]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


# ============================================================================
# ROL - Rotate Left
# ============================================================================

@cocotb.test()
async def test_rol_acc_basic(dut):
    """ROL accumulator: C=0, $01 rotated left = $02, C=0."""
    prog = [
        CLC,                 # 2 cycles
        LDA_IMM, 0x01,      # 2 cycles
        ROL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x02)
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_rol_acc_carry_in(dut):
    """ROL accumulator: C=1, $00 rotated left = $01, C=0."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x00,      # 2 cycles
        ROL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x01)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 0, "N")


@cocotb.test()
async def test_rol_acc_carry_out(dut):
    """ROL accumulator: C=0, $80 rotated left = $00, C=1, Z=1."""
    prog = [
        CLC,                 # 2 cycles
        LDA_IMM, 0x80,      # 2 cycles
        ROL_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")


@cocotb.test()
async def test_rol_zp(dut):
    """ROL zero page: C=0, mem[$10] $01 rotated left = $02."""
    prog = [
        CLC,                 # 2 cycles
        ROL_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x01}, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x02, f"Expected mem[$10]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_rol_zpx(dut):
    """ROL zero page,X: C=0, mem[$15] $01 rotated left = $02."""
    prog = [
        CLC,                 # 2 cycles
        LDX_IMM, 0x05,      # 2 cycles
        ROL_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x01}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x02, f"Expected mem[$15]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_rol_abs(dut):
    """ROL absolute: C=0, mem[$0300] $01 rotated left = $02."""
    prog = [
        CLC,                   # 2 cycles
        ROL_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x01}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x02, f"Expected mem[$0300]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


@cocotb.test()
async def test_rol_abx(dut):
    """ROL absolute,X: C=0, mem[$0304] $01 rotated left = $02."""
    prog = [
        CLC,                   # 2 cycles
        LDX_IMM, 0x04,        # 2 cycles
        ROL_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x01}, cycles=11)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x02, f"Expected mem[$0304]==$02, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_nz(dut, 0x02)


# ============================================================================
# ROR - Rotate Right
# ============================================================================

@cocotb.test()
async def test_ror_acc_basic(dut):
    """ROR accumulator: C=0, $02 rotated right = $01, C=0."""
    prog = [
        CLC,                 # 2 cycles
        LDA_IMM, 0x02,      # 2 cycles
        ROR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x01)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_ror_acc_carry_in(dut):
    """ROR accumulator: C=1, $00 rotated right = $80, C=0, N=1."""
    prog = [
        SEC,                 # 2 cycles
        LDA_IMM, 0x00,      # 2 cycles
        ROR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x80)
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_ror_acc_carry_out(dut):
    """ROR accumulator: C=0, $01 rotated right = $00, C=1, Z=1."""
    prog = [
        CLC,                 # 2 cycles
        LDA_IMM, 0x01,      # 2 cycles
        ROR_A,               # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")


@cocotb.test()
async def test_ror_zp(dut):
    """ROR zero page: C=0, mem[$10] $02 rotated right = $01."""
    prog = [
        CLC,                 # 2 cycles
        ROR_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x02}, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x01, f"Expected mem[$10]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_ror_zpx(dut):
    """ROR zero page,X: C=0, mem[$15] $02 rotated right = $01."""
    prog = [
        CLC,                 # 2 cycles
        LDX_IMM, 0x05,      # 2 cycles
        ROR_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x02}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x01, f"Expected mem[$15]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_ror_abs(dut):
    """ROR absolute: C=0, mem[$0300] $02 rotated right = $01."""
    prog = [
        CLC,                   # 2 cycles
        ROR_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x02}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x01, f"Expected mem[$0300]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


@cocotb.test()
async def test_ror_abx(dut):
    """ROR absolute,X: C=0, mem[$0304] $02 rotated right = $01."""
    prog = [
        CLC,                   # 2 cycles
        LDX_IMM, 0x04,        # 2 cycles
        ROR_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x02}, cycles=11)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x01, f"Expected mem[$0304]==$01, got ${val:02X}"
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_Z, 0, "Z")


# ============================================================================
# STA - Store Accumulator
# ============================================================================

@cocotb.test()
async def test_sta_zp(dut):
    """STA zero page: store A=$42 to mem[$10]."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        STA_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x42, f"Expected mem[$10]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_zpx(dut):
    """STA zero page,X: store A=$42 to mem[$15]."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        STA_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x42, f"Expected mem[$15]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_abs(dut):
    """STA absolute: store A=$42 to mem[$0300]."""
    prog = [
        LDA_IMM, 0x42,        # 2 cycles
        STA_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x42, f"Expected mem[$0300]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_abx(dut):
    """STA absolute,X: store A=$42 to mem[$0304]."""
    prog = [
        LDX_IMM, 0x04,        # 2 cycles
        LDA_IMM, 0x42,        # 2 cycles
        STA_ABX, 0x00, 0x03,  # 5 cycles
    ]
    await setup_and_run(dut, prog, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x42, f"Expected mem[$0304]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_aby(dut):
    """STA absolute,Y: store A=$42 to mem[$0303]."""
    prog = [
        LDY_IMM, 0x03,        # 2 cycles
        LDA_IMM, 0x42,        # 2 cycles
        STA_ABY, 0x00, 0x03,  # 5 cycles
    ]
    await setup_and_run(dut, prog, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0303)
    assert val == 0x42, f"Expected mem[$0303]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_izx(dut):
    """STA (indirect,X): store A=$42 via pointer at zp[$52] → $0300."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        STA_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x52: 0x00, 0x53: 0x03}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x42, f"Expected mem[$0300]==$42, got ${val:02X}"


@cocotb.test()
async def test_sta_izy(dut):
    """STA (indirect),Y: store A=$42 via pointer at zp[$50] → $0300+Y=$0303."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        STA_IZY, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x50: 0x00, 0x51: 0x03}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0303)
    assert val == 0x42, f"Expected mem[$0303]==$42, got ${val:02X}"


# ============================================================================
# STX - Store X Register
# ============================================================================

@cocotb.test()
async def test_stx_zp(dut):
    """STX zero page: store X=$42 to mem[$10]."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        STX_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x42, f"Expected mem[$10]==$42, got ${val:02X}"


@cocotb.test()
async def test_stx_zpy(dut):
    """STX zero page,Y: store X=$42 to mem[$15]."""
    prog = [
        LDY_IMM, 0x05,      # 2 cycles
        LDX_IMM, 0x42,      # 2 cycles
        STX_ZPY, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x42, f"Expected mem[$15]==$42, got ${val:02X}"


@cocotb.test()
async def test_stx_abs(dut):
    """STX absolute: store X=$42 to mem[$0300]."""
    prog = [
        LDX_IMM, 0x42,        # 2 cycles
        STX_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x42, f"Expected mem[$0300]==$42, got ${val:02X}"


# ============================================================================
# STY - Store Y Register
# ============================================================================

@cocotb.test()
async def test_sty_zp(dut):
    """STY zero page: store Y=$42 to mem[$10]."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        STY_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x42, f"Expected mem[$10]==$42, got ${val:02X}"


@cocotb.test()
async def test_sty_zpx(dut):
    """STY zero page,X: store Y=$42 to mem[$15]."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDY_IMM, 0x42,      # 2 cycles
        STY_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x42, f"Expected mem[$15]==$42, got ${val:02X}"


@cocotb.test()
async def test_sty_abs(dut):
    """STY absolute: store Y=$42 to mem[$0300]."""
    prog = [
        LDY_IMM, 0x42,        # 2 cycles
        STY_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x42, f"Expected mem[$0300]==$42, got ${val:02X}"


# ============================================================
# TAX / TAY / TXA / TYA / TSX / TXS - Transfer Registers
# Flags: N, Z (except TXS which affects no flags)
# ============================================================

@cocotb.test()
async def test_tax(dut):
    """TAX: transfer A to X. A=$42 -> X=$42."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        TAX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_tax_zero(dut):
    """TAX: transfer A=0x00 to X, Z=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        TAX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_tax_negative(dut):
    """TAX: transfer A=0x80 to X, N=1."""
    prog = [
        LDA_IMM, 0x80,      # 2 cycles
        TAX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x80)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_tay(dut):
    """TAY: transfer A to Y. A=$42 -> Y=$42."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        TAY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_tay_zero(dut):
    """TAY: transfer A=0x00 to Y, Z=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        TAY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_txa(dut):
    """TXA: transfer X to A. X=$42 -> A=$42."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        TXA,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_txa_zero(dut):
    """TXA: transfer X=0x00 to A, Z=1."""
    prog = [
        LDX_IMM, 0x00,      # 2 cycles
        TXA,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_tya(dut):
    """TYA: transfer Y to A. Y=$42 -> A=$42."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        TYA,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_tya_zero(dut):
    """TYA: transfer Y=0x00 to A, Z=1."""
    prog = [
        LDY_IMM, 0x00,      # 2 cycles
        TYA,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_txs(dut):
    """TXS: transfer X to SP. X=$FF -> SP=$FF. No flags affected."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_sp(dut, 0xFF)

@cocotb.test()
async def test_tsx(dut):
    """TSX: transfer SP to X. Set SP=$FD via TXS, clear X, then TSX -> X=$FD."""
    prog = [
        LDX_IMM, 0xFD,      # 2 cycles
        TXS,                 # 2 cycles
        LDX_IMM, 0x00,      # 2 cycles
        TSX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0xFD)
    assert_nz(dut, 0xFD)


# ============================================================
# PHA / PHP / PLA / PLP - Stack Operations
# Stack area: $0100-$01FF. Push decrements SP, pull increments SP.
# PHA: 3 cycles, PHP: 3 cycles, PLA: 4 cycles, PLP: 4 cycles
# ============================================================

@cocotb.test()
async def test_pha(dut):
    """PHA: push A onto stack. A=$42, SP=$FF -> mem[$01FF]=$42, SP=$FE."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        PHA,                 # 3 cycles
    ]
    await setup_and_run(dut, prog, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_sp(dut, 0xFE)
    val = await read_mem(dut, 0x01FF)
    assert val == 0x42, f"Stack mem[$01FF]: expected 0x42, got {val:#04x}"

@cocotb.test()
async def test_pla(dut):
    """PLA: pull A from stack. Push $42, load $00, then pull -> A=$42, SP=$FF."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        PHA,                 # 3 cycles
        LDA_IMM, 0x00,      # 2 cycles
        PLA,                 # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=15)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_sp(dut, 0xFF)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_pla_zero(dut):
    """PLA: pull zero from stack. Push $00, load $FF, then pull -> A=$00, Z=1."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
        LDA_IMM, 0x00,      # 2 cycles
        PHA,                 # 3 cycles
        LDA_IMM, 0xFF,      # 2 cycles
        PLA,                 # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=15)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x00)
    assert_sp(dut, 0xFF)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_php(dut):
    """PHP: push processor status with B and bit 5 set. Verify pushed byte."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
        CLC,                 # 2 cycles - ensure C=0
        CLV,                 # 2 cycles - ensure V=0
        SEC,                 # 2 cycles - set C=1
        PHP,                 # 3 cycles
    ]
    await setup_and_run(dut, prog, cycles=13)
    assert_pc(dut, START_PC + len(prog))
    assert_sp(dut, 0xFE)
    val = await read_mem(dut, 0x01FF)
    # Check bit we set
    assert (val >> SR_C) & 1 == 1, f"Pushed C: expected 1, got 0 (val={val:#04x})"
    # Check bits that should be clear
    assert (val >> SR_V) & 1 == 0, f"Pushed V: expected 0, got 1 (val={val:#04x})"
    assert (val >> SR_D) & 1 == 0, f"Pushed D: expected 0, got 1 (val={val:#04x})"
    # PHP always pushes with B (bit 4) and bit 5 set to 1
    assert (val >> SR_B) & 1 == 1, f"Pushed B: expected 1, got 0 (val={val:#04x})"
    assert (val >> 5) & 1 == 1, f"Pushed bit5: expected 1, got 0 (val={val:#04x})"

@cocotb.test()
async def test_plp(dut):
    """PLP: pull processor status. SEC, PHP, CLC, PLP -> carry restored to 1."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        TXS,                 # 2 cycles
        SEC,                 # 2 cycles
        PHP,                 # 3 cycles
        CLC,                 # 2 cycles
        PLP,                 # 4 cycles
    ]
    await setup_and_run(dut, prog, cycles=15)
    assert_pc(dut, START_PC + len(prog))
    assert_sp(dut, 0xFF)
    assert_flag(dut, SR_C, 1, "C")


# ============================================================
# INC - Increment Memory
# M = M + 1
# Flags: N, Z
# ============================================================

@cocotb.test()
async def test_inc_zp(dut):
    """INC zero page: mem[0x10] = 0x41 + 1 = 0x42."""
    prog = [
        INC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x41}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x42, f"mem[0x10]: expected 0x42, got {val:#04x}"
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_inc_zp_zero(dut):
    """INC zero page: mem[0x10] = 0xFF + 1 = 0x00, Z=1."""
    prog = [
        INC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0xFF}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x00, f"mem[0x10]: expected 0x00, got {val:#04x}"
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_inc_zp_negative(dut):
    """INC zero page: mem[0x10] = 0x7F + 1 = 0x80, N=1."""
    prog = [
        INC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x7F}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x80, f"mem[0x10]: expected 0x80, got {val:#04x}"
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_inc_zpx(dut):
    """INC zero page,X: X=5, mem[0x15] = 0x41 + 1 = 0x42."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        INC_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x41}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x42, f"mem[0x15]: expected 0x42, got {val:#04x}"
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_inc_abs(dut):
    """INC absolute: mem[0x0300] = 0x41 + 1 = 0x42."""
    prog = [
        INC_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x41}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x42, f"mem[0x0300]: expected 0x42, got {val:#04x}"
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_inc_abx(dut):
    """INC absolute,X: X=4, mem[0x0304] = 0x41 + 1 = 0x42."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        INC_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x41}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x42, f"mem[0x0304]: expected 0x42, got {val:#04x}"
    assert_nz(dut, 0x42)


# ============================================================
# DEC - Decrement Memory
# M = M - 1
# Flags: N, Z
# ============================================================

@cocotb.test()
async def test_dec_zp(dut):
    """DEC zero page: mem[0x10] = 0x42 - 1 = 0x41."""
    prog = [
        DEC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x42}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x41, f"mem[0x10]: expected 0x41, got {val:#04x}"
    assert_nz(dut, 0x41)

@cocotb.test()
async def test_dec_zp_zero(dut):
    """DEC zero page: mem[0x10] = 0x01 - 1 = 0x00, Z=1."""
    prog = [
        DEC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x01}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0x00, f"mem[0x10]: expected 0x00, got {val:#04x}"
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_dec_zp_negative(dut):
    """DEC zero page: mem[0x10] = 0x00 - 1 = 0xFF, N=1."""
    prog = [
        DEC_ZP, 0x10,       # 5 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x00}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x10)
    assert val == 0xFF, f"mem[0x10]: expected 0xFF, got {val:#04x}"
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_dec_zpx(dut):
    """DEC zero page,X: X=5, mem[0x15] = 0x42 - 1 = 0x41."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        DEC_ZPX, 0x10,      # 6 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x42}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x15)
    assert val == 0x41, f"mem[0x15]: expected 0x41, got {val:#04x}"
    assert_nz(dut, 0x41)

@cocotb.test()
async def test_dec_abs(dut):
    """DEC absolute: mem[0x0300] = 0x42 - 1 = 0x41."""
    prog = [
        DEC_ABS, 0x00, 0x03,  # 6 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0300)
    assert val == 0x41, f"mem[0x0300]: expected 0x41, got {val:#04x}"
    assert_nz(dut, 0x41)

@cocotb.test()
async def test_dec_abx(dut):
    """DEC absolute,X: X=4, mem[0x0304] = 0x42 - 1 = 0x41."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        DEC_ABX, 0x00, 0x03,  # 7 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x42}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    val = await read_mem(dut, 0x0304)
    assert val == 0x41, f"mem[0x0304]: expected 0x41, got {val:#04x}"
    assert_nz(dut, 0x41)


# ============================================================
# INX / INY / DEX / DEY - Increment/Decrement Register
# Flags: N, Z
# ============================================================

@cocotb.test()
async def test_inx(dut):
    """INX: X = 0x41 + 1 = 0x42."""
    prog = [
        LDX_IMM, 0x41,      # 2 cycles
        INX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_inx_zero(dut):
    """INX: X = 0xFF + 1 = 0x00, Z=1."""
    prog = [
        LDX_IMM, 0xFF,      # 2 cycles
        INX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_inx_negative(dut):
    """INX: X = 0x7F + 1 = 0x80, N=1."""
    prog = [
        LDX_IMM, 0x7F,      # 2 cycles
        INX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x80)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_iny(dut):
    """INY: Y = 0x41 + 1 = 0x42."""
    prog = [
        LDY_IMM, 0x41,      # 2 cycles
        INY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_nz(dut, 0x42)

@cocotb.test()
async def test_iny_zero(dut):
    """INY: Y = 0xFF + 1 = 0x00, Z=1."""
    prog = [
        LDY_IMM, 0xFF,      # 2 cycles
        INY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_dex(dut):
    """DEX: X = 0x42 - 1 = 0x41."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        DEX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x41)
    assert_nz(dut, 0x41)

@cocotb.test()
async def test_dex_zero(dut):
    """DEX: X = 0x01 - 1 = 0x00, Z=1."""
    prog = [
        LDX_IMM, 0x01,      # 2 cycles
        DEX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_dex_wrap(dut):
    """DEX: X = 0x00 - 1 = 0xFF, N=1."""
    prog = [
        LDX_IMM, 0x00,      # 2 cycles
        DEX,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0xFF)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_dey(dut):
    """DEY: Y = 0x42 - 1 = 0x41."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        DEY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x41)
    assert_nz(dut, 0x41)

@cocotb.test()
async def test_dey_zero(dut):
    """DEY: Y = 0x01 - 1 = 0x00, Z=1."""
    prog = [
        LDY_IMM, 0x01,      # 2 cycles
        DEY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_dey_wrap(dut):
    """DEY: Y = 0x00 - 1 = 0xFF, N=1."""
    prog = [
        LDY_IMM, 0x00,      # 2 cycles
        DEY,                 # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0xFF)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")


# ============================================================
# CMP - Compare Accumulator
# A - M (set flags, result discarded)
# Flags: N, Z, C
# C=1 if A >= M, Z=1 if A == M, N=1 if result bit 7 set
# ============================================================

@cocotb.test()
async def test_cmp_imm_equal(dut):
    """CMP immediate: A=$42, M=$42 -> Z=1, C=1, N=0, A unchanged."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        CMP_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cmp_imm_greater(dut):
    """CMP immediate: A=$42, M=$10 -> Z=0, C=1, N=0, A=$42."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        CMP_IMM, 0x10,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cmp_imm_less(dut):
    """CMP immediate: A=$10, M=$42 -> Z=0, C=0, N=1 (0x10-0x42=0xCE)."""
    prog = [
        LDA_IMM, 0x10,      # 2 cycles
        CMP_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x10)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_cmp_zp(dut):
    """CMP zero page: A=$42, mem[0x10]=$42 -> Z=1, C=1."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        CMP_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x42}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_zpx(dut):
    """CMP zero page,X: X=5, A=$42, mem[0x15]=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x05,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        CMP_ZPX, 0x10,      # 4 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x15: 0x42}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_abs(dut):
    """CMP absolute: A=$42, mem[0x0300]=$42 -> Z=1, C=1."""
    prog = [
        LDA_IMM, 0x42,      # 2 cycles
        CMP_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_abx(dut):
    """CMP absolute,X: X=4, A=$42, mem[0x0304]=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x04,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        CMP_ABX, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0304: 0x42}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_aby(dut):
    """CMP absolute,Y: Y=3, A=$42, mem[0x0303]=$42 -> Z=1, C=1."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        CMP_ABY, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0303: 0x42}, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_izx(dut):
    """CMP (indirect,X): X=2, A=$42, ptr at zp[0x52]->$0300, mem=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x02,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        CMP_IZX, 0x50,      # 6 cycles
    ]
    await setup_and_run(dut, prog,
        zp_data={0x52: 0x00, 0x53: 0x03}, data={0x0300: 0x42}, cycles=10)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cmp_izy(dut):
    """CMP (indirect),Y: Y=3, A=$42, ptr=$0300, addr=$0303, mem=$42 -> Z=1, C=1."""
    prog = [
        LDY_IMM, 0x03,      # 2 cycles
        LDA_IMM, 0x42,      # 2 cycles
        CMP_IZY, 0x50,      # 5 cycles
    ]
    await setup_and_run(dut, prog,
        zp_data={0x50: 0x00, 0x51: 0x03}, data={0x0303: 0x42}, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")


# ============================================================
# CPX - Compare X Register
# X - M (set flags, result discarded)
# Flags: N, Z, C
# ============================================================

@cocotb.test()
async def test_cpx_imm_equal(dut):
    """CPX immediate: X=$42, M=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        CPX_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cpx_imm_greater(dut):
    """CPX immediate: X=$42, M=$10 -> C=1, Z=0."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        CPX_IMM, 0x10,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cpx_imm_less(dut):
    """CPX immediate: X=$10, M=$42 -> C=0, Z=0, N=1."""
    prog = [
        LDX_IMM, 0x10,      # 2 cycles
        CPX_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x10)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_cpx_zp(dut):
    """CPX zero page: X=$42, mem[0x10]=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        CPX_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x42}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cpx_abs(dut):
    """CPX absolute: X=$42, mem[0x0300]=$42 -> Z=1, C=1."""
    prog = [
        LDX_IMM, 0x42,      # 2 cycles
        CPX_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_x(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")


# ============================================================
# CPY - Compare Y Register
# Y - M (set flags, result discarded)
# Flags: N, Z, C
# ============================================================

@cocotb.test()
async def test_cpy_imm_equal(dut):
    """CPY immediate: Y=$42, M=$42 -> Z=1, C=1."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        CPY_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cpy_imm_greater(dut):
    """CPY immediate: Y=$42, M=$10 -> C=1, Z=0."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        CPY_IMM, 0x10,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 1, "C")
    assert_flag(dut, SR_N, 0, "N")

@cocotb.test()
async def test_cpy_imm_less(dut):
    """CPY immediate: Y=$10, M=$42 -> C=0, Z=0, N=1."""
    prog = [
        LDY_IMM, 0x10,      # 2 cycles
        CPY_IMM, 0x42,      # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x10)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_C, 0, "C")
    assert_flag(dut, SR_N, 1, "N")

@cocotb.test()
async def test_cpy_zp(dut):
    """CPY zero page: Y=$42, mem[0x10]=$42 -> Z=1, C=1."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        CPY_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x42}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")

@cocotb.test()
async def test_cpy_abs(dut):
    """CPY absolute: Y=$42, mem[0x0300]=$42 -> Z=1, C=1."""
    prog = [
        LDY_IMM, 0x42,      # 2 cycles
        CPY_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x42}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_y(dut, 0x42)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_C, 1, "C")


# ============================================================
# BIT - Bit Test
# Z = A & M == 0, N = M bit 7, V = M bit 6
# ============================================================

@cocotb.test()
async def test_bit_zp_zero(dut):
    """BIT zero page: A=$00, mem=$FF -> Z=1, N=1, V=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        BIT_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0xFF}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 1, "N")
    assert_flag(dut, SR_V, 1, "V")

@cocotb.test()
async def test_bit_zp_nonzero(dut):
    """BIT zero page: A=$C0, mem=$C0 -> Z=0, N=1, V=1."""
    prog = [
        LDA_IMM, 0xC0,      # 2 cycles
        BIT_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0xC0}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 1, "N")
    assert_flag(dut, SR_V, 1, "V")

@cocotb.test()
async def test_bit_zp_nv_from_mem(dut):
    """BIT zero page: A=$FF, mem=$40 -> Z=0, N=0, V=1."""
    prog = [
        LDA_IMM, 0xFF,      # 2 cycles
        BIT_ZP, 0x10,       # 3 cycles
    ]
    await setup_and_run(dut, prog, zp_data={0x10: 0x40}, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_Z, 0, "Z")
    assert_flag(dut, SR_N, 0, "N")
    assert_flag(dut, SR_V, 1, "V")

@cocotb.test()
async def test_bit_abs(dut):
    """BIT absolute: A=$00, mem[0x0300]=$FF -> Z=1, N=1, V=1."""
    prog = [
        LDA_IMM, 0x00,      # 2 cycles
        BIT_ABS, 0x00, 0x03,  # 4 cycles
    ]
    await setup_and_run(dut, prog, data={0x0300: 0xFF}, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_Z, 1, "Z")
    assert_flag(dut, SR_N, 1, "N")
    assert_flag(dut, SR_V, 1, "V")



# ============================================================
# BCC - Branch if Carry Clear (C=0)
# ============================================================

@cocotb.test()
async def test_bcc_taken(dut):
    """BCC taken: CLC sets C=0, branch skips NOP, executes LDA #$42."""
    prog = [
        CLC,                 # 2 cycles  $0400
        BCC, 0x01,           # 3 cycles  $0401 (taken, target = $0403 + 1 = $0404)
        NOP,                 #           $0403 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bcc_not_taken(dut):
    """BCC not taken: SEC sets C=1, branch falls through to LDA #$42."""
    prog = [
        SEC,                 # 2 cycles  $0400
        BCC, 0x01,           # 2 cycles  $0401 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0403
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BCS - Branch if Carry Set (C=1)
# ============================================================

@cocotb.test()
async def test_bcs_taken(dut):
    """BCS taken: SEC sets C=1, branch skips NOP, executes LDA #$42."""
    prog = [
        SEC,                 # 2 cycles  $0400
        BCS, 0x01,           # 3 cycles  $0401 (taken, target = $0403 + 1 = $0404)
        NOP,                 #           $0403 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bcs_not_taken(dut):
    """BCS not taken: CLC sets C=0, branch falls through to LDA #$42."""
    prog = [
        CLC,                 # 2 cycles  $0400
        BCS, 0x01,           # 2 cycles  $0401 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0403
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BEQ - Branch if Equal (Z=1)
# ============================================================

@cocotb.test()
async def test_beq_taken(dut):
    """BEQ taken: LDA #$00 sets Z=1, branch skips NOP, executes LDA #$42."""
    prog = [
        LDA_IMM, 0x00,       # 2 cycles  $0400
        BEQ, 0x01,           # 3 cycles  $0402 (taken, target = $0404 + 1 = $0405)
        NOP,                 #           $0404 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_beq_not_taken(dut):
    """BEQ not taken: LDA #$01 sets Z=0, branch falls through to LDA #$42."""
    prog = [
        LDA_IMM, 0x01,       # 2 cycles  $0400
        BEQ, 0x01,           # 2 cycles  $0402 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BNE - Branch if Not Equal (Z=0)
# ============================================================

@cocotb.test()
async def test_bne_taken(dut):
    """BNE taken: LDA #$01 sets Z=0, branch skips NOP, executes LDA #$42."""
    prog = [
        LDA_IMM, 0x01,       # 2 cycles  $0400
        BNE, 0x01,           # 3 cycles  $0402 (taken, target = $0404 + 1 = $0405)
        NOP,                 #           $0404 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bne_not_taken(dut):
    """BNE not taken: LDA #$00 sets Z=1, branch falls through to LDA #$42."""
    prog = [
        LDA_IMM, 0x00,       # 2 cycles  $0400
        BNE, 0x01,           # 2 cycles  $0402 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BMI - Branch if Minus (N=1)
# ============================================================

@cocotb.test()
async def test_bmi_taken(dut):
    """BMI taken: LDA #$80 sets N=1, branch skips NOP, executes LDA #$42."""
    prog = [
        LDA_IMM, 0x80,       # 2 cycles  $0400
        BMI, 0x01,           # 3 cycles  $0402 (taken, target = $0404 + 1 = $0405)
        NOP,                 #           $0404 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bmi_not_taken(dut):
    """BMI not taken: LDA #$01 sets N=0, branch falls through to LDA #$42."""
    prog = [
        LDA_IMM, 0x01,       # 2 cycles  $0400
        BMI, 0x01,           # 2 cycles  $0402 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BPL - Branch if Plus (N=0)
# ============================================================

@cocotb.test()
async def test_bpl_taken(dut):
    """BPL taken: LDA #$01 sets N=0, branch skips NOP, executes LDA #$42."""
    prog = [
        LDA_IMM, 0x01,       # 2 cycles  $0400
        BPL, 0x01,           # 3 cycles  $0402 (taken, target = $0404 + 1 = $0405)
        NOP,                 #           $0404 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bpl_not_taken(dut):
    """BPL not taken: LDA #$80 sets N=1, branch falls through to LDA #$42."""
    prog = [
        LDA_IMM, 0x80,       # 2 cycles  $0400
        BPL, 0x01,           # 2 cycles  $0402 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0404
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BVC - Branch if Overflow Clear (V=0)
# ============================================================

@cocotb.test()
async def test_bvc_taken(dut):
    """BVC taken: V=0 after reset, branch skips NOP, executes LDA #$42."""
    prog = [
        BVC, 0x01,           # 3 cycles  $0400 (taken, V=0 after reset, target = $0402 + 1 = $0403)
        NOP,                 #           $0402 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0403
    ]
    await setup_and_run(dut, prog, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bvc_not_taken(dut):
    """BVC not taken: ADC overflow sets V=1, branch falls through to LDA #$42."""
    prog = [
        LDA_IMM, 0x50,       # 2 cycles  $0400
        ADC_IMM, 0x50,       # 2 cycles  $0402 (sets V=1)
        BVC, 0x01,           # 2 cycles  $0404 (not taken)
        LDA_IMM, 0x42,       # 2 cycles  $0406
    ]
    await setup_and_run(dut, prog, cycles=8)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# BVS - Branch if Overflow Set (V=1)
# ============================================================

@cocotb.test()
async def test_bvs_taken(dut):
    """BVS taken: ADC overflow sets V=1, branch skips NOP, executes LDA #$42."""
    prog = [
        LDA_IMM, 0x50,       # 2 cycles  $0400
        ADC_IMM, 0x50,       # 2 cycles  $0402 (sets V=1)
        BVS, 0x01,           # 3 cycles  $0404 (taken, target = $0406 + 1 = $0407)
        NOP,                 #           $0406 (skipped)
        LDA_IMM, 0x42,       # 2 cycles  $0407
    ]
    await setup_and_run(dut, prog, cycles=9)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_bvs_not_taken(dut):
    """BVS not taken: V=0 after reset, branch falls through to LDA #$42."""
    prog = [
        BVS, 0x01,           # 2 cycles  $0400 (not taken, V=0 after reset)
        LDA_IMM, 0x42,       # 2 cycles  $0402
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# Branch backward test
# ============================================================

@cocotb.test()
async def test_branch_backward(dut):
    """BNE backward: loop DEX until X=0. LDX #$02, DEX, BNE back to DEX."""
    prog = [
        LDX_IMM, 0x02,       # 2 cycles  $0400
        DEX,                  # 2 cycles  $0402 (X=1, Z=0)
        BNE, 0xFD,           # 3 cycles  $0403 (taken, target = $0405 + (-3) = $0402)
                              # --- second iteration ---
                              # 2 cycles  DEX (X=0, Z=1)
                              # 2 cycles  BNE (not taken)
    ]
    # Total: LDX(2) + DEX(2) + BNE_taken(3) + DEX(2) + BNE_not_taken(2) = 11
    await setup_and_run(dut, prog, cycles=11)
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")


# ============================================================
# JMP - Jump (absolute)
# 3 cycles
# ============================================================

@cocotb.test()
async def test_jmp_abs(dut):
    """JMP absolute: jump to $0405 skipping two NOPs, executes LDA #$42."""
    prog = [
        JMP_ABS, 0x05, 0x04, # 3 cycles  $0400 (jump to $0405)
        NOP,                  #           $0403 (skipped)
        NOP,                  #           $0404 (skipped)
        LDA_IMM, 0x42,        # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, cycles=5)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# JMP - Jump (indirect)
# 5 cycles
# ============================================================

@cocotb.test()
async def test_jmp_ind(dut):
    """JMP indirect: vector at $0300 points to $0405, executes LDA #$42."""
    prog = [
        JMP_IND, 0x00, 0x03, # 5 cycles  $0400 (read vector at $0300 -> $0405)
        NOP,                  #           $0403 (skipped)
        NOP,                  #           $0404 (skipped)
        LDA_IMM, 0x42,        # 2 cycles  $0405
    ]
    await setup_and_run(dut, prog, data={0x0300: 0x05, 0x0301: 0x04}, cycles=7)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# JSR / RTS - Jump to Subroutine / Return from Subroutine
# JSR: 6 cycles, RTS: 6 cycles
# ============================================================

@cocotb.test()
async def test_jsr_rts(dut):
    """JSR $040A calls subroutine, RTS returns, then LDA #$42 executes.

    Also verifies RTS takes exactly 6 cycles.
    """
    # $0400: LDX #$FF       (2 bytes)  - init stack pointer
    # $0402: TXS             (1 byte)
    # $0403: JSR $040A       (3 bytes)  - pushes $0405 onto stack, jumps to $040A
    # $0406: LDA #$42        (2 bytes)  - executed after RTS (return addr+1 = $0406)
    # $0408: NOP             (1 byte)   - end marker
    # $0409: NOP             (1 byte)   - padding
    # $040A: LDA #$99        (2 bytes)  - subroutine body
    # $040C: RTS             (1 byte)   - return
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles
        TXS,                  # 2 cycles
        JSR_ABS, 0x0A, 0x04, # 6 cycles
        LDA_IMM, 0x42,       # 2 cycles (after return)
        NOP,                  # 2 cycles
        NOP,                  #          (padding)
        LDA_IMM, 0x99,       # 2 cycles (subroutine)
        RTS_IMP,              # 6 cycles
    ]

    # Setup: initialize and run until RTS is about to execute
    # LDX(2) + TXS(2) + JSR(6) + LDA_99(2) = 12 cycles
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1
    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 2)
    await ClockCycles(dut.i_clk, 6)  # init cycles

    # Run LDX(2) + TXS(2) + JSR(6) + LDA_99(2) = 12 cycles
    await ClockCycles(dut.i_clk, 12)

    # Verify we're at RTS instruction ($040C)
    rts_addr = START_PC + 12  # $040C
    assert_pc(dut, rts_addr)
    assert_acc(dut, 0x99)  # LDA #$99 completed

    # Run exactly 6 cycles for RTS
    await ClockCycles(dut.i_clk, 6)

    # After RTS, PC should be at return address ($0406 = $0405 + 1)
    return_addr = START_PC + 6  # $0406
    assert_pc(dut, return_addr)

    # Run remaining instructions: LDA_42(2) + NOP(2) = 4 cycles
    await ClockCycles(dut.i_clk, 4)
    assert_acc(dut, 0x42)
    assert_pc(dut, START_PC + 9)

@cocotb.test()
async def test_jsr_rts_page_cross(dut):
    """JSR at $04FE: pushed return addr $0500 crosses page (high byte $04->$05)."""
    # JSR is placed at $04FE so the 3-byte instruction spans $04FE-$0500.
    # JSR pushes (next_instruction - 1) = $0501 - 1 = $0500 onto the stack.
    # The pushed high byte is $05, not $04 -- verifying the page crossing.
    # RTS pulls $0500, adds 1, returns to $0501.
    prog = [
        LDX_IMM, 0xFF,        # 2 cycles  $0400
        TXS,                   # 2 cycles  $0402
        JMP_ABS, 0xFE, 0x04,  # 3 cycles  $0403 -> jump to $04FE
    ]
    data = {
        # JSR at $04FE: last byte at $0500 crosses into page $05
        0x04FE: JSR_ABS,
        0x04FF: 0x00,          # target low
        0x0500: 0x06,          # target high -> jump to $0600
        # RTS returns to $0500 + 1 = $0501
        0x0501: LDA_IMM,
        0x0502: 0x42,
        # Subroutine at $0600
        0x0600: RTS_IMP,
    }
    # LDX(2) + TXS(2) + JMP(3) + JSR(6) + RTS(6) + LDA(2) = 21
    await setup_and_run(dut, prog, data=data, cycles=21)
    assert_acc(dut, 0x42)
    assert_sp(dut, 0xFF)
    assert_pc(dut, 0x0503)
    # Verify the pushed return address was $0500 (high byte crossed from $04 to $05)
    hi = await read_mem(dut, 0x01FF)
    lo = await read_mem(dut, 0x01FE)
    assert hi == 0x05, f"Return addr high: expected $05, got ${hi:02X}"
    assert lo == 0x00, f"Return addr low: expected $00, got ${lo:02X}"


# ============================================================
# CLC - Clear Carry Flag
# SEC - Set Carry Flag
# Implied, 2 cycles each
# ============================================================

@cocotb.test()
async def test_clc(dut):
    """CLC: SEC then CLC clears the carry flag."""
    prog = [
        SEC,                  # 2 cycles
        CLC,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_C, 0, "C")

@cocotb.test()
async def test_sec(dut):
    """SEC: sets the carry flag."""
    prog = [
        SEC,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_C, 1, "C")


# ============================================================
# CLD - Clear Decimal Flag
# SED - Set Decimal Flag
# Implied, 2 cycles each
# ============================================================

@cocotb.test()
async def test_cld(dut):
    """CLD: SED then CLD clears the decimal flag."""
    prog = [
        SED,                  # 2 cycles
        CLD,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_D, 0, "D")

@cocotb.test()
async def test_sed(dut):
    """SED: sets the decimal flag."""
    prog = [
        SED,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_D, 1, "D")


# ============================================================
# CLI - Clear Interrupt Disable
# SEI - Set Interrupt Disable
# Implied, 2 cycles each
# ============================================================

@cocotb.test()
async def test_cli(dut):
    """CLI: clears the interrupt disable flag (I starts at 1 after reset)."""
    prog = [
        CLI,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=2)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_I, 0, "I")

@cocotb.test()
async def test_sei(dut):
    """SEI: CLI then SEI sets the interrupt disable flag."""
    prog = [
        CLI,                  # 2 cycles
        SEI,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_I, 1, "I")


# ============================================================
# CLV - Clear Overflow Flag
# Implied, 2 cycles
# ============================================================

@cocotb.test()
async def test_clv(dut):
    """CLV: ADC overflow sets V=1, CLV clears it."""
    prog = [
        LDA_IMM, 0x50,       # 2 cycles
        ADC_IMM, 0x50,       # 2 cycles (sets V=1)
        CLV,                  # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=6)
    assert_pc(dut, START_PC + len(prog))
    assert_flag(dut, SR_V, 0, "V")


# ============================================================
# NOP - No Operation
# Implied, 2 cycles
# ============================================================

@cocotb.test()
async def test_nop(dut):
    """NOP: does nothing, PC advances by 1, then LDA #$42 executes."""
    prog = [
        NOP,                  # 2 cycles
        LDA_IMM, 0x42,       # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


# ============================================================
# Illegal Opcodes — should behave as 1-byte, 2-cycle NOPs
# cc=11 opcodes (0x_3, 0x_7, 0x_B, 0x_F) are all unmatched.
# cc=00 gaps (000/010/011 top bits): 0x04, 0x0C, 0x14, 0x1C,
#   0x44, 0x54, 0x5C, 0x64, 0x74, 0x7C
# ============================================================

# Illegal opcodes: representative set from cc=11 and cc=00 gaps
ILLEGAL_OPCODES = [
    0x03, 0x07, 0x0F,      # cc=11
    0x1B, 0x3B, 0x5B,      # cc=11
    0x83, 0xA7, 0xCB, 0xFF,# cc=11
    0x04, 0x44, 0x64, 0x7C,# cc=00 gaps
]


@cocotb.test()
async def test_illegal_opcode_single_nop(dut):
    """Illegal opcode $03: treated as NOP, PC advances by 1, next instruction runs."""
    prog = [
        0x03,                 # illegal — should act as NOP (2 cycles)
        LDA_IMM, 0x42,       # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x42)


@cocotb.test()
async def test_illegal_opcode_no_side_effects(dut):
    """Illegal opcodes don't modify registers or flags."""
    prog = [
        LDA_IMM, 0xAA,       # 2 cycles — A=$AA, N=1 Z=0
        LDX_IMM, 0x55,       # 2 cycles — X=$55
        LDY_IMM, 0x33,       # 2 cycles — Y=$33
        0x47,                 # illegal — 2 cycles, no side effects
        0xCB,                 # illegal — 2 cycles, no side effects
        STA_ZP, 0x00,        # 3 cycles — store A to verify it's intact
    ]
    await setup_and_run(dut, prog, cycles=13)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xAA)
    assert_x(dut, 0x55)
    assert_y(dut, 0x33)
    assert_flag(dut, SR_N, 0, "N")  # last op was STA, flags from LDY: 0x33 is positive
    val = await read_mem(dut, 0x0000)
    assert val == 0xAA, f"ZP $00: expected 0xAA, got {val:#04x}"


@cocotb.test()
async def test_illegal_opcodes_all_representatives(dut):
    """All representative illegal opcodes act as NOPs: PC advances correctly."""
    # Build a program: N illegal opcodes, then LDA #$BE
    prog = list(ILLEGAL_OPCODES) + [LDA_IMM, 0xBE]
    n_illegal = len(ILLEGAL_OPCODES)
    # Each illegal = 2 cycles, LDA_IMM = 2 cycles
    await setup_and_run(dut, prog, cycles=(n_illegal * 2) + 2)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0xBE)


@cocotb.test()
async def test_illegal_opcode_cc00_gap(dut):
    """Illegal cc=00 gap opcode $44: treated as NOP."""
    prog = [
        0x44,                 # illegal — 2 cycles
        LDA_IMM, 0x77,       # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x77)


@cocotb.test()
async def test_illegal_opcode_ff(dut):
    """Illegal opcode $FF: treated as NOP."""
    prog = [
        0xFF,                 # illegal — 2 cycles
        LDA_IMM, 0x11,       # 2 cycles
    ]
    await setup_and_run(dut, prog, cycles=4)
    assert_pc(dut, START_PC + len(prog))
    assert_acc(dut, 0x11)


# ============================================================
# BRK - Force Interrupt
# 7 cycles: pushes PC+2, pushes status (with B set), loads IRQ vector
# ============================================================

@cocotb.test()
async def test_brk(dut):
    """BRK: pushes PC+2 and status, jumps to IRQ vector, sets I flag."""
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles  $0400
        TXS,                  # 2 cycles  $0402
        BRK,                  # 7 cycles  $0403
    ]
    # IRQ handler at $0500 does LDA #$99
    data = {
        0xFFFE: 0x00,         # IRQ vector low byte
        0xFFFF: 0x05,         # IRQ vector high byte
        0x0500: LDA_IMM,      # handler: LDA #$99
        0x0501: 0x99,
    }
    # LDX(2) + TXS(2) + BRK(7) + LDA(2) = 13
    await setup_and_run(dut, prog, data=data, cycles=13)
    assert_acc(dut, 0x99)
    assert_flag(dut, SR_I, 1, "I")
    # SP should be $FC (pushed PCH, PCL, status = 3 bytes from $FF)
    assert_sp(dut, 0xFC)


# ============================================================
# RTI - Return from Interrupt
# 6 cycles: pulls status, pulls PC
# ============================================================

@cocotb.test()
async def test_rti(dut):
    """RTI: BRK into handler that does RTI, returns to instruction after BRK."""
    # $0400: LDX #$FF       (2 bytes)
    # $0402: TXS             (1 byte)
    # $0403: LDA #$01        (2 bytes) - set a known value first
    # $0405: BRK             (1 byte)  - pushes $0407 and status
    # $0406: 0x00            (1 byte)  - BRK padding byte
    # $0407: LDA #$42        (2 bytes) - executed after RTI returns here
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles
        TXS,                  # 2 cycles
        LDA_IMM, 0x01,       # 2 cycles
        BRK,                  # 7 cycles
        0x00,                 #          (BRK padding)
        LDA_IMM, 0x42,       # 2 cycles (after RTI returns)
    ]
    # IRQ handler at $0500 does RTI
    data = {
        0xFFFE: 0x00,         # IRQ vector low byte
        0xFFFF: 0x05,         # IRQ vector high byte
        0x0500: RTI,          # handler: RTI
    }
    # LDX(2) + TXS(2) + LDA(2) + BRK(7) + RTI(6) + LDA(2) = 21
    await setup_and_run(dut, prog, data=data, cycles=21)
    assert_acc(dut, 0x42)
    assert_pc(dut, START_PC + len(prog))


# ============================================================
# IRQ - External Interrupt Request (active low, level-triggered)
# ============================================================

@cocotb.test()
async def test_irq_basic(dut):
    """IRQ fires after CLI when i_irq_n is asserted low."""
    # Program: set up stack, clear interrupt disable, then NOPs
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles  $0400
        TXS,                  # 2 cycles  $0402
        CLI,                  # 2 cycles  $0403
        LDA_IMM, 0x01,       # 2 cycles  $0404
        NOP,                  # 2 cycles  $0406
        NOP,                  # 2 cycles  $0407
        NOP,                  # 2 cycles  $0408
        NOP,                  # 2 cycles  $0409
    ]
    # IRQ handler at $0500 does LDA #$99
    data = {
        0xFFFE: 0x00,         # IRQ vector low byte
        0xFFFF: 0x05,         # IRQ vector high byte
        0x0500: LDA_IMM,      # handler: LDA #$99
        0x0501: 0x99,
    }

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for addr, val in data.items():
        dut.ram.mem[addr].value = val

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)
    await ClockCycles(dut.i_clk, 6)

    # Let LDX, TXS, CLI, LDA execute: 2+2+2+2 = 8 cycles
    await ClockCycles(dut.i_clk, 8)

    # Assert IRQ (active low)
    dut.i_irq_n.value = 0

    # Wait for IRQ to be serviced: 7 cycles for interrupt sequence + 2 for LDA in handler
    await ClockCycles(dut.i_clk, 9)

    assert_acc(dut, 0x99)
    assert_flag(dut, SR_I, 1, "I")
    assert_sp(dut, 0xFC)


@cocotb.test()
async def test_irq_masked(dut):
    """IRQ is ignored when the I flag is set (SEI)."""
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles  $0400
        TXS,                  # 2 cycles  $0402
        SEI,                  # 2 cycles  $0403
        LDA_IMM, 0x42,       # 2 cycles  $0404
        NOP,                  # 2 cycles  $0406
        NOP,                  # 2 cycles  $0407
        NOP,                  # 2 cycles  $0408
        NOP,                  # 2 cycles  $0409
        NOP,                  # 2 cycles  $040A
        NOP,                  # 2 cycles  $040B
        NOP,                  # 2 cycles  $040C
        NOP,                  # 2 cycles  $040D
        NOP,                  # 2 cycles  $040E
    ]
    data = {
        0xFFFE: 0x00,
        0xFFFF: 0x05,
        0x0500: LDA_IMM,
        0x0501: 0x99,
    }

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for addr, val in data.items():
        dut.ram.mem[addr].value = val

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)
    await ClockCycles(dut.i_clk, 6)

    # Let LDX, TXS, SEI execute: 2+2+2 = 6 cycles
    await ClockCycles(dut.i_clk, 6)

    # Assert IRQ while I flag is set
    dut.i_irq_n.value = 0

    # Run more cycles - IRQ should NOT fire
    await ClockCycles(dut.i_clk, 20)

    # A should still be 0x42 from LDA, not 0x99 from handler
    assert_acc(dut, 0x42)
    # SP should be untouched (nothing pushed)
    assert_sp(dut, 0xFF)


# ============================================================
# NMI - Non-Maskable Interrupt (active low, edge-triggered)
# ============================================================

@cocotb.test()
async def test_nmi_basic(dut):
    """NMI fires even when I flag is set (non-maskable)."""
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles  $0400
        TXS,                  # 2 cycles  $0402
        SEI,                  # 2 cycles  $0403
        LDA_IMM, 0x01,       # 2 cycles  $0404
        NOP,                  # 2 cycles  $0406
        NOP,                  # 2 cycles  $0407
        NOP,                  # 2 cycles  $0408
        NOP,                  # 2 cycles  $0409
    ]
    # NMI handler at $0600 does LDA #$BB then NOPs
    data = {
        0xFFFA: 0x00,         # NMI vector low byte
        0xFFFB: 0x06,         # NMI vector high byte
        0x0600: LDA_IMM,      # handler: LDA #$BB
        0x0601: 0xBB,
        0x0602: NOP,          # padding for remaining cycles
        0x0603: NOP,
        0x0604: NOP,
        0x0605: NOP,
        0x0606: NOP,
        0x0607: NOP,
    }

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for addr, val in data.items():
        dut.ram.mem[addr].value = val

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)
    await ClockCycles(dut.i_clk, 6)

    # Let LDX, TXS, SEI, LDA execute: 2+2+2+2 = 8 cycles
    await ClockCycles(dut.i_clk, 8)

    # Trigger NMI (falling edge)
    dut.i_nmi_n.value = 0

    # Wait for NMI to be serviced: 7 cycles + LDA(2) + NOPs
    await ClockCycles(dut.i_clk, 20)

    # NMI should fire despite I flag being set
    assert_acc(dut, 0xBB)
    assert_sp(dut, 0xFC)


@cocotb.test()
async def test_nmi_rti(dut):
    """NMI fires, handler does RTI, original program resumes."""
    # Program: after NMI+RTI, execution continues with LDA #$42
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles  $0400
        TXS,                  # 2 cycles  $0402
        LDA_IMM, 0x01,       # 2 cycles  $0403
        NOP,                  # 2 cycles  $0405
        NOP,                  # 2 cycles  $0406
        NOP,                  # 2 cycles  $0407
        NOP,                  # 2 cycles  $0408
        LDA_IMM, 0x42,       # 2 cycles  $0409 - should execute after RTI
        NOP,                  # 2 cycles  $040B - padding for remaining cycles
        NOP,                  # 2 cycles  $040C
        NOP,                  # 2 cycles  $040D
        NOP,                  # 2 cycles  $040E
    ]
    # NMI handler at $0600 does LDA #$BB then RTI
    data = {
        0xFFFA: 0x00,         # NMI vector low byte
        0xFFFB: 0x06,         # NMI vector high byte
        0x0600: LDA_IMM,      # handler: LDA #$BB
        0x0601: 0xBB,
        0x0602: RTI,          # handler: RTI
    }

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for addr, val in data.items():
        dut.ram.mem[addr].value = val

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)
    await ClockCycles(dut.i_clk, 6)

    # Let LDX, TXS, LDA execute: 2+2+2 = 6 cycles
    await ClockCycles(dut.i_clk, 6)

    # Trigger NMI (falling edge)
    dut.i_nmi_n.value = 0
    await ClockCycles(dut.i_clk, 2)
    # Release NMI so it doesn't re-trigger after RTI
    dut.i_nmi_n.value = 1

    # Wait for NMI service (7 cycles) + LDA(2) + RTI(6) + remaining NOPs + LDA #$42(2) + NOPs
    await ClockCycles(dut.i_clk, 30)

    # After RTI, execution resumes and LDA #$42 should execute
    assert_acc(dut, 0x42)
    # SP should be back to $FF after RTI restores it
    assert_sp(dut, 0xFF)


@cocotb.test()
async def test_irq_after_rti_sustained(dut):
    """
    Test for IRQ-after-RTI bug: When RTI completes and clears the I flag,
    if the IRQ line is still asserted, the CPU should correctly handle the IRQ
    again without getting stuck in an infinite loop or corrupting PC.

    This test keeps IRQ asserted during multiple RTI cycles to verify:
    1. RTI doesn't get stuck fetching from vector addresses ($FFFE/$FFFF)
    2. PC doesn't get corrupted by the first_microinstruction/handle_irq race
    3. Multiple consecutive IRQs after RTI work correctly
    """
    # Simpler program following test_irq_basic pattern
    prog = [
        LDX_IMM, 0xFF,       # 2 cycles
        TXS,                  # 2 cycles
        CLI,                  # 2 cycles: Enable interrupts
        NOP,                  # 2 cycles
        NOP,                  # 2 cycles
        NOP,                  # 2 cycles
    ]

    # IRQ handler: increment $0200, then RTI
    data = {
        0xFFFE: 0x00,         # IRQ vector -> $0500
        0xFFFF: 0x05,
        0x0200: 0x00,         # IRQ counter
        0x0500: INC_ABS,      # INC $0200 (6 cycles)
        0x0501: 0x00,
        0x0502: 0x02,
        0x0503: RTI,          # RTI (6 cycles)
    }

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for addr, val in data.items():
        dut.ram.mem[addr].value = val

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)
    await ClockCycles(dut.i_clk, 6)

    # Execute LDX, TXS, CLI: 2+2+2 = 6 cycles
    await ClockCycles(dut.i_clk, 6)

    # Assert IRQ (active low)
    dut.i_irq_n.value = 0

    # Wait for first IRQ:  7 (interrupt) + 6 (INC) + 6 (RTI) = 19 cycles
    await ClockCycles(dut.i_clk, 20)

    # Check first IRQ fired
    counter = int(dut.ram.mem[0x0200].value)
    assert counter >= 1, f"First IRQ should have fired, counter={counter}"

    # Since IRQ is still asserted, more IRQs should fire after each RTI
    # Wait for 3 more IRQs
    await ClockCycles(dut.i_clk, 20 * 3)

    # Check multiple IRQs fired
    counter = int(dut.ram.mem[0x0200].value)
    assert counter >= 3, f"Multiple IRQs should have fired, counter={counter}"

    # CPU should not be stuck at vector addresses
    pc = get_pc(dut)
    assert pc < 0xFFF0, f"PC stuck at vector region: {pc:#06x}"

    # De-assert IRQ
    dut.i_irq_n.value = 1
    await ClockCycles(dut.i_clk, 20)

    # Final checks
    final_counter = int(dut.ram.mem[0x0200].value)
    assert final_counter >= 3, f"Expected >= 3 IRQs, got {final_counter}"

    # I flag should be CLEAR (restored by RTI from pre-IRQ status where we did CLI)
    # Each IRQ sets I=1 during handling, but RTI restores I=0 from stack
    assert_flag(dut, SR_I, 0, "I")

    assert_pc(dut, 0x0406)

    # Stack should be reasonable
    sp = get_sp(dut)
    assert sp >= 0xF0, f"Stack corrupted: {sp:#04x}"


# ============================================================
# Instruction Sequence Tests
# ============================================================
# Tests for specific instruction patterns that can reveal
# timing or state propagation issues.

@cocotb.test()
async def test_seq_beq_page_cross_backward(dut):
    """BEQ backward branch crossing page boundary (takes extra cycle)."""
    # Jump to code positioned near page boundary, then branch backward across it
    prog = [
        JMP_ABS, 0xFE, 0x04,  # Jump to $04FE
    ]
    # Code near page boundary:
    # $04F0: NOP - landing target (on page $04)
    # $04FE: LDA #$00 - sets Z=1
    # $0500: BEQ $EE - branches back to $04F0 (crosses from page $05 to $04)
    data = {
        0x04F0: NOP,
        0x04FE: LDA_IMM,
        0x04FF: 0x00,
        0x0500: BEQ,
        0x0501: 0xEE,         # offset to reach $04F0: $04F0 - $0502 = -$12 = $EE
        0x04F1: NOP,          # After landing, run a NOP
    }
    # JMP(3) + LDA(2) + BEQ taken+page cross(4) + NOP(2) + NOP(2) = 13 cycles
    await setup_and_run(dut, prog, data=data, cycles=13)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_pc(dut, 0x04F2)  # Landed at $04F0, executed 2 NOPs

@cocotb.test()
async def test_seq_beq_page_cross_forward(dut):
    """BEQ forward branch crossing page boundary (takes extra cycle)."""
    # Position BEQ so PC after fetch is near end of page, branch forward crosses to next page
    # BEQ at $05EE, operand at $05EF, PC after fetch = $05F0 (page $05)
    # Offset $20 -> target = $0610 (page $06) - crosses page boundary
    prog = [
        JMP_ABS, 0xEC, 0x05,  # Jump to $05EC
    ]
    data = {
        0x05EC: LDA_IMM,
        0x05ED: 0x00,         # A = 0, Z = 1
        0x05EE: BEQ,
        0x05EF: 0x20,         # PC after fetch = $05F0, target = $0610 (page cross!)
        0x05F0: LDA_IMM,      # skipped (and next bytes)
        0x05F1: 0xFF,
        0x0610: NOP,          # landing target on page $06
    }
    # JMP(3) + LDA(2) + BEQ taken+page cross(4) + NOP(2) = 11 cycles
    await setup_and_run(dut, prog, data=data, cycles=11)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_pc(dut, 0x0611)

@cocotb.test()
async def test_seq_dey_cpy_beq(dut):
    """DEY / CPY #0 / BEQ - Pattern from Klaus branch range test."""
    prog = [
        LDY_IMM, 0x01,      # Y = 1
        DEY,                 # Y = 0
        CPY_IMM, 0x00,      # Compare Y with 0 (should set Z=1)
        BEQ, 0x02,          # Branch +2 if Z=1 (should take)
        LDA_IMM, 0xFF,      # Should be skipped
        NOP,                 # Landing target
    ]
    # LDY(2) + DEY(2) + CPY(2) + BEQ taken(3) + NOP(2) = 11 cycles
    await setup_and_run(dut, prog, cycles=11)
    assert_y(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_pc(dut, START_PC + len(prog))  # Jumped past LDA

@cocotb.test()
async def test_seq_ldx_dex_bne_loop(dut):
    """LDX / DEX / BNE countdown loop."""
    prog = [
        LDX_IMM, 0x03,      # X = 3
        # loop:
        DEX,                 # X = X - 1
        BNE, 0xFD,          # Branch back to DEX (-3) if X != 0
        NOP,                 # Exit point
    ]
    # LDX(2) + [DEX(2)+BNE taken(3)]*2 + [DEX(2)+BNE not taken(2)] + NOP(2) = 18 cycles
    await setup_and_run(dut, prog, cycles=18)
    assert_x(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")

@cocotb.test()
async def test_seq_lda_beq_zero(dut):
    """LDA #$00 / BEQ - Load zero then branch on zero."""
    prog = [
        LDA_IMM, 0x00,      # A = 0, Z = 1
        BEQ, 0x02,          # Branch +2 (should take)
        LDA_IMM, 0xFF,      # Should be skipped
        NOP,                 # Landing target
    ]
    # LDA(2) + BEQ taken(3) + NOP(2) = 7 cycles
    await setup_and_run(dut, prog, cycles=7)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")
    assert_pc(dut, START_PC + len(prog))

@cocotb.test()
async def test_seq_lda_bne_nonzero(dut):
    """LDA #$42 / BNE - Load nonzero then branch on not zero."""
    prog = [
        LDA_IMM, 0x42,      # A = $42, Z = 0
        BNE, 0x02,          # Branch +2 (should take)
        LDA_IMM, 0xFF,      # Should be skipped
        NOP,                 # Landing target
    ]
    # LDA(2) + BNE taken(3) + NOP(2) = 7 cycles
    await setup_and_run(dut, prog, cycles=7)
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_Z, 0, "Z")
    assert_pc(dut, START_PC + len(prog))

@cocotb.test()
async def test_seq_pha_pla_roundtrip(dut):
    """PHA / PHA / PLA / PLA - Stack push/pull sequence."""
    prog = [
        LDA_IMM, 0x42,      # A = $42
        PHA,                 # Push $42
        LDA_IMM, 0x55,      # A = $55
        PHA,                 # Push $55
        LDA_IMM, 0x00,      # Clear A
        PLA,                 # Pull -> A = $55
        PLA,                 # Pull -> A = $42
    ]
    # LDA(2) + PHA(3) + LDA(2) + PHA(3) + LDA(2) + PLA(4) + PLA(4) = 20 cycles
    await setup_and_run(dut, prog, cycles=20)
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_seq_jsr_rts(dut):
    """JSR / RTS - Subroutine call and return."""
    # JSR to subroutine at START_PC + 6, which has RTS
    prog = [
        JSR_ABS, lo(START_PC + 6), hi(START_PC + 6),  # JSR to subroutine
        NOP,                 # Return point (START_PC + 3)
        NOP,                 # Filler
        NOP,                 # Filler
        RTS_IMP,            # Subroutine at START_PC + 6
    ]
    # JSR(6) + RTS(6) + NOP(2) = 14 cycles
    await setup_and_run(dut, prog, cycles=14)
    # After JSR and RTS, PC should be at START_PC + 4 (NOP after JSR)
    assert_pc(dut, START_PC + 4)

@cocotb.test()
async def test_seq_sta_lda_roundtrip(dut):
    """STA / LDA - Write to memory then read back."""
    prog = [
        LDA_IMM, 0xAB,      # A = $AB
        STA_ZP, 0x50,       # Store to ZP $50
        LDA_IMM, 0x00,      # Clear A
        LDA_ZP, 0x50,       # Load from ZP $50
    ]
    # LDA(2) + STA zp(3) + LDA(2) + LDA zp(3) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0xAB)

@cocotb.test()
async def test_seq_inc_dec_memory(dut):
    """INC / DEC memory - Modify memory value."""
    prog = [
        LDA_IMM, 0x10,      # A = $10
        STA_ZP, 0x50,       # Store to ZP $50
        INC_ZP, 0x50,       # Increment ZP $50 -> $11
        INC_ZP, 0x50,       # Increment ZP $50 -> $12
        DEC_ZP, 0x50,       # Decrement ZP $50 -> $11
        LDA_ZP, 0x50,       # Load result
    ]
    # LDA(2) + STA zp(3) + INC zp(5) + INC zp(5) + DEC zp(5) + LDA zp(3) = 23 cycles
    await setup_and_run(dut, prog, cycles=23)
    assert_acc(dut, 0x11)

@cocotb.test()
async def test_seq_adc_chain(dut):
    """Multi-byte add with carry propagation."""
    # Add $00FF + $0001 = $0100 (16-bit)
    prog = [
        CLC,                 # Clear carry
        LDA_IMM, 0xFF,      # Low byte of first operand
        ADC_IMM, 0x01,      # Add low byte of second (FF + 01 = 00, C=1)
        STA_ZP, 0x50,       # Store low result
        LDA_IMM, 0x00,      # High byte of first operand
        ADC_IMM, 0x00,      # Add high byte + carry (00 + 00 + 1 = 01)
        STA_ZP, 0x51,       # Store high result
    ]
    # CLC(2) + LDA(2) + ADC(2) + STA zp(3) + LDA(2) + ADC(2) + STA zp(3) = 16 cycles
    await setup_and_run(dut, prog, cycles=16)
    assert_acc(dut, 0x01)  # High byte is $01

@cocotb.test()
async def test_seq_compare_branch(dut):
    """CMP / Branch pattern for range checking."""
    prog = [
        LDA_IMM, 0x50,      # A = $50
        CMP_IMM, 0x40,      # Compare A with $40 (A > value, so C=1, Z=0)
        BCS, 0x02,          # Branch if carry set (should take)
        LDA_IMM, 0xFF,      # Should be skipped
        NOP,                 # Landing
    ]
    # LDA(2) + CMP(2) + BCS taken(3) + NOP(2) = 9 cycles
    await setup_and_run(dut, prog, cycles=9)
    assert_acc(dut, 0x50)
    assert_flag(dut, SR_C, 1, "C")
    assert_pc(dut, START_PC + len(prog))

@cocotb.test()
async def test_seq_lda_cmp_zero(dut):
    """LDA #$00 / CMP #$00 - Load zero, compare with zero, check flags."""
    prog = [
        LDA_IMM, 0x00,      # A = 0, sets Z=1, N=0
        CMP_IMM, 0x00,      # Compare A with 0: A-0=0, sets Z=1, N=0, C=1
    ]
    # LDA(2) + CMP(2) = 4 cycles
    await setup_and_run(dut, prog, cycles=4)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 1, "Z")  # Result is zero
    assert_flag(dut, SR_N, 0, "N")  # Result is not negative
    assert_flag(dut, SR_C, 1, "C")  # A >= operand (no borrow)

@cocotb.test()
async def test_seq_lda_cmp_less(dut):
    """LDA #$00 / CMP #$01 - Load zero, compare with 1, A < operand."""
    prog = [
        LDA_IMM, 0x00,      # A = 0
        CMP_IMM, 0x01,      # Compare A with 1: A-1 = $FF, sets Z=0, N=1, C=0
    ]
    # LDA(2) + CMP(2) = 4 cycles
    await setup_and_run(dut, prog, cycles=4)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_Z, 0, "Z")  # Result not zero (A != operand)
    assert_flag(dut, SR_N, 1, "N")  # Result $FF is negative
    assert_flag(dut, SR_C, 0, "C")  # A < operand (borrow occurred)


# ============================================================
# BCD (Binary Coded Decimal) Tests
# ============================================================
# Tests for ADC/SBC in decimal mode (D flag set).
# Each nibble represents a decimal digit (0-9).

@cocotb.test()
async def test_bcd_adc_simple(dut):
    """BCD ADC: $09 + $01 = $10 (9 + 1 = 10 decimal)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry
        LDA_IMM, 0x09,      # A = $09 (9 decimal)
        ADC_IMM, 0x01,      # A = $09 + $01 = $10 (10 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x10)
    assert_flag(dut, SR_C, 0, "C")  # No carry

@cocotb.test()
async def test_bcd_adc_two_digit(dut):
    """BCD ADC: $15 + $27 = $42 (15 + 27 = 42 decimal)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry
        LDA_IMM, 0x15,      # A = $15 (15 decimal)
        ADC_IMM, 0x27,      # A = $15 + $27 = $42 (42 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x42)
    assert_flag(dut, SR_C, 0, "C")  # No carry

@cocotb.test()
async def test_bcd_adc_carry_out(dut):
    """BCD ADC: $99 + $01 = $00 with C=1 (99 + 1 = 100 decimal, wraps)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry
        LDA_IMM, 0x99,      # A = $99 (99 decimal)
        ADC_IMM, 0x01,      # A = $99 + $01 = $00, C=1 (100 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")  # Carry set (overflow past 99)

@cocotb.test()
async def test_bcd_adc_with_carry_in(dut):
    """BCD ADC: $49 + $50 + 1 = $00 with C=1 (49 + 50 + 1 = 100)."""
    prog = [
        SED,                 # Set decimal mode
        SEC,                 # Set carry (input carry = 1)
        LDA_IMM, 0x49,      # A = $49 (49 decimal)
        ADC_IMM, 0x50,      # A = $49 + $50 + 1 = $00, C=1 (100 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + SEC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")  # Carry set

@cocotb.test()
async def test_bcd_sbc_simple(dut):
    """BCD SBC: $10 - $01 = $09 (10 - 1 = 9 decimal)."""
    prog = [
        SED,                 # Set decimal mode
        SEC,                 # Set carry (no borrow)
        LDA_IMM, 0x10,      # A = $10 (10 decimal)
        SBC_IMM, 0x01,      # A = $10 - $01 = $09 (9 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + SEC(2) + LDA(2) + SBC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x09)
    assert_flag(dut, SR_C, 1, "C")  # No borrow (C=1 means no borrow)

@cocotb.test()
async def test_bcd_sbc_two_digit(dut):
    """BCD SBC: $42 - $15 = $27 (42 - 15 = 27 decimal)."""
    prog = [
        SED,                 # Set decimal mode
        SEC,                 # Set carry (no borrow)
        LDA_IMM, 0x42,      # A = $42 (42 decimal)
        SBC_IMM, 0x15,      # A = $42 - $15 = $27 (27 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + SEC(2) + LDA(2) + SBC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x27)
    assert_flag(dut, SR_C, 1, "C")  # No borrow

@cocotb.test()
async def test_bcd_sbc_borrow(dut):
    """BCD SBC: $00 - $01 = $99 with C=0 (0 - 1 = -1, wraps to 99)."""
    prog = [
        SED,                 # Set decimal mode
        SEC,                 # Set carry (no borrow initially)
        LDA_IMM, 0x00,      # A = $00 (0 decimal)
        SBC_IMM, 0x01,      # A = $00 - $01 = $99, C=0 (borrow)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + SEC(2) + LDA(2) + SBC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x99)
    assert_flag(dut, SR_C, 0, "C")  # Borrow occurred (C=0)

@cocotb.test()
async def test_bcd_sbc_with_borrow_in(dut):
    """BCD SBC: $50 - $49 - 1 = $00 (50 - 49 - 1 = 0, with borrow in)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry (borrow in = 1)
        LDA_IMM, 0x50,      # A = $50 (50 decimal)
        SBC_IMM, 0x49,      # A = $50 - $49 - 1 = $00
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + SBC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x00)
    assert_flag(dut, SR_C, 1, "C")  # No borrow out

@cocotb.test()
async def test_bcd_adc_both_nibbles_adjust(dut):
    """BCD ADC: $19 + $19 = $38 (19 + 19 = 38, both nibbles need adjust)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry
        LDA_IMM, 0x19,      # A = $19 (19 decimal)
        ADC_IMM, 0x19,      # A = $19 + $19 = $38 (38 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x38)
    assert_flag(dut, SR_C, 0, "C")  # No carry

@cocotb.test()
async def test_bcd_adc_upper_nibble_carry(dut):
    """BCD ADC: $81 + $92 = $73 with C=1 (81 + 92 = 173 decimal)."""
    prog = [
        SED,                 # Set decimal mode
        CLC,                 # Clear carry
        LDA_IMM, 0x81,      # A = $81 (81 decimal)
        ADC_IMM, 0x92,      # A = $81 + $92 = $73, C=1 (173 decimal)
        CLD,                 # Clear decimal mode
    ]
    # SED(2) + CLC(2) + LDA(2) + ADC(2) + CLD(2) = 10 cycles
    await setup_and_run(dut, prog, cycles=10)
    assert_acc(dut, 0x73)
    assert_flag(dut, SR_C, 1, "C")  # Carry set (result > 99)

# ============================================================
# RDY Signal Tests
# ============================================================

@cocotb.test()
async def test_rdy_pauses_cpu(dut):
    """When i_rdy is low, CPU should pause and not advance PC."""
    prog = [
        LDA_IMM, 0x11,      # A = $11
        LDA_IMM, 0x22,      # A = $22
        LDA_IMM, 0x33,      # A = $33
        LDA_IMM, 0x44,      # A = $44
        NOP,
    ]
    
    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1
    
    await ClockCycles(dut.i_clk, 2)
    
    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    
    # Release reset and wait for init
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)
    
    # Run first instruction (LDA #$11) - 2 cycles
    await ClockCycles(dut.i_clk, 2)
    assert_acc(dut, 0x11)
    pc_after_first = get_pc(dut)
    
    # Now pause the CPU by setting i_rdy low
    dut.i_rdy.value = 0
    
    # Run many clock cycles while paused
    await ClockCycles(dut.i_clk, 20)
    
    # PC and ACC should not have changed
    assert_pc(dut, pc_after_first)
    assert_acc(dut, 0x11)
    
    # Resume by setting i_rdy high
    dut.i_rdy.value = 1
    
    # Run next instruction (LDA #$22) - 2 cycles
    await ClockCycles(dut.i_clk, 2)
    assert_acc(dut, 0x22)
    
    # Continue to verify CPU is running normally
    await ClockCycles(dut.i_clk, 2)
    assert_acc(dut, 0x33)

async def wait_for_sync(dut, timeout=100):
    """Wait for o_sync to go high (opcode fetch cycle)."""
    for _ in range(timeout):
        await RisingEdge(dut.i_clk)
        if int(dut.cpu_6502.o_sync.value) == 1:
            return True
    return False

async def single_step(dut):
    """Execute one instruction by resuming until next SYNC."""
    dut.i_rdy.value = 1
    # Wait for next SYNC (marks start of next instruction = end of current)
    await wait_for_sync(dut)
    # Pause immediately
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 1)

@cocotb.test()
async def test_rdy_single_step(dut):
    """Use i_rdy and o_sync to single-step through instructions."""
    prog = [
        LDA_IMM, 0xAA,      # A = $AA
        TAX,                # X = A
        INX,                # X = X + 1
        TXA,                # A = X
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1  # RDY must be high during reset/init
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b

    # Release reset and wait for init to complete
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Wait for first SYNC (start of LDA), then pause
    await wait_for_sync(dut)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 5)  # verify CPU stays paused

    # Step through LDA #$AA
    await single_step(dut)
    assert_acc(dut, 0xAA)

    # Step through TAX
    await single_step(dut)
    assert_x(dut, 0xAA)

    # Step through INX
    await single_step(dut)
    assert_x(dut, 0xAB)

    # Step through TXA
    await single_step(dut)
    assert_acc(dut, 0xAB)

@cocotb.test()
async def test_rdy_mid_instruction(dut):
    """Pause RDY in the middle of a multi-cycle instruction (LDA absolute = 4 cycles)."""
    prog = [
        LDA_ABS, 0x00, 0x06,   # LDA $0600  (4 cycles)
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    dut.ram.mem[0x0600].value = 0xBE

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Wait for sync (opcode fetch = cycle 1 of 4 for LDA absolute)
    await wait_for_sync(dut)
    pc_before = get_pc(dut)

    # Pause after opcode fetch (mid-instruction)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 30)

    # State should be frozen
    assert_pc(dut, pc_before)

    # Resume — 3 remaining cycles (fetch addr low, fetch addr high, read data)
    dut.i_rdy.value = 1
    await ClockCycles(dut.i_clk, 3)

    assert_acc(dut, 0xBE)

@cocotb.test()
async def test_rdy_preserves_all_registers(dut):
    """Verify RDY=0 freezes A, X, Y, SP, SR, and PC."""
    prog = [
        LDA_IMM, 0x42,         # A = $42
        LDX_IMM, 0x37,         # X = $37
        LDY_IMM, 0x9A,         # Y = $9A
        SEC,                   # set carry
        NOP,
        NOP,
    ]

    await setup_and_run(dut, prog, cycles=8)

    # Capture full CPU state
    expected_a = get_acc(dut)
    expected_x = get_x(dut)
    expected_y = get_y(dut)
    expected_sp = get_sp(dut)
    expected_sr = get_sr(dut)
    expected_pc = get_pc(dut)

    # Pause
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 50)

    # Verify everything is frozen
    assert_acc(dut, expected_a)
    assert_x(dut, expected_x)
    assert_y(dut, expected_y)
    assert_sp(dut, expected_sp)
    assert_pc(dut, expected_pc)
    actual_sr = get_sr(dut)
    assert actual_sr == expected_sr, \
        f"SR: expected {expected_sr:#04x}, got {actual_sr:#04x}"

    # Resume and verify CPU continues
    dut.i_rdy.value = 1
    await ClockCycles(dut.i_clk, 2)
    # NOP should have executed, PC advanced
    assert get_pc(dut) != expected_pc, "PC should advance after resume"

@cocotb.test()
async def test_rdy_during_store(dut):
    """Pause during a STA absolute (write instruction)."""
    prog = [
        LDA_IMM, 0xCD,         # A = $CD
        STA_ABS, 0x00, 0x07,   # STA $0700  (4 cycles)
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    dut.ram.mem[0x0700].value = 0x00

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Execute LDA #$CD (2 cycles)
    await ClockCycles(dut.i_clk, 2)
    assert_acc(dut, 0xCD)

    # Start STA, run 1 cycle, then pause
    await ClockCycles(dut.i_clk, 1)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 20)

    # Resume and let STA complete
    dut.i_rdy.value = 1
    await ClockCycles(dut.i_clk, 10)

    # Verify the store completed
    val = await read_mem(dut, 0x0700)
    assert val == 0xCD, f"MEM[$0700]: expected $CD, got ${val:02x}"

@cocotb.test()
async def test_rdy_during_jsr_rts(dut):
    """Pause during JSR and RTS (stack-heavy multi-cycle instructions)."""
    # Main code at $0400
    # Subroutine at $0500
    prog = [
        LDA_IMM, 0x11,         # A = $11
        JSR_ABS, 0x00, 0x05,   # JSR $0500  (6 cycles)
        LDA_IMM, 0x33,         # A = $33 (return here)
        NOP,
    ]
    sub = [
        LDA_IMM, 0x22,         # A = $22
        RTS_IMP,               # RTS (6 cycles)
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    for i, b in enumerate(sub):
        dut.ram.mem[0x0500 + i].value = b

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Execute LDA #$11
    await ClockCycles(dut.i_clk, 2)
    assert_acc(dut, 0x11)

    # Start JSR, run 2 cycles into it, then pause
    await ClockCycles(dut.i_clk, 2)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 20)
    dut.i_rdy.value = 1

    # Let JSR finish + execute subroutine LDA #$22
    await ClockCycles(dut.i_clk, 10)
    assert_acc(dut, 0x22)

    # Pause mid-RTS
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 20)
    dut.i_rdy.value = 1

    # Let RTS complete + execute LDA #$33
    await ClockCycles(dut.i_clk, 15)
    assert_acc(dut, 0x33)

@cocotb.test()
async def test_rdy_during_push_pull(dut):
    """Pause during PHA (3 cycles) and PLA (4 cycles)."""
    prog = [
        LDA_IMM, 0xAB,        # A = $AB  (2 cycles)
        PHA,                   # push A   (3 cycles)
        LDA_IMM, 0x00,        # A = $00  (2 cycles)
        PLA,                   # pull A   (4 cycles), A = $AB again
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Sync for LDA #$AB, complete it (1 remaining cycle)
    await wait_for_sync(dut)
    await ClockCycles(dut.i_clk, 1)
    assert_acc(dut, 0xAB)

    # Sync for PHA (opcode fetch = cycle 1 of 3)
    await wait_for_sync(dut)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 15)
    dut.i_rdy.value = 1
    # 2 remaining cycles for PHA
    await ClockCycles(dut.i_clk, 2)

    # Sync for LDA #$00, complete it (1 remaining cycle)
    await wait_for_sync(dut)
    await ClockCycles(dut.i_clk, 1)
    assert_acc(dut, 0x00)

    # Sync for PLA (opcode fetch = cycle 1 of 4)
    await wait_for_sync(dut)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 15)
    dut.i_rdy.value = 1
    # 3 remaining cycles for PLA
    await ClockCycles(dut.i_clk, 3)

    assert_acc(dut, 0xAB)

@cocotb.test()
async def test_rdy_during_taken_branch(dut):
    """Pause during a taken branch instruction."""
    prog = [
        LDA_IMM, 0x00,        # A = 0 (sets Z flag)
        BEQ, 0x02,            # BEQ +2 (skip next 2 bytes) — taken, 3 cycles
        LDA_IMM, 0xFF,        # skipped
        LDA_IMM, 0x42,        # branch lands here
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # LDA #$00 (2 cycles)
    await ClockCycles(dut.i_clk, 2)

    # Start BEQ, pause 1 cycle in
    await ClockCycles(dut.i_clk, 1)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 20)
    dut.i_rdy.value = 1

    # Let branch + LDA #$42 complete
    await ClockCycles(dut.i_clk, 10)
    assert_acc(dut, 0x42)

@cocotb.test()
async def test_rdy_during_rmw(dut):
    """Pause during a read-modify-write instruction (INC zeropage = 5 cycles)."""
    prog = [
        INC_ZP, 0x10,         # INC $10  (5 cycles)
        INC_ZP, 0x10,         # INC $10  (5 cycles)
        NOP,
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    dut.ram.mem[0x10].value = 0x40

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Start first INC, pause 2 cycles in (during read-modify-write sequence)
    await ClockCycles(dut.i_clk, 2)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 20)
    dut.i_rdy.value = 1

    # Let both INCs complete
    await ClockCycles(dut.i_clk, 15)

    val = await read_mem(dut, 0x10)
    assert val == 0x42, f"MEM[$10]: expected $42, got ${val:02x}"

@cocotb.test()
async def test_rdy_rapid_toggle(dut):
    """Toggle RDY every cycle — CPU should still execute correctly, just slowly."""
    prog = [
        LDA_IMM, 0x10,        # A = $10
        ADC_IMM, 0x20,        # A = $30  (carry clear from reset)
        TAX,                  # X = $30
        INX,                  # X = $31
        JMP_ABS, 0x06, 0x04,  # spin forever at $0406 (self-loop)
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # Toggle RDY every cycle for 50 cycles
    # (enough for all instructions even at half speed)
    for _ in range(50):
        dut.i_rdy.value = 1
        await ClockCycles(dut.i_clk, 1)
        dut.i_rdy.value = 0
        await ClockCycles(dut.i_clk, 1)

    # Let any remaining instruction finish
    dut.i_rdy.value = 1
    await ClockCycles(dut.i_clk, 10)

    assert_acc(dut, 0x30)
    assert_x(dut, 0x31)

@cocotb.test()
async def test_rdy_during_indirect_indexed(dut):
    """Pause during LDA (indirect),Y — a 5-6 cycle instruction with pointer fetch."""
    prog = [
        LDY_IMM, 0x04,            # Y = $04
        LDA_IZY, 0x20,            # LDA ($20),Y — reads pointer from $20/$21,
        NOP,                      #   adds Y, loads from effective address
    ]

    Clock(dut.i_clk, 100, "ns").start()
    dut.i_reset_n.value = 0
    dut.i_rdy.value = 1
    dut.i_nmi_n.value = 1
    dut.i_irq_n.value = 1

    await ClockCycles(dut.i_clk, 2)

    for i, b in enumerate(prog):
        dut.ram.mem[START_PC + i].value = b
    # Pointer at $20/$21 → $0600
    dut.ram.mem[0x20].value = 0x00
    dut.ram.mem[0x21].value = 0x06
    # Data at $0604 (base $0600 + Y=$04)
    dut.ram.mem[0x0604].value = 0x77

    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 8)

    # LDY #$04 (2 cycles)
    await ClockCycles(dut.i_clk, 2)

    # Start LDA (ind),Y — pause 2 cycles in (during pointer fetch)
    await ClockCycles(dut.i_clk, 2)
    dut.i_rdy.value = 0
    await ClockCycles(dut.i_clk, 25)
    dut.i_rdy.value = 1

    # Let instruction complete
    await ClockCycles(dut.i_clk, 10)
    assert_acc(dut, 0x77)
