module timer (
    input i_clk,
    input i_phi2,
    input i_reset_n,
    input [2:0] i_addr,
    input [7:0] i_data,
    input i_rw,
    input i_en,
    output reg [7:0] o_data,
    output o_irq
);

`define TIMER_CTRL       3'h0
`define TIMER_STATUS     3'h1
`define TIMER_COUNT_LO   3'h2
`define TIMER_COUNT_HI   3'h3
`define TIMER_RELOAD_LO  3'h4
`define TIMER_RELOAD_HI  3'h5
`define TIMER_PRESCALER  3'h6

`define CTRL_ENABLE      0
`define CTRL_AUTO_RELOAD 1
`define CTRL_IRQ_ENABLE  2
`define CTRL_LOAD        3

`define STATUS_OVERFLOW  0

// Registers
reg [7:0] ctrl_reg;
reg [7:0] status_reg;
reg [7:0] reload_lo;
reg [7:0] reload_hi;
reg [7:0] prescaler_reg;

wire ctrl_enable;
wire ctrl_auto_reload;
wire ctrl_irq_enable;
wire ctrl_load;

assign ctrl_enable = ctrl_reg[`CTRL_ENABLE];
assign ctrl_auto_reload = ctrl_reg[`CTRL_AUTO_RELOAD];
assign ctrl_irq_enable = ctrl_reg[`CTRL_IRQ_ENABLE];
assign ctrl_load = ctrl_reg[`CTRL_LOAD];

wire overflow_flag;
assign overflow_flag = status_reg[`STATUS_OVERFLOW];

reg [15:0] timer_count;
reg [7:0] prescale_counter;

wire [15:0] reload_value;
assign reload_value = {reload_hi, reload_lo};

wire prescale_tick;
assign prescale_tick = (prescale_counter >= prescaler_reg);

assign o_irq = overflow_flag && ctrl_irq_enable;

always_ff @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        prescale_counter <= 8'h00;
    end else begin
        if (prescale_counter >= prescaler_reg) begin
            prescale_counter <= 8'h00;
        end else begin
            prescale_counter <= prescale_counter + 8'h01;
        end
    end
end

reg overflow_clear_req;

always_ff @(posedge i_clk or negedge i_reset_n) begin
    if (!i_reset_n) begin
        timer_count <= 16'h0000;
        status_reg <= 8'h00;
    end else begin
        // LOAD only works when timer is stopped (glitchless)
        if (ctrl_load && !ctrl_enable) begin
            timer_count <= reload_value;
        end else if (ctrl_enable && prescale_tick) begin
            if (timer_count == 16'hFFFF) begin
                status_reg[`STATUS_OVERFLOW] <= 1'b1;
                if (ctrl_auto_reload) begin
                    timer_count <= reload_value;
                end else begin
                    timer_count <= 16'h0000;
                end
            end else begin
                timer_count <= timer_count + 16'h0001;
            end
        end

        if (overflow_clear_req) begin
            status_reg[`STATUS_OVERFLOW] <= 1'b0;
        end
    end
end

always_ff @(posedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        o_data <= 8'h00;
    end else if (i_en && i_rw) begin
        case (i_addr)
            `TIMER_CTRL:       o_data <= ctrl_reg;
            `TIMER_STATUS:     o_data <= status_reg;
            `TIMER_COUNT_LO:   o_data <= timer_count[7:0];
            `TIMER_COUNT_HI:   o_data <= timer_count[15:8];
            `TIMER_RELOAD_LO:  o_data <= reload_lo;
            `TIMER_RELOAD_HI:  o_data <= reload_hi;
            `TIMER_PRESCALER:  o_data <= prescaler_reg;
            default:           o_data <= 8'h00;
        endcase
    end
end

reg load_prev;
always_ff @(negedge i_phi2 or negedge i_reset_n) begin
    if (!i_reset_n) begin
        ctrl_reg <= 8'h00;
        reload_lo <= 8'h00;
        reload_hi <= 8'h00;
        prescaler_reg <= 8'h00;
        overflow_clear_req <= 1'b0;
        load_prev <= 1'b0;
    end else begin
        overflow_clear_req <= 1'b0;

        if (load_prev) begin
            ctrl_reg[`CTRL_LOAD] <= 1'b0;
        end
        load_prev <= ctrl_reg[`CTRL_LOAD];

        if (i_en && !i_rw) begin
            case (i_addr)
                `TIMER_CTRL:       ctrl_reg <= i_data;
                `TIMER_STATUS: begin
                    if (i_data[`STATUS_OVERFLOW]) begin
                        overflow_clear_req <= 1'b1;
                    end
                end
                `TIMER_RELOAD_LO:  reload_lo <= i_data;
                `TIMER_RELOAD_HI:  reload_hi <= i_data;
                `TIMER_PRESCALER:  prescaler_reg <= i_data;
                default: ;
            endcase
        end
    end
end

endmodule
