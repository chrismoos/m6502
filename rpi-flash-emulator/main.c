/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/interp.h"
#include "rom.h"

#include "flash.pio.h"

static uint32_t ram_address_ptr;

void setup_pio0_sm0_program(PIO pio) {
    uint offset = pio_add_program(pio, &flash_program);
    pio_sm_config c = flash_program_get_default_config(offset);

    // in pins, gpio0-7 data
    sm_config_set_in_pin_base(&c, 0);

    // out pins, gpio0-7 data
    sm_config_set_out_pins(&c, 0, 8);

    // set pins, mux gpio8-9
    sm_config_set_set_pins(&c, 8, 2);

    sm_config_set_in_shift(&c, false, false, 0);
    sm_config_set_out_shift(&c, true, false, 0);

    sm_config_set_jmp_pin(&c, 10);

    // full speed
    sm_config_set_clkdiv(&c, 1.0);

    pio_sm_init(pio, 0, offset, &c);

    int dma_ch_address = dma_claim_unused_channel(true);
    int dma_ch_read_setup = dma_claim_unused_channel(true);
    int dma_ch_read = dma_claim_unused_channel(true);
    int dma_ch_write = dma_claim_unused_channel(true);
    int dma_ch_write_setup = dma_claim_unused_channel(true);

    // PIO0 RXF -> RAM address ptr
    dma_channel_config dma_address_cfg = dma_channel_get_default_config(dma_ch_address);
    channel_config_set_transfer_data_size(&dma_address_cfg, DMA_SIZE_32);
    channel_config_set_read_increment(&dma_address_cfg, false);
    channel_config_set_write_increment(&dma_address_cfg, false);
    channel_config_set_chain_to(&dma_address_cfg, dma_ch_read_setup);
    channel_config_set_dreq(&dma_address_cfg, pio_get_dreq(pio, 0, false));
    dma_channel_configure(dma_ch_address, &dma_address_cfg,
        &ram_address_ptr, &pio0_hw->rxf[0], 1, true);

    // RAM address ptr -> read address trigger
    dma_channel_config dma_read_setup_cfg = dma_channel_get_default_config(dma_ch_read_setup);
    channel_config_set_transfer_data_size(&dma_read_setup_cfg, DMA_SIZE_32);
    channel_config_set_read_increment(&dma_read_setup_cfg, false);
    channel_config_set_write_increment(&dma_read_setup_cfg, false);
    dma_channel_configure(dma_ch_read_setup, &dma_read_setup_cfg,
        &dma_hw->ch[dma_ch_read].al3_read_addr_trig,
        &ram_address_ptr, 1, false);

    // RAM value -> TX FIFO
    dma_channel_config dma_read_cfg = dma_channel_get_default_config(dma_ch_read);
    channel_config_set_transfer_data_size(&dma_read_cfg, DMA_SIZE_8);
    channel_config_set_read_increment(&dma_read_cfg, false);
    channel_config_set_write_increment(&dma_read_cfg, false);
    channel_config_set_dreq(&dma_read_cfg, pio_get_dreq(pio, 0, true));
    channel_config_set_chain_to(&dma_read_cfg, dma_ch_write_setup);
    dma_channel_configure(dma_ch_read, &dma_read_cfg,
        &pio0_hw->txf[0],
        NULL,  // read address filled in
        1, false);

    // PIO RX FIFO -> RAM write setup
    dma_channel_config dma_write_setup_cfg = dma_channel_get_default_config(dma_ch_write_setup);
    channel_config_set_transfer_data_size(&dma_write_setup_cfg, DMA_SIZE_32);
    channel_config_set_read_increment(&dma_write_setup_cfg, false);
    channel_config_set_write_increment(&dma_write_setup_cfg, false);
    dma_channel_configure(dma_ch_write_setup, &dma_write_setup_cfg,
        &dma_hw->ch[dma_ch_write].al2_write_addr_trig,
        &ram_address_ptr, 1, false);

    // RX FIFO -> RAM write
    dma_channel_config dma_write_cfg = dma_channel_get_default_config(dma_ch_write);
    channel_config_set_transfer_data_size(&dma_write_cfg, DMA_SIZE_8);
    channel_config_set_read_increment(&dma_write_cfg, false);
    channel_config_set_write_increment(&dma_write_cfg, false);
    channel_config_set_dreq(&dma_write_cfg, pio_get_dreq(pio, 0, false));

    // chain back to start
    channel_config_set_chain_to(&dma_write_cfg, dma_ch_address);
    dma_channel_configure(dma_ch_write, &dma_write_cfg,
        NULL, // write address filled in
        &pio0_hw->rxf[0],
        1, false);

    pio_sm_set_enabled(pio, 0, true);
    pio_sm_put_blocking(pio, 0, ((uint32_t)&rom_bin) >> 16);
}


int main() {
    PIO pio = pio0;
    for (int x = 0; x < 32; x++) {
        pio_gpio_init(pio, x);
    }

    setup_pio0_sm0_program(pio);

    while (true) {
        sleep_ms(10000);
    }
}
