`timescale 1ps/1ps

module bus_ram #(
    parameter INIT_FILE = ""
) (
    input i_phi2,
    input i_rw,
    input [15:0] i_addr,
    input [7:0] i_data,
    output reg [7:0] o_data
);

reg [7:0] mem [0:65535];
integer fd, i;
reg [7:0] byte_val;

initial begin
    fd = $fopen(INIT_FILE, "rb");
    if (fd != 0) begin
        for (i = 0; i < 65536; i = i + 1) begin
            if ($fread(byte_val, fd) != 1)
                i = 65536;
            else
                mem[i] = byte_val;
        end
        $fclose(fd);
    end else begin
        $display("ERROR: could not open %s", INIT_FILE);
    end
end

// Read on posedge phi2
always @(posedge i_phi2) begin
    o_data <= mem[i_addr];
end

// Write on negedge phi2
always @(negedge i_phi2) begin
    if (!i_rw) begin
        mem[i_addr] <= i_data;
    end
end

endmodule
