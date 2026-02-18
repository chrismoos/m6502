from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import cocotb

# 6502 opcodes
LDA_IMM = 0xA9  # 2 cycles
STA_ABS = 0x8D  # 4 cycles
LDA_ABS = 0xAD  # 4 cycles
JMP_ABS = 0x4C  # 3 cycles
BNE = 0xD0      # 2 cycles (not taken), 3 cycles (taken, same page)

# GPIO registers at $A000
GPIO_OE  = 0xA000  # Output Enable
GPIO_OUT = 0xA001  # Output
GPIO_IN  = 0xA002  # Input

# SK6812RGBW LED registers at $A010
LED_CONTROL = 0xA010  # Write bit 0 to strobe
LED_CLKDIV  = 0xA011  # Clock divider
LED_RED     = 0xA012
LED_GREEN   = 0xA013
LED_BLUE    = 0xA014
LED_WHITE   = 0xA015
LED_STATUS  = 0xA016  # Bit 0 = busy

# SK6812 reset takes 800 cycles
SK6812_RESET_CYCLES = 800

# CPU initialization takes 6 cycles before first instruction
CPU_INIT_CYCLES = 6

# Program starts at $0400
START_PC = 0x0400


def lo(addr):
    return addr & 0xFF

def hi(addr):
    return (addr >> 8) & 0xFF


async def init_and_reset(dut):
    """Initialize clocks and apply reset."""
    Clock(dut.i_clk, 20, unit="ns").start()        # 50MHz system clock
    dut.i_reset_n.value = 0
    dut.i_gpioa_input.value = 0
    await ClockCycles(dut.i_clk, 5)


async def load_program(dut, program):
    """Load program into BRAM at START_PC."""
    for i, byte in enumerate(program):
        dut.bram.memory[START_PC + i].value = byte


async def release_reset(dut):
    """Release reset."""
    dut.i_reset_n.value = 1


@cocotb.test()
async def test_gpio_output(dut):
    """Test GPIO output by running 6502 code."""
    # Program:
    #   LDA #$FF       ; 2 cycles
    #   STA $A000      ; 4 cycles - GPIO_OE written
    #   LDA #$42       ; 2 cycles
    #   STA $A001      ; 4 cycles - GPIO_OUT written
    # Total: 12 cycles to complete all writes
    program = [
        LDA_IMM, 0xFF,
        STA_ABS, lo(GPIO_OE), hi(GPIO_OE),
        LDA_IMM, 0x42,
        STA_ABS, lo(GPIO_OUT), hi(GPIO_OUT),
        JMP_ABS, 0x0A, 0x04,
    ]

    await init_and_reset(dut)
    await load_program(dut, program)
    await release_reset(dut)

    # CPU init (6) + LDA#(2) + STA(4) + LDA#(2) + STA(4) = 18 cycles minimum
    # Add margin for microcode overhead and cross-clock domain sync
    await ClockCycles(dut.phi2, CPU_INIT_CYCLES + 20)

    assert dut.o_gpioa_oe.value == 0xFF, f"GPIO OE: expected 0xFF, got {hex(dut.o_gpioa_oe.value)}"
    assert dut.o_gpioa_output.value == 0x42, f"GPIO OUT: expected 0x42, got {hex(dut.o_gpioa_output.value)}"


