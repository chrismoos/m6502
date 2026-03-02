`include "cpu_6502_instructions.vh"

module cpu_6502 #(
    START_PC_ENABLED = 0,
    START_PC = 0
) (
    input i_clk,
    output o_phi1,
    output o_phi2,

    input i_reset_n,

    input i_rdy,
    input i_nmi_n,
    input i_irq_n,
    input i_so_n,

    output reg o_sync,

    // bus
    input [7:0] i_bus_data,
    output reg [7:0] o_bus_data,
    output reg [15:0] o_bus_addr,
    output reg o_rw,

    // debug port
    input [2:0] i_debug_sel,
    output reg [7:0] o_debug_data
);

assign o_phi2 = i_clk;
assign o_phi1 = ~i_clk;

localparam RESET_VECTOR = 16'hfffc;
localparam NMI_VECTOR = 16'hfffa;
localparam IRQ_VECTOR = 16'hfffe;

localparam INIT_CYCLES = 6;

typedef enum logic [3:0] {
    INIT = 0,
    OP_ZERO = 1,
    OP_LOAD_ZP = 2,
    OP_LOAD_ZP_INDEXED = 3,
    OP_ABSOLUTE_HI = 4,
    OP_LOAD_INDIRECT_LO = 5,
    OP_CALCULATE_BRANCH_OFFSET = 6,
    OP_BRANCH_PAGE_CROSS = 7,
    OP_ABSOLUTE_LO = 8,
    OP_ABSOLUTE_PAGE_CROSS = 9
} operation_t;
operation_t operation;

reg [15:0] program_counter;
reg status_negative, status_overflow,
    status_decimal, status_interrupt, status_zero,
    status_carry;

reg [7:0] register_x, register_y, register_acc, register_sp;
reg [15:0] effective_address;
wire [7:0] effective_address_lo, effective_address_hi;
reg effective_address_lo_carry;
assign effective_address_lo = effective_address[7:0];
assign effective_address_hi = effective_address[15:8];

reg init;
reg [7:0] opcode;

reg [2:0] init_counter;
reg [7:0] bus_data_write;

alu_op_t alu_operation;
reg [7:0] alu_result, alu_lhs, alu_rhs;
reg alu_carry_out, alu_carry_in, alu_overflow, alu_decimal;

wire init_rdy;
assign init_rdy = operation == INIT && init_counter == INIT_CYCLES;

operand_type_t addressing_mode;

reg handle_irq, handle_nmi;

reg first_microinstruction;
microinstruction_t current_microinstruction, prev_mi;
reg [7:0] current_instruction;
always_comb begin
    current_instruction = first_microinstruction ? i_bus_data : opcode;
end

cpu_6502_ir_decoder cpu_6502_ir_decoder (
    .i_clk(i_clk),
    .i_opcode(current_instruction),
    .o_operand_type(addressing_mode)
);

microinstruction_t next_microinstruction, next2_microinstruction;
microinstruction_t active_microinstruction, next_active_microinstruction;

cpu_6502_microcode microcode_next (
    .i_current_instruction(current_instruction),
    .i_current_microinstruction(current_microinstruction),
    .i_handle_irq(handle_irq),
    .i_init(init),
    .i_irq_n(i_irq_n),
    .i_nmi_n(i_nmi_n),
    .o_next_microinstruction(next_microinstruction)
);

cpu_6502_microcode microcode_next2 (
    .i_current_instruction(current_instruction),
    .i_current_microinstruction(next_microinstruction),
    .i_handle_irq(handle_irq),
    .i_init(init),
    .i_irq_n(i_irq_n),
    .i_nmi_n(i_nmi_n),
    .o_next_microinstruction(next2_microinstruction)
);

always_comb begin
    if (current_microinstruction == START) begin
        active_microinstruction = next_microinstruction;
        next_active_microinstruction = next2_microinstruction;
    end else begin
        active_microinstruction = current_microinstruction;
        next_active_microinstruction = next_microinstruction;
    end
end

reg branch_taken;
always_comb begin
    case (current_instruction)
    OPCODE_BCC: branch_taken = !status_carry;
    OPCODE_BCS: branch_taken = status_carry;
    OPCODE_BEQ: branch_taken = status_zero;
    OPCODE_BNE: branch_taken = !status_zero;
    OPCODE_BPL: branch_taken = !status_negative;
    OPCODE_BMI: branch_taken = status_negative;
    OPCODE_BVS: branch_taken = status_overflow;
    OPCODE_BVC: branch_taken = !status_overflow;
    default:
        branch_taken = 0;
    endcase
end

always @(posedge i_clk) begin
    o_bus_data <= bus_data_write;
end

reg prev_so_n;
reg trigger_overflow;
always @(posedge o_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        prev_so_n <= 0;
        trigger_overflow <= 0;
    end else begin
        trigger_overflow <= 0;
        prev_so_n <= i_so_n;
        if (prev_so_n && !i_so_n)
            trigger_overflow <= 1;
    end
end

reg nmi_n_sync, nmi_n_sync2, prev_nmi_n, pending_nmi;
always @(negedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        nmi_n_sync <= 1;
        nmi_n_sync2 <= 1;
    end else begin
        nmi_n_sync2 <= nmi_n_sync;
        nmi_n_sync <= i_nmi_n;
    end
end


always @(negedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        first_microinstruction <= 0;
        o_rw <= 1;
        o_sync <= 0;
        operation <= INIT;
        init_counter <= 0;
        program_counter <= 0;

        current_microinstruction <= MICRO_INIT;

        o_bus_addr <= 0;
        bus_data_write <= 0;
        effective_address <= 0;
        effective_address_lo_carry <= 0;
        handle_irq <= 0;
        handle_nmi <= 0;
        init <= 0;
        prev_nmi_n <= 1;
        pending_nmi <= 0;
    end
    else begin
        prev_nmi_n <= nmi_n_sync2;
        if (prev_nmi_n && !nmi_n_sync2)
            pending_nmi <= 1;

        if (i_rdy) begin
            first_microinstruction <= 0;
            prev_mi <= active_microinstruction;
            o_rw <= 0;
            o_sync <= 0;

            if (handle_irq || handle_nmi) begin
                if (active_microinstruction == WRITE_SR)
                    bus_data_write <= {status_negative, status_overflow, 1'b1, 1'b1, status_decimal,
                                        status_interrupt, status_zero, status_carry};
                else
                    bus_data_write <= active_microinstruction == PUSH_PCL ? program_counter[7:0] : program_counter[15:8];
            end
            else begin
                priority casez (opcode)
                OPCODE_TYPE_STA, OPCODE_PHA: bus_data_write <= register_acc;
                OPCODE_PHP: bus_data_write <= {status_negative, status_overflow, 1'b1, 1'b1, status_decimal,
                                status_interrupt, status_zero, status_carry};
                OPCODE_TYPE_STX: bus_data_write <= register_x;
                OPCODE_TYPE_STY: bus_data_write <= register_y;
                OPCODE_BRK: begin
                    if (active_microinstruction == WRITE_SR)
                        bus_data_write <= {status_negative, status_overflow, 1'b1, 1'b1, status_decimal,
                                            status_interrupt, status_zero, status_carry};
                    else
                        bus_data_write <= active_microinstruction == PUSH_PCH ? program_counter[15:8] : program_counter[7:0];
                end
                OPCODE_JSR: begin
                    bus_data_write <= active_microinstruction == PUSH_PCL ? program_counter[7:0] : program_counter[15:8];
                end
                default: bus_data_write <= 0;
                endcase
            end

            case (active_microinstruction)
            PUSH_PCH, PUSH_PCL, WRITE_SR, ALU_MODIFY, WRITE: o_rw <= 0;
            default: o_rw <= 1;
            endcase

            if (current_microinstruction == LOAD_INITIAL_PC) begin
                program_counter <= program_counter;
                current_microinstruction <= START;
                o_bus_addr <= program_counter;
                first_microinstruction <= 1;
            end
            else if (next_active_microinstruction == START) begin
                first_microinstruction <= 1;
                o_bus_addr <= program_counter;
                program_counter <= program_counter;
                init <= 0;
            end

            // opcode fetch
            if (first_microinstruction) begin
                opcode <= current_instruction;

                // Ensure we advance forward always for first instruction
                if (!handle_irq && !handle_nmi) begin
                    program_counter <= program_counter + 1;
                    o_bus_addr <= program_counter + 1;
                    o_sync <= 1;
                end
            end

            if (current_microinstruction == MICRO_INIT) begin
                init_counter <= init_counter + 1;
                if (init_rdy) begin
                    if (START_PC_ENABLED) begin
                        program_counter <= START_PC;
                        operation <= OP_ZERO;
                        current_microinstruction <= LOAD_INITIAL_PC;
                        o_bus_addr <= START_PC;
                    end else begin
                        o_bus_addr <= RESET_VECTOR;
                        current_microinstruction <= READ_VECTOR_HI;
                        init <= 1;
                    end
                end
            end
            else if (active_microinstruction == NOP) begin
                program_counter <= program_counter + 1;
                o_bus_addr <= o_bus_addr + 1;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == STALL ||
                    active_microinstruction == PULL_REGISTER || active_microinstruction == WRITE) begin
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == READ_ADL) begin
                program_counter <= program_counter + 2;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == BUFFER_ADL) begin
                effective_address <= {8'b0, i_bus_data};
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= {8'b1, register_sp};
            end
            else if (active_microinstruction == WRITE_SR) begin
                o_bus_addr <= {8'b1, register_sp};
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == PC_INC) begin
                current_microinstruction <= next_active_microinstruction;
                program_counter <= program_counter + 1;
            end
            else if (active_microinstruction == READ_PCL) begin
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= o_bus_addr + 1;
                program_counter <= program_counter + 1;
            end
            else if (active_microinstruction == PULL_PCL || active_microinstruction == PULL_PCH) begin
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= {8'h1, register_sp + 8'b1};
            end
            else if (active_microinstruction == READ_PCH) begin
                effective_address <= {8'b0, i_bus_data};
                o_bus_addr <= o_bus_addr + 1;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == PUSH_PCH || active_microinstruction == PUSH_PCL) begin
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= {8'b1, register_sp};
            end
            else if (active_microinstruction == READ_ADH) begin
                o_bus_addr <= program_counter;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == READ_EFFECTIVE_LO) begin
                o_bus_addr <= program_counter + 1;
                program_counter <= program_counter + 1;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == READ_EFFECTIVE_HI) begin
                effective_address <= {8'b0, i_bus_data};
                o_bus_addr <= program_counter + 1;
                program_counter <= program_counter + 1;
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == LOAD_PC_EFFECTIVE_LO) begin
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= {i_bus_data, effective_address_lo};
            end
            else if (active_microinstruction == LOAD_PC_EFFECTIVE_HI || active_microinstruction == READ_VECTOR_HI) begin
                current_microinstruction <= next_active_microinstruction;
                program_counter <= {8'b0, i_bus_data};
                o_bus_addr <= o_bus_addr + 1;
            end
            else if (active_microinstruction == LOAD_VECTOR) begin
                current_microinstruction <= next_active_microinstruction;
                o_bus_addr <= handle_nmi ? NMI_VECTOR : IRQ_VECTOR;
            end
            else if (active_microinstruction == MAYBE_BRANCH) begin
                if (first_microinstruction) begin
                    program_counter <= program_counter + 2;
                    if (branch_taken) begin
                        operation <= OP_CALCULATE_BRANCH_OFFSET;
                    end else begin
                        current_microinstruction <= next_active_microinstruction;
                    end
                end
                else if (operation == OP_CALCULATE_BRANCH_OFFSET) begin
                    if (branch_taken) begin
                        if ((alu_carry_out && !i_bus_data[7]) || (!alu_carry_out && i_bus_data[7]))
                            operation <= OP_BRANCH_PAGE_CROSS;
                        else begin
                            program_counter <= {program_counter[15:8], alu_result};
                            o_bus_addr <= {program_counter[15:8], alu_result};
                            current_microinstruction <= next_active_microinstruction;
                        end
                    end
                    else begin
                        current_microinstruction <= next_active_microinstruction;
                    end
                end
                else if (operation == OP_BRANCH_PAGE_CROSS) begin
                        program_counter <= {program_counter[15:8] + (i_bus_data[7] ? 8'hff : 8'h01), alu_result};
                        o_bus_addr <= {program_counter[15:8] + (i_bus_data[7] ? 8'hff : 8'h01), alu_result};
                        current_microinstruction <= next_active_microinstruction;
                end
            end
            else if (active_microinstruction == MICRO_EXECUTE) begin
                if (handle_nmi) handle_nmi <= 0;
                if (handle_irq) handle_irq <= 0;

                if (handle_nmi || handle_irq || init) begin
                    o_bus_addr <= {i_bus_data, program_counter[7:0]};
                    program_counter <= {i_bus_data, program_counter[7:0]};
                end
                else begin
                    priority casez (opcode)
                    OPCODE_JMP_ABS: begin
                        program_counter <= {i_bus_data, effective_address_lo};
                        o_bus_addr <= {i_bus_data, effective_address_lo};
                    end
                    OPCODE_JMP_IND: begin
                        program_counter <= {i_bus_data, program_counter[7:0]};
                        o_bus_addr <= {i_bus_data, program_counter[7:0]};
                    end
                    OPCODE_RTS: begin
                        o_bus_addr <= program_counter;
                    end
                    OPCODE_BRK: begin
                        program_counter <= {i_bus_data, program_counter[7:0]};
                        o_bus_addr <= {i_bus_data, program_counter[7:0]};
                    end
                    OPCODE_JSR: begin
                        program_counter <= {i_bus_data, effective_address_lo};
                        o_bus_addr <= {i_bus_data, effective_address_lo};
                    end
                    default: ;
                    endcase
                end

                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == LOAD || active_microinstruction == STORE) begin
                if (first_microinstruction) begin
                    program_counter <= program_counter + 2;
                    o_bus_addr <= program_counter + 1;
                    case (addressing_mode)
                        IMMEDIATE: current_microinstruction <= next_active_microinstruction;
                        ABSOLUTE, ABSOLUTE_X, ABSOLUTE_Y, INDIRECT: operation <= OP_ABSOLUTE_LO;
                        INDEX_X_INDIRECT, INDEX_Y_INDIRECT, ZP, ZP_X, ZP_Y: operation <= OP_LOAD_ZP;

                        // invalid opcode, continue
                        default: begin
                            current_microinstruction <= next_active_microinstruction;
                        end
                    endcase
                end
                else begin
                    if (operation == OP_LOAD_ZP) begin
                        case (addressing_mode)
                            ZP: begin
                                current_microinstruction <= next_active_microinstruction;
                                effective_address <= {8'b0, i_bus_data};
                                o_bus_addr <= {8'b0, i_bus_data};
                                if (active_microinstruction == STORE)
                                    o_rw <= 0;
                            end
                            INDEX_Y_INDIRECT: begin
                                o_bus_addr <= {8'b0, i_bus_data};
                                operation <= OP_ABSOLUTE_LO;
                            end
                            INDEX_X_INDIRECT, ZP_X, ZP_Y: operation <= OP_LOAD_ZP_INDEXED;
                            // invalid opcode, continue
                            default: begin
                                current_microinstruction <= next_active_microinstruction;
                            end
                        endcase
                    end
                    else if (operation == OP_LOAD_ZP_INDEXED) begin
                        o_bus_addr <= {8'b0, alu_result};
                        if (addressing_mode == INDEX_X_INDIRECT) begin
                            operation <= OP_ABSOLUTE_LO;
                        end
                        else begin
                            current_microinstruction <= next_active_microinstruction;
                            if (active_microinstruction == STORE)
                                o_rw <= 0;
                        end
                    end
                    else if (operation == OP_ABSOLUTE_LO) begin
                        if (addressing_mode == ABSOLUTE_X || addressing_mode == ABSOLUTE_Y || addressing_mode == ABSOLUTE)
                            program_counter <= program_counter + 1;

                        effective_address <= {8'b0, i_bus_data};
                        o_bus_addr <= o_bus_addr + 1;
                        operation <= OP_ABSOLUTE_HI;

                        if (opcode == OPCODE_JMP_ABS || opcode == OPCODE_JSR)
                            current_microinstruction <= next_active_microinstruction;
                    end
                    else if (operation == OP_ABSOLUTE_HI) begin
                        effective_address <= {i_bus_data, alu_result};
                        o_bus_addr <= {i_bus_data, alu_result};
                        effective_address_lo_carry <= alu_carry_out;

                        if (opcode == OPCODE_JMP_IND) begin
                            operation <= OP_LOAD_INDIRECT_LO;
                        end
                        else if (alu_carry_out || (active_microinstruction == STORE && addressing_mode != ABSOLUTE))
                            operation <= OP_ABSOLUTE_PAGE_CROSS;
                        else begin
                            priority casez (opcode)
                            OPCODE_TYPE_INC, OPCODE_TYPE_DEC, OPCODE_TYPE_ROR, OPCODE_TYPE_ROL, OPCODE_TYPE_ASL,
                            OPCODE_TYPE_LSR:
                                operation <= OP_ABSOLUTE_PAGE_CROSS;
                            default: begin
                                current_microinstruction <= next_active_microinstruction;
                                if (active_microinstruction == STORE)
                                    o_rw <= 0;
                            end
                            endcase
                        end
                    end
                    else if (operation == OP_LOAD_INDIRECT_LO) begin
                        // NMOS behavior, low byte wraps around (high byte not incremented)
                        o_bus_addr <= o_bus_addr + 1;
                        effective_address <= {8'b0, i_bus_data};
                        current_microinstruction <= next_active_microinstruction;
                    end
                    else if (operation == OP_ABSOLUTE_PAGE_CROSS) begin
                        effective_address <= {alu_result, effective_address[7:0]};
                        o_bus_addr <= {alu_result, effective_address[7:0]};
                        current_microinstruction <= next_active_microinstruction;
                        if (active_microinstruction == STORE)
                            o_rw <= 0;
                    end
                end
            end
            else if (active_microinstruction == POP_STACK) begin
                o_bus_addr <= {8'b1, register_sp + 8'b1};
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == RESTORE_STACK2) begin
                effective_address <= {i_bus_data, effective_address_lo};
                if (opcode == OPCODE_RTS)
                    program_counter <= {i_bus_data, effective_address_lo};
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == RESTORE_STACK) begin
                effective_address <= {8'b0, i_bus_data};
                if (next_active_microinstruction == RESTORE_STACK2)
                    o_bus_addr <= {8'b1, o_bus_addr[7:0] + 8'b1};
                current_microinstruction <= next_active_microinstruction;
            end
            else if (active_microinstruction == PUSH_STACK) begin
                o_bus_addr <= {8'b1, register_sp};
                current_microinstruction <= next_active_microinstruction;

                if (opcode == OPCODE_JSR) begin
                    effective_address <= {i_bus_data, effective_address_lo};
                end
            end
            else if (active_microinstruction == ALU_MODIFY) begin
                current_microinstruction <= next_active_microinstruction;
                bus_data_write <= alu_result;
            end

            case (prev_mi)
                PULL_PCL: program_counter <= {8'b0, i_bus_data};
                PULL_PCH: begin
                    program_counter <= {i_bus_data, program_counter[7:0]};
                end
                default: ;
            endcase

            if (next_active_microinstruction == START && !i_irq_n && !status_interrupt && !handle_irq && !handle_nmi) begin
                handle_irq <= 1;
                o_bus_addr <= {8'b1, register_sp};
            end
            else if (next_active_microinstruction == START && pending_nmi && !handle_irq && !handle_nmi && !init) begin
                handle_irq <= 1;
                handle_nmi <= 1;
                pending_nmi <= 0;
                o_bus_addr <= {8'b1, register_sp};
            end
        end
    end
end

always @(negedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        register_acc <= 0;
        register_y <= 0;
        register_x <= 0;
        register_sp <= 0;
    end
    else begin
        if (i_rdy) begin
            case (active_microinstruction)
                POP_STACK: register_sp <= register_sp + 8'b1;
                PUSH_STACK, PUSH_PCL, PUSH_PCH, WRITE_SR: register_sp <= register_sp - 8'b1;
                PULL_PCL, PULL_PCH: register_sp <= register_sp + 8'b1;
                RESTORE_STACK2: register_sp <= register_sp + 8'b1;
                PULL_REGISTER: begin
                    priority casez (opcode)
                    OPCODE_PLA: begin
                        register_acc <= i_bus_data;
                    end
                    default: ;
                    endcase
                end
                MICRO_EXECUTE: begin
                    priority casez (opcode)
                    OPCODE_PLP, OPCODE_PLA: begin
                        // no updates
                    end
                    OPCODE_TYPE_BRANCH: begin
                        // noop
                    end
                    OPCODE_TAX: register_x <= register_acc;
                    OPCODE_TXA: register_acc <= register_x;
                    OPCODE_TYA: register_acc <= register_y;
                    OPCODE_TAY: register_y <= register_acc;
                    OPCODE_TSX: register_x <= register_sp;
                    OPCODE_TXS: register_sp <= register_x;
                    OPCODE_INX, OPCODE_DEX: register_x <= alu_result;
                    OPCODE_INY, OPCODE_DEY: register_y <= alu_result;
                    OPCODE_ASL_ACC, OPCODE_LSR_ACC, OPCODE_ROL_ACC, OPCODE_ROR_ACC: register_acc <= alu_result;
                    OPCODE_TYPE_LDA: register_acc <= i_bus_data;
                    OPCODE_TYPE_LDX: register_x <= i_bus_data;
                    OPCODE_TYPE_LDY: register_y <= i_bus_data;
                    OPCODE_TYPE_ADC, OPCODE_TYPE_AND, OPCODE_TYPE_ORA,
                    OPCODE_TYPE_EOR, OPCODE_TYPE_SBC:
                        register_acc <= alu_result;
                    default: ;
                    endcase
                end
                default: ;
            endcase
        end
    end
end

always @(negedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        status_negative <= 0;
        status_decimal <= 0;
        status_overflow <= 0;
        status_carry <= 0;
        status_zero <= 0;
        status_interrupt <= 0;
    end else begin
        if (init_rdy) begin
            status_negative <= 0;
            status_overflow <= 0;
            status_decimal <= 0;
            status_interrupt <= 1;
            status_zero <= 0;
            status_carry <= 0;
        end
        if (active_microinstruction == PULL_REGISTER && i_rdy) begin
            priority casez (opcode)
            OPCODE_PLP, OPCODE_RTI: begin
                status_negative <= i_bus_data[7];
                status_overflow <= i_bus_data[6];
                status_decimal <= i_bus_data[3];
                status_interrupt <= i_bus_data[2];
                status_zero <= i_bus_data[1];
                status_carry <= i_bus_data[0];
            end
            default: ;
            endcase
        end
        if (active_microinstruction == MICRO_EXECUTE && i_rdy) begin
            if (handle_irq)
                status_interrupt <= 1;

            priority casez (opcode)
            OPCODE_TYPE_BRANCH: begin
            end
            OPCODE_PLP, OPCODE_JSR: begin
                // no updates
            end
            OPCODE_PLA: begin
                status_negative <= register_acc[7];
                status_zero <= register_acc == 0;
            end
            OPCODE_SEC: status_carry <= 1;
            OPCODE_CLC: status_carry <= 0;
            OPCODE_SED: status_decimal <= 1;
            OPCODE_CLD: status_decimal <= 0;
            OPCODE_SEI: status_interrupt <= 1;
            OPCODE_CLI: status_interrupt <= 0;
            OPCODE_CLV: status_overflow <= 0;
            OPCODE_BRK: status_interrupt <= 1;
            OPCODE_TSX: begin
                status_negative <= register_sp[7];
                status_zero <= register_sp == 0;
            end
            OPCODE_TAX, OPCODE_TAY: begin
                status_negative <= register_acc[7];
                status_zero <= register_acc == 0;
            end
            OPCODE_TYA: begin
                status_negative <= register_y[7];
                status_zero <= register_y == 0;
            end
            OPCODE_TXA: begin
                status_negative <= register_x[7];
                status_zero <= register_x == 0;
            end
            OPCODE_INX, OPCODE_INY, OPCODE_DEX, OPCODE_DEY: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
            end
            OPCODE_TYPE_BIT: begin
                status_negative <= i_bus_data[7];
                status_overflow <= i_bus_data[6];
                status_zero <= alu_result == 0;
            end
            OPCODE_TYPE_CMP, OPCODE_TYPE_CPX, OPCODE_TYPE_CPY: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
                status_carry <= alu_carry_out;
            end
            OPCODE_ROL_ACC, OPCODE_ASL_ACC, OPCODE_LSR_ACC, OPCODE_ROR_ACC: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
                status_carry <= alu_carry_out;
            end
            OPCODE_TYPE_AND, OPCODE_TYPE_EOR, OPCODE_TYPE_ORA: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
            end
            OPCODE_TYPE_LDA, OPCODE_TYPE_LDX, OPCODE_TYPE_LDY: begin
                status_negative <= i_bus_data[7];
                status_zero <= i_bus_data == 0;
            end
            OPCODE_TYPE_ADC, OPCODE_TYPE_SBC: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
                status_carry <= alu_carry_out;
                status_overflow <= alu_overflow;
            end
            default: begin
            end
            endcase
        end
        else if (active_microinstruction == ALU_MODIFY && i_rdy) begin
            priority casez (opcode)
            OPCODE_TYPE_ASL, OPCODE_TYPE_LSR, OPCODE_TYPE_ROL, OPCODE_TYPE_ROR: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
                status_carry <= alu_carry_out;
            end
            OPCODE_TYPE_INC, OPCODE_TYPE_DEC: begin
                status_negative <= alu_result[7];
                status_zero <= alu_result == 0;
            end
            default: ;
            endcase
        end

        if (trigger_overflow)
            status_overflow <= 1;
    end
end

reg load_or_store;
always_comb begin
    alu_operation = ALU_ADC;
    alu_carry_in = 0;
    alu_lhs = 0;
    alu_rhs = 0;
    alu_decimal = 0;
    load_or_store = active_microinstruction == LOAD || active_microinstruction == STORE; 

    if (load_or_store && operation == OP_LOAD_ZP_INDEXED) begin
        alu_lhs = i_bus_data;
        alu_rhs = (addressing_mode == ZP_X || addressing_mode == INDEX_X_INDIRECT) ? register_x : register_y;
    end
    else if (load_or_store && operation == OP_ABSOLUTE_PAGE_CROSS) begin
        alu_lhs = effective_address_hi;
        alu_rhs = {7'b0, effective_address_lo_carry};
    end
    else if (load_or_store && operation == OP_ABSOLUTE_HI) begin
        alu_lhs = effective_address_lo;
        if (addressing_mode == ABSOLUTE_X)
            alu_rhs = register_x;
        else if(addressing_mode == ABSOLUTE_Y || addressing_mode == INDEX_Y_INDIRECT)
            alu_rhs = register_y;
    end
    else if (active_microinstruction == MAYBE_BRANCH) begin
        alu_lhs = program_counter[7:0];
        alu_rhs = i_bus_data;
    end
    else if (active_microinstruction == STORE) begin
        alu_lhs = i_bus_data;
        priority casez (opcode)
        OPCODE_TYPE_INC: alu_rhs = 8'h01;
        OPCODE_TYPE_DEC: alu_rhs = 8'hff;
        default: ;
        endcase
    end
    else if (active_microinstruction == MICRO_EXECUTE) begin
        alu_lhs = register_acc;
        alu_rhs = i_bus_data;
        alu_carry_in = status_carry;
        priority casez (opcode)
        OPCODE_DEY: begin
            alu_lhs = register_y;
            alu_rhs = 8'hff;
            alu_carry_in = 0;
        end
        OPCODE_DEX: begin
            alu_lhs = register_x;
            alu_rhs = 8'hff;
            alu_carry_in = 0;
        end
        OPCODE_INY: begin
            alu_lhs = register_y;
            alu_rhs = 1;
            alu_carry_in = 0;
        end
        OPCODE_INX: begin
            alu_lhs = register_x;
            alu_rhs = 1;
            alu_carry_in = 0;
        end
        OPCODE_TYPE_BRANCH: begin
            alu_lhs = program_counter[7:0];
            alu_carry_in = 0;
            if (i_bus_data[7]) begin
                alu_carry_in = 0;
            end else begin
                alu_rhs = i_bus_data;
            end
        end
        OPCODE_TYPE_BIT: begin
            alu_carry_in = 0;
            alu_lhs = register_acc;
            alu_rhs = i_bus_data;
            alu_operation = ALU_AND;
        end
        OPCODE_TYPE_CPY: begin
            alu_lhs = register_y;
            alu_rhs = ~i_bus_data;
            alu_carry_in = 1;
        end
        OPCODE_TYPE_CPX: begin
            alu_lhs = register_x;
            alu_rhs = ~i_bus_data;
            alu_carry_in = 1;
        end
        OPCODE_TYPE_CMP: begin
            alu_lhs = register_acc;
            alu_rhs = ~i_bus_data;
            alu_carry_in = 1;
        end
        OPCODE_TYPE_AND: alu_operation = ALU_AND;
        OPCODE_TYPE_ORA: alu_operation = ALU_ORA;
        OPCODE_TYPE_EOR: alu_operation = ALU_EOR;
        OPCODE_TYPE_ADC: begin
            alu_rhs = i_bus_data;
            alu_decimal = status_decimal;
        end
        OPCODE_TYPE_SBC: begin
            alu_rhs = ~i_bus_data;
            alu_carry_in = status_carry;
            alu_decimal = status_decimal;
            alu_operation = ALU_SBC;
        end
        OPCODE_TYPE_ROR: begin
            if (opcode == OPCODE_ROR_ACC)
                alu_lhs = register_acc;
            else
                alu_lhs = i_bus_data;

            alu_rhs = 0;
            alu_operation = ALU_ROR;
        end
        OPCODE_TYPE_ROL: begin
            if (opcode == OPCODE_ROL_ACC)
                alu_lhs = register_acc;
            else
                alu_lhs = i_bus_data;

            alu_rhs = 0;
            alu_operation = ALU_ROL;
        end
        OPCODE_TYPE_ASL: begin
            if (opcode == OPCODE_ASL_ACC)
                alu_lhs = register_acc;
            else
                alu_lhs = i_bus_data;

            alu_carry_in = 0;
            alu_rhs = 0;
            alu_operation = ALU_ASL;
        end
        OPCODE_TYPE_LSR: begin
            if (opcode == OPCODE_LSR_ACC)
                alu_lhs = register_acc;
            else
                alu_lhs = i_bus_data;

            alu_carry_in = 0;
            alu_rhs = 0;
            alu_operation = ALU_LSR;
        end
        default: ;
        endcase
    end
    else if (active_microinstruction == ALU_MODIFY) begin
        alu_lhs = i_bus_data;
        priority casez (opcode)
        OPCODE_TYPE_INC: alu_rhs = 1;
        OPCODE_TYPE_DEC: begin
            alu_rhs = 8'hff;
        end
        OPCODE_TYPE_ROR: begin
            alu_rhs = 0;
            alu_operation = ALU_ROR;
            alu_carry_in = status_carry;
        end
        OPCODE_TYPE_ROL: begin
            alu_rhs = 0;
            alu_operation = ALU_ROL;
            alu_carry_in = status_carry;
        end
        OPCODE_TYPE_ASL: begin
            alu_carry_in = 0;
            alu_rhs = 0;
            alu_operation = ALU_ASL;
        end
        OPCODE_TYPE_LSR: begin
            alu_carry_in = 0;
            alu_rhs = 0;
            alu_operation = ALU_LSR;
        end
        default: ;
        endcase
    end
end

cpu_6502_alu alu (
    .i_clk(i_clk),
    .i_operation(alu_operation),
    .i_lhs(alu_lhs),
    .i_rhs(alu_rhs),
    .i_carry(alu_carry_in),
    .i_bcd(alu_decimal),
    .o_result(alu_result),
    .o_carry(alu_carry_out),
    .o_overflow(alu_overflow)
);

always_comb begin
    case (i_debug_sel)
        3'd0: o_debug_data = {2'b00, active_microinstruction};
        3'd1: o_debug_data = {2'b00, next_active_microinstruction};
        3'd2: o_debug_data = opcode;
        3'd3: o_debug_data = {4'b0000, operation};
        3'd4: o_debug_data = program_counter[15:8];
        3'd5: o_debug_data = program_counter[7:0];
        3'd6: o_debug_data = register_acc;
        3'd7: o_debug_data = {status_negative, status_overflow, 1'b1, 1'b1,
                              status_decimal, status_interrupt, status_zero, status_carry};
        default: o_debug_data = 8'h00;
    endcase
end

endmodule
