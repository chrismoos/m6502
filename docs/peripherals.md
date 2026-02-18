# Peripherals

The MCU module integrates several memory-mapped peripherals accessible to 6502 software through standard load and store instructions.

## Memory Map

| Address Range | Peripheral | Description |
|--------------|------------|-------------|
| `0xA000-0xA00B` | GPIO A | 8-bit general-purpose I/O with pin mux |
| `0xA010-0xA017` | SK6812 | RGBW LED controller |
| `0xA020-0xA027` | TIMER0 | 16-bit timer with prescaler and interrupts |
| `0xA030-0xA033` | Clock Control | CPU clock divider |
| `0xA040-0xA047` | UART0 | Serial communication with FIFOs |
| All others | External | Routed to external bus |

## GPIO Peripheral

### Overview

The GPIO peripheral provides 8 bidirectional I/O pins with software-controlled direction and pin multiplexing. Each pin can be individually configured as GPIO or routed to peripheral functions (UART, SPI, I2C, PWM, etc.).

**Base Address**: `0xA000`

### Register Map

| Offset | Register | Access | Description | Reset Value |
|--------|----------|--------|-------------|-------------|
| `+0x0` | OE | R/W | Output Enable (0=input, 1=output) | `0x00` |
| `+0x1` | OUT | R/W | Output Data | `0x00` |
| `+0x2` | IN | R | Input Data | N/A |
| `+0x3` | - | - | Reserved | - |
| `+0x4` | MODE_PIN0 | R/W | Pin 0 function select | `0x00` |
| `+0x5` | MODE_PIN1 | R/W | Pin 1 function select | `0x00` |
| `+0x6` | MODE_PIN2 | R/W | Pin 2 function select | `0x00` |
| `+0x7` | MODE_PIN3 | R/W | Pin 3 function select | `0x00` |
| `+0x8` | MODE_PIN4 | R/W | Pin 4 function select | `0x00` |
| `+0x9` | MODE_PIN5 | R/W | Pin 5 function select | `0x00` |
| `+0xA` | MODE_PIN6 | R/W | Pin 6 function select | `0x00` |
| `+0xB` | MODE_PIN7 | R/W | Pin 7 function select | `0x00` |

### Register Details

#### Output Enable Register (OE) - `0xA000`

Controls the direction of each GPIO pin.

- **Bit [7:0]**: Direction control
  - `0` = Input (tri-state output driver)
  - `1` = Output (drive output data value)
- **Reset value**: `0x00` (all inputs)

#### Output Data Register (OUT) - `0xA001`

Controls the output level for pins configured as outputs.

- **Bit [7:0]**: Output level
  - `0` = Low
  - `1` = High
- **Reset value**: `0x00` (all low)
- **Note**: Only affects pins with OE bit set to 1

#### Input Data Register (IN) - `0xA002`

Reads the current level of all GPIO pins.

- **Bit [7:0]**: Current pin state
  - `0` = Low
  - `1` = High
- **Access**: Read-only
- **Note**: Reflects actual pin state regardless of direction or mode

#### Pin Mode Registers (MODE_PIN0-7) - `0xA004-0xA00B`

Configure the function of each GPIO pin. Each pin has an independent mode register that selects between GPIO mode and various peripheral functions.

- **Access**: Read/Write
- **Reset value**: `0x00` (GPIO mode)

**Mode Values**:

| Value | Function | Description |
|-------|----------|-------------|
| `0x00` | GPIO | Standard GPIO controlled by OE/OUT registers |
| `0x01` | UART0_TX | UART transmit output |
| `0x02` | UART0_RX | UART receive input |
| `0x03` | SK6812_DATA | SK6812 LED data output |
| `0x04-0xFF` | Reserved | Reserved for future peripherals (SPI, I2C, PWM, etc.) |

**Pin Multiplexing Behavior**:

- **GPIO Mode (0x00)**: Pin is controlled by OE and OUT registers (default behavior)
- **UART0_TX Mode (0x01)**: Pin becomes an output and drives the UART TX signal
  - Multiple pins can be configured as UART0_TX (all will drive the same signal)
  - GPIO OE/OUT registers are ignored for this pin
- **UART0_RX Mode (0x02)**: Pin becomes an input for UART RX signal
  - If multiple pins are configured as UART0_RX, the lowest pin number is used
  - Pin pulls high (UART idle state) when configured as RX
  - GPIO OE/OUT registers are ignored for this pin
