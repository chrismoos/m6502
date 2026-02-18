#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""
m6502 Bus Multiplexer Timing Diagram Generator

Generates timing diagrams in classic 6502 datasheet style — with fluid
analog transitions, trapezoidal clock edges, and bus X-crossover patterns.

Timing references real MOS 6502 datasheet parameters at the
configured clock speed.

Bus timing from cpu_6502.sv:
  - negedge PHI2: CPU sets o_bus_addr, o_rw; samples i_bus_data
  - posedge PHI2: CPU registers o_bus_data (write data valid)

Usage:
  uv run docs/timing_diagram.py
  uv run docs/timing_diagram.py --freq 2.0
  uv run docs/timing_diagram.py --freq 1.0 --output docs/timing_1mhz.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import argparse


# ── 6502 Datasheet Timing Parameters (ns) ───────────────────────────
TIMING_1MHZ = {
    'tCYC':  1000,
    'tPHI2': 500,
    'tADS':  150,       # Address Delay Time (typ, after negedge PHI2)
    'tHA':   30,
    'tRWS':  150,       # R/W Delay Time (typ, after negedge PHI2)
    'tHRW':  30,
    'tACC':  575,
    'tDSU':  100,
    'tHR':   10,
    'tMDS':  200,
    'tHW':   30,
}


def get_timing(freq_mhz):
    """Scale 1 MHz timing parameters to the target frequency."""
    scale = 1.0 / freq_mhz
    return {k: v * scale for k, v in TIMING_1MHZ.items()}


# ── Colors ───────────────────────────────────────────────────────────
C_CLK       = '#1e40af'
C_CLK_FILL  = '#dbeafe'
C_ADDR      = '#059669'
C_ADDR_FILL = '#d1fae5'
C_DATA_R    = '#7c3aed'
C_DATA_R_F  = '#ede9fe'
C_DATA_W    = '#dc2626'
C_DATA_W_F  = '#fee2e2'
C_MUX_A     = '#0d9488'
C_MUX_A_F   = '#ccfbf1'
C_RW        = '#d97706'
C_OE        = '#6b7280'
C_TIMING    = '#9ca3af'
C_NEDGE     = '#ef4444'
C_PEDGE     = '#3b82f6'
C_BG        = '#fafbfc'
C_GRID      = '#e5e7eb'


# ── Drawing Primitives ──────────────────────────────────────────────

def draw_clock(ax, y, t_start, t_end, period, color=C_CLK,
               fill_color=None, start_high=False, slew=None):
    """Draw a trapezoidal clock signal with sloped rise/fall edges."""
    if slew is None:
        slew = period * 0.05
    half = period / 2
    height = 0.55
    lo = y - height / 2

    xs, ys = [], []
    level = 1.0 if start_high else 0.0
    t = t_start

    while t < t_end + period:
        xs.append(t)
        ys.append(level)
        new_level = 1.0 - level
        xs.append(t + slew)
        ys.append(new_level)
        level = new_level
        t += half

    scaled = [lo + v * height for v in ys]
    ax.plot(xs, scaled, color=color, linewidth=2.2, solid_capstyle='round',
            zorder=5, clip_on=True)

    if fill_color:
        ax.fill_between(xs, [lo] * len(xs), scaled, color=fill_color,
                        alpha=0.25, zorder=2, clip_on=True)


def _merge_bus_segments(segments):
    """Merge adjacent segments with identical label and color."""
    if len(segments) <= 1:
        return segments
    merged = [segments[0].copy()]
    for seg in segments[1:]:
        prev = merged[-1]
        if (prev['label'] == seg['label'] and prev['color'] == seg['color']
                and prev['t1'] == seg['t0']
                and not prev.get('hatch') and not seg.get('hatch')):
            prev['t1'] = seg['t1']
        else:
            merged.append(seg.copy())
    return merged


