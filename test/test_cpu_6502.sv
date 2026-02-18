`timescale 1ps/1ps

module test_cpu_6502 (
    input i_clk
);

reg i_reset_n;
reg i_rdy;
reg i_nmi_n;
reg i_irq_n;

wire [7:0] ram_read_data;
wire [7:0] bus_write_data;
wire [15:0] bus_addr;
wire bus_rw;
wire cpu_phi1;
wire cpu_phi2;
wire cpu_sync;
wire [7:0] debug_data;

cpu_6502 #(
    .START_PC(16'h400),
    .START_PC_ENABLED(1)
) cpu_6502 (
    .i_clk(i_clk),
    .o_phi1(cpu_phi1),
    .o_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_rdy(i_rdy),
    .i_nmi_n(i_nmi_n),
    .i_irq_n(i_irq_n),
    .i_so_n(1'b1),
    .o_sync(cpu_sync),
    .i_bus_data(ram_read_data),
    .o_bus_data(bus_write_data),
    .o_bus_addr(bus_addr),
    .o_rw(bus_rw),
    .i_debug_sel(3'b000),
    .o_debug_data(debug_data)
);

bus_ram #(
    .INIT_FILE("../test/6502_functional_test.bin")
) ram (
    .i_phi2(cpu_phi2),
    .i_rw(bus_rw),
    .i_addr(bus_addr),
    .i_data(bus_write_data),
    .o_data(ram_read_data)
);

initial begin
    i_rdy = 1;  // Default RDY to high so CPU can run
end

endmodule
