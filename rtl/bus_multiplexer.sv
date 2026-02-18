module bus_multiplexer (
    input [1:0] i_sel,

    // CPU bus lines
    input [7:0] i_cpu_data,
    input [15:0] i_cpu_addr,

    // mux
    output reg [7:0] o_mux_data,
    output reg o_mux_data_oe,
    input [7:0] i_mux_data
);

localparam MUX_ADDRESS_LO = 0;
localparam MUX_ADDRESS_HI = 1;
localparam MUX_DATA_IN = 2;
localparam MUX_DATA_OUT = 3;

always_comb begin
    case (i_sel)
    MUX_ADDRESS_LO: begin
        o_mux_data_oe = 1;
        o_mux_data = i_cpu_addr[7:0];
    end
    MUX_ADDRESS_HI: begin
        o_mux_data_oe = 1;
        o_mux_data = i_cpu_addr[15:8];
    end
    MUX_DATA_IN: begin
        o_mux_data_oe = 0;
        o_mux_data = 8'b0;
    end
    MUX_DATA_OUT: begin
        o_mux_data_oe = 1;
        o_mux_data = i_cpu_data;
    end
    default: begin
        o_mux_data_oe = 0;
        o_mux_data  = 8'b0;
    end
    endcase
end

endmodule
