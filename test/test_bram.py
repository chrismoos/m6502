from cocotb.clock import Clock
from cocotb.triggers import Timer
import cocotb
import random


async def init(dut):
    """Initialize clock and signals."""
    Clock(dut.i_clk, 20, unit="ns").start()  # 50MHz clock
    dut.i_phi2.value = 0
    dut.i_addr.value = 0
    dut.i_data.value = 0
    dut.i_rw.value = 1  # default to read
    dut.i_en.value = 1  # enable
    await Timer(50, unit="ns")  # let clock run a bit


async def phi2_cycle(dut):
    """Complete one phi2 cycle (low -> high -> low)."""
    dut.i_phi2.value = 0
    await Timer(500, unit="ns")  # phi2 low
    dut.i_phi2.value = 1
    await Timer(500, unit="ns")  # phi2 high
    dut.i_phi2.value = 0


async def write_byte(dut, addr, data):
    """Write a byte to memory - data captured on phi2 falling edge."""
    # Setup address, data, and R/W during phi2 high
    dut.i_phi2.value = 1
    await Timer(100, unit="ns")
    dut.i_addr.value = addr
    dut.i_data.value = data
    dut.i_rw.value = 0  # write
    await Timer(400, unit="ns")

    # Falling edge captures the write
    dut.i_phi2.value = 0
    await Timer(100, unit="ns")

    # Return to idle
    dut.i_rw.value = 1  # back to read
    await Timer(100, unit="ns")


async def read_byte(dut, addr):
    """Read a byte from memory - registered on posedge phi2."""
    # Setup address during phi2 low
    dut.i_phi2.value = 0
    await Timer(100, unit="ns")
    dut.i_addr.value = addr
    dut.i_rw.value = 1  # read
    await Timer(100, unit="ns")

    # Rising edge latches the read
    dut.i_phi2.value = 1
    await Timer(100, unit="ns")  # allow register to settle

    data = dut.o_data.value.to_unsigned()

    # Return phi2 to low
    dut.i_phi2.value = 0
    await Timer(100, unit="ns")

    return data


@cocotb.test()
async def test_write_read_single(dut):
    """Test writing and reading a single byte."""
    await init(dut)

    # Write 0xAB to address 0x1234
    await write_byte(dut, 0x1234, 0xAB)

    # Read it back
    data = await read_byte(dut, 0x1234)
    assert data == 0xAB, f"Expected 0xAB, got {hex(data)}"


@cocotb.test()
async def test_write_read_multiple(dut):
    """Test writing and reading multiple addresses."""
    await init(dut)

    test_data = [
        (0x0000, 0x11),
        (0x0100, 0x22),
        (0x1000, 0x33),
        (0x7FFF, 0x44),
        (0x8000, 0x55),
        (0xFFFF, 0xFF),
    ]

    # Write all values
    for addr, data in test_data:
        await write_byte(dut, addr, data)

    # Read all values back
    for addr, expected in test_data:
        data = await read_byte(dut, addr)
        assert data == expected, f"Addr {hex(addr)}: expected {hex(expected)}, got {hex(data)}"


@cocotb.test()
async def test_overwrite(dut):
    """Test that writing to same address overwrites previous value."""
    await init(dut)

    addr = 0x5555

    # Write first value
    await write_byte(dut, addr, 0x11)
    data = await read_byte(dut, addr)
    assert data == 0x11

    # Overwrite with new value
    await write_byte(dut, addr, 0x99)
    data = await read_byte(dut, addr)
    assert data == 0x99, f"Expected 0x99 after overwrite, got {hex(data)}"


@cocotb.test()
async def test_read_registered(dut):
    """Test that reads are registered on posedge phi2."""
    await init(dut)

    # Write known values
    await write_byte(dut, 0x1000, 0xAA)
    await write_byte(dut, 0x2000, 0xBB)

    # Setup address during phi2 low
    dut.i_phi2.value = 0
    dut.i_addr.value = 0x1000
    dut.i_rw.value = 1
    await Timer(100, unit="ns")

    # Rising edge latches the read
    dut.i_phi2.value = 1
    await Timer(100, unit="ns")
    assert dut.o_data.value == 0xAA

    # Change address during phi2 low
    dut.i_phi2.value = 0
    dut.i_addr.value = 0x2000
    await Timer(100, unit="ns")

    # Rising edge latches the new address
    dut.i_phi2.value = 1
    await Timer(100, unit="ns")
    assert dut.o_data.value == 0xBB


@cocotb.test()
async def test_write_needs_phi2(dut):
    """Test that write only happens on phi2 negedge with i_rw=0."""
    await init(dut)

    # Write a known value first
    await write_byte(dut, 0x3000, 0x42)
    data = await read_byte(dut, 0x3000)
    assert data == 0x42

    # Setup write conditions during phi2 high
    dut.i_phi2.value = 1
    await Timer(100, unit="ns")
    dut.i_addr.value = 0x3000
    dut.i_data.value = 0xFF
    dut.i_rw.value = 0  # write mode
    await Timer(400, unit="ns")

    # Switch to read mode BEFORE phi2 falls - write should NOT happen
    dut.i_rw.value = 1  # read mode
    await Timer(100, unit="ns")
    dut.i_phi2.value = 0  # phi2 falls, but we're in read mode now
    await Timer(100, unit="ns")

    # Verify by reading back - should still be 0x42
    data = await read_byte(dut, 0x3000)
    assert data == 0x42, "Write should not occur when i_rw=1 at negedge"


@cocotb.test()
async def test_random_access(dut):
    """Test random read/write patterns."""
    await init(dut)

    random.seed(42)
    test_addresses = random.sample(range(0x10000), 50)
    written_data = {}

    # Write random data to random addresses
    for addr in test_addresses:
        data = random.randint(0, 255)
        await write_byte(dut, addr, data)
        written_data[addr] = data

    # Read back in different order
    random.shuffle(test_addresses)
    for addr in test_addresses:
        data = await read_byte(dut, addr)
        expected = written_data[addr]
        assert data == expected, f"Addr {hex(addr)}: expected {hex(expected)}, got {hex(data)}"


@cocotb.test()
async def test_zero_page(dut):
    """Test zero page access (addresses 0x00-0xFF)."""
    await init(dut)

    # Write to zero page
    for i in range(0, 256, 16):
        await write_byte(dut, i, i & 0xFF)

    # Verify
    for i in range(0, 256, 16):
        data = await read_byte(dut, i)
        assert data == (i & 0xFF), f"Zero page addr {hex(i)}: expected {hex(i)}, got {hex(data)}"


@cocotb.test()
async def test_stack_page(dut):
    """Test stack page access (addresses 0x100-0x1FF)."""
    await init(dut)

    # Write to stack area
    for i in range(0x100, 0x200, 16):
        await write_byte(dut, i, (i - 0x100) & 0xFF)

    # Verify
    for i in range(0x100, 0x200, 16):
        data = await read_byte(dut, i)
        expected = (i - 0x100) & 0xFF
        assert data == expected, f"Stack addr {hex(i)}: expected {hex(expected)}, got {hex(data)}"
