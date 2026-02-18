`ifndef CPU_6502_INSTRUCTIONS_VH
`define CPU_6502_INSTRUCTIONS_VH

/* verilator lint_off UNUSEDPARAM */
// ============================================================
// 6502 Opcode Encoding: aaabbbcc
//
// cc=01: ALU group        (ORA, AND, EOR, ADC, STA, LDA, CMP, SBC)
// cc=10: Shift/RMW group  (ASL, ROL, LSR, ROR, STX, LDX, DEC, INC)
// cc=00: Control group    (BIT, JMP, STY, LDY, CPY, CPX)
// ============================================================

typedef enum logic [3:0] {
    IMMEDIATE, ZP, ZP_X, ZP_Y, IMPLIED,
    INDIRECT, INDEX_X_INDIRECT,
    INDEX_Y_INDIRECT, RELATIVE, ABSOLUTE,
    ABSOLUTE_X, ABSOLUTE_Y, ACCUMULATOR
} operand_type_t;

// ============================================================
// casex patterns — use with casex(opcode)
// ============================================================

// --- cc=01: ALU group — 8'baaa_xxx_01 ---
//
//  bbb | Mode
//  000 | (indirect,X)
//  001 | zero page
//  010 | immediate
//  011 | absolute
//  100 | (indirect),Y
//  101 | zero page,X
//  110 | absolute,Y
//  111 | absolute,X

localparam OPCODE_TYPE_ORA = 8'b000???01;
localparam OPCODE_TYPE_AND = 8'b001???01;
localparam OPCODE_TYPE_EOR = 8'b010???01;
localparam OPCODE_TYPE_ADC = 8'b011???01;
localparam OPCODE_TYPE_STA = 8'b100???01;
localparam OPCODE_TYPE_LDA = 8'b101???01;
localparam OPCODE_TYPE_CMP = 8'b110???01;
localparam OPCODE_TYPE_SBC = 8'b111???01;

// --- cc=10: Shift/RMW group — 8'baaa_xxx_10 ---
//
//  bbb | Mode
//  000 | immediate       (LDX only)
//  001 | zero page
//  010 | accumulator     (shifts/rotates only)
//  011 | absolute
//  101 | zero page,X     (STX/LDX use zero page,Y)
//  111 | absolute,X      (LDX uses absolute,Y)

localparam OPCODE_TYPE_ASL = 8'b000???10;
localparam OPCODE_TYPE_ROL = 8'b001???10;
localparam OPCODE_TYPE_LSR = 8'b010???10;
localparam OPCODE_TYPE_ROR = 8'b011???10;
localparam OPCODE_TYPE_STX = 8'b100???10;
localparam OPCODE_TYPE_LDX = 8'b101???10;
localparam OPCODE_TYPE_DEC = 8'b110???10;
localparam OPCODE_TYPE_INC = 8'b111???10;

// --- cc=00: Control group — 8'baaa_xxx_00 ---
//
//  bbb | Mode
//  000 | immediate
//  001 | zero page
//  011 | absolute
//  101 | zero page,X
//  111 | absolute,X
//
// NOTE: bbb=100 overlaps with branches, bbb=010/110 with implied ops.
// Match branches and implied FIRST, then fall through to these.

localparam OPCODE_TYPE_BIT = 8'b001???00;
localparam OPCODE_TYPE_STY = 8'b100???00;
localparam OPCODE_TYPE_LDY = 8'b101???00;
localparam OPCODE_TYPE_CPY = 8'b110???00;
localparam OPCODE_TYPE_CPX = 8'b111???00;

// --- Branches — 8'bxxx_100_00 ---

localparam OPCODE_TYPE_BRANCH = 8'b???10000;

// ============================================================
// Individual opcodes
// ============================================================

// --- cc=01: ALU group ---

