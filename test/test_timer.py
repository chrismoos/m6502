"""
Test cases for the timer peripheral
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Timer registers
TIMER_BASE = 0xA020
CTRL_REG = TIMER_BASE + 0
STATUS_REG = TIMER_BASE + 1
COUNT_LO_REG = TIMER_BASE + 2
COUNT_HI_REG = TIMER_BASE + 3
RELOAD_LO_REG = TIMER_BASE + 4
RELOAD_HI_REG = TIMER_BASE + 5
PRESCALER_REG = TIMER_BASE + 6

# Control register bits
CTRL_ENABLE = 0x01
CTRL_AUTO_RELOAD = 0x02
CTRL_IRQ_ENABLE = 0x04
CTRL_LOAD = 0x08

# Status register bits
STATUS_OVERFLOW = 0x01


async def reset_mcu(dut):
    """Reset the MCU"""
    dut.i_reset_n.value = 0
    dut.i_gpioa_input.value = 0
    await Timer(100, units='ns')
    dut.i_reset_n.value = 1
    await Timer(100, units='ns')


@cocotb.test()
async def test_timer_reset_values(dut):
    """Test that timer registers have correct reset values"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for CPU to stabilize
    for _ in range(10):
        await RisingEdge(dut.phi2)

    dut._log.info("Testing timer reset values")

    # Access internal timer module signals
    assert dut.mcu.timer0.ctrl_reg.value == 0, f"CTRL should reset to 0, got {dut.mcu.timer0.ctrl_reg.value}"
    assert dut.mcu.timer0.status_reg.value == 0, f"STATUS should reset to 0, got {dut.mcu.timer0.status_reg.value}"
    assert dut.mcu.timer0.timer_count.value == 0, f"COUNT should reset to 0, got {dut.mcu.timer0.timer_count.value}"
    assert dut.mcu.timer0.reload_lo.value == 0, f"RELOAD_LO should reset to 0, got {dut.mcu.timer0.reload_lo.value}"
    assert dut.mcu.timer0.reload_hi.value == 0, f"RELOAD_HI should reset to 0, got {dut.mcu.timer0.reload_hi.value}"
    assert dut.mcu.timer0.prescaler_reg.value == 0, f"PRESCALER should reset to 0, got {dut.mcu.timer0.prescaler_reg.value}"

    dut._log.info("✓ Reset values correct")


@cocotb.test()
async def test_timer_basic_counting(dut):
    """Test that timer counts when enabled"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing basic timer counting")

    # Set prescaler to 0 (every cycle) and enable timer
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # Read initial count
    initial_count = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Initial count: {initial_count}")

    # Wait some cycles
    for _ in range(100):
        await RisingEdge(dut.i_clk)

    # Read final count
    final_count = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Final count after 100 cycles: {final_count}")

    # Should have counted up (allowing for some variation)
    assert final_count > initial_count, f"Timer should count up, initial={initial_count}, final={final_count}"
    assert final_count >= 90, f"Should count approximately 100 times, got {final_count}"

    dut._log.info("✓ Basic counting works")


@cocotb.test()
async def test_timer_prescaler_division(dut):
    """Test timer prescaler with different division ratios"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing timer prescaler")

    # Test PRESCALER=0 (tick every cycle)
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)

    for _ in range(100):
        await RisingEdge(dut.i_clk)

    count_div0 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"PRESCALER=0: count={count_div0} after 100 cycles (expected ~100)")
    assert 95 <= count_div0 <= 105, f"PRESCALER=0 should count ~100, got {count_div0}"

    # Test PRESCALER=1 (divide by 2)
    dut.mcu.timer0.prescaler_reg.value = 1
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    for _ in range(100):
        await RisingEdge(dut.i_clk)

    count_div1 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"PRESCALER=1: count={count_div1} after 100 cycles (expected ~50)")
    assert 45 <= count_div1 <= 55, f"PRESCALER=1 should count ~50, got {count_div1}"

    # Test PRESCALER=3 (divide by 4)
    dut.mcu.timer0.prescaler_reg.value = 3
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    for _ in range(100):
        await RisingEdge(dut.i_clk)

    count_div3 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"PRESCALER=3: count={count_div3} after 100 cycles (expected ~25)")
    assert 20 <= count_div3 <= 30, f"PRESCALER=3 should count ~25, got {count_div3}"

    # Test PRESCALER=7 (divide by 8)
    dut.mcu.timer0.prescaler_reg.value = 7
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    for _ in range(200):
        await RisingEdge(dut.i_clk)

    count_div7 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"PRESCALER=7: count={count_div7} after 200 cycles (expected ~25)")
    assert 20 <= count_div7 <= 30, f"PRESCALER=7 should count ~25, got {count_div7}"

    dut._log.info("✓ Prescaler division works correctly")


