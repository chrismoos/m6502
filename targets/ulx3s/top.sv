module top (
    input clk_25mhz,

    // Active-low reset
    //input gn0,   // i_reset_n

    // Buttons (active-low)
    input [6:0] btn,

    output [7:0] led,

    inout gn4,
    inout gp4,
    inout gn5,
    inout gp5,
    inout gn6,
    inout gp6,
    inout gn7,
    inout gp7,

    input gn8,
    input gp8,
    output gp9,
    output gn9,

    output gp26,  // UART TX
    input gn27,   // UART RX
    output gn26,

    // Debug port outputs 
    output gn16,
    output gp16,
    output gn17,
    output gp17,
    output gn18,
    output gp18,
    output gn19,
    output gp19 
);

wire [7:0] gpioa_input;
wire [7:0] gpioa_output;
wire [7:0] gpioa_oe;
wire cpu_sync;

wire [7:0] bus_mux_data_out;
wire [1:0] bus_mux_sel;
wire bus_mux_data_oe;

wire clk_10, clk_50, clk_100;
wire pll_lock;

wire [7:0] bus_mux_data_in;

wire bus_mux_data_t = ~bus_mux_data_oe;

BB bb0 (.I(bus_mux_data_out[0]), .O(bus_mux_data_in[0]), .T(bus_mux_data_t), .B(gp7));
BB bb1 (.I(bus_mux_data_out[1]), .O(bus_mux_data_in[1]), .T(bus_mux_data_t), .B(gn7));
BB bb2 (.I(bus_mux_data_out[2]), .O(bus_mux_data_in[2]), .T(bus_mux_data_t), .B(gp6));
BB bb3 (.I(bus_mux_data_out[3]), .O(bus_mux_data_in[3]), .T(bus_mux_data_t), .B(gn6));
BB bb4 (.I(bus_mux_data_out[4]), .O(bus_mux_data_in[4]), .T(bus_mux_data_t), .B(gp5));
BB bb5 (.I(bus_mux_data_out[5]), .O(bus_mux_data_in[5]), .T(bus_mux_data_t), .B(gn5));
BB bb6 (.I(bus_mux_data_out[6]), .O(bus_mux_data_in[6]), .T(bus_mux_data_t), .B(gp4));
BB bb7 (.I(bus_mux_data_out[7]), .O(bus_mux_data_in[7]), .T(bus_mux_data_t), .B(gn4));
assign bus_mux_sel = {gp8, gn8}; 

reg reset_n;
reg [2:0] reset_counter;
initial begin
    reset_counter = 0;
    reset_n = 0;
end
always @(posedge clk_50) begin
    if (pll_lock) begin
        reset_counter <= reset_counter + 1;
        if (reset_counter == 7) begin
            reset_n <= 1;
        end
    end
end

reg [2:0] btn_up_sync, btn_down_sync, btn_left_sync;
reg btn_up_prev, btn_down_prev, btn_left_prev;
always @(posedge clk_50 or negedge reset_n) begin
    if (!reset_n) begin
        btn_up_sync <= 3'b000;
        btn_down_sync <= 3'b000;
        btn_left_sync <= 3'b000;
        btn_up_prev <= 1'b0;
        btn_down_prev <= 1'b0;
        btn_left_prev <= 1'b0;
    end else begin
        btn_up_sync <= {btn_up_sync[1:0], btn[3]}; 
        btn_down_sync <= {btn_down_sync[1:0], btn[4]};
        btn_left_sync <= {btn_left_sync[1:0], btn[5]};
        btn_up_prev <= btn_up_sync[2];
        btn_down_prev <= btn_down_sync[2];
        btn_left_prev <= btn_left_sync[2];
    end
end
wire btn_up_pressed = btn_up_sync[2] && !btn_up_prev;
wire btn_down_pressed = btn_down_sync[2] && !btn_down_prev;
wire btn_left_pressed = btn_left_sync[2] && !btn_left_prev;

