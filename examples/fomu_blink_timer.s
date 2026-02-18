; Fomu Blink - Simple LED blinker for Fomu using TIMER0
; Toggles RGB LEDs via GPIO with precise timing
; Works at any CPU clock speed - timing is based on 48MHz system clock
;
; Linked for 8K BRAM - no vectors needed (uses START_PC)
;
; Note: Fomu RGB LEDs are active-low (0=ON, 1=OFF)

PIN_INDEX = $30
TOGGLE_COUNTER = $31

; GPIO registers
GPIOA_OE  = $A000
GPIOA_OUT = $A001

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

; Timing calculation for ~500ms blink interval (1 second total cycle):
; Fomu system clock: 48 MHz
; PRESCALER = 191 → tick_freq = 48MHz / 192 = 250 kHz (4us per tick)
; RELOAD = 0x3CB0 (15536) → counts = 65536 - 15536 = 50,000 ticks
; Overflow period = 50,000 / 250kHz = 200ms
; Count 2.5 overflows ≈ 500ms (we'll use 2 for ~400ms, close enough)

RELOAD_VAL_LO = $B0    ; 0x3CB0 = 15536
RELOAD_VAL_HI = $3C
PRESCALER_VAL = 191    ; Divide by 192 (for 48MHz)
OVERFLOW_COUNT = 2     ; 2 × 200ms = 400ms ≈ 0.5s

init:
    ; Enable GPIO output on pins 0-2 (rgb0, rgb1, rgb2)
    lda #$07
    sta GPIOA_OE

    ; LEDs are active-low: start with all off (0x07 = all high)
    lda #$07
    sta GPIOA_OUT

    ; Configure TIMER0
    ; Set prescaler for 250kHz tick rate (at 48MHz sysclk)
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

    ; Set GPIO pin index and toggle counter
    lda #2
    sta TOGGLE_COUNTER
    lda #1
    sta PIN_INDEX

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
    ; Toggle each of the RGB individually
    lda GPIOA_OUT
    eor PIN_INDEX
    sta GPIOA_OUT

    dec TOGGLE_COUNTER
    bne toggle_loop

    lda #2
    sta TOGGLE_COUNTER

    lda PIN_INDEX
    cmp #4
    bne shift_pin

    lda #1
    sta PIN_INDEX

    jmp toggle_loop

shift_pin:
    asl PIN_INDEX
    jmp toggle_loop