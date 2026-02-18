import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, First, RisingEdge, Timer

# UART register addresses
ADDR_CTRL = 0x0
ADDR_STATUS = 0x1
ADDR_DATA = 0x2
ADDR_BAUD_LO = 0x3
ADDR_BAUD_HI = 0x4

# Control register bits
CTRL_TX_ENABLE = 0x01
CTRL_RX_ENABLE = 0x02
CTRL_TX_IRQ_EN = 0x04
CTRL_RX_IRQ_EN = 0x08

# Status register bits
STATUS_TX_READY = 0x01
STATUS_RX_READY = 0x02
STATUS_TX_EMPTY = 0x04
STATUS_RX_FULL = 0x08
STATUS_TX_ACTIVE = 0x10
STATUS_RX_ERROR = 0x20


async def write_register(dut, addr, value):
    """Write to a UART register."""
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
    """Read from a UART register."""
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


async def init_uart(dut):
    """Initialize UART testbench."""
    Clock(dut.i_clk, 20, unit="ns").start()  # 50MHz
    dut.i_reset_n.value = 0
    dut.i_phi2.value = 0
    dut.i_addr.value = 0
    dut.i_data.value = 0
    dut.i_rw.value = 1
    dut.i_en.value = 0
    dut.i_rx.value = 1  # UART idle high
    await ClockCycles(dut.i_clk, 5)
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 2)


async def send_uart_byte(dut, byte_val, baud_div):
    """Send a byte over UART RX input (simulating external device transmitting)."""
    # UART timing: sysclk / (16 * (baud_div + 1))
    # Each bit takes 16 * (baud_div + 1) clock cycles
    bit_cycles = 16 * (baud_div + 1)

    # Start bit (low)
    dut.i_rx.value = 0
    await ClockCycles(dut.i_clk, bit_cycles)

    # 8 data bits (LSB first)
    for i in range(8):
        bit = (byte_val >> i) & 1
        dut.i_rx.value = bit
        await ClockCycles(dut.i_clk, bit_cycles)

    # Stop bit (high)
    dut.i_rx.value = 1
    await ClockCycles(dut.i_clk, bit_cycles)


async def receive_uart_byte(dut, baud_div):
    """Receive a byte from UART TX output."""
    bit_cycles = 16 * (baud_div + 1)

    # Wait for start bit (falling edge)
    await First(FallingEdge(dut.o_tx), ClockCycles(dut.i_clk, 100))
    assert dut.o_tx.value == 0

    # Wait to middle of start bit
    await ClockCycles(dut.i_clk, bit_cycles // 2)
    assert dut.o_tx.value == 0, "Start bit should be low"

    # Sample 8 data bits
    byte_val = 0
    await ClockCycles(dut.i_clk, bit_cycles)
    for i in range(8):
        bit = int(dut.o_tx.value)
        byte_val |= bit << i
        await ClockCycles(dut.i_clk, bit_cycles)

    # Check stop bit
    assert dut.o_tx.value == 1, "Stop bit should be high"

    print("got byte: " + hex(byte_val))

    return byte_val


@cocotb.test()
async def test_reset_values(dut):
    """Test that registers initialize to correct values."""
    await init_uart(dut)

    ctrl = await read_register(dut, ADDR_CTRL)
    assert ctrl == 0, f"CTRL should be 0x00, got 0x{ctrl:02x}"

    status = await read_register(dut, ADDR_STATUS)
    # TX_READY and TX_EMPTY should be set (FIFO empty)
    assert status & STATUS_TX_READY, "TX_READY should be set on reset"
    assert status & STATUS_TX_EMPTY, "TX_EMPTY should be set on reset"

    baud_lo = await read_register(dut, ADDR_BAUD_LO)
    baud_hi = await read_register(dut, ADDR_BAUD_HI)
    assert baud_lo == 0 and baud_hi == 0, "Baud divisor should be 0 on reset"


@cocotb.test()
async def test_baud_rate_register(dut):
    """Test baud rate register read/write."""
    await init_uart(dut)

    # Write baud divisor
    await write_register(dut, ADDR_BAUD_LO, 0x34)
    await write_register(dut, ADDR_BAUD_HI, 0x12)

    # Read back
    baud_lo = await read_register(dut, ADDR_BAUD_LO)
    baud_hi = await read_register(dut, ADDR_BAUD_HI)

    assert baud_lo == 0x34, f"BAUD_LO: expected 0x34, got 0x{baud_lo:02x}"
    assert baud_hi == 0x12, f"BAUD_HI: expected 0x12, got 0x{baud_hi:02x}"


@cocotb.test()
async def test_control_register(dut):
    """Test control register enable bits."""
    await init_uart(dut)

    # Enable TX and RX
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE | CTRL_RX_ENABLE)

    ctrl = await read_register(dut, ADDR_CTRL)
    assert ctrl & CTRL_TX_ENABLE, "TX_ENABLE should be set"
    assert ctrl & CTRL_RX_ENABLE, "RX_ENABLE should be set"

    # Enable interrupts
    await write_register(
        dut,
        ADDR_CTRL,
        CTRL_TX_ENABLE | CTRL_RX_ENABLE | CTRL_TX_IRQ_EN | CTRL_RX_IRQ_EN,
    )

    ctrl = await read_register(dut, ADDR_CTRL)
    assert ctrl & CTRL_TX_IRQ_EN, "TX_IRQ_EN should be set"
    assert ctrl & CTRL_RX_IRQ_EN, "RX_IRQ_EN should be set"


@cocotb.test()
async def test_tx_single_byte(dut):
    """Test transmitting a single byte."""
    await init_uart(dut)

    # Set baud divisor (50MHz / (16 * 3) = ~1.04 Mbaud)
    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)

    # Enable TX
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE)

    # Write byte to transmit
    await write_register(dut, ADDR_DATA, 0x55)  # 01010101

    # Receive and verify
    received = await receive_uart_byte(dut, baud_div)
    assert received == 0x55, f"Expected 0x55, got 0x{received:02x}"


