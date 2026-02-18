// UART Receiver w/ FIFO, 8N1
// Baud rate = sysclk / (16 * (divisor + 1))
module uart_rx #(
    parameter FIFO_DEPTH = 8
) (
    input i_clk,
    input i_reset_n,

    input i_enable,
    input [15:0] i_baud_div,

    input i_read,
    output [7:0] o_data,

    output o_ready,
    output o_full,
    output reg o_error,

    input i_rx
);

wire fifo_empty, fifo_full_internal;
reg fifo_write;
reg [7:0] fifo_write_data;

fifo #(
    .DEPTH(FIFO_DEPTH),
    .WIDTH(8)
) rx_fifo (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_write(fifo_write),
    .i_data(fifo_write_data),
    .i_read(i_read),
    .o_data(o_data),
    .o_full(fifo_full_internal),
    .o_empty(fifo_empty),
    /* verilator lint_off PINCONNECTEMPTY */
    .o_count()
    /* verilator lint_on PINCONNECTEMPTY */
);

assign o_ready = !fifo_empty;
assign o_full = fifo_full_internal;

reg [15:0] baud_counter;
reg baud_tick;

always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        baud_counter <= 0;
        baud_tick <= 0;
    end else begin
        if (baud_counter >= i_baud_div) begin
            baud_counter <= 0;
            baud_tick <= 1;
        end else begin
            baud_counter <= baud_counter + 1;
            baud_tick <= 0;
        end
    end
end

reg rx_sync1, rx_sync2;
always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        rx_sync1 <= 1;
        rx_sync2 <= 1;
    end else begin
        rx_sync1 <= i_rx;
        rx_sync2 <= rx_sync1;
    end
end

typedef enum logic [2:0] {
    IDLE,
    START_BIT,
    DATA_BITS,
    STOP_BIT
} rx_state_t;

rx_state_t state;
reg [7:0] shift_reg;
reg [3:0] bit_count;
reg [3:0] sample_count;

always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        state <= IDLE;
        shift_reg <= 0;
        bit_count <= 0;
        sample_count <= 0;
        fifo_write <= 0;
        fifo_write_data <= 0;
        o_error <= 0;
    end else if (!i_enable) begin
        state <= IDLE;
        fifo_write <= 0;
        o_error <= 0;
    end else begin
        fifo_write <= 0;

        if (baud_tick) begin
            case (state)
                IDLE: begin
                    if (rx_sync2 == 0) begin
                        sample_count <= 0;
                        state <= START_BIT;
                    end
                end

                START_BIT: begin
                    sample_count <= sample_count + 1;
                    if (sample_count == 7) begin
                        if (rx_sync2 == 0) begin
                            bit_count <= 0;
                            state <= DATA_BITS;
                        end else begin
                            // glitch
                            state <= IDLE;
                        end
                    end else if (sample_count == 15) begin
                        sample_count <= 0;
                    end
                end

                DATA_BITS: begin
                    sample_count <= sample_count + 1;
                    if (sample_count == 4'd7) begin
                        shift_reg <= {rx_sync2, shift_reg[7:1]};
                        bit_count <= bit_count + 1;
                    end else if (sample_count == 4'd15) begin
                        sample_count <= 0;
                        if (bit_count == 4'd8) begin
                            state <= STOP_BIT;
                        end
                    end
                end

                STOP_BIT: begin
                    sample_count <= sample_count + 1;
                    if (sample_count == 7) begin
                        if (rx_sync2 == 1) begin
                            if (!fifo_full_internal) begin
                                fifo_write <= 1;
                                fifo_write_data <= shift_reg;
                            end
                            o_error <= 0;
                        end else begin
                            // stop bit should be high
                            o_error <= 1;
                        end
                    end else if (sample_count == 15) begin
                        state <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end
end

endmodule
