// This manages CPU clock, peripherals have their own dividers for now and no other clock
// selection.
module clock_control #(
    parameter CPU_DIV_DEFAULT = 8'h00
) (
    input i_clk,
    input i_reset_n,
    input i_phi2,

    // Register interface
    input [1:0] i_addr,
    input [7:0] i_data,
    input i_rw,
    input i_en,
    output reg [7:0] o_data,

    // Divided clock output (CPU only)
    output o_cpu_clk
);

// Register Map:
// 0xA030: CPU_DIV - CPU clock divider (0 = no division, N = divide by N+1)
// 0xA031: Reserved (previously PERIPH_DIV, removed)
// 0xA032: STATUS - Clock status register (read-only)
// 0xA033: Reserved

reg [7:0] cpu_div;
reg [7:0] cpu_div_prev;
reg [7:0] cpu_counter;
reg cpu_clk_divided;

wire cpu_locked;
assign cpu_locked = 1'b1;

always_ff @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        cpu_counter <= 8'h00;
        cpu_clk_divided <= 1'b0;
        cpu_div_prev <= 8'h00;
    end else begin
        cpu_div_prev <= cpu_div;

        if (cpu_div != cpu_div_prev) begin
            cpu_counter <= 8'h00;
            cpu_clk_divided <= 1'b0;
        end else begin
            if (cpu_counter >= cpu_div) begin
                cpu_counter <= 8'h00;
            end else begin
                cpu_counter <= cpu_counter + 8'h01;
            end
            cpu_clk_divided <= (cpu_counter < ((cpu_div + 8'h01) >> 1));
        end
    end
end

assign o_cpu_clk = (cpu_div == 8'h00) ? i_clk : cpu_clk_divided;

always_ff @(posedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        o_data <= 8'h00;
    end else if (i_en && i_rw) begin
        case (i_addr)
            2'h0: o_data <= cpu_div;
            2'h1: o_data <= 8'h00;
            2'h2: o_data <= {7'h00, cpu_locked};
            2'h3: o_data <= 8'h00;             
        endcase
    end
end

always_ff @(negedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        cpu_div <= CPU_DIV_DEFAULT;
    end else if (i_en && !i_rw) begin
        case (i_addr)
            2'h0: cpu_div <= i_data;
            default: ;
        endcase
    end
end

endmodule
