# Testing

m6502 includes a comprehensive test suite to verify both the CPU core and MCU wrapper functionality.

## Test Overview

### Unit Tests (Cocotb)
Cocotb-based unit tests verify individual components:

- **test_cpu_6502.py** - CPU core instruction tests covering all opcodes, addressing modes, and flag behavior (~150+ test cases)
- **test_cpu_6502_reset.py** - Reset sequence and initialization behavior
- **test_mcu.py** - MCU wrapper with GPIO and SK6812 peripheral tests
- **test_bram.py** - Block RAM read/write and initialization tests

### Functional Test (Klaus Dormann)
The Klaus Dormann 6502 functional test is a comprehensive validation suite that exercises the entire 6502 instruction set in realistic scenarios:

- **test_mcu_klaus** - Full 6502 instruction set validation
  - Runs Klaus Dormann's complete functional test suite
  - Tests all instructions, addressing modes, and flag interactions
  - Validates cycle-accurate timing
  - Success indicated by reaching PC = 0x3469
  - Uses Verilator for fast simulation (C++ testbench)

The Klaus test is the gold standard for 6502 correctness and catches subtle bugs that unit tests might miss.

## Dependencies

### Required Tools

**uv** - Python package manager (recommended)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

**Verilator** - Verilog simulator
```bash
# macOS
brew install verilator

# Ubuntu/Debian
sudo apt-get install verilator

# Minimum version: 5.0+
```

### Python Dependencies

Install Python dependencies using `uv`:

```bash
uv sync
```

This installs:
- **cocotb** - Hardware verification framework
- **pytest** - Test runner

Alternatively, install manually:
```bash
uv pip install cocotb pytest
```

## Running Tests

### Quick Start - Run All Tests

From the project root:

```bash
make test
```

This runs:
1. All cocotb unit tests (test_cpu_6502, test_mcu, test_bram, test_cpu_6502_reset)
2. Klaus functional test

### Run Only Unit Tests

```bash
uv run pytest test/test_runner.py -s -x
```

Flags:
- `-s` - Show output (don't capture stdout)
- `-x` - Stop on first failure

### Run Only Klaus Test

```bash
make test-klaus
```

Or directly:
```bash
cd test
make -f Makefile.mcu_klaus run
```

### Run Specific Test

Run a single test module:
```bash
uv run pytest test/test_runner.py::test_runner[test_cpu_6502] -s
```

Run a specific test case:
```bash
TESTCASE=test_lda_immediate uv run pytest test/test_runner.py::test_runner[test_cpu_6502] -s
```

### Enable Waveform Debugging

For cocotb tests:
```bash
WAVES=1 uv run pytest test/test_runner.py -s
```

For Klaus test:
```bash
cd test
WAVES=1 make -f Makefile.mcu_klaus run
```

Waveforms are saved as `.vcd` files in the `sim_build/` directory and can be viewed with GTKWave:
```bash
gtkwave sim_build/test_cpu_6502/dump.vcd
```

## Test Structure

```
test/
├── test_runner.py          # Pytest wrapper that runs cocotb tests
├── test_cpu_6502.py        # CPU instruction tests (cocotb)
├── test_cpu_6502_reset.py  # Reset behavior tests (cocotb)
├── test_mcu.py             # MCU wrapper tests (cocotb)
├── test_bram.py            # Block RAM tests (cocotb)
├── Makefile.mcu_klaus      # Klaus test Makefile
├── tb_mcu_klaus.cpp        # Klaus test C++ testbench
├── test_mcu_klaus.sv       # Klaus test top-level RTL
├── 6502_functional_test.bin # Klaus test binary
└── utils.py                # Shared test utilities
```

## Test Coverage

Current test coverage areas:

**Fully Tested**
- All official 6502 instructions and addressing modes
- Illegal/undocumented opcodes (behave as 1-byte, 2-cycle NOPs)
- Flag operations (N, Z, C, V, D, I, B)
- Reset behavior and initialization
- Interrupt handling (IRQ, NMI)
- Stack operations
- Binary and BCD arithmetic
- GPIO peripheral
- SK6812 peripheral
- Block RAM operations

**Partial Coverage**
- Bus multiplexer (tested in hardware, limited simulation tests)
- External memory interface (basic tests only)

## References

- [Cocotb Documentation](https://docs.cocotb.org/)
- [Verilator Manual](https://verilator.org/guide/latest/)
- [Klaus Dormann Test Suite](https://github.com/Klaus2m5/6502_65C02_functional_tests)
- [6502 Instruction Reference](http://www.6502.org/tutorials/6502opcodes.html)
