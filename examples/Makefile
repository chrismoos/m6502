.PHONY: all clean

PROGRAMS = blinky sk6812_rgb pacman blinky_timer sk6812_rgb_timer pacman_timer ulx3s_uart_echo ulx3s_uart_echo_irq
MINI_PROGRAMS = fomu_blink fomu_blink_timer fomu_touch_led

all: $(addsuffix .hex,$(PROGRAMS)) $(addsuffix .hex,$(MINI_PROGRAMS))

build:
	mkdir -p build

clean:
	rm -rf build

%.hex: %.s build
	cl65 -C link.cfg -t none --start-addr "0" -o build/$*.bin $<
	xxd -p build/$*.bin | fold -w2 > build/$*.hex

$(addsuffix .hex,$(MINI_PROGRAMS)): %.hex: %.s build
	cl65 -C mini_link.cfg -t none --start-addr "0" -o build/$*.bin $<
	xxd -p build/$*.bin | fold -w2 > build/$*.hex
