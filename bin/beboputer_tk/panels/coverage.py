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

"""Code Coverage panel -- tkinter front-end for
beboputer_tk.tools.coverage.CoverageSession (see that module's docstring
for the "why" -- reviving the Code Coverage tool pitched in
Educators/more-tools-code-coverage.ppt).

All the real logic (listing parsing, address/line mapping, hit
recording, reporting) lives in CoverageSession, which has zero Qt/
tkinter dependency and is unit-tested directly (tests/test_coverage.py).
This panel is a thin Load/Run/Track/Save wrapper around it, same split
as CompilerPanel around AssemblerRunner.

Two ways to gather coverage, and they compose (hits accumulate into the
same session either way, until Reset Coverage is pressed):

  Run Program   -- loads the compiled program fresh into the shared CPU
                   and single-steps it headlessly (no GUI redraw per
                   instruction) up to a step cap or HALT. Fast, and
                   enough for a program that doesn't wait on keypad
                   input.
  Track Live    -- attaches to the shared CPU so *any* execution driven
                   from elsewhere in the app (Calculator's Step/Run
                   buttons, Memory Walker's Run to BP, ...) is recorded
                   too. Needed for coverage of code paths that only run
                   after specific keys are pressed -- e.g. play the
                   calculator normally with Track Live on, then check
                   what you actually exercised.
"""

from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

from beboputer_tk.tools.coverage import CoverageSession
from compiler_core import Compiler

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
# _DISPLAY_ON_BG) -- used elsewhere for this app's read-only text panels
# (Disassembler, Assembler/Editor's Messages box); reused here so the
# source view matches.
LCD_BG = "#c8f0c8"
MENU_FONT = ("Segoe UI", 15)
BTN_FONT = ("Arial", 13, "bold")
BTN_BG = "#d4d0c8"

# Coverage highlight colours. Deliberately background tints rather than
# just coloured text -- easier to scan a long listing for the uncovered
# rows at a glance, closer to the "colored text display" the original
# tool's pitch deck (Educators/more-tools-code-coverage.ppt, slide 6)
# describes.
COVERED_BG    = "#c8f0c8"
COVERED_FG    = "#004400"
UNCOVERED_BG  = "#f6c9c9"
UNCOVERED_FG  = "#660000"
NEUTRAL_FG    = "#606060"

DEFAULT_MAX_STEPS = 200_000


