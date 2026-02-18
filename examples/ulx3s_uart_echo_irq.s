; ULX3S UART Echo + Timer Demo - Triple Interrupt Version
; Timer interrupt (~10Hz) drives rotating LED pattern on LEDs 0-4
; UART RX interrupt echoes received characters at 115200 baud
; NMI (button 1) prints "NMI event received!" message
; GPIO pin 5 = UART TX (on header pin gp26)
; GPIO pin 6 = UART RX (on header pin gn27)

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
TX_IRQ_EN      = $04
RX_IRQ_EN      = $08

; UART status bits
TX_READY       = $01
RX_READY       = $02

; Timer registers
TIMER_CTRL     = $A020
TIMER_STATUS   = $A021
TIMER_COUNT_LO = $A022
TIMER_COUNT_HI = $A023
TIMER_RELOAD_LO = $A024
TIMER_RELOAD_HI = $A025
TIMER_PRESCALER = $A026

; Timer control bits
TIMER_ENABLE   = $01
TIMER_AUTO_RELOAD = $02
TIMER_IRQ_EN   = $04
TIMER_LOAD     = $08

; Timer status bits
TIMER_OVERFLOW = $01

; Zero page variables
led_pattern    = $00    ; Current LED pattern

init:
    ; Disable interrupts during setup
    sei

    ; Configure GPIO pin 5 as UART TX (mode 0x01)
    lda #$01
    sta MODE_PIN5

    ; Configure GPIO pin 6 as UART RX (mode 0x02)
    lda #$02
    sta MODE_PIN6

    ; Configure LEDs 0-4 as outputs for activity indicator
    lda #$1F             ; Bits 0-4 = LEDs
    sta GPIOA_OE
    lda #$01             ; Start with LED 0 on
    sta GPIOA_OUT
    sta led_pattern

    ; Set baud rate to 115200 @ 50MHz (divisor = 26 = 0x001A)
    lda #$1A
    sta UART_BAUD_LO
    lda #$00
    sta UART_BAUD_HI

    ; Enable UART TX, RX, and RX interrupt
    lda #(TX_ENABLE | RX_ENABLE | RX_IRQ_EN)
    sta UART_CTRL

    ; Configure timer for ~10Hz (0.1 second) LED updates
    ; Prescaler = 255 (divide by 256): 50MHz / 256 = 195,312 Hz
    ; For 0.1s period: 19,531 ticks, reload = 0xFFFF - 19,531 + 1 = 0xB3B6
    lda #$FF
    sta TIMER_PRESCALER
    lda #$B6
    sta TIMER_RELOAD_LO
    lda #$B3
    sta TIMER_RELOAD_HI

    ; Load the reload value into the counter
    lda #TIMER_LOAD
    sta TIMER_CTRL
    lda #$00
    sta TIMER_CTRL

    ; Enable timer with auto-reload and IRQ
    lda #(TIMER_ENABLE | TIMER_AUTO_RELOAD | TIMER_IRQ_EN)
    sta TIMER_CTRL

    ; Send startup message
    ldx #0
send_msg:
    lda startup_msg,x
    beq enable_irq         ; Null terminator, enable IRQ
    jsr uart_send_byte
    inx
    jmp send_msg

enable_irq:
    ; Enable interrupts
    cli

main_loop:
    ; Main loop just waits for interrupts (timer drives LEDs, UART handles echo)
    nop
    jmp main_loop

; IRQ Handler - Called when timer or UART RX triggers
irq_handler:
    ; Save registers
    pha
    txa
    pha

check_timer:
    ; Check if timer overflow
    lda TIMER_STATUS
    and #TIMER_OVERFLOW
    beq check_uart         ; Not timer, check UART

    ; Timer interrupt - update LED pattern
    lda led_pattern
    asl                    ; Shift left (rotate LEDs)
    and #$1F               ; Mask to 5 LEDs
    bne store_leds         ; If non-zero, keep it
    lda #$01               ; Otherwise, wrap back to LED 0
store_leds:
    sta led_pattern
    sta GPIOA_OUT

    ; Clear timer overflow flag by writing 1 to it
    lda #TIMER_OVERFLOW
    sta TIMER_STATUS

check_uart:
    ; Check if UART RX has data
    lda UART_STATUS
    and #RX_READY
    beq irq_done           ; No more data, exit

uart_loop:
    ; Read character from RX FIFO
    lda UART_DATA

    ; Check if it's CR (13) or LF (10) - need to send both for proper newline
    cmp #13                ; Is it CR?
    beq uart_send_crlf
    cmp #10                ; Is it LF?
    beq uart_send_crlf

    ; Regular character - write directly to TX FIFO
    sta UART_DATA
    jmp uart_check_more    ; Check for more data

uart_send_crlf:
    ; Write CR and LF directly to TX FIFO (hardware will handle full FIFO)
    lda #13
    sta UART_DATA
    lda #10
    sta UART_DATA

uart_check_more:
    ; Check if more UART data available
    lda UART_STATUS
    and #RX_READY
    bne uart_loop          ; More data, continue

irq_done:
    ; Restore registers
    pla
    tax
    pla
    rti

; NMI Handler - Called when button 1 is pressed
nmi_handler:
    ; Save registers
    pha
    txa
    pha
    tya
    pha

    ; Send NMI message
    ldx #0
nmi_msg_loop:
    lda nmi_msg,x
    beq nmi_done           ; Null terminator
    jsr uart_send_byte
    inx
    jmp nmi_msg_loop

nmi_done:
    ; Restore registers
    pla
    tay
    pla
    tax
    pla
    rti

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
    .byte "ULX3S UART Echo + Timer IRQ Ready", 13, 10, 0

nmi_msg:
    .byte "NMI event received!", 13, 10, 0

.segment "VECTOR"
    .word nmi_handler  ; NMI vector
    .word init         ; RESET vector
    .word irq_handler  ; IRQ vector
