`timescale 1ps/1ps

module test_bram (
    input i_clk
);

reg i_phi2;
reg [15:0] i_addr;
reg [7:0] i_data;
reg i_rw;
reg i_en;

wire [7:0] o_data;

bram bram (
    .i_clk(i_clk),
    .i_phi2(i_phi2),
    .i_addr(i_addr),
    .i_data(i_data),
    .i_rw(i_rw),
    .i_en(i_en),
    .o_data(o_data)
);

endmodule