// ORA — 8'b000_bbb_01
localparam OPCODE_ORA_IZX   = 8'h01;  // 8'b000_000_01
localparam OPCODE_ORA_ZP    = 8'h05;  // 8'b000_001_01
localparam OPCODE_ORA_IMM   = 8'h09;  // 8'b000_010_01
localparam OPCODE_ORA_ABS   = 8'h0D;  // 8'b000_011_01
localparam OPCODE_ORA_IZY   = 8'h11;  // 8'b000_100_01
localparam OPCODE_ORA_ZP_X  = 8'h15;  // 8'b000_101_01
localparam OPCODE_ORA_ABS_Y = 8'h19;  // 8'b000_110_01
localparam OPCODE_ORA_ABS_X = 8'h1D;  // 8'b000_111_01

// AND — 8'b001_bbb_01
localparam OPCODE_AND_IZX   = 8'h21;  // 8'b001_000_01
localparam OPCODE_AND_ZP    = 8'h25;  // 8'b001_001_01
localparam OPCODE_AND_IMM   = 8'h29;  // 8'b001_010_01
localparam OPCODE_AND_ABS   = 8'h2D;  // 8'b001_011_01
localparam OPCODE_AND_IZY   = 8'h31;  // 8'b001_100_01
localparam OPCODE_AND_ZP_X  = 8'h35;  // 8'b001_101_01
localparam OPCODE_AND_ABS_Y = 8'h39;  // 8'b001_110_01
localparam OPCODE_AND_ABS_X = 8'h3D;  // 8'b001_111_01

// EOR — 8'b010_bbb_01
localparam OPCODE_EOR_IZX   = 8'h41;  // 8'b010_000_01
localparam OPCODE_EOR_ZP    = 8'h45;  // 8'b010_001_01
localparam OPCODE_EOR_IMM   = 8'h49;  // 8'b010_010_01
localparam OPCODE_EOR_ABS   = 8'h4D;  // 8'b010_011_01
localparam OPCODE_EOR_IZY   = 8'h51;  // 8'b010_100_01
localparam OPCODE_EOR_ZP_X  = 8'h55;  // 8'b010_101_01
localparam OPCODE_EOR_ABS_Y = 8'h59;  // 8'b010_110_01
localparam OPCODE_EOR_ABS_X = 8'h5D;  // 8'b010_111_01

// ADC — 8'b011_bbb_01
localparam OPCODE_ADC_IZX   = 8'h61;  // 8'b011_000_01
localparam OPCODE_ADC_ZP    = 8'h65;  // 8'b011_001_01
localparam OPCODE_ADC_IMM   = 8'h69;  // 8'b011_010_01
localparam OPCODE_ADC_ABS   = 8'h6D;  // 8'b011_011_01
localparam OPCODE_ADC_IZY   = 8'h71;  // 8'b011_100_01
localparam OPCODE_ADC_ZP_X  = 8'h75;  // 8'b011_101_01
localparam OPCODE_ADC_ABS_Y = 8'h79;  // 8'b011_110_01
localparam OPCODE_ADC_ABS_X = 8'h7D;  // 8'b011_111_01

// STA — 8'b100_bbb_01 (no immediate mode)
localparam OPCODE_STA_IZX   = 8'h81;  // 8'b100_000_01
localparam OPCODE_STA_ZP    = 8'h85;  // 8'b100_001_01
localparam OPCODE_STA_ABS   = 8'h8D;  // 8'b100_011_01
localparam OPCODE_STA_IZY   = 8'h91;  // 8'b100_100_01
localparam OPCODE_STA_ZP_X  = 8'h95;  // 8'b100_101_01
localparam OPCODE_STA_ABS_Y = 8'h99;  // 8'b100_110_01
localparam OPCODE_STA_ABS_X = 8'h9D;  // 8'b100_111_01

// LDA — 8'b101_bbb_01
localparam OPCODE_LDA_IZX   = 8'hA1;  // 8'b101_000_01
localparam OPCODE_LDA_ZP    = 8'hA5;  // 8'b101_001_01
localparam OPCODE_LDA_IMM   = 8'hA9;  // 8'b101_010_01
localparam OPCODE_LDA_ABS   = 8'hAD;  // 8'b101_011_01
localparam OPCODE_LDA_IZY   = 8'hB1;  // 8'b101_100_01
localparam OPCODE_LDA_ZP_X  = 8'hB5;  // 8'b101_101_01
localparam OPCODE_LDA_ABS_Y = 8'hB9;  // 8'b101_110_01
localparam OPCODE_LDA_ABS_X = 8'hBD;  // 8'b101_111_01

