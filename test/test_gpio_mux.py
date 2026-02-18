from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import cocotb

# GPIO register addresses (relative to GPIO base)
GPIO_OE  = 0x0  # Output Enable
GPIO_OUT = 0x1  # Output
GPIO_IN  = 0x2  # Input
# 0x3 is reserved
GPIO_MODE_PIN0 = 0x4
GPIO_MODE_PIN1 = 0x5
GPIO_MODE_PIN2 = 0x6
GPIO_MODE_PIN3 = 0x7
GPIO_MODE_PIN4 = 0x8
GPIO_MODE_PIN5 = 0x9
GPIO_MODE_PIN6 = 0xA
GPIO_MODE_PIN7 = 0xB

# Pin mode constants
MODE_GPIO     = 0x00
MODE_UART0_TX = 0x01
MODE_UART0_RX = 0x02


async def write_register(dut, addr, value):
    """Write to a GPIO register."""
    await RisingEdge(dut.i_clk)
    dut.i_phi2.value = 1
    dut.i_addr.value = addr
    dut.i_data.value = value
    dut.i_rw.value = 0  # Write
    dut.i_en.value = 1
    await FallingEdge(dut.i_clk)
    dut.i_phi2.value = 0
    await RisingEdge(dut.i_clk)
    dut.i_en.value = 0


async def read_register(dut, addr):
    """Read from a GPIO register."""
    await RisingEdge(dut.i_clk)
    dut.i_phi2.value = 1
    dut.i_addr.value = addr
    dut.i_rw.value = 1  # Read
    dut.i_en.value = 1
    await RisingEdge(dut.i_clk)
    value = dut.o_data.value.integer
    await FallingEdge(dut.i_clk)
    dut.i_phi2.value = 0
    await RisingEdge(dut.i_clk)
    dut.i_en.value = 0
    return value


async def init_gpio(dut):
    """Initialize GPIO testbench."""
    Clock(dut.i_clk, 20, unit="ns").start()  # 50MHz
    dut.i_reset_n.value = 0
    dut.i_phi2.value = 0
    dut.i_addr.value = 0
    dut.i_data.value = 0
    dut.i_rw.value = 1
    dut.i_en.value = 0
    dut.i_pins.value = 0
    dut.i_uart0_tx.value = 1  # UART idle high
    await ClockCycles(dut.i_clk, 5)
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 2)


@cocotb.test()
async def test_reset_values(dut):
    """Test that all MODE_PIN registers initialize to 0 (GPIO mode)."""
    await init_gpio(dut)

    # Read all MODE_PIN registers
    for pin in range(8):
        mode = await read_register(dut, GPIO_MODE_PIN0 + pin)
        assert mode == MODE_GPIO, f"Pin {pin} mode: expected 0x00, got 0x{mode:02x}"

    # Check that OE and OUT are also 0
    oe = await read_register(dut, GPIO_OE)
    out = await read_register(dut, GPIO_OUT)
    assert oe == 0, f"GPIO_OE: expected 0x00, got 0x{oe:02x}"
    assert out == 0, f"GPIO_OUT: expected 0x00, got 0x{out:02x}"


@cocotb.test()
async def test_mode_register_readwrite(dut):
    """Test that MODE_PIN registers can be written and read back."""
    await init_gpio(dut)

    # Write and read each MODE_PIN register
    test_values = [0x00, 0x01, 0x02, 0xFF, 0xAA, 0x55, 0x12, 0x34]
    for pin in range(8):
        await write_register(dut, GPIO_MODE_PIN0 + pin, test_values[pin])

    await ClockCycles(dut.i_clk, 2)

    for pin in range(8):
        mode = await read_register(dut, GPIO_MODE_PIN0 + pin)
        assert mode == test_values[pin], f"Pin {pin} mode: expected 0x{test_values[pin]:02x}, got 0x{mode:02x}"


