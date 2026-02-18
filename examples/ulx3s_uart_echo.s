; ULX3S UART Echo Demo
; Echoes received characters at 115200 baud
; GPIO pin 5 = UART TX (on header pin gp26)
; GPIO pin 6 = UART RX (on header pin gn27)
; Also blinks LED 0 on each received character

; GPIO registers
GPIOA_OE       = $A000
GPIOA_OUT      = $A001
MODE_PIN5      = $A009  ; UART TX pin
MODE_PIN6      = $A00A  ; UART RX pin

; UART registers
UART_CTRL      = $A040
UART_STATUS    = $A041
UART_DATA      = $A042
UART_BAUD_LO   = $A043
UART_BAUD_HI   = $A044

; UART control bits
TX_ENABLE      = $01
RX_ENABLE      = $02

; UART status bits
TX_READY       = $01
RX_READY       = $02

init:
    ; Configure GPIO pin 5 as UART TX (mode 0x01)
    lda #$01
    sta MODE_PIN5

    ; Configure GPIO pin 6 as UART RX (mode 0x02)
    lda #$02
    sta MODE_PIN6

    ; Configure LED 0 as output for activity indicator
    lda #$01
    sta GPIOA_OE
    lda #$00
    sta GPIOA_OUT  ; Start with LED off

    ; Set baud rate to 115200 @ 50MHz (divisor = 26 = 0x001A)
    lda #$1A
    sta UART_BAUD_LO
    lda #$00
    sta UART_BAUD_HI

    ; Enable UART TX and RX
    lda #(TX_ENABLE | RX_ENABLE)
    sta UART_CTRL

    ; Send startup message
    ldx #0
send_msg:
    lda startup_msg,x
    beq echo_loop          ; Null terminator, start echo loop
    jsr uart_send_byte
    inx
    jmp send_msg

echo_loop:
    ; Wait for received character
    lda UART_STATUS
    and #RX_READY
    beq echo_loop

    ; Read character from RX FIFO
    lda UART_DATA

    ; Toggle LED 0 to show activity
    pha                    ; Save received character
    lda GPIOA_OUT
    eor #$01
    sta GPIOA_OUT
    pla                    ; Restore received character

    ; Check if it's CR (13) or LF (10) - need to send both for proper newline
    cmp #13                ; Is it CR?
    beq send_crlf
    cmp #10                ; Is it LF?
    beq send_crlf

    ; Regular character - just echo it
    jsr uart_send_byte
    jmp echo_loop

send_crlf:
    ; Send CR then LF for proper newline
    lda #13
    jsr uart_send_byte
    lda #10
    jsr uart_send_byte
    jmp echo_loop

; Subroutine: Send byte in A via UART
uart_send_byte:
    pha                    ; Save byte to send
tx_wait:
    lda UART_STATUS
    and #TX_READY
    beq tx_wait            ; Wait until TX FIFO has space

    pla                    ; Restore byte
    sta UART_DATA          ; Write to TX FIFO
    rts

startup_msg:
    .byte "ULX3S UART Echo Ready", 13, 10, 0  ; CR, LF, null terminator

.segment "VECTOR"
    .word init    ; NMI vector
    .word init    ; RESET vector
    .word init    ; IRQ vector
