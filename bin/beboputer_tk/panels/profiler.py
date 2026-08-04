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

"""Code Profiler panel -- tkinter front-end for
beboputer_tk.tools.profiler.ProfileSession (see that module's docstring
for the "why" -- reviving the Code Profiler tool pitched in
Educators/more-tools-code-profiler.ppt: the 80:20 rule, find the small
fraction of the code eating most of the run time).

Structurally this is CoveragePanel's twin -- same Load Source / Run
Program / Track Live / Refresh / Reset / Save Report workflow, same
"hits accumulate across runs until Reset" semantics -- just a different
question asked of the same underlying per-line hit data: "where did the
time go" instead of "was this touched at all". See coverage.py's panel
docstring for the full Run Program vs. Track Live explanation.

The source view combines two of the display ideas from the original
tool's own pitch deck: a per-line ASCII bar chart ("vertical bar-chart
type display", slide 7) and a colour-intensity heat map ("using height
as well as color", slides 8-9) -- the hottest lines get both the
longest bar and the strongest highlight, so the 20% of the program
eating 80% of the run time jumps out at a glance.
"""

from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

from beboputer_tk.tools.profiler import ProfileSession
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


LCD_BG = "#c8f0c8"   # same "on" LCD background used by Disassembler/Compiler/Coverage
BTN_FONT = ("Arial", 13, "bold")
BTN_BG = "#d4d0c8"

# Heat-map tiers, coolest to hottest -- bucketed by each line's hit
# share *relative to the single hottest line in the current report*
# (not an absolute percentage), so the actual hot spot(s) always read
# as the strongest colour regardless of how evenly or unevenly the
# total is spread across the program.
HEAT_TAGS = [
    ("heat0", "#fff6c8", "#665500"),   # >0%, < 25% of the max
    ("heat1", "#ffe066", "#5c4400"),   # 25-50%
    ("heat2", "#ffb366", "#5c2f00"),   # 50-75%
    ("heat3", "#ff8080", "#4d0000"),   # 75-100% -- the hot spot(s)
]
COLD_FG    = "#808080"   # executable, never executed
NEUTRAL_FG = "#606060"   # not an executable line at all

DEFAULT_MAX_STEPS = 200_000
BAR_WIDTH = 20


