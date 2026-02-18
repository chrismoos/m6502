`timescale 1ps/1ps

module test_gpio_mux (
    input i_clk
);

reg i_phi2;
reg i_reset_n;
reg [3:0] i_addr;
reg [7:0] i_data;
reg i_rw;
reg i_en;

reg [7:0] i_pins;
wire [7:0] o_pins;
wire [7:0] o_pins_oe;

reg i_uart0_tx;
wire o_uart0_rx;
reg i_sk6812_data;

wire [7:0] o_data;

// Instantiate GPIO module
gpio gpio_inst (
    .i_clk(i_clk),
    .i_phi2(i_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(i_addr),
    .i_data(i_data),
    .i_rw(i_rw),
    .o_data(o_data),
    .i_en(i_en),
    .i_pins(i_pins),
    .o_pins(o_pins),
    .o_pins_oe(o_pins_oe),
    .i_uart0_tx(i_uart0_tx),
    .o_uart0_rx(o_uart0_rx),
    .i_sk6812_data(i_sk6812_data)
);

endmodule