@cocotb.test()
async def test_timer_overflow_detection(dut):
    """Test overflow flag sets at 0xFFFF"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing timer overflow detection")

    # Set counter near overflow
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0xFFFD  # Close to overflow
    await RisingEdge(dut.i_clk)

    # Wait for overflow
    for i in range(10):
        await RisingEdge(dut.i_clk)
        count = int(dut.mcu.timer0.timer_count.value)
        overflow = int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW
        dut._log.info(f"Cycle {i}: count=0x{count:04X}, overflow={overflow}")

        if overflow:
            dut._log.info(f"✓ Overflow detected at count 0x{count:04X}")
            break
    else:
        assert False, "Overflow flag should have been set"

    # Verify overflow flag is set
    assert int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW, "Overflow flag should be set"
    dut._log.info("✓ Overflow detection works")


@cocotb.test()
async def test_timer_auto_reload(dut):
    """Test auto-reload functionality"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing timer auto-reload")

    # Set reload value
    reload_val = 0xFFF0
    dut.mcu.timer0.reload_lo.value = reload_val & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val >> 8) & 0xFF

    # Enable timer with auto-reload
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_AUTO_RELOAD
    dut.mcu.timer0.timer_count.value = 0xFFFE  # Just before overflow
    await RisingEdge(dut.i_clk)

    # Wait for overflow and reload
    for i in range(20):
        await RisingEdge(dut.i_clk)
        count = int(dut.mcu.timer0.timer_count.value)
        overflow = int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW

        if overflow:
            dut._log.info(f"Overflow at cycle {i}, count after reload=0x{count:04X}")
            # Count should have reloaded to reload_val
            assert count >= reload_val, f"Should reload to 0x{reload_val:04X}, got 0x{count:04X}"
            dut._log.info("✓ Auto-reload works")
            break
    else:
        assert False, "Auto-reload should have occurred"


@cocotb.test()
async def test_timer_overflow_flag_clear(dut):
    """Test write-1-to-clear for overflow flag"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing overflow flag clear")

    # Set counter to overflow quickly
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0xFFFE
    await RisingEdge(dut.i_clk)

    # Wait for overflow
    for _ in range(10):
        await RisingEdge(dut.i_clk)
        if int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW:
            break

    # Verify overflow is set
    assert int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW, "Overflow should be set"
    dut._log.info("Overflow flag is set")

    # Simulate write-1-to-clear by directly clearing the status bit
    # In real operation, this would come from writing to STATUS register via CPU
    # For this test, we directly clear it to verify the flag can be cleared
    dut.mcu.timer0.status_reg.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # Verify overflow is cleared
    overflow_after = int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW
    dut._log.info(f"Overflow after clear: {overflow_after}")
    assert overflow_after == 0, "Overflow flag should be cleared"

    dut._log.info("✓ Overflow flag clear works")


@cocotb.test()
async def test_timer_irq_signal(dut):
    """Test IRQ output signal"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing timer IRQ signal")

    # Initially IRQ should be low
    assert int(dut.mcu.timer_irq.value) == 0, "IRQ should be low initially"

    # Enable timer and IRQ, but no overflow yet
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_IRQ_ENABLE
    dut.mcu.timer0.timer_count.value = 0x0100
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    assert int(dut.mcu.timer_irq.value) == 0, "IRQ should be low without overflow"

    # Force overflow
    dut.mcu.timer0.timer_count.value = 0xFFFE
    await RisingEdge(dut.i_clk)

    # Wait for overflow
    for _ in range(10):
        await RisingEdge(dut.i_clk)
        if int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW:
            break

    # IRQ should be high (overflow && irq_enable)
    assert int(dut.mcu.timer_irq.value) == 1, "IRQ should be high when overflow and IRQ enabled"
    dut._log.info("✓ IRQ asserted on overflow")

    # Clear IRQ enable bit (keep overflow set)
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE  # Disable IRQ
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # IRQ should be low even though overflow is set
    assert int(dut.mcu.timer_irq.value) == 0, "IRQ should be low when IRQ disabled"
    dut._log.info("✓ IRQ disabled when IRQ_ENABLE=0")

    # Re-enable IRQ
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_IRQ_ENABLE
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # IRQ should be high again
    assert int(dut.mcu.timer_irq.value) == 1, "IRQ should be high when re-enabled"

    # Clear overflow flag by directly writing to status register
    dut.mcu.timer0.status_reg.value = 0
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # IRQ should be low
    assert int(dut.mcu.timer_irq.value) == 0, f"IRQ should be low when overflow cleared, overflow={int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW}"
    dut._log.info("✓ IRQ signal works correctly")


