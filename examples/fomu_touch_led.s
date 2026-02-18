; Fomu Touch LED - Capacitive touch controlled RGB LED
; Touch any of the 4 pads to cycle through colors
; Uses TIMER0 for debouncing
;
; GPIO Mapping (Fomu):
;   Pins 0-2: RGB LEDs (output)
;   Pins 4-7: Touch pads (input)
;
; Colors cycle: Off → Red → Green → Blue → Yellow → Cyan → Magenta → White → Off

; Zero page variables
color_index     = $00       ; Current color (0-7)
last_touch      = $01       ; Previous touch state
debounce_active = $02       ; 0=idle, 1=debouncing

; GPIO registers
GPIOA_OE  = $A000
GPIOA_OUT = $A001
GPIOA_IN  = $A002

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

; Touch pad mask (pins 4-7)
TOUCH_MASK = $F0

; Debounce timing:
; Fomu system clock: 48 MHz
; PRESCALER = 47 → tick_freq = 48MHz / 48 = 1 MHz (1us per tick)
; RELOAD = 0xB1E0 (45536) → counts = 65536 - 45536 = 20,000 ticks
; Overflow period = 20ms (good debounce delay)

RELOAD_VAL_LO = $E0    ; 0xB1E0 = 45536
RELOAD_VAL_HI = $B1
PRESCALER_VAL = 47     ; Divide by 48 (for 48MHz)

.segment "CODE"

init:
    ; Configure GPIO: pins 0-2 output (LEDs), pins 4-7 input (touch)
    lda #$07
    sta GPIOA_OE

    ; Start with first color (off)
    lda #0
    sta color_index
    sta GPIOA_OUT

    ; Initialize touch state
    lda GPIOA_IN
    and #TOUCH_MASK
    sta last_touch

    ; No active debounce
    lda #0
    sta debounce_active

    ; Configure TIMER0 for 20ms debounce
    lda #PRESCALER_VAL
    sta TIMER_PRESCALER

    lda #RELOAD_VAL_LO
    sta TIMER_RELOAD_LO
    lda #RELOAD_VAL_HI
    sta TIMER_RELOAD_HI

main_loop:
    ; Check if we're debouncing
    lda debounce_active
    bne check_debounce_done

    ; Not debouncing - check for touch
    lda GPIOA_IN
    and #TOUCH_MASK
    sta $03             ; Store current touch state in temp

    ; Compare with last state
    cmp last_touch
    beq main_loop       ; No change, keep looping

    ; Touch state changed - start debounce timer
    sta last_touch      ; Save new state
    lda #1
    sta debounce_active

    ; Load and start timer
    lda #TIMER_LOAD
    sta TIMER_CTRL

    lda #$01
    sta TIMER_STATUS    ; Clear any pending overflow

    lda #(TIMER_ENABLE | TIMER_AUTO_RELOAD)
    sta TIMER_CTRL

    jmp main_loop

check_debounce_done:
    ; Check if debounce timer expired
    lda TIMER_STATUS
    and #$01            ; Check OVERFLOW bit
    beq main_loop       ; Not done yet

    ; Clear overflow flag
    lda #$01
    sta TIMER_STATUS

    ; Debounce complete - re-read touch state
    lda GPIOA_IN
    and #TOUCH_MASK

    ; Check if any pad is pressed (active low, so check if any bit is 0)
    cmp #TOUCH_MASK     ; All high = no touch
    beq touch_released

    ; Still pressed - advance color
    inc color_index
    lda color_index
    cmp #8              ; Check if past last color
    bne update_led
    lda #0              ; Wrap to first color
    sta color_index

update_led:
    ; Look up color from table
    ldx color_index
    lda color_table, X
    sta GPIOA_OUT

    ; Wait for release before accepting next press
    jmp wait_release

touch_released:
    ; Released - ready for next press
    lda #0
    sta debounce_active

    ; Stop timer to save power
    lda #0
    sta TIMER_CTRL

    jmp main_loop

wait_release:
    ; Wait for all pads to be released
    lda GPIOA_IN
    and #TOUCH_MASK
    cmp #TOUCH_MASK     ; All high?
    bne wait_release    ; No, keep waiting

    ; Released - update state
    sta last_touch
    lda #0
    sta debounce_active

    ; Stop timer
    lda #0
    sta TIMER_CTRL

    jmp main_loop

; Color lookup table (8 colors)
; Hardware: rgb0=Green, rgb1=Red, rgb2=Blue (ACTIVE-LOW!)
; 0=ON, 1=OFF, so logic is inverted
; GRB bits: [x x x x x B R G]
color_table:
    .byte $07           ; 0: Off (111 = all high = all off)
    .byte $05           ; 1: Red (101 = Green off, Red on, Blue off)
    .byte $06           ; 2: Green (110 = Green on, Red off, Blue off)
    .byte $03           ; 3: Blue (011 = Green off, Red off, Blue on)
    .byte $04           ; 4: Yellow (100 = Red+Green on, Blue off)
    .byte $02           ; 5: Cyan (010 = Green+Blue on, Red off)
    .byte $01           ; 6: Magenta (001 = Red+Blue on, Green off)
    .byte $00           ; 7: White (000 = all low = all on)
