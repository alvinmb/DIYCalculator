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

"""Assembler / Editor -- tkinter port of beboputer_v7/tools/compiler.py.

AssemblerRunner (compile/write-RAM/load-into-CPU logic) has zero Qt
dependency -- it's imported and reused directly from
beboputer_v7.tools.compiler rather than duplicated, same pattern as
diy_button.py's file-format helpers. Only the Qt *window* (CompilerWindow)
needed a tkinter-native replacement, which is what CompilerPanel is.

tkinter has no MDI-subwindow-with-its-own-menu-bar equivalent -- a
tk.Menu can only attach to a Toplevel/Tk root, not to an arbitrary
Frame -- so this panel's File/Edit/Insert menus are built from
tk.Menubutton + tk.Menu (a dropdown button that looks and behaves like
a menu bar entry) instead of a true attached menu bar. Functionally
equivalent; visually a row of buttons rather than a native menu strip.

Ported: New/Open/Save/Save As, Assemble, Load -> CPU, Find/Find Next/
Go to Line, Insert Directive/Instruction snippets, Insert String,
Insert File.

NOT ported: Font... (QFontDialog has no tkinter built-in equivalent,
same gap TKINTER_MIGRATION.md already flags as low-priority), Printer
Setup / Print (no tkinter printing framework -- same already-flagged
gap as the rest of the app, see TKINTER_MIGRATION.md sec 2/6).
"""

from __future__ import annotations

import os
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from beboputer_v7.tools.assembler_runner import AssemblerRunner

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


# Same "on" background as the Calculator's own LCD (panels/calculator.py's
# _DISPLAY_ON_BG) -- used for the source editor and messages text areas so
# this panel's text background matches the Calculator's display.
LCD_BG = "#c8f0c8"

_DIRECTIVE_SNIPPETS = [
    (".ORG <integer>",            "        .ORG    $4000               # start address\n"),
    ("<Label>: .BYTE <integer>",  "LABEL:  .BYTE   $00                 # reserve 1 byte\n"),
    ("<Label>: .2BYTE <integer>", "LABEL:  .2BYTE  $0000               # reserve 2 bytes\n"),
    (".4BYTE <integer>",          "        .4BYTE  $00000000           # reserve 4 bytes\n"),
    ("<Label>: .EQU <integer>",   "LABEL:  .EQU    $00                 # constant\n"),
    (".END <integer>",            "        .END    $4000               # end of program\n"),
]

# Matches main_window.py's own menu-bar font (_build_menu()'s
# MENU_FONT) -- used both for this panel's File/Edit/Insert
# Menubutton row and for its section labels ("Source (.asm)",
# "Messages"), which previously used a smaller, unrelated Arial 12.
MENU_FONT = ("Segoe UI", 15)

_INSTRUCTION_SNIPPETS = [
    ("Implied",        "        NOP                         # implied\n"),
    ("Immediate",      "        LDA     $00                 # immediate\n"),
    ("Big Immediate",  "        BLDX    $0000               # 16-bit immediate\n"),
    ("Absolute",       "        LDA     [$4000]             # direct\n"),
    ("Indexed",        "        LDA     [$4000,X]           # indexed\n"),
    ("Indirect",       "        JMP     [[$4000]]           # indirect\n"),
    ("PreIndexed",     "        LDA     [[$4000,X]]         # pre-indexed indirect\n"),
]


