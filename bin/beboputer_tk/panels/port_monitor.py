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

"""I/O Ports Display -- memory-mapped I/O monitor.

tkinter port of beboputer_v7/panels/port_monitor.py, kept
behaviorally identical -- same three tracked addresses, same
edit-the-button-value-by-hand escape hatch, same "why refresh() reads
_last_button_val instead of ram[ADDR_BUTTONS] directly" reasoning
(the main window's read-clear strobe wipes that byte back to $FF the
instant the CPU reads it, so on_key_press() has to capture it first).

    $F031   Output to Main Display      (character to print)
    $F032   Output to LED row           (binary bit pattern)
    $F011   Input from Buttons          (current + previous value)
"""

from __future__ import annotations

import tkinter as tk

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"red": "#cc0000", "blue": "#000080", "lcd_bg": "#c8f0c8", "btn_bdr": "#888888"}

ADDR_DISPLAY = 0xF031
ADDR_LEDS    = 0xF032
ADDR_BUTTONS = 0xF011


def _value_box(parent, title):
    box = tk.LabelFrame(
        parent, text=title, fg=C["red"], font=("Arial", 11, "bold"),
        bg="#c0c0c0", bd=2, relief="groove", padx=5, pady=4,
    )
    lbl = tk.Label(
        box, text="---", bg=C["lcd_bg"], fg="#000000",
        font=("Courier New", 16, "bold"), relief="sunken", bd=2,
        width=8, anchor="center",
    )
    lbl.pack(fill="x")
    return box, lbl


def _addr_label(parent, text):
    return tk.Label(
        parent, text=text, fg=C["blue"], bg="#c0c0c0",
        font=("Arial", 11, "bold"),
    )