@cocotb.test()
async def test_tx_multiple_bytes(dut):
    """Test transmitting multiple bytes."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE)

    test_bytes = [0xAA, 0x55, 0xF0, 0x0F]

    # Write all bytes to FIFO
    for byte_val in test_bytes:
        await write_register(dut, ADDR_DATA, byte_val)

    # Receive and verify all bytes
    for expected in test_bytes:
        received = await receive_uart_byte(dut, baud_div)
        assert received == expected, f"Expected 0x{expected:02x}, got 0x{received:02x}"


@cocotb.test()
async def test_tx_fifo_full(dut):
    """Test TX FIFO full condition."""
    await init_uart(dut)

    baud_div = 10  # Slower baud rate to fill FIFO
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE)

    # Fill FIFO with 8 bytes (should fill it)
    for i in range(8):
        status = await read_register(dut, ADDR_STATUS)
        assert status & STATUS_TX_READY, f"TX should be ready before byte {i}"
        await write_register(dut, ADDR_DATA, i)

    # FIFO should now be full
    status = await read_register(dut, ADDR_STATUS)
    assert not (status & STATUS_TX_READY), "TX_READY should be clear when FIFO full"
    assert not (status & STATUS_TX_EMPTY), "TX_EMPTY should be clear when FIFO full"


@cocotb.test()
async def test_rx_single_byte(dut):
    """Test receiving a single byte."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)
    await write_register(dut, ADDR_CTRL, CTRL_RX_ENABLE)

    # Send byte via RX input
    await send_uart_byte(dut, 0xA5, baud_div)

    # Wait a bit for RX to process
    await ClockCycles(dut.i_clk, 100)

    # Check RX_READY flag
    status = await read_register(dut, ADDR_STATUS)
    assert status & STATUS_RX_READY, "RX_READY should be set after receiving byte"

    # Read received byte
    data = await read_register(dut, ADDR_DATA)
    assert data == 0xA5, f"Expected 0xA5, got 0x{data:02x}"


@cocotb.test()
async def test_rx_multiple_bytes(dut):
    """Test receiving multiple bytes."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)
    await write_register(dut, ADDR_CTRL, CTRL_RX_ENABLE)

    test_bytes = [0x12, 0x34, 0x56, 0x78]

    # Send all bytes
    for byte_val in test_bytes:
        await send_uart_byte(dut, byte_val, baud_div)

    await ClockCycles(dut.i_clk, 100)

    # Read and verify all bytes
    for expected in test_bytes:
        status = await read_register(dut, ADDR_STATUS)
        assert status & STATUS_RX_READY, (
            f"RX_READY should be set for byte 0x{expected:02x}"
        )

        data = await read_register(dut, ADDR_DATA)
        assert data == expected, f"Expected 0x{expected:02x}, got 0x{data:02x}"


@cocotb.test()
async def test_rx_fifo_full(dut):
    """Test RX FIFO full condition."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)
    await write_register(dut, ADDR_CTRL, CTRL_RX_ENABLE)

    # Send 8 bytes to fill FIFO
    for i in range(8):
        await send_uart_byte(dut, i, baud_div)

    await ClockCycles(dut.i_clk, 100)

    # Check RX_FULL flag
    status = await read_register(dut, ADDR_STATUS)
    assert status & STATUS_RX_FULL, "RX_FULL should be set when FIFO full"


@cocotb.test()
async def test_tx_irq(dut):
    """Test TX interrupt generation."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)

    # Enable TX and TX IRQ
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE | CTRL_TX_IRQ_EN)

    # IRQ should be asserted when FIFO is ready (not full)
    await ClockCycles(dut.i_clk, 10)
    assert dut.o_tx_irq.value == 1, "TX IRQ should be asserted when FIFO ready"


@cocotb.test()
async def test_rx_irq(dut):
    """Test RX interrupt generation."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)

    # Enable RX and RX IRQ
    await write_register(dut, ADDR_CTRL, CTRL_RX_ENABLE | CTRL_RX_IRQ_EN)

    # Send byte
    await send_uart_byte(dut, 0x42, baud_div)
    await ClockCycles(dut.i_clk, 100)

    # IRQ should be asserted when data is ready
    assert dut.o_rx_irq.value == 1, "RX IRQ should be asserted when data ready"


@cocotb.test()
async def test_loopback(dut):
    """Test TX to RX loopback."""
    await init_uart(dut)

    baud_div = 2
    await write_register(dut, ADDR_BAUD_LO, baud_div)
    await write_register(dut, ADDR_BAUD_HI, 0)

    # Enable both TX and RX
    await write_register(dut, ADDR_CTRL, CTRL_TX_ENABLE | CTRL_RX_ENABLE)

    # Connect TX to RX (loopback in testbench)
    async def loopback():
        while True:
            dut.i_rx.value = dut.o_tx.value
            await RisingEdge(dut.i_clk)

    # Start loopback task
    cocotb.start_soon(loopback())

    # Transmit byte
    test_byte = 0x5A
    await write_register(dut, ADDR_DATA, test_byte)

    # Wait for transmission and reception
    await ClockCycles(dut.i_clk, 20 * 16 * (baud_div + 1))

    # Check if received
    status = await read_register(dut, ADDR_STATUS)
    assert status & STATUS_RX_READY, "Should have received byte in loopback"

    # Read and verify
    received = await read_register(dut, ADDR_DATA)
    assert received == test_byte, (
        f"Loopback: expected 0x{test_byte:02x}, got 0x{received:02x}"
    )
