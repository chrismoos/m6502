`timescale 1ps/1ps

module test_mcu_klaus (
    input i_clk
);

reg i_reset_n;

wire cpu_sync;
wire cpu_phi1;
wire cpu_phi2;
wire cpu_rw;
wire [15:0] bus_addr;
wire [7:0] bus_write_data;
wire [7:0] bus_read_data;
wire [7:0] debug_data;

cpu_6502 #(
    .START_PC(16'h0400),
    .START_PC_ENABLED(1)
) cpu_6502 (
    .i_clk(i_clk),
    .o_phi1(cpu_phi1),
    .o_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_rdy(1'b1),
    .i_nmi_n(1'b1),
    .i_irq_n(1'b1),
    .i_so_n(1'b1),
    .o_sync(cpu_sync),
    .i_bus_data(bus_read_data),
    .o_bus_data(bus_write_data),
    .o_bus_addr(bus_addr),
    .o_rw(cpu_rw),
    .i_debug_sel(3'b000),
    .o_debug_data(debug_data)
);

bram #(
    .INIT_FILE("../6502_functional_test.hex")
) bram (
    .i_clk(i_clk),
    .i_phi2(cpu_phi2),
    .i_addr(bus_addr),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .i_en(1'b1),
    .o_data(bus_read_data)
);

endmodule
