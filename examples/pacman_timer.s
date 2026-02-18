; Pacman — SK6812 LED strip stacking animation (TIMER0 version)
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
; Uses TIMER0 for precise, CPU-speed-independent timing:
;   - ~2.6s pause when strip is full
;   - ~15ms delay between travel animation steps
;   - ~10ms pause after each LED is placed
;
; Works at any CPU clock speed - timing is based on system clock

; SK6812 peripheral registers (base $A010)
LED_CONTROL = $A010
LED_CLKDIV  = $A011
LED_RED     = $A012
LED_GREEN   = $A013
LED_BLUE    = $A014
LED_WHITE   = $A015
LED_STATUS  = $A016

; TIMER0 registers (base $A020)
TIMER_CTRL      = $A020
TIMER_STATUS    = $A021
TIMER_RELOAD_LO = $A024
TIMER_RELOAD_HI = $A025
TIMER_PRESCALER = $A026

; Timer control bits
TIMER_ENABLE     = $01
TIMER_AUTO_RELOAD = $02
TIMER_LOAD       = $08

NUM_LEDS    = 30
BRIGHTNESS  = $40       ; moderate brightness

; Timing configuration using TIMER0:
; System clock: 50 MHz (adjust PRESCALER for other clocks)
; PRESCALER = 49 → tick_freq = 50MHz / 50 = 1 MHz (1us per tick)
; RELOAD = 0xD8F0 (55536) → counts = 65536 - 55536 = 10,000 ticks
; Overflow period = 10ms
;
; Delay durations (in timer overflows):
;   Full-strip pause: 260 × 10ms = 2.6s
;   Travel step: 1-2 × 10ms ≈ 15ms
;   Place pause: 1 × 10ms = 10ms
;
; For 48MHz (Fomu): PRESCALER = 47 → same 10ms period

RELOAD_VAL_LO = $F0    ; 0xD8F0 = 55536
RELOAD_VAL_HI = $D8
PRESCALER_VAL = 49     ; Divide by 50 (for 50MHz sysclk)

; Delay counts (number of 10ms timer overflows)
PAUSE_OVERFLOWS  = 260  ; 2.6 second pause when strip full
TRAVEL_OVERFLOWS = 2    ; 20ms delay between travel steps
PLACE_OVERFLOWS  = 1    ; 10ms pause after placement

; Zero page variables
placed_count = $00      ; how many LEDs permanently placed (0-30)
travel_pos   = $01      ; current position of traveling LED
new_color    = $02      ; color of traveling LED (0=R,1=G,2=B)
destination  = $03      ; where traveling LED will stop
delay_count  = $04      ; timer overflow counter

.segment "CODE"

init:
    lda #0
    sta placed_count

    ; Configure TIMER0 for 10ms intervals
    lda #PRESCALER_VAL
    sta TIMER_PRESCALER

    lda #RELOAD_VAL_LO
    sta TIMER_RELOAD_LO
    lda #RELOAD_VAL_HI
    sta TIMER_RELOAD_HI

    ; Clear any pending overflow flag
    lda #$01
    sta TIMER_STATUS

    ; Load counter from RELOAD registers (timer must be stopped)
    lda #TIMER_LOAD
    sta TIMER_CTRL

    ; Enable timer with auto-reload
    lda #(TIMER_ENABLE | TIMER_AUTO_RELOAD)
    sta TIMER_CTRL

main_loop:
    ; Check if strip is full
    lda placed_count
    cmp #NUM_LEDS
    bne not_full

    ; === Strip full - pause then reset ===
    ; Wait for PAUSE_OVERFLOWS × 10ms = 2.6 seconds
    ldx #<PAUSE_OVERFLOWS   ; Low byte
    ldy #>PAUSE_OVERFLOWS   ; High byte
    jsr wait_timer_16bit

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
    ; Send all 30 LEDs — X = current LED index
    ldx #0

send_loop:
    cpx travel_pos
    beq send_traveling      ; this is where the traveling LED is

    ; Placed LEDs occupy positions > destination
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

    ; Wait TRAVEL_OVERFLOWS × 10ms before next travel step
    ldx #TRAVEL_OVERFLOWS
    ldy #0
    jsr wait_timer_16bit

    ; Move toward destination (increment travel_pos)
    inc travel_pos
    jmp travel_loop

travel_done:
    ; LED has arrived - increment placed count
    inc placed_count

    ; Wait PLACE_OVERFLOWS × 10ms after placement
    ldx #PLACE_OVERFLOWS
    ldy #0
    jsr wait_timer_16bit

    jmp main_loop

; === Subroutine: Wait for timer overflows ===
; Input: X = count low byte, Y = count high byte
; Waits for X + (Y × 256) timer overflows
wait_timer_16bit:
    stx delay_count        ; Only need low byte for our counts
                          ; (all our delays are < 256)
wait_timer_loop:
    ; Wait for timer overflow
wait_overflow:
    lda TIMER_STATUS
    and #$01               ; Check OVERFLOW bit
    beq wait_overflow

    ; Clear overflow flag
    lda #$01
    sta TIMER_STATUS

    ; Decrement count
    dec delay_count
    bne wait_timer_loop

    rts

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
