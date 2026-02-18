; Pacman — SK6812 LED strip stacking animation
;
; Visual effect:
;   A single LED "travels" from position 0 across the strip to the far end,
;   where it stops and stays lit.  The next LED then travels from 0 to the
;   position just before the previous one, and so on.  LEDs accumulate from
;   the far end back toward the beginning until the entire strip is filled.
;   After a pause the strip resets and the cycle repeats.
;
;   Each successive LED cycles through red, green, blue (color = index % 3),
;   producing a repeating RGB pattern once the strip is full.
;
; Strip layout (30 LEDs, positions 0-29):
;
;   During animation (placed_count = 3, traveling LED at position 2):
;
;     pos:  0  1 [2] 3  4 ... 26 [27 28 29]
;           .  .  T  .  .      .   B   G   R     T = traveling, . = off
;
;   Placed LEDs always occupy the TOP of the strip (positions 27-29 here).
;   The traveling LED moves left-to-right from 0 toward its destination
;   (= NUM_LEDS - 1 - placed_count).
;
; SK6812 protocol constraint:
;   The SK6812 interprets >80 us of LOW on the data line as a reset/latch.
;   At 1 MHz each CPU cycle is 1 us, so the code between consecutive strobes
;   must stay under ~80 us (minus the ~38 us the peripheral spends
;   transmitting the previous LED).  Lookup tables replace what would
;   otherwise be an iterative mod-3 subroutine whose cycle count grew with
;   the input value, keeping the worst-case inter-strobe gap at ~78 cycles
;   (~40 us of actual LOW time).
;
; Program flow:
;   init          — reset placed_count to 0
;   main_loop     — if strip full: pause, reset, restart
;                   else: compute destination & color, start travel
;   travel_loop   — send one full frame (30 LEDs) to the strip
;   send_loop     — for each LED: traveling? placed? or off? set color, strobe
;   travel_done   — LED arrived: increment placed_count, brief pause, loop
;
; Configurable timing:
;   PAUSE_OUTER   — controls how long the full strip is displayed before reset
;   TRAVEL_OUTER  — controls animation speed (delay between travel steps)
;   PLACE_DELAY   — brief pause after each LED is placed so position 0
;                   visibly goes dark between journeys

; SK6812 peripheral registers (base $A010)
LED_CONTROL = $A010
LED_CLKDIV  = $A011
LED_RED     = $A012
LED_GREEN   = $A013
LED_BLUE    = $A014
LED_WHITE   = $A015
LED_STATUS  = $A016

NUM_LEDS    = 30
BRIGHTNESS  = $40       ; moderate brightness

; Timing delays — adjust for CPU clock speed
; Pause delay  ≈ PAUSE_OUTER  × 256 × 3332 cycles
; Travel delay ≈ TRAVEL_OUTER × 256 × 7     cycles
;
; Preset suggestions:
;   1 MHz:  PAUSE_OUTER=3,  TRAVEL_OUTER=8   (~2.6s pause, ~14ms/step)
;   4 MHz:  PAUSE_OUTER=12, TRAVEL_OUTER=32  (~2.6s pause, ~14ms/step)
;  10 MHz:  PAUSE_OUTER=30, TRAVEL_OUTER=80  (~2.6s pause, ~14ms/step)
PAUSE_OUTER  = 3        ; outer loop count for strip-full pause
TRAVEL_OUTER = 8        ; outer loop count for travel animation step
PLACE_DELAY  = 8        ; outer loop count for pause after each LED is placed

; Zero page variables
placed_count = $00      ; how many LEDs permanently placed (0-30)
travel_pos   = $01      ; current position of traveling LED
new_color    = $02      ; color of traveling LED (0=R,1=G,2=B)
destination  = $03      ; where traveling LED will stop

.segment "CODE"

init:
    lda #0
    sta placed_count

main_loop:
    ; Check if strip is full
    lda placed_count
    cmp #NUM_LEDS
    bne not_full

    ; === Strip full - pause then reset ===
    ldx #PAUSE_OUTER
long_delay_outer:
    ldy #0
long_delay_middle:
    lda #0
long_delay_inner:
    nop
    nop
    sec
    clc
    adc #1
    bne long_delay_inner
    dey
    bne long_delay_middle
    dex
    bne long_delay_outer

    ; Reset
    lda #0
    sta placed_count
    jmp main_loop

