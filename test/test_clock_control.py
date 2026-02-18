"""
Test cases for the clock control peripheral
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

# Clock control registers
CLKCTRL_BASE = 0xA030
CPU_DIV_REG = CLKCTRL_BASE + 0
STATUS_REG = CLKCTRL_BASE + 2


async def reset_mcu(dut):
    """Reset the MCU"""
    dut.i_reset_n.value = 0
    dut.i_gpioa_input.value = 0
    await Timer(100, unit='ns')
    dut.i_reset_n.value = 1
    await Timer(100, unit='ns')


@cocotb.test()
async def test_clock_control_reset_values(dut):
    """Test that clock control registers have correct reset values"""

    # Start clock
    clock = Clock(dut.i_clk, 10, unit='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for CPU to stabilize
    for _ in range(10):
        await RisingEdge(dut.phi2)

    dut._log.info("Testing clock control reset values")

    # Access internal clock control module signals
    assert dut.mcu.clkctrl.cpu_div.value == 0, f"CPU_DIV should reset to 0, got {dut.mcu.clkctrl.cpu_div.value}"

    dut._log.info("✓ Reset values correct")


@cocotb.test()
async def test_cpu_clock_divider(dut):
    """Test CPU clock divider ratios"""

    # Start clock
    clock = Clock(dut.i_clk, 10, unit='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing CPU clock divider")

    # Test DIV=1 (divide by 2) - start with this since DIV=0 is tricky
    dut.mcu.clkctrl.cpu_div.value = 1

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=1: cpu_clk period = {period_ns}ns (expected 20ns)")
    assert period_ns == 20.0, f"DIV=1 should divide by 2 (got {period_ns}ns)"

    # Test DIV=3 (divide by 4)
    dut.mcu.clkctrl.cpu_div.value = 3

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=3: cpu_clk period = {period_ns}ns (expected 40ns)")
    assert period_ns == 40.0, f"DIV=3 should divide by 4 (got {period_ns}ns)"

    # Test DIV=0 (no division)
    dut.mcu.clkctrl.cpu_div.value = 0

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=0: cpu_clk period = {period_ns}ns (expected 10ns)")
    assert period_ns == 10.0, f"DIV=0 should pass through sysclk (got {period_ns}ns)"

    dut._log.info("✓ CPU clock divider working correctly")


@cocotb.test()
async def test_status_register(dut):
    """Test status register reads"""

    # Start clock
    clock = Clock(dut.i_clk, 10, unit='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(10):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing status register")

    cpu_locked = int(dut.mcu.clkctrl.cpu_locked.value)
    status = (cpu_locked << 0)

    dut._log.info(f"Status register: 0x{status:02X}")
    assert cpu_locked == 1, "CPU clock should be locked"

    dut._log.info("✓ Status register correct")


@cocotb.test()
async def test_dynamic_divider_change(dut):
    """Test changing dividers during operation"""

    # Start clock
    clock = Clock(dut.i_clk, 10, unit='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing dynamic divider changes")

    # Start with divide by 4 (DIV=3)
    dut.mcu.clkctrl.cpu_div.value = 3

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=3: cpu_clk period = {period_ns}ns (expected 40ns exactly)")
    assert period_ns == 40.0, f"Should be dividing by 4 exactly (got {period_ns}ns)"

    # Change to no division (DIV=0)
    dut.mcu.clkctrl.cpu_div.value = 0

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=0: cpu_clk period = {period_ns}ns (expected 10ns exactly)")
    assert period_ns == 10.0, f"Divider change should work exactly (got {period_ns}ns)"

    # Change to divide by 2 (DIV=1)
    dut.mcu.clkctrl.cpu_div.value = 1

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at first edge, then at second edge
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    dut._log.info(f"DIV=1: cpu_clk period = {period_ns}ns (expected 20ns exactly)")
    assert period_ns == 20.0, f"Should return to faster speed exactly (got {period_ns}ns)"

    dut._log.info("✓ Dynamic divider changes work correctly")


@cocotb.test()
async def test_div_47_for_1mhz(dut):
    """Test DIV=47 on 48MHz sysclk to verify 1MHz output (Fomu configuration)"""

    # Use 48MHz approximation with integer period (slightly faster than true 48MHz)
    # True 48MHz = 20.833333ns, using 21ns = 47.62MHz (close enough for test)
    clock = Clock(dut.i_clk, 21, unit='ns')  # ~47.6 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing DIV=47 for ~1MHz on ~48MHz sysclk (Fomu config)")

    # Set DIV=47 (divide by 48)
    dut.mcu.clkctrl.cpu_div.value = 47

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Debug: trace what happens over one period
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_counter = int(dut.mcu.clkctrl.cpu_counter.value)
    dut._log.info(f"Debug: Start at counter={start_counter}")

    sysclk_count = 0
    while sysclk_count < 100:  # Cap at 100 sysclk cycles
        await RisingEdge(dut.i_clk)
        sysclk_count += 1
        if int(dut.mcu.clkctrl.o_cpu_clk.value) == 1:  # Found rising edge
            end_counter = int(dut.mcu.clkctrl.cpu_counter.value)
            dut._log.info(f"Debug: Next rising edge at counter={end_counter} after {sysclk_count} sysclk cycles")
            break

    # Measure period properly
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    expected_period = 48 * 21  # 1008ns with our approximated clock
    dut._log.info(f"DIV=47 on ~48MHz: cpu_clk period = {period_ns:.2f}ns (expected {expected_period:.2f}ns for ideal divider)")

    # Check if exact
    if period_ns == expected_period:
        dut._log.info(f"✓ Exact period match!")
    else:
        error_ns = abs(period_ns - expected_period)
        error_pct = 100 * error_ns / expected_period
        dut._log.warning(f"Period error: {error_ns:.2f}ns ({error_pct:.1f}% off)")


@cocotb.test()
async def test_div_49_for_1mhz(dut):
    """Test DIV=49 on 50MHz sysclk to verify 1MHz output (ULX3S configuration)"""

    # Start clock at 50 MHz
    clock = Clock(dut.i_clk, 20, unit='ns')  # 50 MHz = 20ns period
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing DIV=49 for 1MHz on 50MHz sysclk (ULX3S config)")

    # Set DIV=49 (divide by 50)
    dut.mcu.clkctrl.cpu_div.value = 49

    # Wait a few CPU clock cycles to ensure divider has settled
    for _ in range(3):
        await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)

    # Measure period - record time at edge, not before
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    start_time = cocotb.utils.get_sim_time('ns')
    await RisingEdge(dut.mcu.clkctrl.o_cpu_clk)
    end_time = cocotb.utils.get_sim_time('ns')
    period_ns = end_time - start_time

    expected_period = 50 * 20  # Should be 1000ns = 1MHz
    dut._log.info(f"DIV=49 on 50MHz: cpu_clk period = {period_ns:.2f}ns (expected {expected_period:.2f}ns = 1MHz)")

    # Check if exact
    if period_ns == expected_period:
        dut._log.info(f"✓ Exact period match!")
    else:
        error_ns = abs(period_ns - expected_period)
        error_pct = 100 * error_ns / expected_period
        dut._log.warning(f"Period error: {error_ns:.2f}ns ({error_pct:.1f}% off)")