reg [2:0] debug_sel;
wire [7:0] debug_data;
always @(posedge clk_50 or negedge reset_n) begin
    if (!reset_n)
        debug_sel <= 3'b000; 
    else if (btn_left_pressed)
        debug_sel <= 3'b000; 
    else if (btn_up_pressed)
        debug_sel <= debug_sel + 3'b001;
    else if (btn_down_pressed)
        debug_sel <= debug_sel - 3'b001;
end

assign {gp19, gn19, gp18, gn18, gp17, gn17, gp16, gn16} = debug_data;

assign gpioa_input[5:0] = 6'b0;
assign gpioa_input[6] = gn27;  // UART RX
assign gpioa_input[7] = 1'b0;

wire [15:0] bus_addr;
wire [7:0] bus_cpu_data;
wire bus_rw;
wire bus_phi1, bus_phi2;

assign gp9 = bus_phi2;
assign gn9 = bus_rw;

mcu #(
    .LED_DEFAULT_CLOCK_DIV(5),
    .CPU_CLOCK_DIV_DEFAULT(8'd49)  // 50MHz / 50 = 1MHz
) mcu (
    .i_clk(clk_50),
    .i_reset_n(reset_n),
    .i_bus_data(bus_mux_data_in),
    .o_bus_data(bus_cpu_data),
    .o_bus_addr(bus_addr),
    .o_bus_rw(bus_rw),
    .o_phi1(bus_phi1),
    .o_phi2(bus_phi2),
    .i_gpioa_input(gpioa_input),
    .o_gpioa_output(gpioa_output),
    .o_gpioa_oe(gpioa_oe),
    .o_sync(cpu_sync),
    .i_rdy(1'b1),
    .i_nmi_n(~btn[1]),
    .i_irq_n_ext(1'b1),
    .i_so_n(1'b1),
    .i_debug_sel(debug_sel),
    .o_debug_data(debug_data)
);

assign led[0] = gpioa_output[0];
assign led[1] = gpioa_output[1];
assign led[2] = gpioa_output[2];
assign led[3] = gpioa_output[3];
assign led[4] = gpioa_output[4];
assign led[5] = 0;
assign led[6] = 0;
assign led[7] = 0;
assign gn26 = gpioa_output[7];

// UART pins (controlled via GPIO pin mux modes 0x01/0x02)
assign gp26 = gpioa_output[5];  // UART TX on GPIO pin 5

EHXPLLL#(
    .FEEDBK_PATH("CLKOP"),
    .STDBY_ENABLE("DISABLED"),
    .DPHASE_SOURCE("DISABLED"),
    .CLKOP_ENABLE("ENABLED"),
    .CLKOS_ENABLE("ENABLED"),
    .CLKOS2_ENABLE("ENABLED"),
    .PLL_LOCK_MODE(0),
    .INT_LOCK_STICKY("ENABLED"),

    // ecppll -i 25 --clkout0 100 --clkout1 50 --clkout2 10
    .CLKI_DIV(1),
    .CLKFB_DIV(4),
    .CLKOP_DIV(6),
    .CLKOS_DIV(12),
    .CLKOS2_DIV(60)
) pll(
    .CLKI(clk_25mhz),
    .CLKFB(clk_100),
    .CLKOP(clk_100),
    .CLKOS(clk_50),
    .CLKOS2(clk_10),
    .ENCLKOP(1'b1),
    .ENCLKOS(1'b1),
    .ENCLKOS2(1'b1),
    .ENCLKOS3(1'b0),
    .STDBY(1'b0),
    .PHASESEL1(1'b0),
    .PHASESEL0(1'b0),
    .PHASEDIR(1'b0),
    .PHASESTEP(1'b0),
    .PHASELOADREG(1'b0),
    .PLLWAKESYNC(1'b0),
    .LOCK(pll_lock)
);

bus_multiplexer external_bus (
    .i_sel(bus_mux_sel),
    .i_cpu_data(bus_cpu_data),
    .i_cpu_addr(bus_addr),
    .o_mux_data(bus_mux_data_out),
    .o_mux_data_oe(bus_mux_data_oe),
    .i_mux_data(bus_mux_data_in)
);


endmodule