// CMP — 8'b110_bbb_01
localparam OPCODE_CMP_IZX   = 8'hC1;  // 8'b110_000_01
localparam OPCODE_CMP_ZP    = 8'hC5;  // 8'b110_001_01
localparam OPCODE_CMP_IMM   = 8'hC9;  // 8'b110_010_01
localparam OPCODE_CMP_ABS   = 8'hCD;  // 8'b110_011_01
localparam OPCODE_CMP_IZY   = 8'hD1;  // 8'b110_100_01
localparam OPCODE_CMP_ZP_X  = 8'hD5;  // 8'b110_101_01
localparam OPCODE_CMP_ABS_Y = 8'hD9;  // 8'b110_110_01
localparam OPCODE_CMP_ABS_X = 8'hDD;  // 8'b110_111_01

// SBC — 8'b111_bbb_01
localparam OPCODE_SBC_IZX   = 8'hE1;  // 8'b111_000_01
localparam OPCODE_SBC_ZP    = 8'hE5;  // 8'b111_001_01
localparam OPCODE_SBC_IMM   = 8'hE9;  // 8'b111_010_01
localparam OPCODE_SBC_ABS   = 8'hED;  // 8'b111_011_01
localparam OPCODE_SBC_IZY   = 8'hF1;  // 8'b111_100_01
localparam OPCODE_SBC_ZP_X  = 8'hF5;  // 8'b111_101_01
localparam OPCODE_SBC_ABS_Y = 8'hF9;  // 8'b111_110_01
localparam OPCODE_SBC_ABS_X = 8'hFD;  // 8'b111_111_01

// --- cc=10: Shift/RMW group ---

// ASL — 8'b000_bbb_10
localparam OPCODE_ASL_ZP    = 8'h06;  // 8'b000_001_10
localparam OPCODE_ASL_ACC   = 8'h0A;  // 8'b000_010_10
localparam OPCODE_ASL_ABS   = 8'h0E;  // 8'b000_011_10
localparam OPCODE_ASL_ZP_X  = 8'h16;  // 8'b000_101_10
localparam OPCODE_ASL_ABS_X = 8'h1E;  // 8'b000_111_10

// ROL — 8'b001_bbb_10
localparam OPCODE_ROL_ZP    = 8'h26;  // 8'b001_001_10
localparam OPCODE_ROL_ACC   = 8'h2A;  // 8'b001_010_10
localparam OPCODE_ROL_ABS   = 8'h2E;  // 8'b001_011_10
localparam OPCODE_ROL_ZP_X  = 8'h36;  // 8'b001_101_10
localparam OPCODE_ROL_ABS_X = 8'h3E;  // 8'b001_111_10

// LSR — 8'b010_bbb_10
localparam OPCODE_LSR_ZP    = 8'h46;  // 8'b010_001_10
localparam OPCODE_LSR_ACC   = 8'h4A;  // 8'b010_010_10
localparam OPCODE_LSR_ABS   = 8'h4E;  // 8'b010_011_10
localparam OPCODE_LSR_ZP_X  = 8'h56;  // 8'b010_101_10
localparam OPCODE_LSR_ABS_X = 8'h5E;  // 8'b010_111_10

// ROR — 8'b011_bbb_10
localparam OPCODE_ROR_ZP    = 8'h66;  // 8'b011_001_10
localparam OPCODE_ROR_ACC   = 8'h6A;  // 8'b011_010_10
localparam OPCODE_ROR_ABS   = 8'h6E;  // 8'b011_011_10
localparam OPCODE_ROR_ZP_X  = 8'h76;  // 8'b011_101_10
localparam OPCODE_ROR_ABS_X = 8'h7E;  // 8'b011_111_10