@cocotb.test()
async def test_gpio_toggle(dut):
    """Test GPIO toggling between two values."""
    # Program:
    #   LDA #$FF       ; 2 cycles
    #   STA $A000      ; 4 cycles - GPIO_OE = 0xFF
    # loop:
    #   LDA #$AA       ; 2 cycles
    #   STA $A001      ; 4 cycles - GPIO_OUT = 0xAA
    #   LDA #$55       ; 2 cycles
    #   STA $A001      ; 4 cycles - GPIO_OUT = 0x55
    #   JMP loop       ; 3 cycles
    # Loop iteration: 15 cycles
    program = [
        LDA_IMM, 0xFF,
        STA_ABS, lo(GPIO_OE), hi(GPIO_OE),
        LDA_IMM, 0xAA,
        STA_ABS, lo(GPIO_OUT), hi(GPIO_OUT),
        LDA_IMM, 0x55,
        STA_ABS, lo(GPIO_OUT), hi(GPIO_OUT),
        JMP_ABS, 0x05, 0x04,
    ]

    await init_and_reset(dut)
    await load_program(dut, program)
    await release_reset(dut)

    # Wait for program to execute and verify OE is set, output is toggling
    await ClockCycles(dut.phi2, CPU_INIT_CYCLES + 100)
    assert dut.o_gpioa_oe.value == 0xFF, f"GPIO OE: expected 0xFF, got {hex(dut.o_gpioa_oe.value)}"

    # Capture current value, wait one loop iteration, verify it changed
    first_val = int(dut.o_gpioa_output.value)
    assert first_val in [0xAA, 0x55], f"GPIO OUT: expected 0xAA or 0x55, got {hex(first_val)}"

    # Wait for loop to toggle (15 cycles per iteration)
    # Wait 8 cycles - enough to execute one half of the loop body
    await ClockCycles(dut.phi2, 8)
    second_val = int(dut.o_gpioa_output.value)
    assert second_val in [0xAA, 0x55], f"GPIO OUT: expected 0xAA or 0x55, got {hex(second_val)}"
    assert first_val != second_val, f"GPIO OUT should have toggled from {hex(first_val)}"


@cocotb.test()
async def test_gpio_input(dut):
    """Test reading GPIO input."""
    # Program:
    #   LDA $A002      ; 4 cycles - read GPIO_IN
    #   STA $0000      ; 4 cycles - store to zero page
    # Total: 8 cycles
    program = [
        LDA_ABS, lo(GPIO_IN), hi(GPIO_IN),
        STA_ABS, 0x00, 0x00,
        JMP_ABS, 0x06, 0x04,
    ]

    await init_and_reset(dut)
    dut.i_gpioa_input.value = 0xCD
    await load_program(dut, program)
    await release_reset(dut)

    # CPU init (6) + LDA abs(4) + STA abs(4) = 14 cycles
    await ClockCycles(dut.phi2, CPU_INIT_CYCLES + 30)

    zp_val = int(dut.bram.memory[0x0000].value)
    assert zp_val == 0xCD, f"Zero page $0000: expected 0xCD, got {hex(zp_val)}"


@cocotb.test()
async def test_led_write_colors(dut):
    """Test writing RGBW color values to SK6812 peripheral."""
    # Program:
    #   LDA #$11       ; 2 cycles
    #   STA $A010      ; 4 cycles - RED
    #   LDA #$22       ; 2 cycles
    #   STA $A011      ; 4 cycles - GREEN
    #   LDA #$33       ; 2 cycles
    #   STA $A012      ; 4 cycles - BLUE
    #   LDA #$44       ; 2 cycles
    #   STA $A013      ; 4 cycles - WHITE
    # Total: 24 cycles
    program = [
        LDA_IMM, 0x11,
        STA_ABS, lo(LED_RED), hi(LED_RED),
        LDA_IMM, 0x22,
        STA_ABS, lo(LED_GREEN), hi(LED_GREEN),
        LDA_IMM, 0x33,
        STA_ABS, lo(LED_BLUE), hi(LED_BLUE),
        LDA_IMM, 0x44,
        STA_ABS, lo(LED_WHITE), hi(LED_WHITE),
        JMP_ABS, 0x18, 0x04,
    ]

    await init_and_reset(dut)
    await load_program(dut, program)
    await release_reset(dut)

    # CPU init (6) + 4x(LDA# + STA) = 6 + 4*(2+4) = 30 cycles
    await ClockCycles(dut.phi2, CPU_INIT_CYCLES + 30)

    # led_color format: [31:24]=GREEN, [23:16]=RED, [15:8]=BLUE, [7:0]=WHITE
    led_color = int(dut.mcu.sk6812.led_color.value)
    red = (led_color >> 16) & 0xFF
    green = (led_color >> 24) & 0xFF
    blue = (led_color >> 8) & 0xFF
    white = led_color & 0xFF

    assert red == 0x11, f"LED RED: expected 0x11, got {hex(red)}"
    assert green == 0x22, f"LED GREEN: expected 0x22, got {hex(green)}"
    assert blue == 0x33, f"LED BLUE: expected 0x33, got {hex(blue)}"
    assert white == 0x44, f"LED WHITE: expected 0x44, got {hex(white)}"


