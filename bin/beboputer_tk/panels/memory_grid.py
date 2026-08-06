# Copyright (c) 2026 Alvin Brown & Clive Maxfield
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""memory_grid.py -- the 256-row BP/STEP/ADDRESS/DATA table widget at the
heart of Memory Walker.

Promoted from prototypes/tkinter_migration/memory_grid.py (Phase 0 spike,
verified at ~9.3ms/refresh for a full 256-row redraw -- comfortably fast
enough for single-stepping and Run's refresh cadence). Two changes from
the spike version:

  - Breakpoints and the view's base address are no longer owned by this
    widget (the spike's toggle_bp_local()/self.base were a demo
    convenience). They're owned by MemoryWalker instead, matching the Qt
    panel's self._breakpoints/self._base -- so main_window.py can inspect
    mem_walker._breakpoints directly for Run's breakpoint check, the same
    way beboputer_v7.main_window._run_tick() does. This widget just reads
    them through get_base()/is_bp() callables.
  - Added scroll_to_offset(), matching Qt's QTableWidget.scrollToItem()
    call in highlight_pc() -- keeps the ▶ PC marker in view as it moves.

Rendering approach (why not ttk.Treeview or 1,024 individual Label
widgets -- see the spike's original docstring for the full reasoning):
one monospaced tk.Text widget, the whole grid as plain text, per-
substring color tags at fixed character-column offsets so a click's
(row, col) is recovered directly from the Text index tkinter already
provides.
"""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {
        "green": "#006400", "green_mid": "#004d00", "amber": "#8b6914",
        "red": "#cc0000", "grey": "#606060", "bg": "#f5f5f0",
        "lcd_bg": "#c8f0c8",
    }

ROWS = 256
# DATA is auto-sized to its real content (max(header, widest value) +
# a 2-space separator gap: "DATA"/"FF" -> max(4,2)+2 = 6). BP and STEP
# are set equal to ADDR's width instead of their own auto-sized value
# -- a deliberate visual choice (all three "marker" columns read as one
# consistent width) rather than the tightest-possible fit.
COL_ADDR_W = 7  # max(4,5)+2 = 7, from "ADDR" vs. "$FFFF"
COL_BP_W = COL_STEP_W = COL_ADDR_W
COL_DATA_W = 6

# Column-separator "|" characters -- one between each pair of adjacent
# fields (3 total: BP|STEP|ADDR|DATA), drawn via a plain grey-foreground
# tag on a literal character rather than tk.Text tag borderwidth/relief.
# The border/relief route was prototyped first and rejected: Tk merges
# a tag's relief-bordered regions across *all* lines that share that
# tag into one contiguous shape (confirmed via screenshot -- the BP
# column's border became a single tall blob spanning many rows instead
# of a per-row box), and relief only renders at all when the tag also
# sets -background, which would have meant overriding the existing
# per-cell foreground/background colour tags. Literal separator
# characters have neither failure mode and stay exactly in step with
# the existing character-column offset math everywhere else in this
# file.
SEP_W = 1
BP_START, BP_END = 0, COL_BP_W
SEP1_COL = BP_END
STEP_START = SEP1_COL + SEP_W
STEP_END = STEP_START + COL_STEP_W
SEP2_COL = STEP_END
ADDR_START = SEP2_COL + SEP_W
ADDR_END = ADDR_START + COL_ADDR_W
SEP3_COL = ADDR_END
DATA_START = SEP3_COL + SEP_W
DATA_END = DATA_START + COL_DATA_W

# BP/STEP glyphs (●/▶/·) render 3pt larger than the rest of the row.
# Earlier this tagged the glyph's WHOLE padded field (all COL_BP_W/
# COL_STEP_W characters, including the surrounding blank spaces) with
# the bigger font -- but a monospace font's characters are wider at
# 23pt than at 20pt, so a "7-char" BP/STEP field at 23pt is physically
# wider on screen than the header's 7-char BP/STEP field at 20pt. That
# extra width (x2, for both BP and STEP) accumulated and pushed every
# column after it -- ADDR, DATA -- visibly rightward of where the
# header expected them. Now only the single glyph character itself
# (found at the centered offset `_center_offset()` puts it, matching
# Python's `:^` format spec) gets the bigger font; the surrounding
# padding spaces stay at the base 20pt size, so each field's total
# character-cell width tracks the header's 20pt-based math almost
# exactly (residual: one character's worth of 23pt-vs-20pt width
# difference per field, not the whole field's).
# Bold: header and data body share this exact tuple (see the class's
# tk.Label/tk.Text construction below) so the "make headers bold"
# request can't reopen the header/data-drift bug above -- a bold vs.
# regular weight split is the previously-fixed root cause, so both
# widgets are kept on the identical bold tuple rather than only
# bolding the header.
_BASE_FONT_SIZE = 20
BASE_FONT = ("Courier New", _BASE_FONT_SIZE, "bold")
SYMBOL_FONT = ("Courier New", _BASE_FONT_SIZE + 3, "bold")


def _center_offset(width: int) -> int:
    """Index of a single centered character within an f'{c:^{width}}'
    field -- must match str.format's own centering rule exactly."""
    return (width - 1) // 2


BP_GLYPH_COL = BP_START + _center_offset(COL_BP_W)
STEP_GLYPH_COL = STEP_START + _center_offset(COL_STEP_W)

# Exact character span of the ADDR/DATA *value* text within its
# (wider, centered) field -- e.g. "$0005" (5 chars) inside a 7-char
# ADDR field, "05" (2 chars) inside a 6-char DATA field. Both value
# strings are fixed-length ("$" + 4 hex digits; 2 hex digits), so their
# centered offset is computable the same way _center_offset() derives
# a single glyph's column, just generalised to a >1-char string: Python's
# `:^width` centering puts the extra padding character on the right
# when width-len is odd, i.e. left padding is (width - len) // 2.
# Used below (see the "rowline" comment in refresh()) to keep the grey
# grid-line's colour from being overridden by addr_normal/data_normal's
# green/black -- the line is only drawn across the padding, not across
# the coloured value text itself.
_ADDR_VAL_LEN = 5  # "$FFFF"
_DATA_VAL_LEN = 2  # "FF"
ADDR_VAL_START = ADDR_START + (COL_ADDR_W - _ADDR_VAL_LEN) // 2
ADDR_VAL_END = ADDR_VAL_START + _ADDR_VAL_LEN
DATA_VAL_START = DATA_START + (COL_DATA_W - _DATA_VAL_LEN) // 2
DATA_VAL_END = DATA_VAL_START + _DATA_VAL_LEN


class MemoryGrid(tk.Frame):
    """Scrollable 256-row memory dump: BP | STEP | ADDRESS | DATA.

    Parameters
    ----------
    get_byte(addr) -> int
    get_touched(addr) -> bool
        Undefined (never-written) RAM shows "XX", matching real hardware
        where power-on RAM contents are indeterminate.
    get_pc() -> int
    get_base() -> int
        Absolute RAM address shown in row 0.
    is_bp(addr) -> bool
    on_toggle_bp(addr), on_step()
        Called when the user clicks the BP or STEP column.
    """

    def __init__(self, parent, get_byte, get_touched, get_pc, get_base,
                 is_bp, on_toggle_bp, on_step, visible_rows=20, **kwargs):
        super().__init__(parent, **kwargs)
        self.get_byte = get_byte
        self.get_touched = get_touched
        self.get_pc = get_pc
        self.get_base = get_base
        self.is_bp = is_bp
        self.on_toggle_bp = on_toggle_bp
        self.on_step = on_step

        col_total = DATA_END  # includes the 3 single-char "|" separators

        # bd/highlightthickness/padx/pady are set explicitly and
        # identically on the header Label and the Text widget below --
        # they default similarly but not necessarily *identically*
        # across platforms/themes, and any difference between the two
        # shifts the header text sideways relative to the data columns
        # beneath it even though both use the exact same COL_*_W
        # character counts. relief differs (flat vs. sunken) but that's
        # just shading of the same reserved 1px border, not extra width.
        HDR_TXT_BD, HDR_TXT_PADX, HDR_TXT_PADY = 1, 1, 1

        # Header uses the exact same font tuple as the data body
        # (BASE_FONT, now bold per the "make headers bold" request) --
        # a weight split between the two isn't guaranteed to share
        # identical character advance width on every platform, which
        # would drift the header sideways relative to the data columns
        # beneath it, worse for later columns as the per-character
        # difference accumulates. So the body is bolded too instead of
        # only the header.
        header = tk.Label(
            self, text=f"{'BP':^{COL_BP_W}}|{'STEP':^{COL_STEP_W}}|"
                       f"{'ADDR':^{COL_ADDR_W}}|{'DATA':^{COL_DATA_W}}",
            font=BASE_FONT, anchor="w", bg="#dcdcdc",
            bd=HDR_TXT_BD, relief="flat", highlightthickness=0,
            padx=HDR_TXT_PADX, pady=HDR_TXT_PADY,
        )
        header.pack(fill="x")

        text_frame = tk.Frame(self)
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            text_frame, font=BASE_FONT, width=col_total, height=visible_rows,
            # Same mint LCD green as the Assembler/Editor and Disassembler
            # windows (LCD_BG = "#c8f0c8" in those panels) -- was the
            # generic system-grey "bg" colour before, which made Memory
            # Walker's table look like an unrelated, plainer widget next
            # to the other text-based panels.
            bg=C.get("lcd_bg", "#c8f0c8"), cursor="arrow", wrap="none", state="disabled",
            highlightthickness=0, bd=HDR_TXT_BD, relief="sunken",
            padx=HDR_TXT_PADX, pady=HDR_TXT_PADY,
        )
        vsb = tk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set)
        self.text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for name, color in (
            ("addr_normal", C["green_mid"]), ("addr_pc", C["green"]),
            ("data_normal", "#000000"), ("data_undefined", C["grey"]),
            ("data_pc", C["amber"]),
        ):
            self.text.tag_configure(name, foreground=color)

        # BP/STEP tags additionally carry the larger SYMBOL_FONT --
        # bp_idle is new (the "no breakpoint here" case previously went
        # untagged, at the base font size; now it's tagged too so the
        # whole column is consistently sized whether or not a
        # breakpoint dot is showing).
        for name, color in (
            ("bp_set", C["red"]), ("bp_idle", C["grey"]),
            ("step_pc", C["amber"]), ("step_idle", C["grey"]),
        ):
            self.text.tag_configure(name, foreground=color, font=SYMBOL_FONT)

        self.text.tag_configure("row_pc_bg", background="#fff2cc")

        # Grid lines: "sep" colours the literal "|" column-separator
        # characters inserted between fields (see the SEP_W/SEP*_COL
        # comment above); "rowline" underlines each row to form a
        # horizontal rule beneath it, in a muted dark grey.
        #
        # "rowline" DOES set its own foreground (unlike a first attempt
        # that left it unset) -- Tk's Text tag underline colour is tied
        # to whichever tag actually supplies -foreground for a given
        # character, same priority-cascade as the text colour itself
        # (confirmed by prototyping: giving "rowline" a foreground and a
        # higher priority than addr_normal repainted the ADDR text itself
        # grey, not just its underline -- there's no way to set an
        # underline-only colour independent of text colour in tk.Text).
        # So instead of covering the whole row, refresh() applies
        # "rowline" only across the padding/separator characters
        # (ADDR_VAL_START/END and DATA_VAL_START/END, plus the BP/STEP
        # glyph columns, are deliberately excluded) -- the grey line runs
        # continuously under BP/STEP's padding and the "|" separators,
        # with small gaps exactly where the coloured ADDR/DATA value text
        # and BP/STEP glyphs sit, so those keep their own colour.
        self.text.tag_configure("sep", foreground="#c8c8c8")
        self.text.tag_configure("rowline", underline=True, foreground="#c8c8c8")

        self.text.bind("<Button-1>", self._on_click)

        self.refresh()

    # -- rendering ------------------------------------------------------------

    def refresh(self):
        base = self.get_base()
        pc = self.get_pc()

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        for row in range(ROWS):
            addr = (base + row) & 0xFFFF
            is_pc = addr == pc
            touched = self.get_touched(addr)
            b = self.get_byte(addr)

            bp_char = "●" if self.is_bp(addr) else " "
            step_char = "▶" if is_pc else "·"
            addr_str = f"${addr:04X}"
            data_str = f"{b:02X}" if touched else "XX"

            # All four columns center-justified (^) to match the header,
            # with a literal "|" between each pair of adjacent fields.
            line = (f"{bp_char:^{COL_BP_W}}|{step_char:^{COL_STEP_W}}|"
                    f"{addr_str:^{COL_ADDR_W}}|{data_str:^{COL_DATA_W}}\n")
            line_start = f"{row + 1}.0"
            self.text.insert("end", line)

            def span(col_start, col_end, row=row):
                return (f"{row + 1}.{col_start}", f"{row + 1}.{col_end}")

            # Font-size tag only spans the single glyph character
            # (BP_GLYPH_COL/STEP_GLYPH_COL), not the whole padded
            # field -- see the SYMBOL_FONT comment above for why.
            s, e = span(BP_GLYPH_COL, BP_GLYPH_COL + 1)
            self.text.tag_add("bp_set" if self.is_bp(addr) else "bp_idle", s, e)

            s, e = span(STEP_GLYPH_COL, STEP_GLYPH_COL + 1)
            self.text.tag_add("step_pc" if is_pc else "step_idle", s, e)

            s, e = span(ADDR_START, ADDR_END)
            self.text.tag_add("addr_pc" if is_pc else "addr_normal", s, e)

            s, e = span(DATA_START, DATA_END)
            if is_pc:
                self.text.tag_add("data_pc", s, e)
            elif not touched:
                self.text.tag_add("data_undefined", s, e)
            else:
                self.text.tag_add("data_normal", s, e)

            if is_pc:
                self.text.tag_add("row_pc_bg", line_start, f"{row + 1}.end")

            for sep_col in (SEP1_COL, SEP2_COL, SEP3_COL):
                s, e = span(sep_col, sep_col + 1)
                self.text.tag_add("sep", s, e)

            # "rowline" (muted dark grey underline) is applied only in
            # the gaps between the coloured glyph/value spans above, not
            # across them -- see the tag_configure comment for why a
            # single foreground can't be independent per-underline vs.
            # per-glyph in tk.Text (setting it across the whole row would
            # repaint the green ADDR / black-or-amber DATA text grey too).
            for s_col, e_col in (
                (0, BP_GLYPH_COL),
                (BP_GLYPH_COL + 1, STEP_GLYPH_COL),
                (STEP_GLYPH_COL + 1, ADDR_VAL_START),
                (ADDR_VAL_END, DATA_VAL_START),
                (DATA_VAL_END, DATA_END),
            ):
                s, e = span(s_col, e_col)
                self.text.tag_add("rowline", s, e)

        self.text.configure(state="disabled")

    def scroll_to_offset(self, offset):
        """Scroll so row *offset* is visible -- mirrors Qt's
        table.scrollToItem() call in MemoryWalker.highlight_pc()."""
        self.text.see(f"{offset + 1}.0")

    # -- clicking ---------------------------------------------------------------

    def _on_click(self, event):
        index = self.text.index(f"@{event.x},{event.y}")
        line_str, col_str = index.split(".")
        row = int(line_str) - 1
        col = int(col_str)
        if not (0 <= row < ROWS):
            return "break"
        addr = (self.get_base() + row) & 0xFFFF
        if BP_START <= col < BP_END:
            self.on_toggle_bp(addr)
        elif STEP_START <= col < STEP_END:
            self.on_step()
        return "break"  # swallow the click so Text doesn't move its own cursor
