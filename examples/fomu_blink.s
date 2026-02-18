; Fomu Blink - Simple LED blinker for Fomu
; Toggles RGB LEDs via GPIO
; Linked for 8K BRAM - no vectors needed (uses START_PC)
;
; Note: Fomu RGB LEDs are active-low (0=ON, 1=OFF)

GPIOA_OE  = $A000
GPIOA_OUT = $A001

init:
    ; enable GPIO output on pins 0-2 (rgb0, rgb1, rgb2)
    lda #$07
    sta GPIOA_OE

    ; LEDs are active-low: start with all off (0x07 = all high)
    lda #$07
    sta GPIOA_OUT

toggle_loop:
    ldx #0
    ldy #0
    lda #0
loop1:
    inx
    bne loop1
    iny
    bne loop1
    adc #1
    cmp #3
    bne loop1

toggle:
    lda GPIOA_OUT
    eor #$07
    sta GPIOA_OUT
    jmp toggle_loop
