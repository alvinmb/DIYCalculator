"""
memory_grid.py -- tkinter prototype of Memory Walker's 256-row BP/STEP/
ADDRESS/DATA table (panels/memory_walker.py in the Qt app).

The hard part isn't the data, it's the per-CELL coloring: within one row,
the BP cell, STEP cell, ADDRESS cell, and DATA cell can each need a
*different* color at the same time (e.g. the PC row shows amber STEP +
green-bright ADDRESS + amber DATA, and independently the BP cell is red
only if that address also has a breakpoint). ttk.Treeview only colors
whole rows via tags, not individual cells, so it can't reproduce this.
A grid of 256*4 = 1024 individual Label widgets could do it, but
recreating/restyling a thousand widgets on every single-step (which
happens on every CPU instruction during a run) is the real question
mark -- that's what this prototype measures.

The approach used here: one tk.Text widget, monospaced, with the whole
grid as text and per-substring color tags (foreground only -- Text tags
support background too, but the Qt version only recolors text, not
cell backgrounds, so this matches it exactly). Column positions are
fixed-width, so a click's (row, col) is recovered from the Text index
tkinter already gives us -- no per-cell widgets, so redrawing all 256
rows is one .delete()+.insert() pass rather than 1024 widget updates.

Run this file directly for a live demo against a fake CPU that steps
through a tiny counting loop -- click STEP to single-step, click BP to
toggle a breakpoint, click "Run" to run to the next breakpoint.
"""

from __future__ import annotations

import tkinter as tk
import time


# Same palette as bin/beboputer_v7/styles.py's C dict, so a real port
# would just import that instead of redefining it here.
C = {
    "green":      "#006400",
    "green_mid":  "#004d00",
    "amber":      "#8b6914",
    "red":        "#cc0000",
    "grey":       "#606060",
    "bg":         "#f5f5f0",
}

ROWS = 256
COL_BP_W, COL_STEP_W, COL_ADDR_W, COL_DATA_W = 4, 4, 8, 6
# fixed character offsets within each line, so a click's column index
# in the Text widget maps directly onto (BP | STEP | ADDR | DATA)
BP_START, BP_END       = 0, COL_BP_W
STEP_START, STEP_END   = BP_END, BP_END + COL_STEP_W
ADDR_START, ADDR_END   = STEP_END, STEP_END + COL_ADDR_W
DATA_START, DATA_END   = ADDR_END, ADDR_END + COL_DATA_W


class MemoryGrid(tk.Frame):
    """Scrollable 256-row memory dump: BP | STEP | ADDRESS | DATA.

    Parameters
    ----------
    get_byte(addr) -> int
    get_touched(addr) -> bool
        Whether that byte has ever been written (undefined RAM shows "XX").
    get_pc() -> int
    on_toggle_bp(addr), on_step()
        Called when the user clicks the BP or STEP column.
    """

    def __init__(self, parent, get_byte, get_touched, get_pc,
                 on_toggle_bp, on_step, base=0x0000, visible_rows=24):
        super().__init__(parent)
        self.get_byte = get_byte
        self.get_touched = get_touched
        self.get_pc = get_pc
        self.on_toggle_bp = on_toggle_bp
        self.on_step = on_step
        self.base = base
        self.breakpoints: set[int] = set()

        header = tk.Label(
            self, text=f"{'BP':<{COL_BP_W}}{'ST':<{COL_STEP_W}}"
                       f"{'ADDR':<{COL_ADDR_W}}{'DATA':<{COL_DATA_W}}",
            font=("Courier New", 11, "bold"), anchor="w", bg="#dcdcdc",
        )
        header.pack(fill="x")

        text_frame = tk.Frame(self)
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            text_frame, font=("Courier New", 11), width=22, height=visible_rows,
            bg=C["bg"], cursor="arrow", wrap="none", state="disabled",
            highlightthickness=0, bd=1, relief="sunken",
        )
        vsb = tk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set)
        self.text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for name, color in (
            ("addr_normal", C["green_mid"]), ("addr_pc", C["green"]),
            ("data_normal", "#000000"), ("data_undefined", C["grey"]),
            ("data_pc", C["amber"]),
            ("bp_set", C["red"]), ("step_pc", C["amber"]), ("step_idle", C["grey"]),
        ):
            self.text.tag_configure(name, foreground=color)

        self.text.tag_configure("row_pc_bg", background="#fff2cc")

        self.text.bind("<Button-1>", self._on_click)

        self._last_refresh_ms = 0.0
        self.refresh()

    # -- rendering ------------------------------------------------------------

    def refresh(self):
        t0 = time.perf_counter()
        pc = self.get_pc()

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        for row in range(ROWS):
            addr = (self.base + row) & 0xFFFF
            is_pc = addr == pc
            touched = self.get_touched(addr)
            b = self.get_byte(addr)

            bp_char = "●" if addr in self.breakpoints else " "
            step_char = "▶" if is_pc else "·"
            addr_str = f"${addr:04X}"
            data_str = f"{b:02X}" if touched else "XX"

            line = (f"{bp_char:<{COL_BP_W}}{step_char:<{COL_STEP_W}}"
                    f"{addr_str:<{COL_ADDR_W}}{data_str:<{COL_DATA_W}}\n")
            line_start = f"{row + 1}.0"
            self.text.insert("end", line)

            def span(col_start, col_end):
                return (f"{row + 1}.{col_start}", f"{row + 1}.{col_end}")

            if addr in self.breakpoints:
                s, e = span(BP_START, BP_END)
                self.text.tag_add("bp_set", s, e)

            s, e = span(STEP_START, STEP_END)
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

        self.text.configure(state="disabled")
        self._last_refresh_ms = (time.perf_counter() - t0) * 1000

    # -- clicking ---------------------------------------------------------------

    def _on_click(self, event):
        index = self.text.index(f"@{event.x},{event.y}")
        line_str, col_str = index.split(".")
        row = int(line_str) - 1
        col = int(col_str)
        if not (0 <= row < ROWS):
            return "break"
        addr = (self.base + row) & 0xFFFF
        if BP_START <= col < BP_END:
            self.on_toggle_bp(addr)
        elif STEP_START <= col < STEP_END:
            self.on_step()
        return "break"  # swallow the click so Text doesn't move its cursor

    def toggle_bp_local(self, addr):
        """Default BP bookkeeping a real port would delegate to the CPU
        panel controller instead -- kept here only so the demo below is
        self-contained."""
        if addr in self.breakpoints:
            self.breakpoints.discard(addr)
        else:
            self.breakpoints.add(addr)
        self.refresh()


