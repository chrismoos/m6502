module sk6812rgbw_peripheral #(
    parameter CLOCK_DIV_DEFAULT = 1
) (
    input i_clk,
    input i_phi2,
    input i_reset_n,
    input [2:0] i_addr,
    input [7:0] i_data,
    output reg [7:0] o_data,
    input i_en,
    input i_rw,

    output o_led_data
);

localparam REGISTER_CONTROL = 0;
localparam REGISTER_CLKDIV = 1;
localparam REGISTER_RED = 2;
localparam REGISTER_GREEN = 3;
localparam REGISTER_BLUE = 4;
localparam REGISTER_WHITE = 5;
localparam REGISTER_STATUS = 6;

wire busy;
reg [7:0] clk_div;
reg [31:0] led_color;
reg led_strb;

always @(posedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        o_data <= 0;
    end else if (i_rw && i_en) begin
        case (i_addr)
        REGISTER_CONTROL: o_data <= 8'b0;
        REGISTER_CLKDIV: o_data <= clk_div;
        REGISTER_RED: o_data <= led_color[23:16];
        REGISTER_GREEN: o_data <= led_color[31:24];
        REGISTER_BLUE: o_data <= led_color[15:8];
        REGISTER_WHITE: o_data <= led_color[7:0];
        REGISTER_STATUS: o_data <= {7'b0, busy};
        default: o_data <= 0;
        endcase
    end
end

always @(negedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        led_strb <= 0;
        clk_div <= CLOCK_DIV_DEFAULT;
        led_color <= 0;
    end else begin
        led_strb <= 0;
        if (!i_rw && i_en) begin
            case (i_addr)
            REGISTER_CONTROL: led_strb <= i_data[0];
            REGISTER_CLKDIV: clk_div <= i_data;
            REGISTER_RED: led_color[23:16] <= i_data;
            REGISTER_GREEN: led_color[31:24] <= i_data;
            REGISTER_BLUE: led_color[15:8] <= i_data;
            REGISTER_WHITE: led_color[7:0] <= i_data;
            endcase
        end
    end
end

sk6812rgbw sk6812rgbw (
    .i_clk(i_clk),
    .i_clk_div(clk_div),
    .i_reset_n(i_reset_n),
    .i_led_strb(led_strb),
    .i_led_color(led_color),
    .i_reset_strb(1'b0),
    .o_data(o_led_data),
    .o_busy(busy)
);

endmodule
