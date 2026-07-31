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

"""EPROM Burner dialog -- dump / load RAM ranges to/from .rom files.
tkinter port of beboputer_v7/dialogs/eprom_burner.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from beboputer_v7.paths import default_open_dir as _default_open_dir, \
        default_save_dir as _default_save_dir
except Exception:  # pragma: no cover
    def _default_open_dir() -> str:
        return str(Path.home())

    def _default_save_dir() -> str:
        d = Path.home() / "beboputer"
        d.mkdir(exist_ok=True)
        return str(d)

try:
    from beboputer_v7.styles import C
except ImportError:  # pragma: no cover
    C = {"lcd_bg": "#c8f0c8", "btn_bdr": "#888888", "green_mid": "#004d00"}


class EpromBurner(tk.Toplevel):
    """A fresh EpromBurner is created every time it's opened (Tools menu),
    same as the Qt version -- no state persists between opens."""

    def __init__(self, parent, cpu, on_ram_changed=None, calculator=None):
        super().__init__(parent)
        self.cpu = cpu
        self._on_ram_changed = on_ram_changed
        self._calculator = calculator  # for the "must be powered on" gate below
        self.title("EPROM Burner")
        self.resizable(False, False)
        self.configure(bg="#c0c0c0")
        self._build()
        self.transient(parent)

    def _build(self):
        root = tk.Frame(self, bg="#c0c0c0", padx=12, pady=12)
        root.pack(fill="both", expand=True)

        field_kwargs = dict(
            bg=C["lcd_bg"], fg="#000000", relief="sunken", bd=2,
            font=("Courier New", 15, "bold"),
        )

        form = tk.Frame(root, bg="#c0c0c0")
        form.pack(fill="x", pady=(0, 8))
        tk.Label(form, text="File Name:", bg="#c0c0c0", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="e", pady=3)
        self.file_var = tk.StringVar()
        tk.Entry(form, textvariable=self.file_var, width=32, **field_kwargs).grid(
            row=0, column=1, sticky="w", pady=3, padx=6)

        tk.Label(form, text="Start Address $", bg="#c0c0c0", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky="e", pady=3)
        self.start_var = tk.StringVar(value="0000")
        tk.Entry(form, textvariable=self.start_var, width=10, **field_kwargs).grid(
            row=1, column=1, sticky="w", pady=3, padx=6)

        tk.Label(form, text="End Address $", bg="#c0c0c0", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky="e", pady=3)
        self.end_var = tk.StringVar(value="00FF")
        tk.Entry(form, textvariable=self.end_var, width=10, **field_kwargs).grid(
            row=2, column=1, sticky="w", pady=3, padx=6)

        avail_box = tk.LabelFrame(
            root, text="Available System EPROMs", bg="#c0c0c0",
            font=("Arial", 12, "bold"),
        )
        avail_box.pack(fill="x", pady=(0, 8))
        columns = ("file", "size")
        self.eprom_tree = ttk.Treeview(avail_box, columns=columns, show="headings", height=4)
        self.eprom_tree.heading("file", text="File")
        self.eprom_tree.heading("size", text="Size")
        self.eprom_tree.column("file", width=280)
        self.eprom_tree.column("size", width=100)
        self.eprom_tree.pack(fill="x", padx=4, pady=4)

        btn_row = tk.Frame(root, bg="#c0c0c0")
        btn_row.pack(fill="x", pady=(0, 6))
        for label, cmd in [
            ("Browse...", self._browse), ("Burn ROM", self._burn),
            ("Load ROM", self._load_rom), ("Swap ROMs", self._swap),
            ("Cancel", self.destroy),
        ]:
            tk.Button(btn_row, text=label, font=("Arial", 12), command=cmd).pack(
                side="left", padx=3)

        self.status_lbl = tk.Label(
            root, text="", bg="#c0c0c0", fg=C["green_mid"], font=("Arial", 12), anchor="w",
        )
        self.status_lbl.pack(fill="x")

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select ROM file", initialdir=_default_open_dir(),
            filetypes=[("ROM Files", "*.rom *.bin"), ("All Files", "*.*")],
        )
        if not path:
            return
        self.file_var.set(path)
        try:
            size = f"{os.path.getsize(path)} B"
        except OSError:
            size = ""
        self.eprom_tree.insert("", "end", values=(os.path.basename(path), size))

    def _burn(self):
        path = self.file_var.get()
        if not path:
            path = filedialog.asksaveasfilename(
                title="Burn to File", initialdir=_default_save_dir(),
                defaultextension=".rom",
                filetypes=[("ROM Files", "*.rom"), ("All Files", "*.*")],
            )
            if not path:
                return
            self.file_var.set(path)
        try:
            start = int(self.start_var.get(), 16) & 0xFFFF
            end = int(self.end_var.get(), 16) & 0xFFFF
            if end < start:
                end = start
            data = bytes(self.cpu.ram[start:end + 1])
            with open(path, "wb") as f:
                f.write(data)
            self.status_lbl.configure(text=f"Burned ${start:04X}-${end:04X} -> {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Burn Error", str(e), parent=self)

    def _load_rom(self):
        # Same gate as File > Load RAM (BebopMain._load_file()): the
        # calculator must be switched ON before a program can be loaded.
        calc = self._calculator
        if calc is None or not calc.powered:
            messagebox.showwarning(
                "Calculator Off",
                "The calculator must be switched ON before you can load a "
                "ROM file.\n\nPress the On/Off button on the calculator, "
                "then try again.",
                parent=self,
            )
            return
        path = self.file_var.get()
        if not path:
            path = filedialog.askopenfilename(
                title="Load ROM", initialdir=_default_open_dir(),
                filetypes=[("ROM Files", "*.rom *.bin"), ("All Files", "*.*")],
            )
            if not path:
                return
            self.file_var.set(path)
        try:
            start = int(self.start_var.get(), 16) & 0xFFFF
            with open(path, "rb") as f:
                data = f.read()
            for i, b in enumerate(data):
                if start + i >= 0x10000:
                    break
                self.cpu.ram[start + i] = b
                self.cpu.ram_touched[start + i] = 1
            self.status_lbl.configure(
                text=f"Loaded {len(data)}B at ${start:04X} from {os.path.basename(path)}"
            )
            if self._on_ram_changed is not None:
                self._on_ram_changed()
        except Exception as e:
            messagebox.showerror("Load Error", str(e), parent=self)

    def _swap(self):
        try:
            start = int(self.start_var.get(), 16) & 0xFFFF
            end = int(self.end_var.get(), 16) & 0xFFFF
            mid = (start + end) // 2 + 1
            for i in range(end - mid + 1):
                a, b = self.cpu.ram[start + i], self.cpu.ram[mid + i]
                self.cpu.ram[start + i], self.cpu.ram[mid + i] = b, a
                ta, tb = self.cpu.ram_touched[start + i], self.cpu.ram_touched[mid + i]
                self.cpu.ram_touched[start + i], self.cpu.ram_touched[mid + i] = tb, ta
            self.status_lbl.configure(
                text=f"Swapped ${start:04X}-${mid - 1:04X} <-> ${mid:04X}-${end:04X}"
            )
            if self._on_ram_changed is not None:
                self._on_ram_changed()
        except Exception as e:
            messagebox.showerror("Swap Error", str(e), parent=self)
