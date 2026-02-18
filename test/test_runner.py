import os
from pathlib import Path
import pytest
from cocotb_tools.runner import get_runner

TESTS = ['test_mcu', 'test_cpu_6502', 'test_cpu_6502_reset', 'test_bram', 'test_clock_control', 'test_timer', 'test_gpio_mux', 'test_uart']

@pytest.mark.parametrize("test", TESTS)
def test_runner(test):
    sim = os.getenv("SIM", "verilator")
    waves = os.getenv("WAVES", "0") == "1"

    proj_path = Path(__file__).resolve().parent
    # Add .vh files FIRST so they're processed before .sv files
    sources = list(proj_path.glob('../rtl/**/*.vh'))
    sources.append(proj_path / f"{test}.sv")
    sources.extend(proj_path.glob('../rtl/**/*.sv'))

    # Add bus_ram for cpu tests
    if test in ["test_cpu_6502", "test_cpu_6502_reset"]:
        sources.append(proj_path / "bus_ram.sv")

    runner = get_runner(sim)

    build_args = []
    if sim == "verilator":
        build_args = ["--timing", "-Wall", "-Werror-PINMISSING", "-Werror-WIDTHTRUNC", "-Werror-WIDTHEXPAND", "-Werror-WIDTHCONCAT"]

    build_dir = proj_path.parent / "sim_build" / test
    runner.build(
        sources=sources,
        hdl_toplevel=test,
        includes=[proj_path / "../rtl/"],
        build_dir=build_dir,
        always=True,
        waves=waves,
        build_args=build_args
    )

    testcase = os.getenv("TESTCASE", None)
    print(testcase)
    runner.test(hdl_toplevel=test, test_module=test, testcase=testcase)