@cocotb.test()
async def test_timer_read_while_running(dut):
    """Test reading counter while timer is running"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing reading timer while running")

    # Enable timer with slow prescaler
    dut.mcu.timer0.prescaler_reg.value = 3  # Divide by 4
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)

    # Read counter multiple times
    prev_count = 0
    for i in range(5):
        await RisingEdge(dut.i_clk)
        for _ in range(20):
            await RisingEdge(dut.i_clk)

        count = int(dut.mcu.timer0.timer_count.value)
        dut._log.info(f"Read {i}: count={count}")
        assert count >= prev_count, "Count should be monotonically increasing"
        prev_count = count

    dut._log.info("✓ Timer can be read while running")


@cocotb.test()
async def test_timer_disable_mid_count(dut):
    """Test disabling timer stops counting"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing timer disable")

    # Enable timer
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0
    await RisingEdge(dut.i_clk)

    # Let it count for a bit
    for _ in range(50):
        await RisingEdge(dut.i_clk)

    count_before_disable = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Count before disable: {count_before_disable}")
    assert count_before_disable > 0, "Timer should have counted"

    # Disable timer
    dut.mcu.timer0.ctrl_reg.value = 0  # Clear ENABLE bit
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # Allow time for disable to propagate (clock domain crossing)
    for _ in range(5):
        await RisingEdge(dut.i_clk)

    # Read count after disable takes effect
    count_after_stable = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Count after disable stabilized: {count_after_stable}")

    # Wait and verify count doesn't change further
    for _ in range(50):
        await RisingEdge(dut.i_clk)

    count_after_disable = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Count after waiting: {count_after_disable}")
    assert count_after_disable == count_after_stable, "Count should not change when disabled"

    dut._log.info("✓ Timer stops when disabled")