# ── demo: fake CPU running a tiny counting loop ─────────────────────────────

class _FakeCPU:
    """Minimal stand-in so this file has no dependency on the real cpu.py --
    just enough state (ram, ram_touched, pc) to drive the grid."""

    def __init__(self):
        self.ram = bytearray(65536)
        self.ram_touched = bytearray(65536)
        self.pc = 0x4000
        # seed a few bytes as "already touched", like a loaded program
        program = bytes([0x90, 0x00, 0x99, 0x41, 0xEB, 0x91, 0xF0, 0x11])
        for i, b in enumerate(program):
            self.ram[0x4000 + i] = b
            self.ram_touched[0x4000 + i] = 1

    def step(self):
        # not a real CPU -- just advances pc through the seeded bytes and
        # writes an incrementing counter to $4100 so DATA visibly changes
        self.pc = 0x4000 + ((self.pc - 0x4000 + 1) % 8)
        addr = 0x4100
        self.ram[addr] = (self.ram[addr] + 1) & 0xFF
        self.ram_touched[addr] = 1


def _demo():
    root = tk.Tk()
    root.title("Memory Walker grid prototype")
    root.geometry("420x560")

    cpu = _FakeCPU()

    grid_holder = {}

    def get_byte(addr):
        return cpu.ram[addr]

    def get_touched(addr):
        return bool(cpu.ram_touched[addr])

    def get_pc():
        return cpu.pc

    def on_toggle_bp(addr):
        grid.toggle_bp_local(addr)

    def on_step():
        cpu.step()
        grid.refresh()
        status.config(text=f"last refresh: {grid._last_refresh_ms:.2f} ms  "
                            f"(256 rows, full redraw)")

    controls = tk.Frame(root)
    controls.pack(fill="x", padx=6, pady=6)
    tk.Button(controls, text="Step", command=on_step).pack(side="left")

    def run_10():
        for _ in range(10):
            cpu.step()
        grid.refresh()
        status.config(text=f"last refresh: {grid._last_refresh_ms:.2f} ms  "
                            f"(after 10 steps, full redraw)")

    tk.Button(controls, text="Step x10", command=run_10).pack(side="left", padx=4)

    status = tk.Label(root, text="", anchor="w")
    status.pack(fill="x", padx=6)

    grid = MemoryGrid(root, get_byte, get_touched, get_pc, on_toggle_bp, on_step,
                       base=0x4000, visible_rows=28)
    grid.pack(fill="both", expand=True, padx=6, pady=6)
    grid_holder["grid"] = grid

    status.config(text=f"last refresh: {grid._last_refresh_ms:.2f} ms  (initial)")

    root.mainloop()


if __name__ == "__main__":
    _demo()