@cocotb.test()
async def test_gpio_mode(dut):
    """Test that GPIO mode (0x00) allows GPIO OE/OUT to control the pin."""
    await init_gpio(dut)

    # Set pin 3 to GPIO mode (should be default)
    await write_register(dut, GPIO_MODE_PIN3, MODE_GPIO)

    # Enable output on pin 3
    await write_register(dut, GPIO_OE, 0x08)  # Bit 3
    await write_register(dut, GPIO_OUT, 0x08) # Pin 3 high

    await ClockCycles(dut.i_clk, 2)

    assert dut.o_pins.value.integer & 0x08, "Pin 3 should be high"
    assert dut.o_pins_oe.value.integer & 0x08, "Pin 3 should be output"

    # Set pin 3 low
    await write_register(dut, GPIO_OUT, 0x00)
    await ClockCycles(dut.i_clk, 2)

    assert not (dut.o_pins.value.integer & 0x08), "Pin 3 should be low"


@cocotb.test()
async def test_uart_tx_mode(dut):
    """Test that UART TX mode makes pin follow i_uart0_tx signal."""
    await init_gpio(dut)

    # Set pin 2 to UART TX mode
    await write_register(dut, GPIO_MODE_PIN2, MODE_UART0_TX)

    await ClockCycles(dut.i_clk, 2)

    # Pin should be output and follow i_uart0_tx
    assert dut.o_pins_oe.value.integer & 0x04, "Pin 2 should be output"

    # Test UART TX high
    dut.i_uart0_tx.value = 1
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_pins.value.integer & 0x04, "Pin 2 should be high when UART TX is high"

    # Test UART TX low
    dut.i_uart0_tx.value = 0
    await ClockCycles(dut.i_clk, 2)
    assert not (dut.o_pins.value.integer & 0x04), "Pin 2 should be low when UART TX is low"

    # GPIO OUT should not affect the pin in UART TX mode
    await write_register(dut, GPIO_OUT, 0xFF)
    dut.i_uart0_tx.value = 0
    await ClockCycles(dut.i_clk, 2)
    assert not (dut.o_pins.value.integer & 0x04), "Pin 2 should still follow UART TX, not GPIO OUT"


@cocotb.test()
async def test_uart_rx_mode(dut):
    """Test that UART RX mode makes pin input and routes to o_uart0_rx."""
    await init_gpio(dut)

    # Set pin 5 to UART RX mode
    await write_register(dut, GPIO_MODE_PIN5, MODE_UART0_RX)

    await ClockCycles(dut.i_clk, 2)

    # Pin should be input
    assert not (dut.o_pins_oe.value.integer & 0x20), "Pin 5 should be input"

    # Test RX high
    dut.i_pins.value = 0x20  # Pin 5 high
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_uart0_rx.value == 1, "UART RX should be high when pin 5 is high"

    # Test RX low
    dut.i_pins.value = 0x00  # Pin 5 low
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_uart0_rx.value == 0, "UART RX should be low when pin 5 is low"


@cocotb.test()
async def test_multiple_rx_pins(dut):
    """Test that when multiple pins are RX, lowest pin number wins."""
    await init_gpio(dut)

    # Set pins 1, 3, and 6 to UART RX mode
    await write_register(dut, GPIO_MODE_PIN1, MODE_UART0_RX)
    await write_register(dut, GPIO_MODE_PIN3, MODE_UART0_RX)
    await write_register(dut, GPIO_MODE_PIN6, MODE_UART0_RX)

    await ClockCycles(dut.i_clk, 2)

    # All should be inputs
    assert not (dut.o_pins_oe.value.integer & 0x02), "Pin 1 should be input"
    assert not (dut.o_pins_oe.value.integer & 0x08), "Pin 3 should be input"
    assert not (dut.o_pins_oe.value.integer & 0x40), "Pin 6 should be input"

    # Only pin 1 (lowest) should control UART RX
    dut.i_pins.value = 0x02  # Only pin 1 high
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_uart0_rx.value == 1, "UART RX should be high (from pin 1)"

    dut.i_pins.value = 0x48  # Pins 3 and 6 high, pin 1 low
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_uart0_rx.value == 0, "UART RX should be low (pin 1 is low, others ignored)"

    dut.i_pins.value = 0x4A  # All three pins high
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_uart0_rx.value == 1, "UART RX should be high (pin 1 is high)"


