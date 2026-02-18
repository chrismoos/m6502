module bram #(
    parameter INIT_FILE = "",
    parameter SIZE = 64*1024
) (
    input i_clk,
    input i_phi2,
    input [15:0] i_addr,
    input [7:0] i_data,
    input i_rw,
    output reg [7:0] o_data,
    input i_en
);

localparam ADDR_WIDTH = $clog2(SIZE);
wire [ADDR_WIDTH-1:0] addr = i_addr[ADDR_WIDTH-1:0];

reg [7:0] memory [0:SIZE-1];

initial begin
    if (INIT_FILE != "")
        $readmemh(INIT_FILE, memory);
end

always @(negedge i_phi2) begin
    if (!i_rw && i_en)
        memory[addr] <= i_data;
end

always @(posedge i_phi2) begin
    o_data <= memory[addr];
end

endmodule
