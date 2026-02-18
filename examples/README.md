# m6502 Examples

This directory contains example 6502 assembly programs demonstrating the capabilities of the m6502 core.

## Building Examples

All examples can be built using the included Makefile:

```bash
make all        # Build all examples
make clean      # Clean build artifacts
```

Individual examples can be built with:
```bash
make blinky.hex
make fomu_blink.hex
```

Build outputs are placed in the `build/` directory:
- `.bin` - Raw binary file
- `.hex` - Hexadecimal text format (one byte per line)

## Available Examples

### Standard Programs

These programs use the full memory configuration (`link.cfg`) with interrupt vectors:

**blinky.s**
- Simple LED blink demo
- Toggles GPIO pin 0 approximately once per second
- Demonstrates basic GPIO control and interrupt handling (BRK instruction)
- Assumes 1 MHz CPU clock

**sk6812_rgb.s**
- RGB LED strip breathing effect
- Controls 30 SK6812 addressable LEDs
- Fades RGB colors in and out every ~2 seconds
- Demonstrates SK6812 peripheral usage
- Assumes 10 MHz CPU clock

**pacman.s**
- LED strip "stacking" animation
- LEDs travel across the strip one by one and accumulate at the far end
- Creates a cycling RGB pattern as the strip fills
- Demonstrates timing-sensitive SK6812 protocol handling
- More complex program showing lookup tables and precise timing

**blinky_timer.s**
- LED blink demo using TIMER0 peripheral
- Precise 1-second blink intervals independent of CPU clock speed
- Demonstrates TIMER0 polling mode with auto-reload
- Works at any CPU frequency (timing based on system clock)

**sk6812_rgb_timer.s**
- RGB LED strip breathing effect using TIMER0
- Exactly 4ms delays between brightness updates
- Demonstrates precise timing for smooth animations
- CPU-speed independent implementation

**pacman_timer.s**
- LED strip "stacking" animation using TIMER0
- Multiple precise delays (10ms, 20ms, 2.6s)
- Shows advanced TIMER0 usage with subroutines
- Platform-portable timing (works at any CPU/system clock)

See [TIMER0_EXAMPLES.md](TIMER0_EXAMPLES.md) for detailed comparison between software delay loops and TIMER0-based timing.

### Mini Programs

These programs use a compact memory configuration (`mini_link.cfg`) designed for smaller FPGA block RAM:

**fomu_blink.s**
- Simple RGB LED blinker for Fomu board
- Toggles all three RGB LED channels via GPIO
- Minimal memory footprint for 8KB BRAM targets

**fomu_blink_timer.s**
- RGB LED blinker for Fomu using TIMER0
- Precise 400ms blink intervals
- Configured for Fomu's 48MHz system clock
- Demonstrates TIMER0 usage in compact BRAM configuration

**fomu_touch_led.s**
- Interactive capacitive touch controlled RGB LED
- Touch any of 4 pads to cycle through 8 colors
- 20ms debouncing using TIMER0
- Demonstrates GPIO input, debouncing, and state management
- Colors: Off → Red → Green → Blue → Yellow → Cyan → Magenta → White

## Linker Configurations

The examples use two different linker configurations:

### Standard Configuration (`link.cfg`)
- **Memory size:** 64KB ($0000-$FFFF)
- **Code location:** $E000-$FFF9
- **Vector table:** $FFFA-$FFFF (RESET, NMI, IRQ vectors)
- **Use case:** Full-featured programs with interrupt support

### Mini Configuration (`mini_link.cfg`)
- **Memory size:** 8KB ($0000-$1FFF)
- **Code location:** $1000-$1FFF
- **No vector table** - uses START_PC mechanism instead
- **Use case:** Small FPGA designs with limited block RAM (like Fomu)

The mini configuration is ideal for compact FPGA implementations where you want to minimize resource usage. Programs start execution at the beginning of the code segment without requiring the standard 6502 reset vector at $FFFC.

## Requirements

- **cc65 toolchain** - The examples use `cl65` for assembling and linking
- **xxd** - For converting binary to hex format

Install cc65 on macOS:
```bash
brew install cc65
```

## Running Examples

After building, load the `.hex` files onto your FPGA using your preferred method. The exact loading procedure depends on your FPGA board and toolchain (e.g., `iceprog` for iCE40 boards, `dfu-util` for Fomu).
