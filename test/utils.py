from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

async def start_clock_and_reset(dut):
    dut.i_reset_n.value = 0
    clk = Clock(dut.i_clk, 100, "ns").start()
    await ClockCycles(dut.i_clk, 2)
    dut.i_reset_n.value = 1
    await ClockCycles(dut.i_clk, 1)