module mcu #(
    parameter START_PC = 16'h0400,
    parameter START_PC_ENABLED = 0,
    parameter LED_DEFAULT_CLOCK_DIV = 2,
    parameter CPU_CLOCK_DIV_DEFAULT = 8'h00,
    parameter UART_FIFO_DEPTH = 8
) (
    input i_clk,
    input i_reset_n,

    input [7:0] i_bus_data,
    output [7:0] o_bus_data,
    output [15:0] o_bus_addr,

    input [7:0] i_gpioa_input,
    output [7:0] o_gpioa_output,
    output [7:0] o_gpioa_oe,

    output o_bus_rw,
    output o_phi1,
    output o_phi2,

    output o_sync,

    input i_rdy,
    input i_nmi_n,
    input i_irq_n_ext,
    input i_so_n,

    // debug port
    input [2:0] i_debug_sel,
    output [7:0] o_debug_data
);

wire cpu_phi1;
wire cpu_phi2;
wire cpu_rw;
wire [15:0] bus_addr;
wire [7:0] gpioa_read_data, ext_read_data, led_read_data, clkctrl_read_data, timer_read_data, uart_read_data;
wire [7:0] bus_write_data;
reg [7:0] bus_read_data;
reg gpioa_en, ext_en, led_en, clkctrl_en, timer_en, uart_en;

wire cpu_clk;

wire timer_irq;

wire uart_tx, uart_rx;
wire uart_tx_irq, uart_rx_irq;

wire sk6812_data;

// Any peripheral IRQ active (high) pulls CPU IRQ low
// Combine external IRQ input with peripheral IRQs
wire cpu_irq_n;
assign cpu_irq_n = i_irq_n_ext & !(timer_irq | uart_tx_irq | uart_rx_irq);

assign o_bus_addr = bus_addr;
assign o_bus_data = bus_write_data;
assign o_bus_rw = cpu_rw;
assign o_phi1 = cpu_phi1;
assign o_phi2 = cpu_phi2;

cpu_6502 #(
    .START_PC(START_PC),
    .START_PC_ENABLED(START_PC_ENABLED)
) cpu_6502 (
    .i_clk(cpu_clk),
    .o_phi1(cpu_phi1),
    .o_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_rdy(i_rdy),
    .i_nmi_n(i_nmi_n),
    .i_irq_n(cpu_irq_n),
    .i_so_n(i_so_n),
    .o_sync(o_sync),
    .i_bus_data(bus_read_data),
    .o_bus_data(bus_write_data),
    .o_bus_addr(bus_addr),
    .o_rw(cpu_rw),
    .i_debug_sel(i_debug_sel),
    .o_debug_data(o_debug_data)
);

gpio gpioa (
    .i_clk(i_clk),
    .i_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(bus_addr[3:0]),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .o_data(gpioa_read_data),
    .i_pins(i_gpioa_input),
    .o_pins(o_gpioa_output),
    .o_pins_oe(o_gpioa_oe),
    .i_en(gpioa_en),
    .i_uart0_tx(uart_tx),
    .o_uart0_rx(uart_rx),
    .i_sk6812_data(sk6812_data)
);

sk6812rgbw_peripheral #(
    .CLOCK_DIV_DEFAULT(LED_DEFAULT_CLOCK_DIV)
) sk6812 (
    .i_clk(i_clk),
    .i_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(bus_addr[2:0]),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .o_data(led_read_data),
    .i_en(led_en),
    .o_led_data(sk6812_data)
);

clock_control #(
    .CPU_DIV_DEFAULT(CPU_CLOCK_DIV_DEFAULT)
) clkctrl (
    .i_clk(i_clk),
    .i_reset_n(i_reset_n),
    .i_phi2(cpu_phi2),
    .i_addr(bus_addr[1:0]),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .o_data(clkctrl_read_data),
    .i_en(clkctrl_en),
    .o_cpu_clk(cpu_clk)
);

timer timer0 (
    .i_clk(i_clk),
    .i_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(bus_addr[2:0]),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .i_en(timer_en),
    .o_data(timer_read_data),
    .o_irq(timer_irq)
);

uart #(
    .FIFO_DEPTH(UART_FIFO_DEPTH)
) uart0 (
    .i_clk(i_clk),
    .i_phi2(cpu_phi2),
    .i_reset_n(i_reset_n),
    .i_addr(bus_addr[2:0]),
    .i_data(bus_write_data),
    .i_rw(cpu_rw),
    .i_en(uart_en),
    .o_data(uart_read_data),
    .i_rx(uart_rx),
    .o_tx(uart_tx),
    .o_tx_irq(uart_tx_irq),
    .o_rx_irq(uart_rx_irq)
);

`define GPIOA_BASE   16'hA000
`define GPIOA_SIZE   12
`define LED_BASE     16'hA010
`define LED_SIZE     8
`define TIMER_BASE   16'hA020
`define TIMER_SIZE   8
`define CLKCTRL_BASE 16'hA030
`define CLKCTRL_SIZE 4
`define UART_BASE    16'hA040
`define UART_SIZE    8

always_comb begin
    gpioa_en = 0;
    ext_en = 0;
    led_en = 0;
    timer_en = 0;
    clkctrl_en = 0;
    uart_en = 0;
    bus_read_data = 8'h00;

    if (bus_addr >= `GPIOA_BASE && bus_addr < (`GPIOA_BASE + `GPIOA_SIZE)) begin
        gpioa_en = 1;
        bus_read_data = gpioa_read_data;
    end else if (bus_addr >= `LED_BASE && bus_addr < (`LED_BASE + `LED_SIZE)) begin
        led_en = 1;
        bus_read_data = led_read_data;
    end else if (bus_addr >= `TIMER_BASE && bus_addr < (`TIMER_BASE + `TIMER_SIZE)) begin
        timer_en = 1;
        bus_read_data = timer_read_data;
    end else if (bus_addr >= `CLKCTRL_BASE && bus_addr < (`CLKCTRL_BASE + `CLKCTRL_SIZE)) begin
        clkctrl_en = 1;
        bus_read_data = clkctrl_read_data;
    end else if (bus_addr >= `UART_BASE && bus_addr < (`UART_BASE + `UART_SIZE)) begin
        uart_en = 1;
        bus_read_data = uart_read_data;
    end else begin
        ext_en = 1;
        bus_read_data = i_bus_data;
    end
end

endmodule