class CompilerPanel(tk.Frame):
    """Assembler / Editor window. All compile logic lives in AssemblerRunner."""

    def __init__(self, parent, host_main=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self._host = host_main
        self._runner = AssemblerRunner()
        self.current_path: Path | None = None
        self._find_query = ""
        self._last_bytecode: bytes | None = None

        self._build_menu_row()
        self._build_toolbar()
        self._build_editor()
        self._build_statusbar()

        if not self._runner.available:
            self._append_message(
                "WARNING: compiler_core / das.py not found.\n"
                f"Import error: {self._runner.import_error}"
            )
            self.compile_button.configure(state="disabled")

    # ------------------------------------------------------------- menu row --

    def _build_menu_row(self):
        # MENU_FONT (module-level) matches the main window's own menu
        # bar font exactly (see main_window.py's _build_menu()'s
        # MENU_FONT) -- this row used a smaller, different font
        # (Arial 12) than every other menu in the app.
        bar = tk.Frame(self, bg="#d4d0c8", bd=1, relief="raised")
        bar.pack(fill="x")

        # Menus are posted manually via tk_popup() rather than via
        # Menubutton's built-in ``menu=`` auto-post option -- see
        # main_window.py's _build_menu()._menu() for the full story: on a
        # Raspberry Pi 5, the automatic mechanism left only the first menu
        # in a bar responding to clicks at all. This panel's own
        # File/Edit/Insert row hit the exact same bug.
        #
        # Deliberately NOT pairing tk_popup() with an explicit
        # menu.grab_release() (an earlier fix here did, following the
        # commonly-cited tkinter FAQ idiom) -- that combination is what
        # locked up the ENTIRE app (every button anywhere, not just
        # menus): tk_popup() already manages its own grab/ungrab
        # internally, and our extra manual release fired essentially
        # immediately (tk_popup doesn't block) and raced Tk's own
        # internal release, corrupting its grab bookkeeping. tk_popup()
        # alone, same as main_window.py now does, lets Tk release the
        # grab itself when the menu is actually dismissed.
        def _wire_menubutton(mbut, menu):
            def _post(event):
                menu.tk_popup(mbut.winfo_rootx(), mbut.winfo_rooty() + mbut.winfo_height())
            mbut.bind("<Button-1>", _post)

        file_mb = tk.Menubutton(bar, text="File", bg="#d4d0c8", relief="flat",
                                 font=MENU_FONT, padx=8)
        file_menu = tk.Menu(bar, tearoff=0, font=MENU_FONT)
        file_menu.add_command(label="New", command=self.on_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.on_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.on_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Assemble", command=self.on_compile, accelerator="F5")
        _wire_menubutton(file_mb, file_menu)
        file_mb.pack(side="left")

        edit_mb = tk.Menubutton(bar, text="Edit", bg="#d4d0c8", relief="flat",
                                 font=MENU_FONT, padx=8)
        edit_menu = tk.Menu(bar, tearoff=0, font=MENU_FONT)
        edit_menu.add_command(label="Cut", command=lambda: self.editor.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", command=lambda: self.editor.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", command=lambda: self.editor.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", command=self.on_find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Find Next", command=self.on_find_next, accelerator="F3")
        edit_menu.add_command(label="Go to Line...", command=self.on_goto_line, accelerator="Ctrl+G")
        _wire_menubutton(edit_mb, edit_menu)
        edit_mb.pack(side="left")

        insert_mb = tk.Menubutton(bar, text="Insert", bg="#d4d0c8", relief="flat",
                                   font=MENU_FONT, padx=8)
        insert_menu = tk.Menu(bar, tearoff=0, font=MENU_FONT)
        directive_menu = tk.Menu(insert_menu, tearoff=0, font=MENU_FONT)
        for label, snippet in _DIRECTIVE_SNIPPETS:
            directive_menu.add_command(label=label, command=lambda s=snippet: self._insert_text(s))
        insert_menu.add_cascade(label="Directive", menu=directive_menu)
        instr_menu = tk.Menu(insert_menu, tearoff=0, font=MENU_FONT)
        for label, snippet in _INSTRUCTION_SNIPPETS:
            instr_menu.add_command(label=label, command=lambda s=snippet: self._insert_text(s))
        insert_menu.add_cascade(label="Instruction", menu=instr_menu)
        insert_menu.add_separator()
        insert_menu.add_command(label="Insert String...", command=self.on_insert_string)
        insert_menu.add_command(label="Insert File...", command=self.on_insert_file)
        _wire_menubutton(insert_mb, insert_menu)
        insert_mb.pack(side="left")

        # keyboard accelerators
        self.bind_all_local = [
            ("<Control-n>", lambda e: self.on_new()),
            ("<Control-o>", lambda e: self.on_open()),
            ("<Control-s>", lambda e: self.on_save()),
            ("<F5>", lambda e: self.on_compile()),
            ("<Control-f>", lambda e: self.on_find()),
            ("<F3>", lambda e: self.on_find_next()),
            ("<Control-g>", lambda e: self.on_goto_line()),
        ]

    def _bind_accelerators(self):
        """Bind keyboard shortcuts scoped to this panel's editor widget
        only -- not bind_all(), so multiple Compiler panels (or other
        text widgets elsewhere in the app) don't fight over F5/Ctrl+S."""
        for seq, handler in self.bind_all_local:
            self.editor.bind(seq, handler)

    # ------------------------------------------------------------- toolbar --

    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#c0c0c0")
        bar.pack(fill="x", padx=6, pady=4)

        # Bigger font + real padding, matching the BTN_FONT/BTN_PADX/
        # BTN_PADY/BTN_BG convention used elsewhere (System Clock dialog,
        # Memory Walker) instead of these two buttons' previous smaller
        # font with no padding -- and no bg -- at all (which left them
        # showing tkinter's default white button face instead of the
        # app's standard grey).
        BTN_FONT = ("Arial", 14, "bold")
        BTN_PADX, BTN_PADY = 14, 8
        BTN_BG = "#d4d0c8"

        # Packed in workflow order (Assemble first, then Load -> CPU) --
        # both use side="right", so the *first* one packed ends up
        # rightmost; packing Load -> CPU first now puts it to the right
        # of Assemble, reversing the previous [Load -> CPU][Assemble]
        # visual order to [Assemble][Load -> CPU].
        self.load_into_cpu_button = tk.Button(
            bar, text="Load -> CPU", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self.on_load_into_cpu, state="disabled",
        )
        self.load_into_cpu_button.pack(side="right", padx=2)

        self.compile_button = tk.Button(
            bar, text="Assemble", font=BTN_FONT, bg=BTN_BG,
            padx=BTN_PADX, pady=BTN_PADY,
            command=self.on_compile,
        )
        self.compile_button.pack(side="right", padx=2)

    # -------------------------------------------------------------- editor --

    def _build_editor(self):
        pane = tk.PanedWindow(self, orient="vertical", bg="#c0c0c0", sashwidth=4)
        pane.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        ed_box = tk.Frame(pane, bg="#c0c0c0")
        tk.Label(ed_box, text="Source (.asm)", bg="#c0c0c0", font=MENU_FONT).pack(anchor="w")
        ed_frame = tk.Frame(ed_box)
        ed_frame.pack(fill="both", expand=True)
        self.editor = tk.Text(
            ed_frame, font=("Courier New", 15), wrap="none", undo=True,
            bg=LCD_BG,
        )
        ed_vsb = tk.Scrollbar(ed_frame, orient="vertical", command=self.editor.yview)
        ed_hsb = tk.Scrollbar(ed_frame, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=ed_vsb.set, xscrollcommand=ed_hsb.set)
        self.editor.grid(row=0, column=0, sticky="nsew")
        ed_vsb.grid(row=0, column=1, sticky="ns")
        ed_hsb.grid(row=1, column=0, sticky="ew")
        ed_frame.grid_rowconfigure(0, weight=1)
        ed_frame.grid_columnconfigure(0, weight=1)
        pane.add(ed_box, stretch="always", height=340)

        msg_box = tk.Frame(pane, bg="#c0c0c0")
        tk.Label(msg_box, text="Messages", bg="#c0c0c0", font=MENU_FONT).pack(anchor="w")
        msg_frame = tk.Frame(msg_box)
        msg_frame.pack(fill="both", expand=True)
        msg_vsb = tk.Scrollbar(msg_frame, orient="vertical")
        msg_vsb.pack(side="right", fill="y")
        self.messages = tk.Text(
            msg_frame, font=("Courier New", 14), height=8, state="disabled",
            bg=LCD_BG, yscrollcommand=msg_vsb.set,
        )
        self.messages.pack(side="left", fill="both", expand=True)
        msg_vsb.configure(command=self.messages.yview)
        pane.add(msg_box, stretch="always", height=110)

        self._bind_accelerators()

    def _build_statusbar(self):
        self.status = tk.Label(
            self, text="", anchor="w", bg="#d4d0c8", relief="sunken", bd=1, padx=4,
        )
        self.status.pack(fill="x", side="bottom")

    def _set_status(self, text):
        self.status.configure(text=text)

    def _append_message(self, text):
        self.messages.configure(state="normal")
        self.messages.insert("end", text + "\n")
        self.messages.see("end")
        self.messages.configure(state="disabled")

    def _clear_messages(self):
        self.messages.configure(state="normal")
        self.messages.delete("1.0", "end")
        self.messages.configure(state="disabled")

    # -------------------------------------------------------------- title --

    def _update_title(self, name=None):
        """Best-effort title update -- if this panel lives inside an
        MdiChild, update its title bar too, matching the Qt window's
        setWindowTitle() calls on Open/Save/New."""
        title = "Assembler / Editor" + (f"  -  {name}" if name else "")
        child = getattr(self.master, "master", None)
        if child is not None and hasattr(child, "set_title"):
            child.set_title(title)

    # ------------------------------------------------------------ file I/O --

    def on_open(self):
        initialdir = str(self.current_path.parent) if self.current_path else _default_open_dir()
        path = filedialog.askopenfilename(
            title="Open Assembly Source", initialdir=initialdir,
            filetypes=[
                ("Assembly Files", "*.asm"), ("Listing Files", "*.lst"),
                ("RAM Image", "*.ram"), ("ROM Files", "*.rom"), ("All Files", "*.*"),
            ],
        )
        if not path:
            return
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self._clear_messages()
        self._last_bytecode = None
        self.load_into_cpu_button.configure(state="disabled")
        self.current_path = path
        self._update_title(path.name)
        self._set_status(f"Opened: {path}")

    def on_save(self):
        if self.current_path is None:
            self.on_save_as()
        elif not os.access(str(self.current_path.parent), os.W_OK):
            self.on_save_as()
        else:
            self._write_source(self.current_path)

    def on_save_as(self):
        initialdir = (
            str(self.current_path.parent)
            if self.current_path and os.access(str(self.current_path.parent), os.W_OK)
            else _default_save_dir()
        )
        initialfile = self.current_path.with_suffix(".asm").name if self.current_path else "untitled.asm"
        path = filedialog.asksaveasfilename(
            title="Save Assembly Source", initialdir=initialdir, initialfile=initialfile,
            defaultextension=".asm",
            filetypes=[("Assembly Files", "*.asm"), ("All Files", "*.*")],
        )
        if not path:
            return
        path = Path(path)
        if path.suffix.lower() != ".asm":
            path = path.with_suffix(".asm")
        self._write_source(path)
        self.current_path = path
        self._update_title(path.name)

    def _write_source(self, path: Path):
        try:
            path.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
            self._set_status(f"Saved: {path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    # ------------------------------------------------------------ compile --

    def on_compile(self):
        self._clear_messages()
        self._last_bytecode = None
        self.load_into_cpu_button.configure(state="disabled")

        result = self._runner.compile(self.editor.get("1.0", "end-1c"))
        if result is None:
            self._append_message("Cannot compile: compiler_core / das.py not available.")
            return

        for msg in result.messages:
            self._append_message(msg)

        if result.success and result.bytecode:
            self._last_bytecode = bytes(result.bytecode)
            self._save_ram_image(self._last_bytecode)
            self.load_into_cpu_button.configure(
                state="normal" if self._host is not None else "disabled"
            )
        else:
            self._set_status("Compilation failed")

    def _save_ram_image(self, bytecode: bytes):
        if self.current_path is not None and os.access(str(self.current_path.parent), os.W_OK):
            out_path = self.current_path.with_suffix(".ram")
        else:
            initialfile = self.current_path.with_suffix(".ram").name if self.current_path else "untitled.ram"
            path = filedialog.asksaveasfilename(
                title="Save RAM Image", initialdir=_default_save_dir(),
                initialfile=initialfile, defaultextension=".ram",
                filetypes=[("RAM Image", "*.ram"), ("All Files", "*.*")],
            )
            if not path:
                self._append_message("RAM image not saved (cancelled).")
                return
            out_path = Path(path)
            if out_path.suffix.lower() != ".ram":
                out_path = out_path.with_suffix(".ram")

        try:
            self._runner.write_ram(bytecode, out_path)
            self._append_message(f"RAM image written to: {out_path}")
            self._set_status(f"Compiled -> {out_path.name}")
        except Exception as exc:
            self._append_message(f"Failed to write RAM image: {exc}")
            self._set_status("Write failed")
            return

        self._save_listing(out_path.with_suffix(".lst"))

    def _save_listing(self, lst_path: Path):
        source_label = str(self.current_path) if self.current_path else None
        listing = self._runner.generate_listing(
            self.editor.get("1.0", "end-1c"), source_path=source_label
        )
        if listing is None:
            return
        if not listing.success:
            self._append_message("Listing not written:")
            for msg in listing.messages:
                self._append_message(f"  {msg}")
            return
        try:
            lst_path.write_text(listing.text, encoding="utf-8")
            self._append_message(f"Listing written to: {lst_path}")
        except Exception as exc:
            self._append_message(f"Failed to write listing: {exc}")

    # ------------------------------------------------------- load into CPU --

    def on_load_into_cpu(self):
        if self._last_bytecode is None or self._host is None:
            return
        # Must be ON to load a program -- same gate as BebopMain's Load
        # RAM and beboputer_v7's on_load_into_cpu().
        calc = getattr(self._host, "calculator", None)
        if calc is None or not calc.powered:
            messagebox.showwarning(
                "Calculator Off",
                "The calculator must be switched ON before you can load a "
                "program into it.\n\nPress the On/Off button on the "
                "calculator, then try again.",
            )
            return
        n = self._runner.load_into_cpu(self._last_bytecode, self._host.cpu)
        self._host._do_reset(clear_calc_display=False)
        addr = self._runner.LOAD_ADDR
        if self._host.msg_display is not None:
            self._host.msg_display.message(
                f"Loaded compiled image ({n} bytes) into CPU @ ${addr:04X}."
            )
        self._append_message(
            f"-> Image ({n} bytes) loaded into Beboputer CPU @ ${addr:04X} and reset."
        )

    # ------------------------------------------------------------ edit menu --

    def on_new(self):
        if self.editor.get("1.0", "end-1c").strip():
            if not messagebox.askyesno(
                "New File", "Discard the current source and start a new file?"
            ):
                return
        self.editor.delete("1.0", "end")
        self._clear_messages()
        self.current_path = None
        self._last_bytecode = None
        self.load_into_cpu_button.configure(state="disabled")
        self._update_title()
        self._set_status("New file")

    def on_find(self):
        text = simpledialog.askstring("Find", "Find text:", initialvalue=self._find_query,
                                       parent=self)
        if text is None:
            return
        self._find_query = text
        if text:
            self._do_find(text)

    def on_find_next(self):
        if not self._find_query:
            self.on_find()
            return
        self._do_find(self._find_query)

    def _do_find(self, text):
        start = self.editor.index("insert")
        pos = self.editor.search(text, start, stopindex="end")
        wrapped = False
        if not pos:
            pos = self.editor.search(text, "1.0", stopindex="end")
            wrapped = True
        if not pos:
            self._set_status(f"Not found: {text!r}")
            return
        end = f"{pos}+{len(text)}c"
        self.editor.tag_remove("sel", "1.0", "end")
        self.editor.tag_add("sel", pos, end)
        self.editor.mark_set("insert", end)
        self.editor.see(pos)
        self._set_status(f"Wrapped to top. Found {text!r}." if wrapped else f"Found {text!r}.")

    def on_goto_line(self):
        last_line = int(self.editor.index("end-1c").split(".")[0])
        line = simpledialog.askinteger(
            "Go to Line", f"Line number (1-{last_line}):",
            minvalue=1, maxvalue=last_line, parent=self,
        )
        if line is None:
            return
        self.editor.mark_set("insert", f"{line}.0")
        self.editor.see(f"{line}.0")

    # ---------------------------------------------------------- insert menu --

    def _insert_text(self, text: str):
        self.editor.insert("insert", text)
        self.editor.focus_set()

    def on_insert_string(self):
        text = simpledialog.askstring(
            "Insert String", "String to embed as .BYTE data (null-terminated):",
            parent=self,
        )
        if not text:
            return
        blist = [f"${ord(c):02X}" for c in text] + ["$00"]
        chunks = [blist[i:i + 8] for i in range(0, len(blist), 8)]
        snippet = (
            f'        # "{text}"\n'
            + "\n".join(f"        .BYTE   {', '.join(c)}" for c in chunks)
            + "\n"
        )
        self._insert_text(snippet)

    def on_insert_file(self):
        initialdir = str(self.current_path.parent) if self.current_path else _default_open_dir()
        path = filedialog.askopenfilename(
            title="Insert File at Cursor", initialdir=initialdir,
            filetypes=[("Assembly / Text", "*.asm *.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            self._insert_text(Path(path).read_text(encoding="utf-8", errors="replace"))
            self._set_status(f"Inserted: {path}")
        except Exception as exc:
            messagebox.showerror("Insert failed", str(exc))