def draw_bus(ax, y, segments, height=0.50, tw=30):
    """
    Draw a bus signal in classic datasheet X-crossover style.

    Each segment: {'t0': float, 't1': float, 'label': str,
                   'fill': color, 'color': color, 'hatch': bool}
    Adjacent segments share boundaries; X crossovers drawn at each.
    """
    if not segments:
        return

    h = height / 2
    htw = tw / 2

    for i, seg in enumerate(segments):
        t0, t1 = seg['t0'], seg['t1']
        color = seg.get('color', '#374151')
        fill = seg.get('fill', None)
        label = seg.get('label', '')
        hatched = seg.get('hatch', False)

        has_left = i > 0
        has_right = i < len(segments) - 1
        sl = t0 + htw if has_left else t0
        sr = t1 - htw if has_right else t1

        if sr <= sl:
            continue

        # Stable top and bottom rails
        ax.plot([sl, sr], [y + h, y + h], color=color, lw=1.5, zorder=5)
        ax.plot([sl, sr], [y - h, y - h], color=color, lw=1.5, zorder=5)

        # Fill
        if fill and not hatched:
            ax.fill_between([sl, sr], y - h, y + h,
                            color=fill, alpha=0.35, zorder=2)
        if hatched:
            ax.add_patch(plt.Rectangle(
                (sl, y - h), sr - sl, height,
                facecolor='#e8e8e8', edgecolor='none', alpha=0.3, zorder=2))
            ax.add_patch(plt.Rectangle(
                (sl, y - h), sr - sl, height,
                facecolor='none', edgecolor=color,
                hatch='///', alpha=0.3, zorder=3, lw=0.5))

        # Label
        if label and (sr - sl) > tw:
            ax.text((sl + sr) / 2, y, label,
                    ha='center', va='center', fontsize=9.5, fontweight='bold',
                    fontfamily='monospace', color='#111827', zorder=6)

        # End caps (vertical bars at start/end of entire signal)
        if not has_left:
            ax.plot([t0, t0], [y - h, y + h], color=color, lw=1.5, zorder=5)
        if not has_right:
            ax.plot([t1, t1], [y - h, y + h], color=color, lw=1.5, zorder=5)

    # X crossovers between adjacent segments
    for i in range(len(segments) - 1):
        tc = segments[i]['t1']
        color = segments[i].get('color', '#374151')
        ax.plot([tc - htw, tc + htw], [y + h, y - h],
                color=color, lw=1.5, zorder=5)
        ax.plot([tc - htw, tc + htw], [y - h, y + h],
                color=color, lw=1.5, zorder=5)


def draw_timing_arrow(ax, y, t0, t1, label, color=C_TIMING, above=True,
                      vlines_y=None):
    """Draw a horizontal timing measurement arrow with label.

    vlines_y: if set to (y_bottom, y_top), draw thin vertical reference
              lines at t0 and t1 spanning that range so the reader can
              visually compare the endpoint to other signals (e.g. PHI2).
    """
    dy = 0.18 if above else -0.18
    yt = y + dy
    ax.annotate('', xy=(t1, yt), xytext=(t0, yt),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.2,
                                shrinkA=0, shrinkB=0))
    ax.text((t0 + t1) / 2, yt + (0.12 if above else -0.15), label,
            ha='center', va='center', fontsize=7.5, color=color,
            fontfamily='monospace', fontstyle='italic',
            bbox=dict(facecolor='white', edgecolor='none', pad=1, alpha=0.85),
            zorder=7)
    if vlines_y is not None:
        yb, yt_top = vlines_y
        for tx in (t0, t1):
            ax.plot([tx, tx], [yb, yt_top], color=color,
                    linewidth=0.8, linestyle='--', alpha=0.55, zorder=8)


# ── Main Diagram ────────────────────────────────────────────────────

