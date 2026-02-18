module uart #(
    parameter FIFO_DEPTH = 8
) (
    input i_clk,
    input i_phi2,
    input i_reset_n,

    input [2:0] i_addr,
    input [7:0] i_data,
    input i_rw,
    output reg [7:0] o_data,
    input i_en,

    input i_rx,
    output o_tx,

    output o_tx_irq,
    output o_rx_irq
);

localparam ADDR_CTRL    = 3'h0;
localparam ADDR_STATUS  = 3'h1;
localparam ADDR_DATA    = 3'h2;
localparam ADDR_BAUD_LO = 3'h3;
localparam ADDR_BAUD_HI = 3'h4;

localparam CTRL_TX_EN     = 0;
localparam CTRL_RX_EN     = 1;
localparam CTRL_TX_IRQ_EN = 2;
localparam CTRL_RX_IRQ_EN = 3;

reg tx_enable;
reg rx_enable;
reg tx_irq_en;
reg rx_irq_en;

reg [15:0] baud_div;

reg [7:0] tx_data;
reg tx_write_toggle;
reg rx_read_toggle;

wire tx_ready, tx_empty, tx_active;
wire tx_write_pulse;

wire rx_ready, rx_full, rx_error;
wire [7:0] rx_data;
wire rx_read_pulse;

uart_tx #(
    .FIFO_DEPTH(FIFO_DEPTH)
) uart_tx_inst (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_enable(tx_enable),
    .i_baud_div(baud_div),
    .i_write(tx_write_pulse),
    .i_data(tx_data),
    .o_ready(tx_ready),
    .o_empty(tx_empty),
    .o_active(tx_active),
    .o_tx(o_tx)
);

uart_rx #(
    .FIFO_DEPTH(FIFO_DEPTH)
) uart_rx_inst (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_enable(rx_enable),
    .i_baud_div(baud_div),
    .i_read(rx_read_pulse),
    .o_data(rx_data),
    .o_ready(rx_ready),
    .o_full(rx_full),
    .o_error(rx_error),
    .i_rx(i_rx)
);

assign o_tx_irq = tx_irq_en && tx_ready;
assign o_rx_irq = rx_irq_en && rx_ready;

reg tx_toggle_sync1, tx_toggle_sync2;
reg rx_toggle_sync1, rx_toggle_sync2;

always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        tx_toggle_sync1 <= 0;
        tx_toggle_sync2 <= 0;
        rx_toggle_sync1 <= 0;
        rx_toggle_sync2 <= 0;
    end else begin
        tx_toggle_sync1 <= tx_write_toggle;
        tx_toggle_sync2 <= tx_toggle_sync1;
        rx_toggle_sync1 <= rx_read_toggle;
        rx_toggle_sync2 <= rx_toggle_sync1;
    end
end

assign tx_write_pulse = tx_toggle_sync1 ^ tx_toggle_sync2;
assign rx_read_pulse = rx_toggle_sync1 ^ rx_toggle_sync2;

always @(posedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        o_data <= 0;
        rx_read_toggle <= 0;
    end else if (i_rw && i_en) begin
        case (i_addr)
            ADDR_CTRL: begin
                o_data[CTRL_TX_EN] <= tx_enable;
                o_data[CTRL_RX_EN] <= rx_enable;
                o_data[CTRL_TX_IRQ_EN] <= tx_irq_en;
                o_data[CTRL_RX_IRQ_EN] <= rx_irq_en;
                o_data[7:4] <= 4'b0;
            end

            ADDR_STATUS: begin
                o_data <= {2'b0, rx_error, tx_active, rx_full, tx_empty, rx_ready, tx_ready};
            end

            ADDR_DATA: begin
                o_data <= rx_data;
                rx_read_toggle <= !rx_read_toggle;
            end

            ADDR_BAUD_LO: begin
                o_data <= baud_div[7:0];
            end

            ADDR_BAUD_HI: begin
                o_data <= baud_div[15:8];
            end

            default: o_data <= 0;
        endcase
    end
end

always @(negedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        tx_enable <= 0;
        rx_enable <= 0;
        tx_irq_en <= 0;
        rx_irq_en <= 0;
        baud_div <= 0;
        tx_data <= 0;
        tx_write_toggle <= 0;
    end else begin
        if (!i_rw && i_en) begin
            case (i_addr)
                ADDR_CTRL: begin
                    tx_enable <= i_data[CTRL_TX_EN];
                    rx_enable <= i_data[CTRL_RX_EN];
                    tx_irq_en <= i_data[CTRL_TX_IRQ_EN];
                    rx_irq_en <= i_data[CTRL_RX_IRQ_EN];
                end

                ADDR_DATA: begin
                    tx_data <= i_data;
                    tx_write_toggle <= !tx_write_toggle;
                end

                ADDR_BAUD_LO: begin
                    baud_div[7:0] <= i_data;
                end

                ADDR_BAUD_HI: begin
                    baud_div[15:8] <= i_data;
                end

                default: ;
            endcase
        end
    end
end

endmodule