class CoveragePanel(tk.Frame):
    """Code Coverage panel: load an .asm source, run it (headlessly and/
    or by tracking live execution), and see which lines were and weren't
    exercised."""

    def __init__(self, parent, host_main=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self._host = host_main
        self.session: CoverageSession | None = None
        self._compiled = None            # compiler_core.CompileResult, for Run Program
        self.current_path: Path | None = None
        self._track_var = tk.BooleanVar(value=False)

        self._build_toolbar()
        self._build_summary()
        self._build_view()
        self._build_statusbar()

        self._render()

    # ------------------------------------------------------------ build --

    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#c0c0c0")
        bar.pack(fill="x", padx=6, pady=(6, 2))

        tk.Button(
            bar, text="Load Source...", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self.on_load_source,
        ).pack(side="left", padx=(0, 4))

        self.run_button = tk.Button(
            bar, text="Run Program", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self.on_run_program, state="disabled",
        )
        self.run_button.pack(side="left", padx=4)

        tk.Checkbutton(
            bar, text="Track Live", font=BTN_FONT, bg="#c0c0c0",
            variable=self._track_var, command=self.on_toggle_live_tracking,
        ).pack(side="left", padx=8)

        tk.Button(
            bar, text="Refresh", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self._render,
        ).pack(side="left", padx=4)

        tk.Button(
            bar, text="Reset Coverage", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self.on_reset_coverage,
        ).pack(side="left", padx=4)

        self.save_button = tk.Button(
            bar, text="Save Report...", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self.on_save_report, state="disabled",
        )
        self.save_button.pack(side="right", padx=(4, 0))

    def _build_summary(self):
        self.summary_label = tk.Label(
            self, text="Load a .asm source file to begin.",
            font=("Segoe UI", 13, "bold"), bg="#c0c0c0", anchor="w",
        )
        self.summary_label.pack(fill="x", padx=8, pady=(2, 4))

    def _build_view(self):
        frame = tk.Frame(self, bg="#c0c0c0")
        frame.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        vbar = tk.Scrollbar(frame, orient="vertical")
        vbar.pack(side="right", fill="y")
        hbar = tk.Scrollbar(frame, orient="horizontal")
        hbar.pack(side="bottom", fill="x")

        self.view = tk.Text(
            frame, font=("Courier New", 13), bg=LCD_BG, wrap="none",
            state="disabled", yscrollcommand=vbar.set, xscrollcommand=hbar.set,
        )
        self.view.pack(side="left", fill="both", expand=True)
        vbar.configure(command=self.view.yview)
        hbar.configure(command=self.view.xview)

        self.view.tag_configure("covered", background=COVERED_BG, foreground=COVERED_FG)
        self.view.tag_configure("uncovered", background=UNCOVERED_BG, foreground=UNCOVERED_FG)
        self.view.tag_configure("neutral", foreground=NEUTRAL_FG)

    def _build_statusbar(self):
        self.status = tk.Label(
            self, text="", anchor="w", bg="#d4d0c8", relief="sunken", bd=1, padx=4,
        )
        self.status.pack(fill="x", side="bottom")

    def _set_status(self, text: str):
        self.status.configure(text=text)

    # -------------------------------------------------------------- load --

    def on_load_source(self):
        initialdir = str(self.current_path.parent) if self.current_path else _default_open_dir()
        path = filedialog.askopenfilename(
            title="Load Source for Coverage", initialdir=initialdir,
            filetypes=[("Assembly Files", "*.asm"), ("All Files", "*.*")],
        )
        if not path:
            return
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))
            return

        try:
            session = CoverageSession.from_source(text, source_path=str(path))
        except RuntimeError as exc:
            messagebox.showerror("Assembly failed", str(exc))
            return

        compiled = Compiler().compile_source(text)
        if not compiled.ok:
            # Listing succeeded but a plain compile didn't -- shouldn't
            # happen (both walk the same source through the same
            # engine), but Run Program needs real bytecode, so surface
            # it rather than silently leaving Run Program disabled.
            messagebox.showerror(
                "Assembly failed", "\n".join(compiled.messages) or "Unknown error.",
            )
            return

        # Loading a new source invalidates any hits gathered against the
        # old one -- detach and drop the previous session so a stale
        # attach()ed step() wrapper doesn't keep recording into it.
        was_tracking = self._track_var.get()
        if self.session is not None:
            self.session.detach()

        self.session = session
        self._compiled = compiled
        self.current_path = path
        self.run_button.configure(state="normal" if self._host is not None else "disabled")
        self.save_button.configure(state="normal")

        if was_tracking and self._host is not None:
            self.session.attach(self._host.cpu)

        self._render()
        self._set_status(
            f"Loaded: {path.name}  ({len(session.line_map.executable_lines)} executable lines)"
        )

    # --------------------------------------------------------------- run --

    def on_run_program(self):
        if self.session is None or self._compiled is None or self._host is None:
            return
        cpu = self._host.cpu
        calc = getattr(self._host, "calculator", None)
        if calc is None or not calc.powered:
            messagebox.showwarning(
                "Calculator Off",
                "The calculator must be switched ON before Run Program can "
                "load and execute a program.\n\nPress the On/Off button on "
                "the calculator, then try again.",
            )
            return

        cpu.reset()
        origin = self._compiled.origin if self._compiled.origin is not None else cpu.RESET_VECTOR
        data = self._compiled.bytecode or b""
        cpu.ram[origin:origin + len(data)] = data
        if hasattr(cpu, "ram_touched"):
            cpu.ram_touched[origin:origin + len(data)] = b"\x01" * len(data)
        cpu.pc = origin
        cpu.ram[0xF011] = 0xFF  # idle keypad sentinel, matches the app's own reset state

        executed = self.session.run_headless(cpu, max_steps=DEFAULT_MAX_STEPS)

        # Bring the rest of the app's own views (Calculator, Memory
        # Walker, CPU Registers, ...) up to date with the state the run
        # just left the CPU in -- same as any other action that changes
        # cpu state from outside the normal Step/Run buttons.
        if hasattr(self._host, "_refresh_all"):
            self._host._refresh_all()

        status = "HALTed" if cpu.halted else f"stopped after {executed:,} instructions (step limit reached)"
        self._render()
        self._set_status(f"Run complete -- {status}.")
        if getattr(self._host, "msg_display", None) is not None:
            name = self.current_path.name if self.current_path else "program"
            self._host.msg_display.message(f"Code Coverage: ran {name} -- {status}.")

    # ---------------------------------------------------------- tracking --

    def on_toggle_live_tracking(self):
        if self.session is None or self._host is None:
            self._track_var.set(False)
            return
        if self._track_var.get():
            self.session.attach(self._host.cpu)
            self._set_status(
                "Live tracking ON -- Step/Run/Memory Walker executions are "
                "now recorded. Press Refresh to update the view."
            )
        else:
            self.session.detach()
            self._set_status("Live tracking OFF.")

    def shutdown(self):
        """Called when this panel's MdiChild is closed -- detach from the
        shared CPU so a wrapped step() doesn't keep recording into a
        session nobody can see anymore."""
        if self.session is not None:
            self.session.detach()

    # -------------------------------------------------------------- misc --

    def on_reset_coverage(self):
        if self.session is None:
            return
        self.session.reset()
        self._render()
        self._set_status("Coverage reset.")

    def on_save_report(self):
        if self.session is None:
            return
        initialdir = str(self.current_path.parent) if self.current_path else _default_save_dir()
        initialfile = self.current_path.with_suffix(".cov.txt").name if self.current_path else "coverage.txt"
        path = filedialog.asksaveasfilename(
            title="Save Coverage Report", initialdir=initialdir, initialfile=initialfile,
            defaultextension=".txt",
            filetypes=[("Text Report", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        title = f"Coverage for {self.current_path.name}" if self.current_path else "Coverage Report"
        try:
            Path(path).write_text(self.session.render_text_report(title=title) + "\n", encoding="utf-8")
            self._set_status(f"Report saved: {path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    # ------------------------------------------------------------ render --

    def _render(self):
        self.view.configure(state="normal")
        self.view.delete("1.0", "end")

        if self.session is None or self.session.source_lines is None:
            self.view.insert(
                "1.0",
                "Load a .asm source file (Load Source...) to see its "
                "coverage here.\n",
            )
            self.view.configure(state="disabled")
            self.summary_label.configure(text="Load a .asm source file to begin.")
            return

        rep = self.session.report()
        for i, text in enumerate(self.session.source_lines, start=1):
            addr = self.session.line_map.address_for_line(i)
            addr_str = f"${addr:04X}" if addr is not None else ""
            if i in rep.covered:
                marker, tag = "+", "covered"
            elif i in rep.uncovered:
                marker, tag = "!", "uncovered"
            else:
                marker, tag = " ", "neutral"
            start = self.view.index("end-1c")
            self.view.insert("end", f"{addr_str:>6}  {marker} {i:5d}  {text}\n")
            self.view.tag_add(tag, start, self.view.index("end-1c"))

        self.view.configure(state="disabled")

        if rep.total_executable:
            self.summary_label.configure(
                text=(
                    f"Covered {len(rep.covered)} / {rep.total_executable} "
                    f"executable lines  ({rep.percent:.1f}%)"
                    + ("  -- fully covered" if rep.percent >= 100.0 else "")
                )
            )
        else:
            self.summary_label.configure(text="Program has no executable lines.")