class PortMonitor(tk.Frame):
    def __init__(self, parent, cpu, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self.cpu = cpu
        self._prev_button_val = None
        self._last_button_val = 0  # tracks previous port value across refresh() calls
        self._build()

    def _build(self):
        outer = tk.Frame(self, bg="#c0c0c0")
        outer.pack(fill="both", expand=True, padx=8, pady=6)
        for c in (1, 2):
            outer.grid_columnconfigure(c, weight=1)

        _addr_label(outer, "$F031").grid(row=0, column=0, padx=(0, 4))
        disp_box, self.lbl_display_hex = _value_box(outer, "O/P to Main Display")
        char_box, self.lbl_display_char = _value_box(outer, "Character etc")
        disp_box.grid(row=0, column=1, padx=4, pady=3, sticky="ew")
        char_box.grid(row=0, column=2, padx=4, pady=3, sticky="ew")

        _addr_label(outer, "$F032").grid(row=1, column=0, padx=(0, 4))
        led_box, self.lbl_led_hex = _value_box(outer, "O/P to LED's")
        bin_box, self.lbl_led_bin = _value_box(outer, "Binary")
        led_box.grid(row=1, column=1, padx=4, pady=3, sticky="ew")
        bin_box.grid(row=1, column=2, padx=4, pady=3, sticky="ew")

        bracket = tk.Label(
            outer, text="$F011", fg=C["blue"], bg="#c0c0c0",
            font=("Arial", 11, "bold"),
            highlightbackground=C["blue"], highlightthickness=1,
        )
        bracket.grid(row=2, column=0, rowspan=2, padx=(0, 4), sticky="ns")

        cur_box = tk.LabelFrame(
            outer, text="I/P from Buttons", fg=C["red"], font=("Arial", 11, "bold"),
            bg="#c0c0c0", bd=2, relief="groove", padx=5, pady=4,
        )
        self.btn_edit = tk.Entry(
            cur_box, justify="center", font=("Courier New", 16, "bold"),
            bg=C["lcd_bg"], fg="#000000", relief="sunken", bd=2, width=8,
        )
        self.btn_edit.insert(0, "$00")
        self.btn_edit.pack(fill="x")
        self.btn_edit.bind("<Return>", self._on_button_changed)
        self.btn_edit.bind("<FocusOut>", self._on_button_changed)
        cur_box.grid(row=2, column=1, padx=4, pady=3, sticky="ew")

        ann_box, self.lbl_btn_ann = _value_box(outer, "Annotation")
        ann_box.grid(row=2, column=2, padx=4, pady=3, sticky="ew")

        old_box, self.lbl_old_btn = _value_box(outer, "Old I/P from Button")
        old_box.grid(row=3, column=1, padx=4, pady=3, sticky="ew")

        old_ann_box, self.lbl_old_btn_ann = _value_box(outer, "Annotation")
        old_ann_box.grid(row=3, column=2, padx=4, pady=3, sticky="ew")

        self.lbl_display_hex.config(text="$XX")
        self.lbl_display_char.config(text="---")
        self.lbl_led_hex.config(text="---")
        self.lbl_led_bin.config(text="XXXXXXXX")
        self.lbl_btn_ann.config(text="---")
        self.lbl_old_btn.config(text="---")
        self.lbl_old_btn_ann.config(text="---")

    def _on_button_changed(self, event=None):
        txt = self.btn_edit.get().strip().lstrip("$")
        if txt.lower().startswith("0x"):
            txt = txt[2:]
        try:
            val = int(txt, 16) & 0xFF
        except ValueError:
            return
        prev = self.cpu.ram[ADDR_BUTTONS]
        if prev != val:
            self._prev_button_val = prev
        self.cpu.ram[ADDR_BUTTONS] = val
        self.btn_edit.delete(0, "end")
        self.btn_edit.insert(0, "$%02X" % val)
        self.refresh()

    @staticmethod
    def _char_annot(b):
        if 32 <= b < 127:
            return "'" + chr(b) + "'"
        if 0x00 <= b <= 0x09:
            return "'" + str(b) + "'"          # raw digit
        if 0x0A <= b <= 0x0F:
            return "'" + chr(b - 0x0A + ord('A')) + "'"  # raw hex letter
        named = {0x07: "BEL", 0x08: "BS", 0x09: "TAB", 0x0D: "CR", 0x1B: "ESC"}
        return named.get(b, "---")

    def reset(self):
        """Clear all displayed values back to initial state (called on CPU reset)."""
        self._prev_button_val = None
        self._last_button_val = 0xFF  # idle sentinel
        self.lbl_display_hex.config(text="$00")
        self.lbl_display_char.config(text="---")
        self.lbl_led_hex.config(text="$00")
        self.lbl_led_bin.config(text="00000000")
        self.btn_edit.delete(0, "end")
        self.btn_edit.insert(0, "$FF")
        self.lbl_btn_ann.config(text="---")
        self.lbl_old_btn.config(text="---")
        self.lbl_old_btn_ann.config(text="---")

    def on_key_press(self, val):
        """Called by the $F011 write hook the moment a button is written.
        Captures the value before the read-clear strobe wipes ram[$F011]."""
        if val != self._last_button_val:
            self._prev_button_val = self._last_button_val
            self._last_button_val = val
        if self.focus_get() is not self.btn_edit:
            self.btn_edit.delete(0, "end")
            self.btn_edit.insert(0, "$%02X" % val)
        self.lbl_btn_ann.config(text=self._char_annot(val))
        if self._prev_button_val is not None:
            self.lbl_old_btn.config(text="$%02X" % self._prev_button_val)
            self.lbl_old_btn_ann.config(text=self._char_annot(self._prev_button_val))

    def refresh(self):
        ram = self.cpu.ram
        d = ram[ADDR_DISPLAY]
        self.lbl_display_hex.config(text="$%02X" % d)
        self.lbl_display_char.config(text=self._char_annot(d))
        led = ram[ADDR_LEDS]
        self.lbl_led_hex.config(text="$%02X" % led)
        self.lbl_led_bin.config(text=format(led, "08b"))
        # Button section: use _last_button_val set by on_key_press() -- do NOT
        # read ram[ADDR_BUTTONS] directly, same reasoning as the Qt version:
        # the read-clear strobe resets it to $FF the instant the CPU reads it.
        cur = self._last_button_val
        if self.focus_get() is not self.btn_edit:
            self.btn_edit.delete(0, "end")
            self.btn_edit.insert(0, "$%02X" % cur)
        self.lbl_btn_ann.config(text=self._char_annot(cur))
        if self._prev_button_val is None:
            self.lbl_old_btn.config(text="---")
            self.lbl_old_btn_ann.config(text="---")
        else:
            self.lbl_old_btn.config(text="$%02X" % self._prev_button_val)
            self.lbl_old_btn_ann.config(text=self._char_annot(self._prev_button_val))