@cocotb.test()
async def test_timer_load_when_stopped(dut):
    """Test LOAD bit loads counter when timer is stopped"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing LOAD bit when timer stopped")

    # Set reload value
    reload_val = 0x1234
    dut.mcu.timer0.reload_lo.value = reload_val & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val >> 8) & 0xFF
    await RisingEdge(dut.phi2)

    # Verify counter is at 0
    assert int(dut.mcu.timer0.timer_count.value) == 0, "Counter should start at 0"

    # Set LOAD bit (timer is stopped)
    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)  # Cycle 1: load_prev gets set
    await RisingEdge(dut.phi2)  # Cycle 2: LOAD auto-clears
    await RisingEdge(dut.i_clk)  # Wait for i_clk (counter domain)
    await RisingEdge(dut.i_clk)

    # Verify counter loaded from RELOAD
    count_after_load = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Counter after LOAD: 0x{count_after_load:04X} (expected 0x{reload_val:04X})")
    assert count_after_load == reload_val, f"Counter should be 0x{reload_val:04X}, got 0x{count_after_load:04X}"

    # Verify LOAD bit auto-cleared
    ctrl_after = int(dut.mcu.timer0.ctrl_reg.value)
    dut._log.info(f"CTRL after LOAD: 0x{ctrl_after:02X}")
    assert (ctrl_after & CTRL_LOAD) == 0, "LOAD bit should auto-clear"

    dut._log.info("✓ LOAD works when timer stopped and auto-clears")


@cocotb.test()
async def test_timer_load_when_running_ignored(dut):
    """Test LOAD bit is ignored when timer is running (glitchless)"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing LOAD bit ignored when timer running")

    # Set reload value
    reload_val = 0x5678
    dut.mcu.timer0.reload_lo.value = reload_val & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val >> 8) & 0xFF

    # Enable timer and let it count
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE
    dut.mcu.timer0.timer_count.value = 0x0100
    await RisingEdge(dut.i_clk)

    # Let it count for a bit
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    count_before_load = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Counter before LOAD attempt: 0x{count_before_load:04X}")

    # Try to set LOAD bit while timer is running (should be ignored)
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    count_after_load = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"Counter after LOAD attempt: 0x{count_after_load:04X}")

    # Counter should NOT have been loaded (should have continued counting)
    assert count_after_load != reload_val, f"Counter should NOT load to 0x{reload_val:04X} when running"
    assert count_after_load > count_before_load, "Counter should continue counting normally"

    dut._log.info("✓ LOAD ignored when timer running (glitchless)")


@cocotb.test()
async def test_timer_load_fixes_first_overflow(dut):
    """Test LOAD fixes first overflow timing issue"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing LOAD fixes first overflow timing")

    # Set reload value for short overflow period
    reload_val = 0xFFF0  # Count 16 ticks to overflow
    dut.mcu.timer0.reload_lo.value = reload_val & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val >> 8) & 0xFF
    await RisingEdge(dut.i_clk)

    # === Test WITHOUT LOAD (old behavior) ===
    dut._log.info("Testing WITHOUT LOAD...")
    dut.mcu.timer0.prescaler_reg.value = 0
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_AUTO_RELOAD
    dut.mcu.timer0.timer_count.value = 0  # Starts at 0
    dut.mcu.timer0.status_reg.value = 0
    await RisingEdge(dut.i_clk)

    # Count cycles to first overflow
    cycles_without_load = 0
    for _ in range(70000):
        await RisingEdge(dut.i_clk)
        cycles_without_load += 1
        if int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW:
            break

    dut._log.info(f"First overflow WITHOUT LOAD: {cycles_without_load} cycles")
    # Should be ~65536 (full count from 0 to FFFF)
    assert 65000 < cycles_without_load < 66000, f"First overflow should be ~65536, got {cycles_without_load}"

    # Clear overflow
    dut.mcu.timer0.status_reg.value = 0
    await RisingEdge(dut.i_clk)

    # Count cycles to second overflow
    cycles_second = 0
    for _ in range(100):
        await RisingEdge(dut.i_clk)
        cycles_second += 1
        if int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW:
            break

    dut._log.info(f"Second overflow WITHOUT LOAD: {cycles_second} cycles")
    expected_cycles = 65536 - reload_val
    assert expected_cycles - 5 < cycles_second < expected_cycles + 5, f"Second overflow should be ~{expected_cycles}, got {cycles_second}"

    # === Test WITH LOAD (new behavior) ===
    dut._log.info("Testing WITH LOAD...")
    dut.mcu.timer0.ctrl_reg.value = 0  # Stop timer
    await RisingEdge(dut.i_clk)

    # Load counter before starting
    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    # Verify counter was loaded
    count_after_load = int(dut.mcu.timer0.timer_count.value)
    assert count_after_load == reload_val, f"Counter should be loaded to 0x{reload_val:04X}"

    # Clear overflow flag
    dut.mcu.timer0.status_reg.value = 0
    await RisingEdge(dut.i_clk)

    # Start timer
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_AUTO_RELOAD
    await RisingEdge(dut.i_clk)

    # Count cycles to first overflow WITH LOAD
    cycles_with_load = 0
    for _ in range(100):
        await RisingEdge(dut.i_clk)
        cycles_with_load += 1
        if int(dut.mcu.timer0.status_reg.value) & STATUS_OVERFLOW:
            break

    dut._log.info(f"First overflow WITH LOAD: {cycles_with_load} cycles")
    # Should be ~16 (same as subsequent overflows)
    assert expected_cycles - 5 < cycles_with_load < expected_cycles + 5, f"First overflow should be ~{expected_cycles}, got {cycles_with_load}"

    dut._log.info(f"✓ LOAD fixes first overflow timing ({cycles_without_load} → {cycles_with_load} cycles)")


@cocotb.test()
async def test_timer_load_multiple_times(dut):
    """Test LOAD can be used multiple times"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing multiple LOAD operations")

    # Set initial reload value
    reload_val1 = 0x1000
    dut.mcu.timer0.reload_lo.value = reload_val1 & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val1 >> 8) & 0xFF
    await RisingEdge(dut.i_clk)

    # First LOAD
    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    count1 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"After first LOAD: 0x{count1:04X}")
    assert count1 == reload_val1, f"Should be 0x{reload_val1:04X}"

    # Change reload value
    reload_val2 = 0x2000
    dut.mcu.timer0.reload_lo.value = reload_val2 & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val2 >> 8) & 0xFF
    await RisingEdge(dut.phi2)

    # Second LOAD
    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    count2 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"After second LOAD: 0x{count2:04X}")
    assert count2 == reload_val2, f"Should be 0x{reload_val2:04X}"

    # Third LOAD with different value
    reload_val3 = 0xABCD
    dut.mcu.timer0.reload_lo.value = reload_val3 & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val3 >> 8) & 0xFF
    await RisingEdge(dut.phi2)

    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    count3 = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"After third LOAD: 0x{count3:04X}")
    assert count3 == reload_val3, f"Should be 0x{reload_val3:04X}"

    dut._log.info("✓ LOAD can be used multiple times")


