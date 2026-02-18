`timescale 1ps/1ps

module test_timer (
    input i_clk
);

reg i_reset_n;
reg [7:0] i_gpioa_input;
wire [7:0] o_gpioa_output;
wire [7:0] o_gpioa_oe;
wire o_sync;

wire [15:0] bus_addr;
wire [7:0] bus_write_data;
wire [7:0] bus_read_data;
wire bus_rw;
wire phi1, phi2;
wire [7:0] debug_data;
mcu #(
    .START_PC_ENABLED(1)
) mcu (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_bus_data(bus_read_data),
    .o_bus_data(bus_write_data),
    .o_bus_addr(bus_addr),
    .o_bus_rw(bus_rw),
    .o_phi1(phi1),
    .o_phi2(phi2),
    .i_gpioa_input(i_gpioa_input),
    .o_gpioa_output(o_gpioa_output),
    .o_gpioa_oe(o_gpioa_oe),
    .o_sync(o_sync),
    .i_rdy(1'b1),
    .i_nmi_n(1'b1),
    .i_irq_n_ext(1'b1),
    .i_so_n(1'b1),
    .i_debug_sel(3'b000),
    .o_debug_data(debug_data)
);

bram bram (
    .i_clk(i_clk),
    .i_phi2(phi2),
    .i_addr(bus_addr),
    .i_data(bus_write_data),
    .i_rw(bus_rw),
    .i_en(1'b1),
    .o_data(bus_read_data)
);

endmodule