class ProfilerPanel(tk.Frame):
    """Code Profiler panel: load an .asm source, run it, and see which
    lines accounted for the largest share of total execution."""

    def __init__(self, parent, host_main=None, **kwargs):
        super().__init__(parent, bg="#c0c0c0", **kwargs)
        self._host = host_main
        self.session: ProfileSession | None = None
        self._compiled = None            # compiler_core.CompileResult, for Run Program
        self.current_path: Path | None = None
        self._track_var = tk.BooleanVar(value=False)

        self._build_toolbar()
        self._build_summary()
        self._build_hotspots()
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
            bar, text="Reset Profile", font=BTN_FONT, bg=BTN_BG,
            padx=10, pady=6, command=self.on_reset_profile,
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

    def _build_hotspots(self):
        box = tk.Frame(self, bg="#c0c0c0")
        box.pack(fill="x", padx=6, pady=(0, 4))
        tk.Label(
            box, text="Hot Spots (80:20 rule -- start here)",
            font=("Segoe UI", 11, "bold"), bg="#c0c0c0", anchor="w",
        ).pack(fill="x")
        self.hotspots = tk.Text(
            box, font=("Courier New", 12), height=6, bg=LCD_BG, state="disabled", wrap="none",
        )
        self.hotspots.pack(fill="x")
        for tag, bg, fg in HEAT_TAGS:
            self.hotspots.tag_configure(tag, background=bg, foreground=fg)

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

        for tag, bg, fg in HEAT_TAGS:
            self.view.tag_configure(tag, background=bg, foreground=fg)
        self.view.tag_configure("cold", foreground=COLD_FG)
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
            title="Load Source for Profiling", initialdir=initialdir,
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
            session = ProfileSession.from_source(text, source_path=str(path))
        except RuntimeError as exc:
            messagebox.showerror("Assembly failed", str(exc))
            return

        compiled = Compiler().compile_source(text)
        if not compiled.ok:
            messagebox.showerror(
                "Assembly failed", "\n".join(compiled.messages) or "Unknown error.",
            )
            return

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

        if hasattr(self._host, "_refresh_all"):
            self._host._refresh_all()

        status = "HALTed" if cpu.halted else f"stopped after {executed:,} instructions (step limit reached)"
        self._render()
        self._set_status(f"Run complete -- {status}.")
        if getattr(self._host, "msg_display", None) is not None:
            name = self.current_path.name if self.current_path else "program"
            self._host.msg_display.message(f"Code Profiler: ran {name} -- {status}.")

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

    def on_reset_profile(self):
        if self.session is None:
            return
        self.session.reset()
        self._render()
        self._set_status("Profile reset.")

    def on_save_report(self):
        if self.session is None:
            return
        initialdir = str(self.current_path.parent) if self.current_path else _default_save_dir()
        initialfile = self.current_path.with_suffix(".prof.txt").name if self.current_path else "profile.txt"
        path = filedialog.asksaveasfilename(
            title="Save Profile Report", initialdir=initialdir, initialfile=initialfile,
            defaultextension=".txt",
            filetypes=[("Text Report", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        title = f"Profile for {self.current_path.name}" if self.current_path else "Profile Report"
        try:
            Path(path).write_text(self.session.render_text_report(title=title) + "\n", encoding="utf-8")
            self._set_status(f"Report saved: {path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    # ------------------------------------------------------------ render --

    @staticmethod
    def _bar(percent: float, width: int = BAR_WIDTH) -> str:
        n = min(width, int(round(percent / 100.0 * width)))
        return "#" * n

    @staticmethod
    def _heat_tag(hits: int, max_hits: int) -> str | None:
        if hits <= 0 or max_hits <= 0:
            return None
        ratio = hits / max_hits
        if ratio >= 0.75:
            return "heat3"
        if ratio >= 0.5:
            return "heat2"
        if ratio >= 0.25:
            return "heat1"
        return "heat0"

    def _render(self):
        self.view.configure(state="normal")
        self.view.delete("1.0", "end")
        self.hotspots.configure(state="normal")
        self.hotspots.delete("1.0", "end")

        if self.session is None or self.session.source_lines is None:
            self.view.insert(
                "1.0",
                "Load a .asm source file (Load Source...) to see its "
                "profile here.\n",
            )
            self.view.configure(state="disabled")
            self.hotspots.insert("1.0", "(no program loaded)\n")
            self.hotspots.configure(state="disabled")
            self.summary_label.configure(text="Load a .asm source file to begin.")
            return

        rep = self.session.report()
        max_hits = max((ln.hits for ln in rep.lines), default=0)

        # -- hot spots box --
        hot = rep.hottest(8)
        if not hot:
            self.hotspots.insert("1.0", "(no instructions executed yet -- Run Program or Track Live)\n")
        for ln in hot:
            start = self.hotspots.index("end-1c")
            row = (
                f"{ln.line_no:5d}  {ln.hits:7d}  {ln.percent:5.1f}%  "
                f"{self._bar(ln.percent):<{BAR_WIDTH}}  {ln.text}\n"
            )
            self.hotspots.insert("end", row)
            tag = self._heat_tag(ln.hits, max_hits)
            if tag:
                self.hotspots.tag_add(tag, start, self.hotspots.index("end-1c"))
        self.hotspots.configure(state="disabled")

        # -- full annotated source --
        by_line = {ln.line_no: ln for ln in rep.lines}
        for i, text in enumerate(self.session.source_lines, start=1):
            hot_line = by_line.get(i)
            start = self.view.index("end-1c")
            if hot_line is None:
                self.view.insert("end", f"{'':7} {'':7}  {i:5d}  {text}\n")
                tag = "neutral"
            else:
                bar = self._bar(hot_line.percent)
                self.view.insert(
                    "end",
                    f"{hot_line.hits:7d} {hot_line.percent:6.1f}%  {bar:<{BAR_WIDTH}}  {i:5d}  {text}\n",
                )
                tag = self._heat_tag(hot_line.hits, max_hits) or "cold"
            self.view.tag_add(tag, start, self.view.index("end-1c"))

        self.view.configure(state="disabled")

        if rep.total_instructions:
            top = rep.hottest(1)
            top_desc = (
                f"  |  hottest: line {top[0].line_no} ({top[0].percent:.1f}%)"
                if top else ""
            )
            self.summary_label.configure(
                text=f"{rep.total_instructions:,} instructions executed{top_desc}"
            )
        else:
            self.summary_label.configure(text="No instructions executed yet -- Run Program or Track Live.")
