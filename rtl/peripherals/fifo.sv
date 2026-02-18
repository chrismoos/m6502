module fifo #(
    parameter DEPTH = 8,
    parameter WIDTH = 8
) (
    input i_clk,
    input i_reset_n,

    input i_write,
    input [WIDTH-1:0] i_data,

    input i_read,
    output [WIDTH-1:0] o_data,

    output o_full,
    output o_empty,
    output [$clog2(DEPTH):0] o_count
);

reg [WIDTH-1:0] memory [0:DEPTH-1];

reg [$clog2(DEPTH)-1:0] write_ptr;
reg [$clog2(DEPTH)-1:0] read_ptr;

reg [$clog2(DEPTH):0] count;

assign o_empty = (count == 0);
assign o_full = (count == DEPTH);
assign o_count = count;

assign o_data = memory[read_ptr];

always @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        write_ptr <= 0;
        read_ptr <= 0;
        count <= 0;
    end else begin
        if (i_write && i_read && !o_empty && !o_full) begin
            memory[write_ptr] <= i_data;
            write_ptr <= (write_ptr == ($clog2(DEPTH))'(DEPTH-1)) ? 0 : write_ptr + 1;
            read_ptr <= (read_ptr == ($clog2(DEPTH))'(DEPTH-1)) ? 0 : read_ptr + 1;
        end
        else if (i_write && !o_full) begin
            memory[write_ptr] <= i_data;
            write_ptr <= (write_ptr == ($clog2(DEPTH))'(DEPTH-1)) ? 0 : write_ptr + 1;
            count <= count + 1;
        end
        else if (i_read && !o_empty) begin
            read_ptr <= (read_ptr == ($clog2(DEPTH))'(DEPTH-1)) ? 0 : read_ptr + 1;
            count <= count - 1;
        end
    end
end

endmodule
