# Fomu Touch LED Example

Interactive capacitive touch controlled RGB LED demonstration for Fomu.

## Features

- **8 Color Cycle**: Touch any pad to advance through colors
- **20ms Debouncing**: Clean, glitch-free touch detection using TIMER0
- **Release Detection**: Waits for pad release before accepting next touch
- **Power Efficient**: Timer stops when idle

## How It Works

### Touch Sequence

1. **Idle**: Monitoring touch pads (pins 4-7)
2. **Touch Detected**: Any change in touch state triggers debounce
3. **Debounce (20ms)**: TIMER0 ensures stable reading
4. **Validate**: Re-read touch state after timer expires
5. **Action**: If still pressed, advance to next color
6. **Wait Release**: Hold current color until all pads released
7. **Idle**: Ready for next touch

### Color Cycle

Touch any pad to cycle through these colors:

| Index | Color | GRB Bits | Hex | Notes |
|-------|-------|----------|-----|-------|
| 0 | Off | 111 | 0x07 | All high (off) |
| 1 | Red | 101 | 0x05 | Pin 1 low only |
| 2 | Green | 110 | 0x06 | Pin 0 low only |
| 3 | Blue | 011 | 0x03 | Pin 2 low only |
| 4 | Yellow | 100 | 0x04 | Pins 0+1 low |
| 5 | Cyan | 010 | 0x02 | Pins 0+2 low |
| 6 | Magenta | 001 | 0x01 | Pins 1+2 low |
| 7 | White | 000 | 0x00 | All low (on) |

**ACTIVE-LOW:** LEDs are active-low - writing `0` turns LED **ON**, writing `1` turns LED **OFF**

**Format:** GRB - Bits are [B R G]: `rgb0`=Green, `rgb1`=Red, `rgb2`=Blue

After White, cycles back to Off.

## Hardware Changes

### Fomu Top Module (`targets/fomu/top.sv`)

Added touch pad inputs and GPIO mapping:

```systemverilog
module top (
    input clki,
    output rgb0,
    output rgb1,
    output rgb2,
    input touch_1,
    input touch_2,
    input touch_3,
    input touch_4
);

// GPIO mapping:
//   Pins 0-2: RGB LEDs (output)
//   Pins 4-7: Touch pads (input)
assign gpioa_input = {touch_4, touch_3, touch_2, touch_1, 4'b0};
```

**Pin Mapping:**

| GPIO Pin | Function | PCF Signal | FPGA Pin | Note |
|----------|----------|------------|----------|------|
| 0 | RGB Green | rgb0 | A5 | rgb0 = Green |
| 1 | RGB Red | rgb1 | B5 | rgb1 = Red |
| 2 | RGB Blue | rgb2 | C5 | rgb2 = Blue |
| 4 | Touch Pad 1 | touch_1 | E4 | |
| 5 | Touch Pad 2 | touch_2 | D5 | |
| 6 | Touch Pad 3 | touch_3 | E5 | |
| 7 | Touch Pad 4 | touch_4 | F5 | |

**Note:** Fomu's RGB LED has GRB mapping - `rgb0`=Green, `rgb1`=Red, `rgb2`=Blue

### PCF File

The touch pads were already defined in `targets/fomu/fomu-pvt.pcf`:

```
set_io touch_1 E4
set_io touch_2 D5
set_io touch_3 E5
set_io touch_4 F5
```

## Software Implementation

### Debounce Algorithm

Uses TIMER0 for precise 20ms debounce delay:

```
Fomu system clock: 48 MHz
PRESCALER = 47 → 1 MHz tick rate (1µs per tick)
RELOAD = 0xB1E0 (45,536) → 20,000 ticks to overflow
Period = 20ms
```

### State Machine

```
┌─────────────┐
│    IDLE     │ ← Monitor touch pads
└──────┬──────┘
       │ Touch detected
       ▼
┌─────────────┐
│ DEBOUNCING  │ ← Start 20ms timer
└──────┬──────┘
       │ Timer expires
       ▼
┌─────────────┐
│  VALIDATE   │ ← Re-read touch state
└──────┬──────┘
       │ Still pressed?
       ▼ Yes
┌─────────────┐
│ ADVANCE     │ ← Increment color
│   COLOR     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│WAIT RELEASE │ ← Poll until released
└──────┬──────┘
       │ Released
       └──────→ IDLE
```

