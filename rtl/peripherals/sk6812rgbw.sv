module sk6812rgbw (
    input i_clk,
    input [7:0] i_clk_div,
    input i_reset_n,
    input i_led_strb,
    input [31:0] i_led_color,
    input i_reset_strb,
    output reg o_data,
    output o_busy
);

reg [7:0] counter;
reg [5:0] pixel_counter;
reg [31:0] color;

wire tick_strb;
assign tick_strb = counter == i_clk_div - 1;

typedef enum logic [2:0] {
    STATE_RESET = 0,
    STATE_DATA = 1,
    STATE_IDLE = 2
} state_t;

state_t state;
reg [9:0] low_cycles;
reg [2:0] high_cycles;

assign o_busy = state == STATE_DATA || state == STATE_RESET;

localparam RESET_CYCLES = 800;

always @(posedge i_clk or negedge i_reset_n) begin
    if(!i_reset_n) begin
        state <= STATE_RESET;
        low_cycles <= RESET_CYCLES;
        high_cycles <= 0;
        o_data <= 0;
        counter <= 0;
        pixel_counter <= 0;
        color <= 0;
    end
    else begin
        counter <= counter + 1;
        if (counter == i_clk_div - 1) begin
            counter <= 0;
        end

        if (i_reset_strb) begin
            state <= STATE_RESET;
            low_cycles <= RESET_CYCLES;
            o_data <= 0;
        end

        else begin
            case (state)
                STATE_RESET: begin
                    if (tick_strb) begin
                        if (low_cycles > 0)
                            low_cycles <= low_cycles - 1;
                    end
                    if (low_cycles == 0)
                        state <= STATE_IDLE;
                end
                STATE_IDLE: begin
                    o_data <= 0;
                    if (i_led_strb && !o_busy) begin
                        state <= STATE_DATA;
                        color <= i_led_color;
                        pixel_counter <= 32;
                        low_cycles <= 0;
                    end
                end
                STATE_DATA: begin
                    if (tick_strb) begin
                        if (high_cycles > 0) begin
                            o_data <= 1;
                            high_cycles <= high_cycles - 1;
                        end
                        else begin
                            o_data <= 0;
                            if (low_cycles > 0)
                                low_cycles <= low_cycles - 1;
                        end

                        if (low_cycles == 0) begin
                            if (color[pixel_counter -1]) begin
                                high_cycles <= 6;
                                low_cycles <= 5;
                            end else begin
                                high_cycles <= 3;
                                low_cycles <= 8;
                            end

                            pixel_counter <= pixel_counter - 1;
                            if (pixel_counter == 0) begin
                                state <= STATE_IDLE;
                                high_cycles <= 0;
                                low_cycles <= 0;
                            end
                        end
                    end
                end
                default: begin
                end
            endcase
        end
    end
end

endmodule