// STX — 8'b100_bbb_10 (uses Y index)
localparam OPCODE_STX_ZP    = 8'h86;  // 8'b100_001_10
localparam OPCODE_STX_ABS   = 8'h8E;  // 8'b100_011_10
localparam OPCODE_STX_ZP_Y  = 8'h96;  // 8'b100_101_10

// LDX — 8'b101_bbb_10 (uses Y index)
localparam OPCODE_LDX_IMM   = 8'hA2;  // 8'b101_000_10
localparam OPCODE_LDX_ZP    = 8'hA6;  // 8'b101_001_10
localparam OPCODE_LDX_ABS   = 8'hAE;  // 8'b101_011_10
localparam OPCODE_LDX_ZP_Y  = 8'hB6;  // 8'b101_101_10
localparam OPCODE_LDX_ABS_Y = 8'hBE;  // 8'b101_111_10

// DEC — 8'b110_bbb_10
localparam OPCODE_DEC_ZP    = 8'hC6;  // 8'b110_001_10
localparam OPCODE_DEC_ABS   = 8'hCE;  // 8'b110_011_10
localparam OPCODE_DEC_ZP_X  = 8'hD6;  // 8'b110_101_10
localparam OPCODE_DEC_ABS_X = 8'hDE;  // 8'b110_111_10

// INC — 8'b111_bbb_10
localparam OPCODE_INC_ZP    = 8'hE6;  // 8'b111_001_10
localparam OPCODE_INC_ABS   = 8'hEE;  // 8'b111_011_10
localparam OPCODE_INC_ZP_X  = 8'hF6;  // 8'b111_101_10
localparam OPCODE_INC_ABS_X = 8'hFE;  // 8'b111_111_10

// --- cc=00: Control group ---

// BIT — 8'b001_bbb_00
localparam OPCODE_BIT_ZP    = 8'h24;  // 8'b001_001_00
localparam OPCODE_BIT_ABS   = 8'h2C;  // 8'b001_011_00

// JMP — 8'b01x_011_00
localparam OPCODE_JMP_ABS   = 8'h4C;  // 8'b010_011_00
localparam OPCODE_JMP_IND   = 8'h6C;  // 8'b011_011_00

// STY — 8'b100_bbb_00
localparam OPCODE_STY_ZP    = 8'h84;  // 8'b100_001_00
localparam OPCODE_STY_ABS   = 8'h8C;  // 8'b100_011_00
localparam OPCODE_STY_ZP_X  = 8'h94;  // 8'b100_101_00

// LDY — 8'b101_bbb_00
localparam OPCODE_LDY_IMM   = 8'hA0;  // 8'b101_000_00
localparam OPCODE_LDY_ZP    = 8'hA4;  // 8'b101_001_00
localparam OPCODE_LDY_ABS   = 8'hAC;  // 8'b101_011_00
localparam OPCODE_LDY_ZP_X  = 8'hB4;  // 8'b101_101_00
localparam OPCODE_LDY_ABS_X = 8'hBC;  // 8'b101_111_00

// CPY — 8'b110_bbb_00
localparam OPCODE_CPY_IMM   = 8'hC0;  // 8'b110_000_00
localparam OPCODE_CPY_ZP    = 8'hC4;  // 8'b110_001_00
localparam OPCODE_CPY_ABS   = 8'hCC;  // 8'b110_011_00

// CPX — 8'b111_bbb_00
localparam OPCODE_CPX_IMM   = 8'hE0;  // 8'b111_000_00
localparam OPCODE_CPX_ZP    = 8'hE4;  // 8'b111_001_00
localparam OPCODE_CPX_ABS   = 8'hEC;  // 8'b111_011_00

// --- Branches — 8'bxxy_100_00 ---

localparam OPCODE_BPL = 8'h10;  // 8'b000_100_00  N=0
localparam OPCODE_BMI = 8'h30;  // 8'b001_100_00  N=1
localparam OPCODE_BVC = 8'h50;  // 8'b010_100_00  V=0
localparam OPCODE_BVS = 8'h70;  // 8'b011_100_00  V=1
localparam OPCODE_BCC = 8'h90;  // 8'b100_100_00  C=0
localparam OPCODE_BCS = 8'hB0;  // 8'b101_100_00  C=1
localparam OPCODE_BNE = 8'hD0;  // 8'b110_100_00  Z=0
localparam OPCODE_BEQ = 8'hF0;  // 8'b111_100_00  Z=1

