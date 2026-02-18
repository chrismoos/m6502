`timescale 1ps/1ps

module test_uart (
    input i_clk
);

reg i_phi2;
reg i_reset_n;
reg [2:0] i_addr;
reg [7:0] i_data;
reg i_rw;
reg i_en;

wire [7:0] o_data;
wire o_tx;
reg i_rx;
wire o_tx_irq;
wire o_rx_irq;

// Instantiate UART module
uart uart0 (
    .i_clk(i_clk),
    .i_phi2(i_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(i_addr),
    .i_data(i_data),
    .i_rw(i_rw),
    .o_data(o_data),
    .i_en(i_en),
    .i_rx(i_rx),
    .o_tx(o_tx),
    .o_tx_irq(o_tx_irq),
    .o_rx_irq(o_rx_irq)
);

endmodule