@cocotb.test()
async def test_timer_load_with_enable_sequence(dut):
    """Test proper LOAD → ENABLE sequence"""

    # Start clock
    clock = Clock(dut.i_clk, 10, units='ns')  # 100 MHz
    cocotb.start_soon(clock.start())

    # Reset
    await reset_mcu(dut)

    # Wait for initialization
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    dut._log.info("Testing LOAD → ENABLE sequence")

    # Set reload value
    reload_val = 0x8000
    dut.mcu.timer0.reload_lo.value = reload_val & 0xFF
    dut.mcu.timer0.reload_hi.value = (reload_val >> 8) & 0xFF
    dut.mcu.timer0.prescaler_reg.value = 0
    await RisingEdge(dut.i_clk)

    # Step 1: LOAD (timer stopped)
    dut.mcu.timer0.ctrl_reg.value = CTRL_LOAD
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.phi2)
    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    count_after_load = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"After LOAD: 0x{count_after_load:04X}")
    assert count_after_load == reload_val, f"Should be 0x{reload_val:04X}"

    # Step 2: ENABLE (separate write)
    dut.mcu.timer0.ctrl_reg.value = CTRL_ENABLE | CTRL_AUTO_RELOAD
    await RisingEdge(dut.i_clk)

    # Let it count a bit
    for _ in range(20):
        await RisingEdge(dut.i_clk)

    count_after_enable = int(dut.mcu.timer0.timer_count.value)
    dut._log.info(f"After ENABLE: 0x{count_after_enable:04X}")
    assert count_after_enable > reload_val, "Counter should be counting up from loaded value"
    assert count_after_enable < reload_val + 50, "Should have counted ~20 ticks"

    dut._log.info("✓ LOAD → ENABLE sequence works correctly")