@cocotb.test()
async def test_multiple_tx_pins(dut):
    """Test that multiple pins can be TX and all drive the same signal."""
    await init_gpio(dut)

    # Set pins 0, 4, and 7 to UART TX mode
    await write_register(dut, GPIO_MODE_PIN0, MODE_UART0_TX)
    await write_register(dut, GPIO_MODE_PIN4, MODE_UART0_TX)
    await write_register(dut, GPIO_MODE_PIN7, MODE_UART0_TX)

    await ClockCycles(dut.i_clk, 2)

    # All should be outputs
    assert dut.o_pins_oe.value.integer & 0x01, "Pin 0 should be output"
    assert dut.o_pins_oe.value.integer & 0x10, "Pin 4 should be output"
    assert dut.o_pins_oe.value.integer & 0x80, "Pin 7 should be output"

    # All should follow UART TX high
    dut.i_uart0_tx.value = 1
    await ClockCycles(dut.i_clk, 2)
    assert dut.o_pins.value.integer & 0x01, "Pin 0 should be high"
    assert dut.o_pins.value.integer & 0x10, "Pin 4 should be high"
    assert dut.o_pins.value.integer & 0x80, "Pin 7 should be high"

    # All should follow UART TX low
    dut.i_uart0_tx.value = 0
    await ClockCycles(dut.i_clk, 2)
    assert not (dut.o_pins.value.integer & 0x01), "Pin 0 should be low"
    assert not (dut.o_pins.value.integer & 0x10), "Pin 4 should be low"
    assert not (dut.o_pins.value.integer & 0x80), "Pin 7 should be low"


@cocotb.test()
async def test_dynamic_mode_change(dut):
    """Test changing pin mode dynamically while active."""
    await init_gpio(dut)

    # Start with pin 2 as GPIO
    await write_register(dut, GPIO_MODE_PIN2, MODE_GPIO)
    await write_register(dut, GPIO_OE, 0x04)
    await write_register(dut, GPIO_OUT, 0x04)

    await ClockCycles(dut.i_clk, 2)
    assert dut.o_pins.value.integer & 0x04, "Pin 2 should be high in GPIO mode"

    # Change to UART TX mode
    dut.i_uart0_tx.value = 0
    await write_register(dut, GPIO_MODE_PIN2, MODE_UART0_TX)

    await ClockCycles(dut.i_clk, 2)
    assert not (dut.o_pins.value.integer & 0x04), "Pin 2 should be low in UART TX mode"

    # Change to UART RX mode
    await write_register(dut, GPIO_MODE_PIN2, MODE_UART0_RX)

    await ClockCycles(dut.i_clk, 2)
    assert not (dut.o_pins_oe.value.integer & 0x04), "Pin 2 should be input in UART RX mode"

    # Change back to GPIO
    await write_register(dut, GPIO_MODE_PIN2, MODE_GPIO)

    await ClockCycles(dut.i_clk, 2)
    assert dut.o_pins.value.integer & 0x04, "Pin 2 should be high again in GPIO mode"


@cocotb.test()
async def test_in_register_always_reads_actual_pins(dut):
    """Test that IN register always reads actual pin state regardless of mode."""
    await init_gpio(dut)

    # Set various pin modes
    await write_register(dut, GPIO_MODE_PIN0, MODE_GPIO)
    await write_register(dut, GPIO_MODE_PIN1, MODE_UART0_TX)
    await write_register(dut, GPIO_MODE_PIN2, MODE_UART0_RX)

    # Set physical pin values
    dut.i_pins.value = 0xAA  # 10101010

    await ClockCycles(dut.i_clk, 2)

    # Read IN register
    in_value = await read_register(dut, GPIO_IN)
    assert in_value == 0xAA, f"IN register should read 0xAA, got 0x{in_value:02x}"

    # Change physical pins
    dut.i_pins.value = 0x55  # 01010101

    await ClockCycles(dut.i_clk, 2)

    in_value = await read_register(dut, GPIO_IN)
    assert in_value == 0x55, f"IN register should read 0x55, got 0x{in_value:02x}"
