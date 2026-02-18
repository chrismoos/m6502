; Blinks an LED about once a second
; CPU should be running at 1Mhz

init:
    ; enable GPIO output on pin 0
    lda #1
    sta $a000

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
    ; get current LED output value and toggle
    lda $a001
    eor #1
    sta $a001

    ; irq test
    brk
    jmp toggle_loop

clear:
    pla     ; pop status register
    tax

    ; pop off old return address
    pla
    pla

    ; push new ret
    lda #>init
    pha
    lda #<init
    pha

    ; put back status register
    txa
    pha

    rti

.segment "VECTOR"
.word clear
.word init
.word clear