module top (
    input clki,
    output rgb0,
    output rgb1,
    output rgb2,
    input touch_1,
    input touch_2,
    input touch_3,
    input touch_4
);

reg reset_n;
reg [2:0] reset_counter;

initial begin
    reset_counter = 0;
    reset_n = 0;
end
always @(posedge clki) begin
    reset_counter <= reset_counter + 1;
    if (reset_counter == 7) begin
        reset_n <= 1;
    end
end


reg [7:0] gpioa_oe;
wire [7:0] gpioa_input;
reg [7:0] gpioa_output;

// GPIO mapping:
//   Pins 0-2: RGB LEDs (output)
//   Pins 4-7: Touch pads (input)
assign gpioa_input = {touch_4, touch_3, touch_2, touch_1, 4'b0};
assign {rgb0, rgb1, rgb2} = {gpioa_output[0], gpioa_output[1], gpioa_output[2]};

always @(posedge clki) begin
    if (!reset_n) begin
    end
end

wire bus_phi1, bus_phi2, cpu_sync, bus_rw;
wire [15:0] bus_addr;
wire [7:0] bus_cpu_data, bram_read_data;
wire [7:0] debug_data;

mcu #(
    .START_PC(16'h1000),
    .START_PC_ENABLED(1),
    .LED_DEFAULT_CLOCK_DIV(5),
    .CPU_CLOCK_DIV_DEFAULT(8'd47)  // 48MHz / 48 = 1MHz
) mcu (
    .i_clk(clki),
    .i_reset_n(reset_n),
    .i_bus_data(bram_read_data),
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
    .i_nmi_n(1'b1),
    .i_irq_n_ext(1'b1),
    .i_so_n(1'b1),
    .i_debug_sel(3'b000),
    .o_debug_data(debug_data)
);

bram #(
    .INIT_FILE("../../examples/build/fomu_touch_led.hex"),
    .SIZE(8192)
) bram (
    .i_clk(clki),
    .i_phi2(bus_phi2),
    .i_addr(bus_addr),
    .i_data(bus_cpu_data),
    .i_rw(bus_rw),
    .i_en(1'b1),
    .o_data(bram_read_data)
);

endmodule