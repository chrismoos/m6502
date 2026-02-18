# TIMER0-Based Examples

This directory contains updated versions of the examples that use the TIMER0 peripheral for precise, CPU-speed-independent timing instead of software delay loops.

## Updated Examples

| Original Example | TIMER0 Version | Timing Improvement |
|-----------------|----------------|-------------------|
| `blinky.s` | `blinky_timer.s` | ~1 second precise intervals |
| `fomu_blink.s` | `fomu_blink_timer.s` | ~400ms precise intervals |
| `sk6812_rgb.s` | `sk6812_rgb_timer.s` | Exactly 4ms per brightness step |
| `pacman.s` | `pacman_timer.s` | Multiple precise delays (10ms, 20ms, 2.6s) |

## Key Advantages of TIMER0 Versions

### CPU-Speed Independent
The original examples use software delay loops that depend on CPU clock speed:
- `blinky.s` comments: "CPU should be running at 1Mhz"
- `sk6812_rgb.s` comments: "CPU running at 10MHz"
- `pacman.s` has different timing presets for 1MHz, 4MHz, and 10MHz

**TIMER0 versions work at ANY CPU speed** because timing is based on the system clock (sysclk), not the CPU clock divider. The same code works whether the CPU is running at 1MHz, 4MHz, 10MHz, or any other frequency.

### Precise Timing
Software delay loops provide approximate timing:
- Cycle counts are hard to calculate exactly
- Timing varies with code changes
- No way to verify actual delay duration

**TIMER0 provides exact timing:**
- `blinky_timer.s`: Exactly 1.0 second (5 × 200ms overflows)
- `sk6812_rgb_timer.s`: Exactly 4.0ms per step
- `pacman_timer.s`: Exactly 10ms, 20ms, and 2.6s delays

### More Readable Code
Compare the software delay loops:

```asm
; Original blinky.s - unclear timing
loop1:
    inx
    bne loop1
    iny
    bne loop1
    adc #1
    cmp #3
    bne loop1
```

With TIMER0:

```asm
; blinky_timer.s - crystal clear timing
wait_overflow:
    lda TIMER_STATUS
    and #$01           ; Check OVERFLOW bit
    beq wait_overflow
```

### Adjustable Without Code Changes
To change blink rate in original examples, you must:
1. Recalculate nested loop counts
2. Modify multiple constants
3. Recompile and test

**With TIMER0:** Just change `RELOAD` value or `PRESCALER` - no code rewrite needed.

### CPU Can Do Other Work
Software delay loops burn CPU cycles in tight loops doing nothing.

**TIMER0 allows the CPU to:**
- Poll the timer less frequently
- Do useful work between checks
- Enter low-power mode (when available)
- Handle interrupts (when IRQ mode is enabled)

## Timing Calculations

All TIMER0 examples assume a **50MHz system clock** (common on ULX3S and many FPGA platforms). Comments show how to adjust for other clocks.

### Common Configuration (10ms period)

Used by `pacman_timer.s`:

```
System clock: 50 MHz
PRESCALER = 49 → tick_freq = 50MHz / 50 = 1 MHz (1µs per tick)
RELOAD = 0xD8F0 (55536) → counts = 65536 - 55536 = 10,000 ticks
Overflow period = 10,000µs = 10ms
```

### For Different System Clocks

| System Clock | PRESCALER | Notes |
|-------------|-----------|-------|
| 48 MHz (Fomu) | 47 | Same reload value gives 10ms |
| 50 MHz (ULX3S) | 49 | Configured in examples |
| 25 MHz | 24 | Half the prescaler value |
| 100 MHz | 99 | Double the prescaler value |

The formula: `PRESCALER = (sysclk_mhz / desired_tick_freq_mhz) - 1`

For 1MHz tick rate: `PRESCALER = sysclk_mhz - 1`

## Code Size Comparison

TIMER0 versions are slightly larger due to timer configuration code, but eliminate complex nested loops:

| Example | Original Size | TIMER0 Size | Difference |
|---------|--------------|-------------|------------|
| blinky | ~50 bytes | ~80 bytes | +30 bytes |
| pacman | ~400 bytes | ~420 bytes | +20 bytes |

The small size increase is worth it for precise, portable timing.

## Compatibility Notes

### TIMER0 Register Map

All examples use these registers at base address `0xA020`:

```asm
TIMER_CTRL      = $A020  ; Control: ENABLE, AUTO_RELOAD, IRQ_ENABLE
TIMER_STATUS    = $A021  ; Status: OVERFLOW flag (write 1 to clear)
TIMER_RELOAD_LO = $A024  ; Reload value low byte
TIMER_RELOAD_HI = $A025  ; Reload value high byte
TIMER_PRESCALER = $A026  ; Clock prescaler (0-255)
```

### Polling vs Interrupt Mode

Current examples use **polling mode** - they check the OVERFLOW flag in a loop:

```asm
wait_overflow:
    lda TIMER_STATUS
    and #$01           ; Check OVERFLOW bit
    beq wait_overflow
```

When TIMER0 IRQ is connected to the CPU, examples can be updated to use **interrupt mode** for even more efficient operation.

## Platform-Specific Notes

### Fomu (48MHz sysclk)
- Use `PRESCALER = 47` for 1MHz tick rate
- `fomu_blink_timer.s` is pre-configured for Fomu

### ULX3S (50MHz sysclk)
- Use `PRESCALER = 49` for 1MHz tick rate
- All examples default to 50MHz

### Custom Platforms
Adjust `PRESCALER_VAL` constant at the top of each file:
1. Determine your system clock frequency
2. Set `PRESCALER = (sysclk_mhz / 1) - 1` for 1MHz tick rate
3. Or use the formulas in the comments to calculate custom periods

## Building

Build TIMER0 examples the same way as originals:

```bash
cd examples
make blinky_timer.bin
make fomu_blink_timer.bin
make sk6812_rgb_timer.bin
make pacman_timer.bin
```

## Future Enhancements

When TIMER0 IRQ is connected to CPU:

1. **Interrupt-driven mode**: Use IRQ handler instead of polling
2. **CPU sleep**: CPU can halt between timer events
3. **Nested timers**: Handle multiple timing events simultaneously
4. **Precise event scheduling**: Queue events with exact timing

## Recommendations

- **Use TIMER0 versions for production** - more reliable timing
- **Use original versions for educational purposes** - show software delay concepts
- **Adjust PRESCALER for your platform** - see timing calculations above
- **Experiment with different RELOAD values** - easy to customize timing