- **SK6812_DATA Mode (0x03)**: Pin becomes an output and drives the SK6812 LED data signal
  - Multiple pins can be configured as SK6812_DATA (all will drive the same signal)
  - GPIO OE/OUT registers are ignored for this pin
  - Connect to the data input of SK6812/WS2812 addressable LED chains

**Important**: The IN register (`0xA002`) always reflects the actual pin state regardless of mode, allowing software to monitor pins even when assigned to peripherals.

### Timing

GPIO updates occur on the CPU's PHI2 clock edge:
- **Writes**: Take effect on the negative edge of PHI2
- **Reads**: Sample pin state on the positive edge of PHI2

## SK6812 RGBW LED Controller

### Overview

Hardware controller for SK6812 addressable RGBW LEDs. Handles precise timing requirements for the SK6812 protocol, allowing CPU-independent LED updates.

**Base Address**: `0xA010`

### Pin Configuration

SK6812 uses the GPIO pin multiplexing system. Any GPIO pin can be configured as SK6812 data output by writing `0x03` to the corresponding `MODE_PINx` register. See the [GPIO Peripheral](#gpio-peripheral) section for details on pin multiplexing.

### Register Map

| Offset | Register | Access | Description | Reset Value |
|--------|----------|--------|-------------|-------------|
| `+0x0` | CONTROL | R/W | Control (start transmission) | `0x00` |
| `+0x1` | CLKDIV | R/W | Clock divider | Platform-dependent |
| `+0x2` | RED | R/W | Red component | `0x00` |
| `+0x3` | GREEN | R/W | Green component | `0x00` |
| `+0x4` | BLUE | R/W | Blue component | `0x00` |
| `+0x5` | WHITE | R/W | White component | `0x00` |
| `+0x6` | STATUS | R | Status (busy flag) | `0x00` |
| `+0x7` | - | - | Reserved | - |

### Register Details

#### Control Register (CONTROL) - `0xA010`

Controls the LED controller operation.

**Write bits**:
- **Bit 0**: START - Begin transmission
  - Write `1` to start sending color data
  - Auto-clears when transmission begins
- **Bits [7:1]**: Reserved

- **Reset value**: `0x00`

#### Clock Divider Register (CLKDIV) - `0xA011`

Controls the bit timing for the SK6812 protocol.

- **Bits [7:0]**: Clock divisor value
- **Tick period formula**: `tick_period = CLKDIV × sysclk_period`
  - Each tick is one unit of the hardware state machine
- **Reset value**: Platform-dependent (typically configured for system clock)

The SK6812 hardware state machine uses the following tick counts per bit. Each bit period is 12 ticks: the low period is `low_cycles + 1` because the final "loading tick" (which fires when `low_cycles` reaches 0) also outputs low.

| Bit | `high_cycles` | High ticks | `low_cycles` | Low ticks (low_cycles+1) | Total ticks |
|-----|--------------|------------|-------------|--------------------------|-------------|
| `0` | 3 | 3 | 8 | 9 | 12 |
| `1` | 6 | 6 | 5 | 6 | 12 |

Which gives the following timing at each CLKDIV value:
- `T0H = 3 × CLKDIV × sysclk_period`
- `T0L = 9 × CLKDIV × sysclk_period`
- `T1H = 6 × CLKDIV × sysclk_period`
- `T1L = 6 × CLKDIV × sysclk_period`

SK6812 protocol timing requirements:
- T0H: 300ns ± 150ns (0 bit high time)
- T0L: 900ns ± 150ns (0 bit low time)
- T1H: 600ns ± 150ns (1 bit high time)
- T1L: 600ns ± 150ns (1 bit low time)

**Example**: At 50 MHz sysclk, `CLKDIV = 5` gives a 100ns tick — producing T0H=300ns, T0L=900ns, T1H=600ns, T1L=600ns, all exactly centered in the spec.

#### Color Component Registers - `0xA012-0xA015`

Set the RGBW color components for the next LED update.

- **RED** (`0xA012`): Red intensity (0-255)
- **GREEN** (`0xA013`): Green intensity (0-255)
- **BLUE** (`0xA014`): Blue intensity (0-255)
- **WHITE** (`0xA015`): White intensity (0-255)

Write all four components before triggering transmission with the CONTROL register.

- **Reset value**: `0x00` (all components off)

#### Status Register (STATUS) - `0xA016`

Read-only status register.

**Read bits**:
- **Bit 0**: BUSY - Transmission in progress
  - `1` = Busy (transmitting data)
  - `0` = Idle (ready for next color)
- **Bits [7:1]**: Reserved (read as 0)

- **Reset value**: `0x00` (idle)

### Protocol Sequence

To update an LED:

1. Wait for BUSY=0 (controller idle)
2. Write RED, GREEN, BLUE, WHITE values
3. Write `0x01` to CONTROL to start transmission
4. Repeat for each LED in chain

### Timing Considerations

The SK6812 controller operates asynchronously from the CPU clock once started. The BUSY flag must be checked before starting a new transmission to avoid corrupting data.

After the last LED in a chain, maintain idle (low) for at least 50µs to latch all LED data.

## Clock Control

### Overview

The Clock Control peripheral provides runtime-configurable CPU clock division for dynamic frequency scaling.

**Base Address**: `0xA030`

**Clock Architecture**:
- **System Clock (i_clk)**: Base FPGA clock (e.g., 48 MHz on Fomu, 50 MHz on ULX3S)
- **CPU Clock**: Software-divided from system clock via programmable divider
- **Peripherals**: Use system clock directly with internal dividers (UART baud, Timer prescaler, LED timing)

### Register Map

| Offset | Register | Access | Description | Reset Value |
|--------|----------|--------|-------------|-------------|
| `+0x0` | CPU_DIV | R/W | CPU clock divider | Platform default |
| `+0x1` | - | - | Reserved | - |
| `+0x2` | STATUS | R | Clock status | `0x01` |
| `+0x3` | - | - | Reserved | - |

### Register Details

#### CPU Clock Divider (CPU_DIV) - `0xA030`

Software-configurable clock divider for the CPU.

- **Bits [7:0]**: Clock divisor (0-255)
- **Formula**: `cpu_clk frequency = sysclk / (CPU_DIV + 1)`
- **Reset value**: Platform default (typically configured for 1 MHz)

Examples (on 48 MHz system clock):
- `CPU_DIV = 0`: 48 MHz (no division)
- `CPU_DIV = 1`: 24 MHz
- `CPU_DIV = 3`: 12 MHz
- `CPU_DIV = 47`: 1 MHz
- `CPU_DIV = 255`: 187.5 kHz

#### Status Register (STATUS) - `0xA032`

Read-only status register.

- **Bit 0**: CPU_LOCKED - CPU clock stable (always `1`)
- **Bits [7:1]**: Reserved (read as 0)
- **Reset value**: `0x01`

### Implementation Details

**Single-Level Clock Division**:
- Software divider (runtime): `sysclk → cpu_clk` via programmable counter
- Generates actual divided clock with ~50% duty cycle
- `CPU_DIV = 0` passes system clock through directly (no delay)
- PHI2 output matches CPU clock frequency exactly

**Peripheral Clocking**:
- Peripherals run on `sysclk` (system clock) directly
- Each peripheral has internal dividers for timing:
  - UART: Baud rate generator
  - Timer: Prescaler register
  - SK6812 LED: Clock divider parameter

This approach:
- Simple single clock domain architecture
- PHI2 always phase-aligned with CPU operations
- Simplifies timing analysis
- Works reliably on FPGAs

### Timing Considerations

- Clock divider changes take effect within a few system clock cycles
- Generated CPU clock has clean edges with ~50% duty cycle
- CPU and peripheral clocks are in the same clock domain (peripherals use sysclk)
- Changing CPU_DIV affects instruction execution rate but not correctness
- PHI2 output frequency equals CPU clock frequency (no phase offset)

## TIMER0

### Overview

The TIMER0 peripheral provides a 16-bit up-counter with configurable prescaler, auto-reload capability, and interrupt generation. It can be used for precise timing, delays, periodic interrupts, and event counting.

**Base Address**: `0xA020`

### Register Map

| Offset | Register | Access | Description | Reset Value |
|--------|----------|--------|-------------|-------------|
| `+0x0` | CTRL | R/W | Control register | `0x00` |
| `+0x1` | STATUS | R/W | Status register | `0x00` |
| `+0x2` | COUNT_LO | R | Counter low byte | `0x00` |
| `+0x3` | COUNT_HI | R | Counter high byte | `0x00` |
| `+0x4` | RELOAD_LO | R/W | Reload value low byte | `0x00` |
| `+0x5` | RELOAD_HI | R/W | Reload value high byte | `0x00` |
| `+0x6` | PRESCALER | R/W | Clock prescaler (0-255) | `0x00` |
| `+0x7` | - | - | Reserved | - |

### Register Details

#### Control Register (CTRL) - `0xA020`

Controls timer operation.

**Write/Read bits**:
- **Bit 0**: ENABLE - Enable timer counting
  - `0` = Timer stopped
  - `1` = Timer counting
- **Bit 1**: AUTO_RELOAD - Enable auto-reload on overflow
  - `0` = Counter wraps to 0 on overflow
  - `1` = Counter reloads from RELOAD_LO/HI on overflow
- **Bit 2**: IRQ_ENABLE - Enable interrupt on overflow
  - `0` = No interrupt generated
  - `1` = IRQ asserted when overflow occurs
- **Bit 3**: LOAD - Load counter from RELOAD registers (write-only strobe)
  - Write `1` to load counter from RELOAD_LO/HI
  - **Only works when ENABLE=0** (timer stopped) - ignored if running
  - Auto-clears to `0` after write (strobe behavior)
  - Use to initialize counter before starting timer
- **Bits [7:4]**: Reserved (write 0, read as 0)

- **Reset value**: `0x00` (all disabled)

#### Status Register (STATUS) - `0xA021`

Timer status flags.

**Read/Write bits**:
- **Bit 0**: OVERFLOW - Overflow flag (write 1 to clear)
  - `0` = No overflow occurred
  - `1` = Counter overflowed from 0xFFFF
  - Write `1` to this bit to clear the flag
- **Bits [7:1]**: Reserved (read as 0)

- **Reset value**: `0x00`

#### Counter Registers (COUNT_LO, COUNT_HI) - `0xA022-0xA023`

Read the current 16-bit counter value.

- **COUNT_LO** (`0xA022`): Counter bits [7:0]
- **COUNT_HI** (`0xA023`): Counter bits [15:8]
- **Access**: Read-only
- **Reset value**: `0x0000`

**Note**: The counter continues running while being read. For consistent reads of the full 16-bit value, disable the timer or use the prescaler to slow counting.

#### Reload Registers (RELOAD_LO, RELOAD_HI) - `0xA024-0xA025`

Set the 16-bit reload value used when AUTO_RELOAD is enabled.

- **RELOAD_LO** (`0xA024`): Reload bits [7:0]
- **RELOAD_HI** (`0xA025`): Reload bits [15:8]
- **Access**: Read/Write
- **Reset value**: `0x0000`

When the counter reaches `0xFFFF` and AUTO_RELOAD is enabled, the counter will be loaded with the value from RELOAD_LO/HI on the next tick.

#### Prescaler Register (PRESCALER) - `0xA026`

Controls the timer tick rate by dividing the system clock.

- **Bits [7:0]**: Clock divisor value (0-255)
- **Formula**: `timer_freq = sysclk / (PRESCALER + 1)`
- **Reset value**: `0x00` (no division, timer ticks at sysclk)

Examples:
- `PRESCALER = 0`: Timer ticks at sysclk (every clock cycle)
- `PRESCALER = 1`: Timer ticks at sysclk / 2
- `PRESCALER = 9`: Timer ticks at sysclk / 10
- `PRESCALER = 99`: Timer ticks at sysclk / 100

### Interrupt Operation

The timer generates an interrupt request (IRQ) when:
1. The OVERFLOW flag is set (counter reached 0xFFFF)
2. The IRQ_ENABLE bit is set in the CTRL register

The IRQ output is combinational: `IRQ = OVERFLOW && IRQ_ENABLE`

The timer IRQ is OR'd with the UART IRQs and routed to the CPU's active-low IRQ input. Set `IRQ_ENABLE` in the CTRL register and clear the CPU interrupt mask (`CLI`) to receive timer overflow interrupts. Inside the IRQ handler, check the OVERFLOW flag and write `0x01` to STATUS to clear it.

### Timing Calculations

Given:
- System clock: `sysclk` Hz
- Prescaler value: `P`
- Counter overflow period: `65536` counts (0x0000 to 0xFFFF)

Timer tick frequency:
```
tick_freq = sysclk / (P + 1)
```

Overflow period:
```
overflow_period = 65536 / tick_freq
                = 65536 * (P + 1) / sysclk
```

Example for 50MHz system clock:
- `PRESCALER = 0`: Overflow every 1.31 ms
- `PRESCALER = 9`: Overflow every 13.1 ms (10× slower)
- `PRESCALER = 49`: Overflow every 65.5 ms (50× slower)
- `PRESCALER = 99`: Overflow every 131 ms (100× slower)
- `PRESCALER = 255`: Overflow every 335 ms (256× slower)

### Timing Considerations

- Counter updates occur on the system clock edge
- Register reads/writes occur on PHI2 edges (CPU clock)
- Counter can be read while running, but value may increment between byte reads
- Overflow flag is set when counter transitions from 0xFFFF to reload value (or 0)
- Write-1-to-clear for overflow flag ensures atomic flag management

## UART0

### Overview

The UART0 (Universal Asynchronous Receiver/Transmitter) peripheral provides serial communication with 8-byte TX/RX FIFOs and configurable baud rate. It uses the standard 8N1 format (8 data bits, no parity, 1 stop bit) and supports interrupt-driven or polled operation.

**Base Address**: `0xA040`

### Pin Configuration

UART uses the GPIO pin multiplexing system. Any GPIO pin can be configured as UART TX (mode `0x01`) or RX (mode `0x02`) via the corresponding `MODE_PINx` register. See the [GPIO Peripheral](#gpio-peripheral) section for details on pin multiplexing.

### Register Map

| Offset | Register | Access | Description | Reset Value |
|--------|----------|--------|-------------|-------------|
| `+0x0` | CTRL | R/W | Control register | `0x00` |
| `+0x1` | STATUS | R | Status register | `0x05` |
| `+0x2` | DATA | R/W | Data register (FIFO access) | N/A |
| `+0x3` | BAUD_LO | R/W | Baud divisor low byte | `0x00` |
| `+0x4` | BAUD_HI | R/W | Baud divisor high byte | `0x00` |

### Register Details

#### Control Register (CTRL) - `0xA040`

Controls UART operation and interrupts.

**Write/Read bits**:
- **Bit 0**: TX_ENABLE - Enable transmitter
  - `0` = Transmitter disabled
  - `1` = Transmitter enabled
- **Bit 1**: RX_ENABLE - Enable receiver
  - `0` = Receiver disabled
  - `1` = Receiver enabled
- **Bit 2**: TX_IRQ_EN - Enable TX ready interrupt
  - `0` = No interrupt when TX ready
  - `1` = IRQ asserted when TX FIFO not full
- **Bit 3**: RX_IRQ_EN - Enable RX ready interrupt
  - `0` = No interrupt when RX ready
  - `1` = IRQ asserted when RX FIFO not empty
- **Bits [7:4]**: Reserved (write 0, read as 0)

**Reset value**: `0x00` (all disabled)

#### Status Register (STATUS) - `0xA041`

Read-only status flags.

**Read bits**:
- **Bit 0**: TX_READY - TX FIFO not full (can write)
  - `0` = TX FIFO full
  - `1` = TX FIFO has space (can accept data)
- **Bit 1**: RX_READY - RX FIFO not empty (can read)
  - `0` = RX FIFO empty (no data)
  - `1` = RX FIFO has data available
- **Bit 2**: TX_EMPTY - TX FIFO completely empty
  - `0` = TX FIFO has data
  - `1` = TX FIFO is empty
- **Bit 3**: RX_FULL - RX FIFO full
  - `0` = RX FIFO has space
  - `1` = RX FIFO is full
- **Bit 4**: TX_ACTIVE - Currently transmitting
  - `0` = Idle
  - `1` = Transmitting byte
- **Bit 5**: RX_ERROR - Framing error detected
  - `0` = No error
  - `1` = Framing error (stop bit not high)
- **Bits [7:6]**: Reserved (read as 0)

**Reset value**: `0x05` (TX_READY and TX_EMPTY set)

#### Data Register (DATA) - `0xA042`

FIFO access for transmit and receive.

**Write**: Push byte to TX FIFO (if not full)
- Writing when TX_READY=0 has no effect
- Data is queued for transmission

**Read**: Pop byte from RX FIFO (if not empty)
- Reading when RX_READY=0 returns undefined data
- Reading removes byte from FIFO

#### Baud Rate Divisor (BAUD_LO, BAUD_HI) - `0xA043-0xA044`

16-bit baud rate divisor value.

**Formula**: `baud_rate = sysclk / (16 * (divisor + 1))`

**BAUD_LO** (`0xA043`): Divisor bits [7:0]
**BAUD_HI** (`0xA044`): Divisor bits [15:8]

**Reset value**: `0x0000`

**Common Baud Rates** (50 MHz sysclk):


| Baud Rate | Divisor | BAUD_HI | BAUD_LO | Actual Rate | Error |
|-----------|---------|---------|---------|-------------|-------|
| 9600 | 325 | `0x01` | `0x45` | 9600.6 | +0.006% |
| 19200 | 162 | `0x00` | `0xA2` | 19202.9 | +0.015% |
| 38400 | 80 | `0x00` | `0x50` | 38580.2 | +0.47% |
| 57600 | 53 | `0x00` | `0x35` | 57803.5 | +0.35% |
| 115200 | 26 | `0x00` | `0x1A` | 115740.7 | +0.47% |

### FIFO Configuration

- **TX FIFO**: 8 bytes (default, configurable via `UART_FIFO_DEPTH` MCU parameter)
- **RX FIFO**: 8 bytes (default, configurable via `UART_FIFO_DEPTH` MCU parameter)
- Circular buffer implementation
- Independent read/write pointers

### Serial Format

- **8 data bits**, LSB first
- **No parity**
- **1 stop bit**
- Standard UART timing (8N1)

### Operation Modes

**Polled**: Poll TX_READY (`STATUS` bit 0) before writing to DATA; poll RX_READY (`STATUS` bit 1) before reading from DATA.

**Interrupt-driven**: Set TX_IRQ_EN and/or RX_IRQ_EN in CTRL, call `CLI`, and handle UART conditions inside the CPU's IRQ handler by checking the STATUS register.

### Error Handling

Check the RX_ERROR bit (`STATUS` bit 5) for framing errors. Clear the error by re-writing the CTRL register with RX_ENABLE set.

### Timing Considerations

- **Baud rate accuracy**: Choose divisor to minimize error
- **16x oversampling**: RX samples at 16x baud rate for accurate bit detection
- **Start bit detection**: RX looks for falling edge then validates at mid-bit
- **Stop bit checking**: Framing error if stop bit not high
- **FIFO latency**: Up to 8 bytes can be buffered before overflow
- **Transmission timing**: TX starts immediately when byte written to empty FIFO
- **Register access**: CPU register reads/writes on phi2 clock, automatically synchronized to peripheral i_clk domain

### Implementation Notes

**Clock Domain Crossing**: The UART peripheral runs on the system clock (`i_clk`) while the CPU register interface uses the phi2 clock. Register writes/reads use toggle-based synchronization:
- Toggle bits flip on each register access (phi2 domain)
- 2-stage synchronizers transfer toggle to i_clk domain
- XOR detection generates single-cycle pulses to FIFO write/read
- Prevents multiple FIFO operations from sustained phi2 signals
- Ensures reliable operation across arbitrary clock frequency ratios

**TX Data Path**: A latching register captures FIFO data before the read pointer advances, preventing transmission of incorrect bytes.

**RX Data Path**: FIFO output is read directly (combinational) before the read pointer advances, ensuring correct data is returned to CPU.

### Interrupt Operation

UART generates two independent interrupt signals:

**TX IRQ**: `IRQ = TX_IRQ_EN && TX_READY`
- Asserted (high) when TX FIFO is not full and TX_IRQ_EN is set
- Use to refill TX FIFO in interrupt handler

**RX IRQ**: `IRQ = RX_IRQ_EN && RX_READY`
- Asserted (high) when RX FIFO is not empty and RX_IRQ_EN is set
- Use to read received data in interrupt handler

**IRQ Connection**: UART0 IRQs are OR'd with TIMER0 IRQ and inverted to drive the CPU's active-low IRQ input. Any peripheral asserting an interrupt will trigger the CPU's IRQ handler.

## Custom Peripherals

The MCU architecture supports adding custom memory-mapped peripherals. New peripherals are assigned addresses in the I/O region (0xA000-0xAFFF or beyond) and accessed via standard load/store instructions.

### Design Requirements

Custom peripherals should follow these guidelines:

- **Address decoding**: Respond only to assigned address range
- **Bus timing**: Register access synchronized to CPU PHI2 clock
- **Reset behavior**: Properly initialize on system reset
- **Read/Write protocol**: Follow standard 6502 bus timing
  - Reads: Data valid during PHI2 high
  - Writes: Data latched on PHI2 falling edge