not_full:
    ; Calculate destination: NUM_LEDS - 1 - placed_count
    lda #NUM_LEDS-1
    sec
    sbc placed_count
    sta destination

    ; Calculate color for new LED: placed_count % 3 (via lookup table)
    ldx placed_count
    lda mod3_table, X
    sta new_color

    ; === Animate LED traveling from 0 to destination ===
    lda #0
    sta travel_pos

travel_loop:
    ; Send all 30 LEDs — X = current LED index.
    ; Uses X register as loop counter and lookup tables for O(1) color
    ; computation.  Worst-case strobe-to-strobe is ~78 cycles (~78 µs
    ; at 1 MHz); ~38 µs of that overlaps with peripheral transmission,
    ; leaving a ~40 µs LOW gap — well under the SK6812 reset threshold.
    ldx #0

send_loop:
    cpx travel_pos
    beq send_traveling      ; this is where the traveling LED is

    ; Placed LEDs occupy positions > destination.
    ; (destination = NUM_LEDS - 1 - placed_count)
    cpx destination
    beq send_off            ; at destination — not yet placed
    bcc send_off            ; below destination — not placed

    ; Placed LED — look up color directly by position (O(1))
    lda placed_color, X
    jmp send_color

send_traveling:
    ; Send the traveling LED with its color
    lda new_color

send_color:
    cmp #0
    beq send_red
    cmp #1
    beq send_green
    jmp send_blue

send_red:
    lda #BRIGHTNESS
    sta LED_RED
    lda #0
    sta LED_GREEN
    sta LED_BLUE
    sta LED_WHITE
    jmp do_send

send_green:
    lda #0
    sta LED_RED
    lda #BRIGHTNESS
    sta LED_GREEN
    lda #0
    sta LED_BLUE
    sta LED_WHITE
    jmp do_send

send_blue:
    lda #0
    sta LED_RED
    sta LED_GREEN
    lda #BRIGHTNESS
    sta LED_BLUE
    lda #0
    sta LED_WHITE
    jmp do_send

send_off:
    lda #0
    sta LED_RED
    sta LED_GREEN
    sta LED_BLUE
    sta LED_WHITE

do_send:
    ; Wait for not busy
wait_ready:
    lda LED_STATUS
    and #1
    bne wait_ready

    ; Strobe
    lda #1
    sta LED_CONTROL

    ; Next LED
    inx
    cpx #NUM_LEDS
    beq send_done
    jmp send_loop

send_done:
    ; === Frame complete ===

    ; Check if LED has reached destination
    lda travel_pos
    cmp destination
    beq travel_done

    ; Delay before next travel step
    ldx #TRAVEL_OUTER
travel_delay_outer:
    ldy #0
travel_delay_inner:
    nop
    dey
    bne travel_delay_inner
    dex
    bne travel_delay_outer

    ; Move toward destination (increment travel_pos)
    inc travel_pos
    jmp travel_loop

travel_done:
    ; LED has arrived - increment placed count
    inc placed_count

    ; Pause after placement so LED 0 visibly goes dark between journeys.
    ; Without this, the next traveling LED re-lights LED 0 almost instantly,
    ; causing it to appear stuck on (especially for short journeys near the end).
    ldx #PLACE_DELAY
place_delay_outer:
    ldy #0
place_delay_inner:
    nop
    dey
    bne place_delay_inner
    dex
    bne place_delay_outer

    jmp main_loop

; === Lookup tables (O(1) replacement for calc_mod3 subroutine) ===

; mod3_table[N] = N % 3  — used for new_color = placed_count % 3
mod3_table:
    .byte 0, 1, 2, 0, 1, 2, 0, 1, 2, 0
    .byte 1, 2, 0, 1, 2, 0, 1, 2, 0, 1
    .byte 2, 0, 1, 2, 0, 1, 2, 0, 1, 2

; placed_color[N] = (29 - N) % 3  — color for placed LED at position N
; Indexed directly by X (LED position) to avoid a subtraction in the loop
placed_color:
    .byte 2, 1, 0, 2, 1, 0, 2, 1, 0, 2
    .byte 1, 0, 2, 1, 0, 2, 1, 0, 2, 1
    .byte 0, 2, 1, 0, 2, 1, 0, 2, 1, 0

.segment "VECTOR"
.word 0                 ; $FFFA NMI
.word init              ; $FFFC RESET
.word 0                 ; $FFFE IRQ
