; Blinks an LED approximately once per second using TIMER0
; Works at any CPU clock speed - timing is based on system clock
;
; Assumes 50MHz system clock (common on ULX3S, configurable for other platforms)
; Adjust PRESCALER and RELOAD values for different system clocks

; GPIO registers
GPIOA_OE  = $A000
GPIOA_OUT = $A001

; TIMER0 registers (base $A020)
TIMER_CTRL      = $A020
TIMER_STATUS    = $A021
TIMER_COUNT_LO  = $A022
TIMER_COUNT_HI  = $A023
TIMER_RELOAD_LO = $A024
TIMER_RELOAD_HI = $A025
TIMER_PRESCALER = $A026

; Timer control bits
TIMER_ENABLE     = $01
TIMER_AUTO_RELOAD = $02
TIMER_IRQ_ENABLE = $04
TIMER_LOAD       = $08

; Timing calculation for ~1 second blink interval:
; System clock: 50 MHz
; PRESCALER = 199 → tick_freq = 50MHz / 200 = 250 kHz (4us per tick)
; For 500ms (half of 1 second): 500ms / 4us = 125,000 ticks
; Need 2 overflows for 1 second blink cycle
; Counts per overflow: 125,000 ticks
; But max is 65,536... so we need a different approach
;
; Better approach:
; PRESCALER = 199 → 250kHz tick rate
; RELOAD = 0x3CB0 (15536) → counts = 65536 - 15536 = 50,000 ticks
; Overflow period = 50,000 / 250kHz = 200ms
; Count 5 overflows = 1 second

; For other system clocks:
;   48 MHz (Fomu): PRESCALER = 191, same RELOAD → 200ms
;   25 MHz: PRESCALER = 99, same RELOAD → 200ms

RELOAD_VAL_LO = $B0    ; 0x3CB0 = 15536
RELOAD_VAL_HI = $3C
PRESCALER_VAL = 199    ; Divide by 200
OVERFLOW_COUNT = 5     ; 5 × 200ms = 1 second

.segment "CODE"

init:
    ; Enable GPIO output on pin 0
    lda #1
    sta GPIOA_OE

    ; Configure TIMER0
    ; Set prescaler for 250kHz tick rate (at 50MHz sysclk)
    lda #PRESCALER_VAL
    sta TIMER_PRESCALER

    ; Set reload value for 200ms overflow period
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

    ; Initialize overflow counter
    ldx #OVERFLOW_COUNT

toggle_loop:
    ; Wait for timer overflow
wait_overflow:
    lda TIMER_STATUS
    and #$01           ; Check OVERFLOW bit
    beq wait_overflow

    ; Clear overflow flag (write 1 to clear)
    lda #$01
    sta TIMER_STATUS

    ; Decrement overflow counter
    dex
    bne wait_overflow  ; Keep waiting if not done

    ; Reset overflow counter
    ldx #OVERFLOW_COUNT

toggle:
    ; Toggle LED
    lda GPIOA_OUT
    eor #1
    sta GPIOA_OUT

    jmp toggle_loop

.segment "VECTOR"
.word init              ; $FFFA NMI
.word init              ; $FFFC RESET
.word init              ; $FFFE IRQ
