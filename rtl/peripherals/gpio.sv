module gpio (
    input i_clk,
    input i_phi2,
    input i_reset_n,
    input [3:0] i_addr,
    input [7:0] i_data,
    input i_rw,
    output reg [7:0] o_data,
    input i_en,

    input [7:0] i_pins,
    output reg [7:0] o_pins,
    output reg [7:0] o_pins_oe,

    input i_uart0_tx,
    output o_uart0_rx,
    input i_sk6812_data
);

`define GPIO_OUTPUT_ENABLE_REGISTER 0
`define GPIO_OUTPUT_REGISTER 1
`define GPIO_INPUT_REGISTER 2
`define GPIO_RESERVED 3
`define GPIO_MODE_PIN0 4
`define GPIO_MODE_PIN1 5
`define GPIO_MODE_PIN2 6
`define GPIO_MODE_PIN3 7
`define GPIO_MODE_PIN4 8
`define GPIO_MODE_PIN5 9
`define GPIO_MODE_PIN6 10
`define GPIO_MODE_PIN7 11

/* verilator lint_off UNUSEDPARAM */
localparam MODE_GPIO     = 8'h00;
/* verilator lint_on UNUSEDPARAM */
localparam MODE_UART0_TX = 8'h01;
localparam MODE_UART0_RX = 8'h02;
localparam MODE_SK6812_DATA = 8'h03;

reg [7:0] gpio_pins_oe;
reg [7:0] gpio_pins;

reg [7:0] mode_pin[0:7];

always @(posedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        o_data <= 0;
    end else if (i_rw && i_en) begin
        case (i_addr)
            `GPIO_OUTPUT_ENABLE_REGISTER: o_data <= gpio_pins_oe;
            `GPIO_OUTPUT_REGISTER: o_data <= gpio_pins;
            `GPIO_INPUT_REGISTER: o_data <= i_pins;
            `GPIO_MODE_PIN0: o_data <= mode_pin[0];
            `GPIO_MODE_PIN1: o_data <= mode_pin[1];
            `GPIO_MODE_PIN2: o_data <= mode_pin[2];
            `GPIO_MODE_PIN3: o_data <= mode_pin[3];
            `GPIO_MODE_PIN4: o_data <= mode_pin[4];
            `GPIO_MODE_PIN5: o_data <= mode_pin[5];
            `GPIO_MODE_PIN6: o_data <= mode_pin[6];
            `GPIO_MODE_PIN7: o_data <= mode_pin[7];
            default: o_data <= 0;
        endcase
    end
end

always @(negedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        gpio_pins_oe <= 0;
        gpio_pins <= 0;
        mode_pin[0] <= 0; 
        mode_pin[1] <= 0;
        mode_pin[2] <= 0;
        mode_pin[3] <= 0;
        mode_pin[4] <= 0;
        mode_pin[5] <= 0;
        mode_pin[6] <= 0;
        mode_pin[7] <= 0;
    end else if (!i_rw && i_en) begin
        case (i_addr)
            `GPIO_OUTPUT_ENABLE_REGISTER: gpio_pins_oe <= i_data;
            `GPIO_OUTPUT_REGISTER: gpio_pins <= i_data;
            `GPIO_MODE_PIN0: mode_pin[0] <= i_data;
            `GPIO_MODE_PIN1: mode_pin[1] <= i_data;
            `GPIO_MODE_PIN2: mode_pin[2] <= i_data;
            `GPIO_MODE_PIN3: mode_pin[3] <= i_data;
            `GPIO_MODE_PIN4: mode_pin[4] <= i_data;
            `GPIO_MODE_PIN5: mode_pin[5] <= i_data;
            `GPIO_MODE_PIN6: mode_pin[6] <= i_data;
            `GPIO_MODE_PIN7: mode_pin[7] <= i_data;
            default: ;
        endcase
    end
end

genvar i;
generate
    for (i = 0; i < 8; i = i + 1) begin : pin_mux
        always_comb begin
            case (mode_pin[i])
                MODE_UART0_TX: begin
                    o_pins[i] = i_uart0_tx;
                    o_pins_oe[i] = 1'b1;
                end
                MODE_UART0_RX: begin
                    o_pins[i] = 1'b1;
                    o_pins_oe[i] = 1'b0;
                end
                MODE_SK6812_DATA: begin
                    o_pins[i] = i_sk6812_data;
                    o_pins_oe[i] = 1'b1;
                end
                default: begin
                    o_pins[i] = gpio_pins[i];
                    o_pins_oe[i] = gpio_pins_oe[i];
                end
            endcase
        end
    end
endgenerate

// lowest pin # takes priority
reg [7:0] uart_rx_select;
integer j;
always_comb begin
    uart_rx_select = 8'b0;
    for (j = 0; j < 8; j = j + 1) begin
        if (mode_pin[j] == MODE_UART0_RX && uart_rx_select == 8'b0) begin
            uart_rx_select = 8'b1 << j;
        end
    end
end

assign o_uart0_rx = |(i_pins & uart_rx_select);

endmodule
