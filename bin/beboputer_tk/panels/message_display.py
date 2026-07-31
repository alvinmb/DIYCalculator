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

"""Message Display -- always-on diagnostic log panel.

tkinter port of beboputer_v7/panels/message_display.py. Same behavior:
a read-only, dark-themed scrolling log with one public method,
message(text), that appends a line and auto-scrolls to the bottom.
Completely independent of calculator power state -- always active.
"""

from __future__ import annotations

import tkinter as tk


class MessageDisplay(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1c1c1c", **kwargs)

        hdr = tk.Label(
            self, text="▸ Message Display", bg="#2e2e2e", fg="#aaaaaa",
            font=("Arial", 12), anchor="w", padx=6, pady=2,
        )
        hdr.pack(side="top", fill="x")

        text_frame = tk.Frame(self, bg="#1c1c1c")
        text_frame.pack(side="top", fill="both", expand=True)

        self.log = tk.Text(
            text_frame, bg="#1c1c1c", fg="#c8c8c8", insertbackground="#c8c8c8",
            font=("Courier New", 14), bd=0, highlightthickness=0,
            wrap="word", state="disabled",
        )
        vsb = tk.Scrollbar(text_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=vsb.set)
        self.log.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def message(self, text: str):
        """Append a line to the log. Always visible regardless of power state."""
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
