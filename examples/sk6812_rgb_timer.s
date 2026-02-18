; SK6812 RGB Pulse - 30 LEDs with breathing RGB pattern using TIMER0
; Fades in and out with precise timing
; Works at any CPU clock speed - timing is based on system clock
;
; Uses TIMER0 for precise ~4ms delays between brightness updates
; Total fade cycle: 510 steps × 4ms = ~2 seconds

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

NUM_LEDS = 30

; Timing calculation for 4ms delay between brightness updates:
; System clock: 50 MHz
; PRESCALER = 49 → tick_freq = 50MHz / 50 = 1 MHz (1us per tick)
; For 4ms: 4000 ticks needed
; RELOAD = 0xF060 (61536) → counts = 65536 - 61536 = 4000 ticks
; Overflow period = 4000us = 4ms
;
; For 48MHz (Fomu): PRESCALER = 47 → 48MHz / 48 = 1MHz → same RELOAD

RELOAD_VAL_LO = $60    ; 0xF060 = 61536
RELOAD_VAL_HI = $F0
PRESCALER_VAL = 49     ; Divide by 50 (for 50MHz sysclk)

; Zero page variables
brightness  = $00       ; current brightness level
direction   = $01       ; 0 = up, 1 = down
color_index = $02       ; 0=red, 1=green, 2=blue
led_count   = $03

.segment "CODE"

init:
    ; Initialize brightness and direction
    lda #1
    sta brightness      ; start dim
    lda #0
    sta direction       ; start fading up

    ; Configure TIMER0 for 4ms intervals
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
    ; === Send all 30 LEDs with current brightness ===
    lda #0
    sta color_index
    lda #NUM_LEDS
    sta led_count

send_loop:
    ; Clear all colors first
    lda #0
    sta LED_RED
    sta LED_GREEN
    sta LED_BLUE
    sta LED_WHITE

    ; Set the appropriate color based on color_index
    lda color_index
    cmp #0
    beq set_red
    cmp #1
    beq set_green
    jmp set_blue

set_red:
    lda brightness
    sta LED_RED
    jmp send_pixel

set_green:
    lda brightness
    sta LED_GREEN
    jmp send_pixel

set_blue:
    lda brightness
    sta LED_BLUE

send_pixel:
    ; Wait for not busy
wait_ready:
    lda LED_STATUS
    and #1
    bne wait_ready

    ; Strobe to send
    lda #1
    sta LED_CONTROL

    ; Next color (0->1->2->0)
    inc color_index
    lda color_index
    cmp #3
    bne no_color_wrap
    lda #0
    sta color_index
no_color_wrap:

    ; Next LED
    dec led_count
    bne send_loop

    ; === Wait for timer overflow (4ms delay) ===
wait_timer:
    lda TIMER_STATUS
    and #$01           ; Check OVERFLOW bit
    beq wait_timer

    ; Clear overflow flag
    lda #$01
    sta TIMER_STATUS

    ; === Update brightness ===
    lda direction
    bne fading_down

fading_up:
    inc brightness
    lda brightness
    cmp #$FF            ; reached max?
    bne main_loop
    lda #1
    sta direction       ; switch to fading down
    jmp main_loop

fading_down:
    dec brightness
    lda brightness
    cmp #1              ; reached min? (not 0, keep some glow)
    bne main_loop
    lda #0
    sta direction       ; switch to fading up
    jmp main_loop

.segment "VECTOR"
.word 0                 ; $FFFA NMI
.word init              ; $FFFC RESET
.word 0                 ; $FFFE IRQ
