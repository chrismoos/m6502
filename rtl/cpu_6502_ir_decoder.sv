`include "cpu_6502_instructions.vh"
module cpu_6502_ir_decoder (
    input i_clk,
    input [7:0] i_opcode,
    output operand_type_t o_operand_type
);

wire [2:0] instruction_mode;
assign instruction_mode = i_opcode[4:2];

always_comb begin
    priority casez (i_opcode)
    OPCODE_BRK, OPCODE_RTI, OPCODE_RTS, OPCODE_NOP,
    OPCODE_PHP, OPCODE_PLP, OPCODE_PHA, OPCODE_PLA,
    OPCODE_DEY, OPCODE_TAY, OPCODE_INY, OPCODE_INX,
    OPCODE_CLC, OPCODE_SEC, OPCODE_CLI, OPCODE_SEI,
    OPCODE_TYA, OPCODE_CLV, OPCODE_CLD, OPCODE_SED,
    OPCODE_TXA, OPCODE_TXS, OPCODE_TAX, OPCODE_TSX,
    OPCODE_DEX:
        o_operand_type = IMPLIED;

    OPCODE_TYPE_BRANCH:
        o_operand_type = RELATIVE;

    OPCODE_JMP_ABS, OPCODE_JSR:
        o_operand_type = ABSOLUTE;
    OPCODE_JMP_IND:
        o_operand_type = INDIRECT;

    OPCODE_TYPE_ORA, OPCODE_TYPE_AND, OPCODE_TYPE_EOR, OPCODE_TYPE_ADC,
    OPCODE_TYPE_STA, OPCODE_TYPE_LDA, OPCODE_TYPE_CMP, OPCODE_TYPE_SBC: begin
        case (instruction_mode)
            3'b000: o_operand_type = INDEX_X_INDIRECT;
            3'b001: o_operand_type = ZP;
            3'b010: o_operand_type = IMMEDIATE;
            3'b011: o_operand_type = ABSOLUTE;
            3'b100: o_operand_type = INDEX_Y_INDIRECT;
            3'b101: o_operand_type = ZP_X;
            3'b110: o_operand_type = ABSOLUTE_Y;
            3'b111: o_operand_type = ABSOLUTE_X;
        endcase
    end

    OPCODE_TYPE_ASL, OPCODE_TYPE_ROL, OPCODE_TYPE_LSR, OPCODE_TYPE_ROR: begin
        case (instruction_mode)
            3'b001: o_operand_type = ZP;
            3'b010: o_operand_type = ACCUMULATOR;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_X;
            3'b111: o_operand_type = ABSOLUTE_X;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_DEC, OPCODE_TYPE_INC: begin
        case (instruction_mode)
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_X;
            3'b111: o_operand_type = ABSOLUTE_X;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_STX: begin
        case (instruction_mode)
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_Y;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_LDX: begin
        case (instruction_mode)
            3'b000: o_operand_type = IMMEDIATE;
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_Y;
            3'b111: o_operand_type = ABSOLUTE_Y;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_BIT: begin
        case (instruction_mode)
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_STY: begin
        case (instruction_mode)
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_X;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_LDY: begin
        case (instruction_mode)
            3'b000: o_operand_type = IMMEDIATE;
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            3'b101: o_operand_type = ZP_X;
            3'b111: o_operand_type = ABSOLUTE_X;
            default: o_operand_type = IMPLIED;
        endcase
    end

    OPCODE_TYPE_CPY, OPCODE_TYPE_CPX: begin
        case (instruction_mode)
            3'b000: o_operand_type = IMMEDIATE;
            3'b001: o_operand_type = ZP;
            3'b011: o_operand_type = ABSOLUTE;
            default: o_operand_type = IMPLIED;
        endcase
    end

    default:
        o_operand_type = IMPLIED;
    endcase
end
endmodule