@cocotb.test()
async def test_led_strobe(dut):
    """Test LED strobe triggers data output."""
    # Program: wait for not busy, set color, strobe
    # wait:
    #   LDA $A014      ; Read status
    #   BNE wait       ; Loop while busy
    #   LDA #$AA       ; Set color
    #   STA $A010      ; Write RED
    #   LDA #$01       ; Strobe bit
    #   STA $A015      ; Trigger strobe
    # done:
    #   JMP done
    program = [
        # wait at $0400:
        LDA_ABS, lo(LED_STATUS), hi(LED_STATUS),
        BNE, 0xFB,  # Branch back to $0400
        LDA_IMM, 0xAA,
        STA_ABS, lo(LED_RED), hi(LED_RED),
        LDA_IMM, 0x01,
        STA_ABS, lo(LED_CONTROL), hi(LED_CONTROL),
        JMP_ABS, 0x10, 0x04,  # done at $0410
    ]

    await init_and_reset(dut)
    await load_program(dut, program)
    await release_reset(dut)

    # Wait for SK6812 to exit reset, then CPU executes strobe
    await FallingEdge(dut.mcu.sk6812.sk6812rgbw.o_busy)

    # Wait for transmission to complete (busy goes high then low again)
    await RisingEdge(dut.mcu.sk6812.sk6812rgbw.o_busy)
    await FallingEdge(dut.mcu.sk6812.sk6812rgbw.o_busy)

    # Verify color was latched
    color = int(dut.mcu.sk6812.sk6812rgbw.color.value)
    assert (color >> 16) & 0xFF == 0xAA, f"Color RED should be 0xAA, got {hex(color)}"


@cocotb.test()
async def test_led_status_busy(dut):
    """Test LED status register reflects busy state during transmission."""
    # Program reads status at different points and stores to zero page
    program = [
        # Read status during reset, store to $0000
        LDA_ABS, lo(LED_STATUS), hi(LED_STATUS),
        STA_ABS, 0x00, 0x00,
        # wait_idle loop at $0406
        LDA_ABS, lo(LED_STATUS), hi(LED_STATUS),
        BNE, 0xFB,  # Branch back to $0406
        STA_ABS, 0x01, 0x00,  # Store idle status to $0001
        # Strobe
        LDA_IMM, 0xFF,
        STA_ABS, lo(LED_RED), hi(LED_RED),
        LDA_IMM, 0x01,
        STA_ABS, lo(LED_CONTROL), hi(LED_CONTROL),
        # Read status after strobe, store to $0002
        LDA_ABS, lo(LED_STATUS), hi(LED_STATUS),
        STA_ABS, 0x02, 0x00,
        JMP_ABS, 0x20, 0x04,
    ]

    await init_and_reset(dut)
    await load_program(dut, program)
    await release_reset(dut)

    # Wait for SK6812 to exit reset
    await FallingEdge(dut.mcu.sk6812.sk6812rgbw.o_busy)

    # Run CPU to complete all operations
    await ClockCycles(dut.phi2, 50)

    busy_during_reset = int(dut.bram.memory[0x0000].value)
    idle_after_reset = int(dut.bram.memory[0x0001].value)
    busy_after_strobe = int(dut.bram.memory[0x0002].value)

    assert busy_during_reset == 0x01, f"Status during reset: expected 0x01 (busy), got {hex(busy_during_reset)}"
    assert idle_after_reset == 0x00, f"Status after reset: expected 0x00 (idle), got {hex(idle_after_reset)}"
    assert busy_after_strobe == 0x01, f"Status after strobe: expected 0x01 (busy), got {hex(busy_after_strobe)}"