// --- Implied / Single-byte ---

// Interrupts/subroutines — 8'b0xx_000_00
localparam OPCODE_BRK = 8'h00;  // 8'b000_000_00
localparam OPCODE_JSR = 8'h20;  // 8'b001_000_00
localparam OPCODE_RTI = 8'h40;  // 8'b010_000_00
localparam OPCODE_RTS = 8'h60;  // 8'b011_000_00

// Stack/register — 8'bxxx_010_00
localparam OPCODE_PHP = 8'h08;  // 8'b000_010_00
localparam OPCODE_PLP = 8'h28;  // 8'b001_010_00
localparam OPCODE_PHA = 8'h48;  // 8'b010_010_00
localparam OPCODE_PLA = 8'h68;  // 8'b011_010_00
localparam OPCODE_DEY = 8'h88;  // 8'b100_010_00
localparam OPCODE_TAY = 8'hA8;  // 8'b101_010_00
localparam OPCODE_INY = 8'hC8;  // 8'b110_010_00
localparam OPCODE_INX = 8'hE8;  // 8'b111_010_00

// Flag operations — 8'bxxx_110_00
localparam OPCODE_CLC = 8'h18;  // 8'b000_110_00
localparam OPCODE_SEC = 8'h38;  // 8'b001_110_00
localparam OPCODE_CLI = 8'h58;  // 8'b010_110_00
localparam OPCODE_SEI = 8'h78;  // 8'b011_110_00
localparam OPCODE_TYA = 8'h98;  // 8'b100_110_00
localparam OPCODE_CLV = 8'hB8;  // 8'b101_110_00
localparam OPCODE_CLD = 8'hD8;  // 8'b110_110_00
localparam OPCODE_SED = 8'hF8;  // 8'b111_110_00

// Transfer/misc — 8'bxxx_xx0_10
localparam OPCODE_TXA = 8'h8A;  // 8'b100_010_10
localparam OPCODE_TXS = 8'h9A;  // 8'b100_110_10
localparam OPCODE_TAX = 8'hAA;  // 8'b101_010_10
localparam OPCODE_TSX = 8'hBA;  // 8'b101_110_10
localparam OPCODE_DEX = 8'hCA;  // 8'b110_010_10
localparam OPCODE_NOP = 8'hEA;  // 8'b111_010_10


typedef enum logic [3:0] {
    ALU_ADC = 0, ALU_AND = 1, ALU_ORA = 2, ALU_EOR = 3,
    ALU_ASL = 4, ALU_LSR = 5, ALU_ROL = 6, ALU_ROR = 7, ALU_SBC = 8
} alu_op_t;

typedef enum logic [5:0] {
    NOP = 0, LOAD = 1, MICRO_INIT = 2, MICRO_EXECUTE = 3, WRITE = 4, STORE = 5,
    PUSH_STACK = 6, POP_STACK = 7, RESTORE_STACK = 8, START = 9, LOAD_INITIAL_PC = 10,
    MAYBE_BRANCH = 11, STALL = 12, RESTORE_STACK2 = 13, ALU_MODIFY = 14,
    READ_ADL = 15, BUFFER_ADL = 16, PUSH_PCH = 17, PUSH_PCL = 18, READ_ADH = 19, PC_INC = 20,
    READ_PCL = 21, READ_PCH = 22, LOAD_PC_EFFECTIVE_LO = 23, LOAD_PC_EFFECTIVE_HI = 24,
    READ_EFFECTIVE_LO = 25, READ_EFFECTIVE_HI = 26, PULL_REGISTER = 27, WRITE_SR = 28,
    READ_VECTOR_HI = 29, PULL_PCH = 30, PULL_PCL = 31, LOAD_VECTOR = 32
} microinstruction_t;

/* verilator lint_on UNUSEDPARAM */

`endif