def generate_diagram(freq_mhz=1.0, num_cycles=2, filename=None):
    """Generate the bus multiplexer timing diagram."""
    t = get_timing(freq_mhz)
    period = t['tCYC']
    half = period / 2
    total = num_cycles * period
    tw = period * 0.03  # X-crossover transition width

    rows = {
        'PHI1':     8.0,
        'PHI2':     7.0,
        'ADDR':     5.8,
        'RW':       4.8,
        'MUX_SEL':  3.5,
        'MUX_DATA': 2.3,
        'MUX_OE':   1.2,
    }

    fig, ax = plt.subplots(figsize=(18, 9.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor(C_BG)

    # ── Clocks (trapezoidal) ────────────────────────────────────────
    draw_clock(ax, rows['PHI2'], 0, total, period,
               color=C_CLK, fill_color=C_CLK_FILL, start_high=True)
    draw_clock(ax, rows['PHI1'], 0, total, period,
               color=C_CLK, fill_color=C_CLK_FILL, start_high=False)

    # ── Build segments per signal ───────────────────────────────────
    cycle_types = ['read', 'write'] if num_cycles >= 2 else ['read']
    while len(cycle_types) < num_cycles:
        cycle_types.append('read')

    addr_segs, rw_segs, sel_segs, data_segs, oe_segs = [], [], [], [], []

    for cyc in range(num_cycles):
        c0 = cyc * period
        c_pos = c0 + half
        c1 = (cyc + 1) * period
        is_write = cycle_types[cyc] == 'write'

        addr = 0x8000 + cyc
        alo = addr & 0xFF
        ahi = (addr >> 8) & 0xFF
        data_val = 0xAA if is_write else 0x55
        data_valid_read = c1 - t['tDSU']
        data_valid_write = c1 - t['tMDS']

        # Mux phases: wait for tADS, then two equal address phases, then data
        # Phase 1 = ADDR_HI, Phase 2 = ADDR_LO (HI first for earlier decode)
        t_mux_su = 10  # mux propagation delay (ns)
        mux_addr_start = c0 + t['tADS']           # mux starts after addr valid
        addr_phase_width = (c_pos - mux_addr_start) / 2  # equal HI & LO
        mux_mid = mux_addr_start + addr_phase_width  # HI→LO boundary

        # CPU ADDR — hatched during tADS delay, then valid
        addr_segs.append({
            't0': c0, 't1': mux_addr_start,
            'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        addr_segs.append({
            't0': mux_addr_start, 't1': c1,
            'label': f'${addr:04X}', 'fill': C_ADDR_FILL, 'color': C_ADDR,
        })

        # R/W — hatched during tRWS delay, then valid
        rw_color = C_DATA_W if is_write else C_ADDR
        rw_fill = C_DATA_W_F if is_write else C_ADDR_FILL
        rw_label = 'WRITE' if is_write else 'READ'
        rw_segs.append({
            't0': c0, 't1': c0 + t['tRWS'],
            'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        rw_segs.append({
            't0': c0 + t['tRWS'], 't1': c1,
            'label': rw_label, 'fill': rw_fill, 'color': rw_color,
        })

        # MUX_SEL — idle during tADS wait, then HI, then LO, then DATA
        dsel = '11 DATA_OUT' if is_write else '10 DATA_IN'
        dfc = C_DATA_W_F if is_write else C_DATA_R_F
        dec = C_DATA_W if is_write else C_DATA_R
        sel_segs.append({
            't0': c0, 't1': mux_addr_start,
            'label': 'WAIT', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        sel_segs.extend([
            {'t0': mux_addr_start, 't1': mux_mid,
             'label': '01 ADDR_HI', 'fill': C_MUX_A_F, 'color': C_MUX_A},
            {'t0': mux_mid, 't1': c_pos,
             'label': '00 ADDR_LO', 'fill': C_MUX_A_F, 'color': C_MUX_A},
            {'t0': c_pos,   't1': c1,
             'label': dsel, 'fill': dfc, 'color': dec},
        ])

        # MUX_DATA — wait for tADS, then HI (+ tMUX prop), then LO (+ tMUX)
        # Wait / idle during tADS
        data_segs.append({
            't0': c0, 't1': mux_addr_start,
            'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        # ADDR_HI phase — mux output valid after tMUX propagation
        ahi_valid = mux_addr_start + t_mux_su
        data_segs.append({
            't0': mux_addr_start, 't1': ahi_valid,
            'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        data_segs.append({
            't0': ahi_valid, 't1': mux_mid,
            'label': f'A[15:8]=${ahi:02X}', 'fill': C_MUX_A_F, 'color': C_MUX_A,
        })
        # ADDR_LO phase — mux select changes, another tMUX propagation
        alo_valid = mux_mid + t_mux_su
        data_segs.append({
            't0': mux_mid, 't1': alo_valid,
            'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
        })
        data_segs.append({
            't0': alo_valid, 't1': c_pos,
            'label': f'A[7:0]=${alo:02X}', 'fill': C_MUX_A_F, 'color': C_MUX_A,
        })
        if is_write:
            if data_valid_write > c_pos:
                data_segs.append({
                    't0': c_pos, 't1': data_valid_write,
                    'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
                })
            data_segs.append({
                't0': data_valid_write, 't1': c1,
                'label': f'D=${data_val:02X}', 'fill': C_DATA_W_F, 'color': C_DATA_W,
            })
        else:
            data_segs.append({
                't0': c_pos, 't1': data_valid_read,
                'label': '', 'fill': None, 'color': '#9ca3af', 'hatch': True,
            })
            data_segs.append({
                't0': data_valid_read, 't1': c1,
                'label': f'D=${data_val:02X}', 'fill': C_DATA_R_F, 'color': C_DATA_R,
            })

        # MUX_OE
        if is_write:
            oe_segs.append({
                't0': c0, 't1': c1,
                'label': 'OE=1', 'fill': '#e5e7eb', 'color': C_OE,
            })
        else:
            oe_segs.extend([
                {'t0': c0,   't1': c_pos,
                 'label': 'OE=1', 'fill': '#e5e7eb', 'color': C_OE},
                {'t0': c_pos, 't1': c1,
                 'label': 'OE=0 (Hi-Z)', 'fill': '#fef3c7', 'color': '#f59e0b'},
            ])

    # Merge adjacent identical segments (e.g. consecutive OE=1)
    oe_segs = _merge_bus_segments(oe_segs)

    # ── Draw bus signals ─────────────────────────────────────────────
    draw_bus(ax, rows['ADDR'],     addr_segs, height=0.50, tw=tw)
    draw_bus(ax, rows['RW'],       rw_segs,   height=0.50, tw=tw)
    draw_bus(ax, rows['MUX_SEL'],  sel_segs,  height=0.50, tw=tw)
    draw_bus(ax, rows['MUX_DATA'], data_segs,  height=0.50, tw=tw)
    draw_bus(ax, rows['MUX_OE'],   oe_segs,   height=0.50, tw=tw)

    # ── Timing annotations (first read cycle) ───────────────────────
    c_pos = half
    c1 = period
    data_valid_read = c1 - t['tDSU']
    # Vertical reference lines span from bottom of lowest row to top of PHI1
    vl_bot = rows['MUX_OE'] - 0.40
    vl_top = rows['PHI1'] + 0.35
    vl = (vl_bot, vl_top)

    # tADS: delay from negedge PHI2 to address valid
    draw_timing_arrow(ax, rows['ADDR'], 0, t['tADS'],
                      f'tADS={t["tADS"]:.0f}ns', color=C_ADDR,
                      vlines_y=vl)
    # tHA: address hold after next negedge PHI2
    draw_timing_arrow(ax, rows['ADDR'], c1, c1 + t['tHA'],
                      f'tHA={t["tHA"]:.0f}ns', color=C_ADDR, above=False,
                      vlines_y=vl)
    # tRWS: delay from negedge PHI2 to R/W valid
    draw_timing_arrow(ax, rows['RW'], 0, t['tRWS'],
                      f'tRWS={t["tRWS"]:.0f}ns', color=C_RW,
                      vlines_y=vl)
    # tHRW: R/W hold after next negedge PHI2
    draw_timing_arrow(ax, rows['RW'], c1, c1 + t['tHRW'],
                      f'tHRW={t["tHRW"]:.0f}ns', color=C_RW, above=False,
                      vlines_y=vl)
    # tACC: memory access time from posedge PHI2
    draw_timing_arrow(ax, rows['MUX_DATA'] - 0.45,
                      c_pos, c_pos + t['tACC'],
                      f'tACC={t["tACC"]:.0f}ns max', color=C_DATA_R,
                      vlines_y=vl)
    # tDSU: data setup before negedge PHI2
    draw_timing_arrow(ax, rows['MUX_DATA'], data_valid_read, c1,
                      f'tDSU={t["tDSU"]:.0f}ns', color=C_DATA_R,
                      vlines_y=vl)
    # tMUX: mux propagation time (10ns) at ADDR_HI→ADDR_LO transition
    t_mux_su = 10  # ns, fixed IC parameter
    mux_mid_0 = t['tADS'] + (half - t['tADS']) / 2  # HI→LO boundary (cycle 0)
    draw_timing_arrow(ax, rows['MUX_SEL'], mux_mid_0,
                      mux_mid_0 + t_mux_su,
                      f'tMUX={t_mux_su}ns', color=C_MUX_A, above=False,
                      vlines_y=vl)

    # Write cycle annotations
    if num_cycles >= 2 and cycle_types[1] == 'write':
        c1_w = 2 * period  # falling edge ending write cycle
        data_valid_write = c1_w - t['tMDS']
        # tMDS: write data setup before falling edge
        draw_timing_arrow(ax, rows['MUX_DATA'],
                          data_valid_write, c1_w,
                          f'tMDS={t["tMDS"]:.0f}ns', color=C_DATA_W,
                          vlines_y=vl)
        # tHW: write data hold after falling edge
        draw_timing_arrow(ax, rows['MUX_DATA'], c1_w, c1_w + t['tHW'],
                          f'tHW={t["tHW"]:.0f}ns', color=C_DATA_W,
                          above=False, vlines_y=vl)

    # ── Cycle labels ─────────────────────────────────────────────────
    for cyc in range(num_cycles):
        c0 = cyc * period
        is_write = cycle_types[cyc] == 'write'
        ctype = cycle_types[cyc].upper()
        ccolor = C_DATA_W if is_write else C_DATA_R
        ax.text(c0 + period / 2, 0.2, f'{ctype} CYCLE',
                ha='center', va='center', fontsize=11, fontweight='bold',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=ccolor,
                          alpha=0.12, edgecolor=ccolor, linewidth=1.2),
                zorder=7)

    # ── Edge markers ─────────────────────────────────────────────────
    for cyc in range(num_cycles + 1):
        te = cyc * period
        if te <= total:
            ax.axvline(x=te, color=C_NEDGE, linestyle='--',
                       linewidth=1.0, alpha=0.45, zorder=1)
            if cyc < num_cycles:
                ax.text(te + period * 0.008, rows['PHI2'] + 0.48,
                        'negedge\nPHI2', fontsize=7, color=C_NEDGE,
                        fontfamily='monospace', alpha=0.8, va='bottom',
                        linespacing=0.9, zorder=7)

    for cyc in range(num_cycles):
        tp = cyc * period + half
        ax.axvline(x=tp, color=C_PEDGE, linestyle=':',
                   linewidth=0.9, alpha=0.35, zorder=1)
        ax.text(tp + period * 0.008, rows['PHI2'] + 0.48,
                'posedge\nPHI2', fontsize=7, color=C_PEDGE,
                fontfamily='monospace', alpha=0.65, va='bottom',
                linespacing=0.9, zorder=7)

    # ── Edge annotations ─────────────────────────────────────────────
    ax.annotate('CPU: addr + R/W set up\n         data sampled',
                xy=(0, rows['PHI2'] - 0.42),
                xytext=(period * 0.22, rows['PHI1'] + 0.9),
                fontsize=8, fontfamily='monospace', color=C_NEDGE,
                arrowprops=dict(arrowstyle='->', color=C_NEDGE, lw=1.3),
                ha='center', zorder=7,
                bbox=dict(facecolor='white', edgecolor=C_NEDGE,
                          alpha=0.85, pad=3, boxstyle='round,pad=0.3'))

    ax.annotate('CPU: write data\n         registered',
                xy=(half, rows['PHI2'] - 0.42),
                xytext=(half + period * 0.20, rows['PHI1'] + 0.9),
                fontsize=8, fontfamily='monospace', color=C_PEDGE,
                arrowprops=dict(arrowstyle='->', color=C_PEDGE, lw=1.3),
                ha='center', zorder=7,
                bbox=dict(facecolor='white', edgecolor=C_PEDGE,
                          alpha=0.85, pad=3, boxstyle='round,pad=0.3'))

    # ── Row labels ───────────────────────────────────────────────────
    label_x = -0.035 * total
    for _, ypos, lbl in [
        ('PHI1',     rows['PHI1'],     'PHI1'),
        ('PHI2',     rows['PHI2'],     'PHI2'),
        ('ADDR',     rows['ADDR'],     'CPU\nADDR'),
        ('RW',       rows['RW'],       'R/W'),
        ('MUX_SEL',  rows['MUX_SEL'],  'MUX_SEL\n[1:0]'),
        ('MUX_DATA', rows['MUX_DATA'], 'MUX_DATA\n[7:0]'),
        ('MUX_OE',   rows['MUX_OE'],   'MUX_OE'),
    ]:
        ax.text(label_x, ypos, lbl, ha='right', va='center',
                fontsize=10, fontweight='bold', fontfamily='monospace',
                color='#1f2937')

    # ── Axes ─────────────────────────────────────────────────────────
    margin_l = 0.12 * total
    margin_r = 0.04 * total
    ax.set_xlim(-margin_l, total + margin_r)
    ax.set_ylim(-0.5, max(rows.values()) + 2.0)

    tick_step = 100 if period >= 500 else 50
    xticks = np.arange(0, total + 1, tick_step)
    ax.set_xticks(xticks)
    ax.set_xticklabels([f'{int(x)}' for x in xticks], fontsize=8,
                       fontfamily='monospace')
    ax.set_xlabel('Time (ns)', fontsize=11, fontfamily='monospace')
    ax.set_yticks([])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', color=C_GRID, linewidth=0.5, alpha=0.5, zorder=0)

    # ── Title ────────────────────────────────────────────────────────
    title = (f'6502 Bus Multiplexer Timing \u2014 {freq_mhz} MHz '
             f'({period:.0f} ns/cycle)')
    subtitle = ('Address + data multiplexed on 8 shared pins '
                'within one CPU cycle \u2014 no speed penalty')
    ax.set_title(f'{title}\n{subtitle}', fontsize=13, fontweight='bold',
                 fontfamily='monospace', pad=15, linespacing=1.6)

    # ── Legend ────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(facecolor=C_MUX_A_F, edgecolor=C_MUX_A,
                       linewidth=1.2, label='Address on mux pins'),
        mpatches.Patch(facecolor=C_DATA_R_F, edgecolor=C_DATA_R,
                       linewidth=1.2, label='Read data on mux pins'),
        mpatches.Patch(facecolor=C_DATA_W_F, edgecolor=C_DATA_W,
                       linewidth=1.2, label='Write data on mux pins'),
        mpatches.Patch(facecolor='#e8e8e8', edgecolor='#9ca3af',
                       linewidth=1.2, label='Transitioning / not yet valid',
                       hatch='///'),
    ]
    ax.legend(handles=legend_items, loc='upper right', fontsize=8.5,
              framealpha=0.92, edgecolor='#d1d5db', fancybox=True,
              prop={'family': 'monospace'})

    plt.tight_layout()

    if filename:
        plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"Saved: {filename}")
    else:
        plt.show()
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='m6502 bus multiplexer timing diagram generator')
    parser.add_argument('--freq', type=float, default=1.0,
                        help='CPU clock frequency in MHz (default: 1.0)')
    parser.add_argument('--cycles', type=int, default=2,
                        help='Number of CPU cycles to show (default: 2)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output PNG filename (default: display)')

    args = parser.parse_args()

    t = get_timing(args.freq)
    print(f"CPU: {args.freq} MHz  ({t['tCYC']:.0f} ns/cycle)")
    print(f"  tADS  = {t['tADS']:.0f} ns  (addr setup before posedge PHI2)")
    print(f"  tACC  = {t['tACC']:.0f} ns  (memory access time max)")
    print(f"  tDSU  = {t['tDSU']:.0f} ns  (data setup before negedge PHI2)")
    print(f"  tMDS  = {t['tMDS']:.0f} ns  (write data setup after posedge PHI2)")
    print(f"  tHA   = {t['tHA']:.0f} ns  (addr hold after negedge PHI2)")

    generate_diagram(
        freq_mhz=args.freq,
        num_cycles=args.cycles,
        filename=args.output,
    )


if __name__ == '__main__':
    main()
