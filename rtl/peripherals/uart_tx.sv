// UART Transmitter w/ FIFO, 8N1
// Baud rate = sysclk / (16 * (divisor + 1))
module uart_tx #(
    parameter FIFO_DEPTH = 8
) (
    input i_clk,
    input i_reset_n,

    input i_enable,
    input [15:0] i_baud_div,

    input i_write,
    input [7:0] i_data,

    output o_ready,    // FIFO not full
    output o_empty,    // FIFO empty
    output o_active,   // Currently transmitting

    output reg o_tx
);

wire [7:0] fifo_data;
wire fifo_full, fifo_empty;
reg fifo_read;

fifo #(
    .DEPTH(FIFO_DEPTH),
    .WIDTH(8)
) tx_fifo (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_write(i_write),
    .i_data(i_data),
    .i_read(fifo_read),
    .o_data(fifo_data),
    .o_full(fifo_full),
    .o_empty(fifo_empty),
    /* verilator lint_off PINCONNECTEMPTY */
    .o_count()
    /* verilator lint_on PINCONNECTEMPTY */
);

assign o_ready = !fifo_full;
assign o_empty = fifo_empty;

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

typedef enum logic [2:0] {
    IDLE,
    START_BIT,
    DATA_BITS,
    STOP_BIT
} tx_state_t;

tx_state_t state;
reg [7:0] shift_reg;
reg [7:0] tx_byte;
reg [2:0] bit_count;
reg [3:0] sample_count; 

assign o_active = (state != IDLE);

always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        state <= IDLE;
        o_tx <= 1;
        shift_reg <= 0;
        tx_byte <= 0;
        bit_count <= 0;
        sample_count <= 0;
        fifo_read <= 0;
    end else if (!i_enable) begin
        state <= IDLE;
        o_tx <= 1;
        fifo_read <= 0;
    end else begin
        fifo_read <= 0;

        if (baud_tick) begin
            sample_count <= sample_count + 1;

            if (sample_count == 15) begin
                sample_count <= 0;

                case (state)
                    IDLE: begin
                        o_tx <= 1;
                        if (!fifo_empty) begin
                            tx_byte <= fifo_data;
                            fifo_read <= 1;
                            state <= START_BIT;
                        end
                    end

                    START_BIT: begin
                        shift_reg <= tx_byte;
                        o_tx <= 0;
                        bit_count <= 0;
                        state <= DATA_BITS;
                    end

                    DATA_BITS: begin
                        o_tx <= shift_reg[0];
                        shift_reg <= {1'b0, shift_reg[7:1]};
                        if (bit_count == 3'd7) begin
                            state <= STOP_BIT;
                            bit_count <= 0;
                        end else begin
                            bit_count <= bit_count + 1;
                        end
                    end

                    STOP_BIT: begin
                        o_tx <= 1;
                        state <= IDLE;
                    end

                    default: state <= IDLE;
                endcase
            end
        end
    end
end

endmodule
