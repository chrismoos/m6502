; SK6812 RGB Pulse - 30 LEDs with breathing RGB pattern
; Fades in and out every ~2 seconds
; CPU running at 10MHz

; SK6812 peripheral registers (base $A010)
LED_CONTROL = $A010
LED_CLKDIV  = $A011
LED_RED     = $A012
LED_GREEN   = $A013
LED_BLUE    = $A014
LED_WHITE   = $A015
LED_STATUS  = $A016

NUM_LEDS    = 30

; Zero page variables
brightness  = $00       ; current brightness level
direction   = $01       ; 0 = up, 1 = down
color_index = $02       ; 0=red, 1=green, 2=blue
led_count   = $03
delay_lo    = $04
delay_hi    = $05

.segment "CODE"

init:
    lda #1
    sta brightness      ; start dim
    lda #0
    sta direction       ; start fading up

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

    ; === Delay between brightness updates ===
    ; ~4ms per step * 510 steps = ~2 second cycle
    ldx #20             ; outer loop count (adjust for speed)
delay_outer:
    ldy #0              ; inner loop: 256 iterations
delay_inner:
    nop
    nop
    dey
    bne delay_inner
    dex
    bne delay_outer

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