## Building

```bash
cd examples
make fomu_touch_led.hex
```

## Loading to Fomu

```bash
dfu-util -D build/fomu_touch_led.bin
```

## Usage

1. Power on - LED starts Off (all dark)
2. Touch any pad - Advances to Red
3. Touch again - Advances to Green
4. Keep touching - Cycles through all 8 colors
5. After White - Wraps back to Off

## Technical Details

### Touch Pad Characteristics

- **Technology**: Capacitive touch sensing
- **Active State**: Active-low (touch = 0)
- **Sensitivity**: Finger touch or conductive object
- **Response Time**: Less than 20ms after debouncing

### Debounce Logic

```asm
; Detect change
lda GPIOA_IN
and #TOUCH_MASK    ; Isolate pins 4-7
cmp last_touch
beq no_change      ; Same state, ignore

; State changed - start debounce
sta last_touch
lda #TIMER_LOAD
sta TIMER_CTRL     ; Load counter
lda #(ENABLE | AUTO_RELOAD)
sta TIMER_CTRL     ; Start timer

; Later, when timer overflows

; Re-read and validate
lda GPIOA_IN
and #TOUCH_MASK
cmp #TOUCH_MASK    ; All high = released
beq touch_released

; Still pressed - advance color
```

### Power Optimization

- Timer disabled when idle (no polling overhead)
- Only starts on touch detection
- Stops after release confirmed

## Code Size

- **Program**: Approximately 200 bytes (including lookup table)
- **Variables**: 3 bytes zero page
- **Total**: Fits comfortably in 8KB BRAM

## Extending the Example

### Add More Colors

Extend `color_table` and update wrap check:

```asm
color_table:
    .byte $07  ; Off
    .byte $05  ; Red
    .byte $06  ; Green
    .byte $03  ; Blue
    .byte $04  ; Yellow
    .byte $02  ; Cyan
    .byte $01  ; Magenta
    .byte $00  ; White
    .byte $05  ; Dim Red (could implement with PWM)
    .byte $06  ; Dim Green
    ; ... etc

; Update wrap check:
cmp #10        ; Now 10 colors
```

### Per-Pad Actions

Make each pad do something different:

```asm
; Check which pad was touched
lda GPIOA_IN
and #$10       ; Pad 1?
beq pad1_action
and #$20       ; Pad 2?
beq pad2_action
; ... etc
```

### Brightness Control

Use TIMER0 for PWM-like brightness:

```asm
; Toggle LED rapidly with variable duty cycle
; (Requires more complex timer usage)
```

## Testing

### Verify Touch Detection

1. Program Fomu with example
2. Touch each pad individually
3. Verify LED changes color
4. Verify no bouncing or glitching
5. Verify release detection works

### Debug Mode

Add visual feedback for each pad:

```asm
; Show which pad is being touched
lda GPIOA_IN
and #TOUCH_MASK
lsr                ; Shift to RGB positions
lsr
lsr
lsr
sta GPIOA_OUT      ; Display touch state directly
```

## Troubleshooting

**LED doesn't change:**
- Check touch pad connections in top.sv
- Verify GPIOA_IN assignment is correct
- Try different touch pressure or duration

**Colors change randomly:**
- Increase debounce time (larger RELOAD value)
- Check for floating input (pull-ups or pull-downs)

**Color skips:**
- Timer may be running too fast
- Verify PRESCALER matches system clock (48MHz)

## Related Examples

- `fomu_blink.s` - Basic GPIO LED control
- `fomu_blink_timer.s` - TIMER0 usage for delays
- `blinky_timer.s` - Generic TIMER0 example

## Implementation Highlights

This example demonstrates:
- GPIO input (touch pads)
- GPIO output (RGB LEDs)
- TIMER0 for debouncing
- State machine design
- Lookup tables
- Interactive embedded programming
