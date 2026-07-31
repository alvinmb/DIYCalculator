# Migrating PY-DIYCALCULATOR from PyQt5 to tkinter

**Status:** Phase 0 (spike/validation) complete — all three spikes
verified working, including Hi-DPI on real Windows hardware. **Phase 1
(app shell) complete** — see §5. **Phase 2 part 1 (CPU wiring + Message
Display + Port Monitor + Control Panel) complete** — see §7. **Phase 2
part 2 (Calculator + DIYButton grid) complete** — see §8. Not started:
Memory Walker, Disassembler, Compiler/Editor, remaining dialogs,
printing/sound.
**Driver:** move off PyQt5's GPL/commercial licensing onto a permissively
licensed stack. tkinter ships in the Python standard library under the
PSF license — no GPL, no royalty, no separate install.

---

## 1. What does and doesn't need to change

The CPU simulator, assembler, and all program content have **zero** Qt
dependency and need no changes at all:

| Module | Qt dependency |
|---|---|
| `bin/beboputer_v7/cpu.py` | none — pure Python |
| `bin/das.py`, `bin/compiler_core.py` | none — pure Python |
| `tutorial/*.asm`, `Data/*.asm` | none — plain text |
| `Config/defbuttons.ini` | none — plain text, format is toolkit-agnostic |

This migration is scoped entirely to the UI layer: **~7,100 lines across
20 files** under `bin/beboputer_v7/` that import `PyQt5`.

---

## 2. Widget mapping

### Direct, mostly mechanical

| Qt5 today | tkinter equivalent |
|---|---|
| `QMainWindow`, `QMenuBar`, `QToolBar`, `QStatusBar` | `Tk()` root, `Menu`, a `Frame` of buttons, a docked `Label` |
| `.clicked.connect(fn)` | `command=fn` |
| `QTimer` (CPU run loop) | `.after(ms, callback)` |
| `QPainter`-drawn LEDs (`widgets/leds.py`) | `Canvas.create_oval`/`create_rectangle`, redrawn on state change |
| `QPlainTextEdit` (Compiler editor, Terminal) | `Text` widget — tags for syntax highlighting, native undo/redo |
| `QFileDialog` / `QMessageBox` / `QInputDialog` | `tkinter.filedialog` / `messagebox` / `simpledialog` |
| `QDialog` (About, EPROM Burner, Configure Button Attributes) | `Toplevel` + `grab_set()` for modality |
| `QSplashScreen` | borderless `Toplevel` + image `Label`, shown briefly |

### Needs real design work — this is what Phase 0 targeted

| Gap | Resolution |
|---|---|
| `QMdiArea`/`QMdiSubWindow` — no MDI container in tkinter at all | **Spiked, working.** See §3.1 |
| Memory Walker's per-cell colored 256-row grid — no per-cell coloring in `ttk.Treeview` | **Spiked, working.** See §3.2 |
| Windows Hi-DPI scaling — no `AA_EnableHighDpiScaling` equivalent | **Spiked, verified on real Windows hardware.** See §3.3 |
| Printing (`QPrinter`/`QPrintDialog`/`QPageSetupDialog`) | Not spiked. Plan: drop native print dialogs, replace with "Export to PDF" and let the OS handle printing from there — tkinter has no printing framework to build this on top of. |
| `QSound` (sound effects) | Not spiked. No tkinter equivalent; likely `winsound` on Windows + drop or shell out (`aplay`) on Linux/Pi. |
| `QFontDialog` (if used) | Not spiked. No tkinter built-in; would need a small custom picker. Low priority — confirm it's actually used anywhere before spending time on it. |
| Multi-monitor screen geometry (`QScreen.availableGeometry()`, used by this session's maximize/panel-layout fixes) | Not spiked. `winfo_screenwidth()`/`winfo_screenheight()` only see the primary monitor. Needs either the third-party `screeninfo` package or raw `ctypes` calls to `EnumDisplayMonitors`. |

---

## 3. Phase 0 — spike results

Three prototypes, in `prototypes/tkinter_migration/`. Each is a standalone,
runnable file with no dependency on the rest of the app — run any of them
directly (`python <file>.py`) for a live interactive demo.

### 3.1 `pseudo_mdi.py` — MdiArea / MdiChild

tkinter has no MDI container, so this builds one: `MdiArea` (the desktop —
a plain `Frame`) holding `MdiChild` sub-windows (title bar, drag-to-move,
resize grip, maximize/restore, close, raise-to-front, active/inactive
title shading), all via `.place()` geometry management and mouse-event
bindings. No third-party packages.

`tile_children()` ports `main_window.py`'s `_layout_startup_panels()`
3-tier fallback (side-by-side → two-row wrap → stacked column) to compute
initial non-overlapping positions against the `MdiArea`'s size instead of
the screen's.

**Verified** (headless, via Xvfb + programmatic event simulation — no
exceptions, correct results):
- Initial tiling picks the right tier and produces zero overlap
- Drag moves a child by the expected offset
- Resize respects the min size and the desktop's bounds
- Maximize fills the desktop exactly; restore returns to the saved geometry
- Raise-to-front correctly updates which window is "active"
- Close removes the child and updates the count

**Open question:** independent `MdiChild` windows change the "everything
lives in one app window" feel versus real Qt MDI (which also supports
this, so it's a like-for-like replacement, not a downgrade) — but it's
worth a quick sanity check on the actual Pi touchscreen once panels have
real content in them, since touch dragging a title bar is a different
motion than a mouse drag.

### 3.2 `memory_grid.py` — Memory Walker's BP/STEP/ADDRESS/DATA table

The hard part isn't the data, it's that **within one row**, the BP cell,
STEP cell, ADDRESS cell, and DATA cell each need a *different* color
simultaneously (e.g. the PC row shows amber STEP + bright-green ADDRESS +
amber DATA, independently of whether that address also has a red BP
marker). `ttk.Treeview` only colors whole rows via tags, not individual
cells, so it can't reproduce this directly. The alternative of one
`Label` widget per cell (1,024 widgets for 256 rows × 4 columns) raised a
real performance question, since Memory Walker redraws on every single
CPU step during a Run.

**Approach used:** one `tk.Text` widget, monospaced, with the whole grid
as plain text and per-substring color tags (fixed character-column
offsets, so a click's `(row, col)` is recovered directly from the `Text`
index tkinter already gives you). One `.delete()` + `.insert()` pass
redraws all 256 rows, instead of updating 1,024 separate widgets.

**Verified** (headless, via Xvfb):
- Address/data columns render correctly; untouched RAM shows `XX`
- PC row gets the correct arrow + amber + highlighted-background tags
- Clicking the BP column toggles a red breakpoint marker at the right row
- Clicking the STEP column single-steps the (fake) CPU
- **Performance:** 200 consecutive full-grid refreshes (256 rows each)
  averaged **9.3 ms/refresh** (~107 refreshes/sec) — comfortably fast
  enough for interactive single-stepping and for a Run loop's refresh
  cadence.

### 3.3 `dpi_awareness.py` — Windows Hi-DPI scaling

Replaces the Qt side of this session's earlier fix
(`AA_EnableHighDpiScaling`). Two steps, order matters:

1. `SetProcessDpiAwareness()` (via `ctypes`), called *before* any window
   exists, so Windows doesn't upscale the whole window as a blurry bitmap
   after the fact — the exact bug this project fixed for the Qt build.
2. Read the real monitor DPI (`GetDpiForWindow`) once the root window
   exists, and feed the ratio into `tk.call('tk', 'scaling', ratio)` so
   widget/font sizes render crisp instead of tkinter drawing at 96 DPI
   and Windows stretching the result.

**Validated on real Windows hardware.** This sandbox is Linux with no
real display DPI to test against, so the self-test only confirmed the
module imports cleanly and the Windows-only code paths no-op safely
elsewhere. The self-test's first version also had a bug — it hardcoded
`assert did_set is False`, an assumption that only held on the Linux
sandbox, so it raised a false-alarm `AssertionError` the first time it
was actually run on Windows (fixed by making the assertions
platform-aware instead of Linux-only). Once fixed and re-run on your
Windows machine, `set_process_dpi_aware()` correctly returned `True`,
and the sample-text window it pops up was confirmed **readable/crisp by
eye** — the actual point of this spike. Still worth a follow-up check
at a couple of different scaling levels (125%/150%/200%) and across a
monitor drag if you have a multi-monitor Hi-DPI setup, but the core
mechanism is now proven, not just "should work."

Also flagged: this module only handles DPI *scaling*, not multi-monitor
*screen geometry* — the `_layout_startup_panels()`/`_reassert_maximized()`
logic from this session's Qt fixes still needs a tkinter equivalent for
"which monitor is this maximizing onto," which is a separate, not-yet-
spiked piece (see the gap table in §2).

---

## 4. Recommended sequencing (Phase 1 onward)

Panel-by-panel, easiest first, so the architecture gets validated before
the hardest pieces, on a branch — keep shipping PyQt5 releases while
migration proceeds, rather than a big-bang rewrite:

1. **Phase 1 — infrastructure. ✅ Done — see §5.** `app.py` entry point:
   `Tk()` root + `dpi.py` wired in, `MdiArea` shell, full menu bar,
   status bar, non-overlapping startup layout. CPU engine and assembler
   are reused unchanged.
2. **Phase 2 — panels, simple to hard:**
   1. Message Display (simple text/label panel)
   2. Control Panel / LEDs widget (`Canvas`-based, low risk — already
      close to `widgets/leds.py`'s existing `QPainter` logic)
   3. Port Monitor (labels + a small table)
   4. Calculator + `DIYButton` grid (large but repetitive — same
      `ButtonDef` data model reused, `tkinter.Button` subclass instead of
      `QPushButton`)
   5. Memory Walker (hardest — but now de-risked by §3.2)
   6. Disassembler / CPU panel / Terminal
   7. Compiler/Editor window (`Text` widget, find/replace, syntax
      highlighting)
   8. Remaining dialogs, menu/toolbar/shortcut wiring
   9. Printing → PDF export, splash screen, sound
3. **Phase 3 — platform validation.** Hi-DPI spot-checks at other scaling
   levels/multi-monitor (core mechanism already verified, §3.3), Raspberry
   Pi touchscreen validation (button sizes, small-screen layout fallback,
   touch-drag on `MdiChild` title bars), macOS if relevant.
4. **Phase 4 — regression pass.** `test_harness.py` and
   `tests/test_*.py` don't touch the GUI at all, so they stay green
   throughout — but every tutorial and `Data/*.asm` file needs a manual
   click-through against the new GUI. Rebuild both the `.deb` and the
   Windows installer (PyInstaller still bundles tkinter's Tcl/Tk runtime,
   so the release pipeline shape stays similar — output should be
   noticeably smaller than the current PyQt5 build).

---

## 5. Phase 1 — what was built

New package, `bin/beboputer_tk/` (parallel to `bin/beboputer_v7/`, not a
replacement of it — the Qt build still ships unchanged):

| File | Role |
|---|---|
| `app.py` | Entry point — DPI awareness before `Tk()`, root window, splash screen (reuses `bin/splash.png` directly), hands off to `main_window.py`, `mainloop()`. |
| `main_window.py` | `BebopMain` — menu bar, status bar, `MdiArea`, startup panel tiling. Every panel a menu item opens is currently a placeholder `MdiChild` (Phase 2 replaces the placeholder content per-panel). |
| `mdi.py` | Promoted from `prototypes/tkinter_migration/pseudo_mdi.py` — same `MdiArea`/`MdiChild`/`tile_children()`, trimmed of the demo block for use as a real library module. |
| `dpi.py` | Promoted from `prototypes/tkinter_migration/dpi_awareness.py` the same way. |
| `__init__.py` | Re-exports `__version__` from `beboputer_v7` — one source of truth (`VERSIONING.md`); both builds are the same app at the same version. |
| `bin/run_beboputer_tk.py` | Launcher script, mirrors `run_beboputer_v7.py`. |

**Menu structure** (File/Setup/Display/Memory/Tools/Help, every item
label) is copied directly from `beboputer_v7/menus.py`, so the tkinter
build is immediately recognizable as the same app, not a stripped-down
placeholder shell. Panel-opening menu items (Calculator, Memory Walker,
Message Display, CPU Registers, Terminal, Port Map Status, Disassembler,
EPROM Burner, Keyboard, Workbench 1, Assembler/Editor) all go through
one `_open_panel()` helper that opens-or-raises an `MdiChild` by a
registry key, so clicking an already-open panel's menu item raises it
instead of creating a duplicate — the same behavior `QMdiArea` gives the
Qt app for free. File/Setup items that depend on state Phase 2+ hasn't
built yet (project save/load, RAM load/save, button file load/save,
Restore Defaults, System Clock) show a plain "not yet implemented, see
TKINTER_MIGRATION.md" message rather than silently doing nothing —
`Exit` and `About` are the two fully real handlers at this stage.

**Verified** (headless, via Xvfb + programmatic calls to the exact same
callables the menu's `command=` entries invoke — equivalent to clicking
them, since that's literally what tkinter calls on a real click):

- Window title correctly shows the live version pulled from
  `beboputer_v7.__version__` (confirms the shared-version-source design
  works, not just that a string was hardcoded)
- Calculator, Memory Walker, and Message Display all open at startup,
  tiled via `tile_children()` with **zero overlap**
- Opening an already-open panel raises it rather than duplicating it
- Closing a panel correctly removes it from the registry, and it can be
  re-opened cleanly afterward
- Multiple different panels can be open simultaneously
- Status bar reads "Ready" after startup, positioned correctly
  (confirmed via direct widget-geometry query — screenshot capture
  under headless Xvfb with no window manager clips a small strip off
  window screenshots, a tooling artifact, not an app issue; the
  geometry query is the more reliable check in this environment)
- `test_harness.py`'s full 47-test suite still passes unchanged — this
  package is purely additive, nothing in `beboputer_v7` was touched

**Not yet real** (by design — this is Phase 1, infrastructure only):
every panel's actual content, all File/Setup menu actions that need CPU
or project state, toolbar (menu bar only so far), keyboard shortcuts,
and window icon.

---

## 6. Risks carried forward from Phase 0

1. **Printing** — real capability gap, no tkinter framework to build on.
   Needs a product decision (drop printing entirely / PDF-export-only /
   shell out to the OS print command) before Phase 2 reaches any panel
   that currently prints.
2. **MDI feel** — independent `Toplevel`-based `MdiChild` windows versus
   Qt's `QMdiSubWindow`; functionally equivalent per §3.1, worth a Pi
   touchscreen sanity check once real content is in the panels.
3. **Hi-DPI** — verified crisp/readable on real Windows hardware (§3.3).
   Still worth spot-checking at a few different scaling levels
   (125%/150%/200%) and across a monitor drag if a multi-monitor Hi-DPI
   setup is available, but the core mechanism is proven.
4. **Multi-monitor geometry** — no tkinter equivalent spiked yet for
   `QScreen.availableGeometry()`; needed for maximize/panel-layout
   parity with this session's Qt fixes.
5. **Sound** — no tkinter built-in; small gap, low effort either way
   (drop or shim).

---

## 7. Phase 2 part 1 — what was built

First real-content slice of Phase 2, landed in the same `bin/beboputer_tk/`
package. Adds a `panels/` subpackage and wires a real `CPU()` instance
into `main_window.py` for the first time:

| File | Role |
|---|---|
| `panels/message_display.py` | Direct port of `beboputer_v7/panels/message_display.py` — dark-themed scrolling log, one `message(text)` method. Behaviorally identical. |
| `panels/port_monitor.py` | Direct port of `beboputer_v7/panels/port_monitor.py` — tracks `$F031` (display out), `$F032` (LEDs), `$F011` (buttons, current + previous), editable button-value override field. Same `_last_button_val` / `on_key_press()` design as the Qt version (and the same reasoning comment: the read-clear strobe wipes `ram[$F011]` back to `$FF` the instant the CPU reads it, so the write hook has to capture the value *before* that happens). |
| `panels/control_panel.py` | **New, not a Qt port** — RUN/STEP/HALT/RESET buttons, address/data bus readout, 8 manual data switches, `ENTER`. `beboputer_v7/panels/control_panel.py` exists but is dead code — `main_window.py` never instantiates it (`REFACTORING_NOTES.md` §2 flags this as an open decision). Wired in here as a clearly-labeled `[new]` Tools-menu item — the Qt `pyqtSignal`s become plain `on_run=`/`on_step=`/`on_halt=`/`on_reset=` callback params, since a single button → single handler wire-up doesn't need a signal/slot layer in tkinter. |

`main_window.py` changes: constructs a real `beboputer_v7.cpu.CPU()` and
`InstructionMessages()` in `__init__`; wires the same two keypad hooks as
`beboputer_v7/main_window.py` (`$F011` read-clear strobe, CE/Clear→display-
clear write shortcut); replaces the Message Display placeholder with a real
`MessageDisplay` at startup; Port Map Status and the new Control Panel get
real content the first time they're opened from the menu (lazy, matching
how Qt's own panels are constructed); adds real `_do_run`/`_do_step`/
`_do_halt`/`_do_reset`/`_run_tick` methods (`root.after()` replacing
`QTimer`, same 10-instructions-per-tick and clock-Hz-to-ms conversion as
the Qt build); replaces the stub `Load RAM...` menu item with a real
`tkinter.filedialog` handler using the same `.rom`→`$0000` / else→`$4000`
load-address rule and full-64KB-image special case as
`beboputer_v7.main_window._load_file()`.

**Verified** (headless, via Xvfb + `/tmp/localtk`-style local `python3-tk`
+ `tk8.6-blt2.5` install, calling the exact callables wired to
`command=`/write-hooks — equivalent to real clicks/keypresses):

- Message Display is real from startup; Port Monitor and Control Panel
  build real content the first time they're opened, and stay `None`
  until then
- Loading tutorial 17's known-good `.ram` (13/13 test cases verified
  earlier this session against a bare `CPU()`) lands the exact same
  1,020 bytes at `$4000`, resets `PC` to the reset vector, and logs the
  load to Message Display
- `Control Panel.on_step` (the literal STEP button handler) advances the
  real CPU and the bus readout tracks the live `PC`/opcode after each
  step
- Simulated keypresses (`cpu._write(0xF011, ...)`) correctly update Port
  Monitor's current-value and previous-value fields through the same
  `on_key_press()` path a real `DIYButton` click uses
- A synchronous RUN burst (200 ticks, `_run_tick()` called directly to
  avoid waiting on real `.after()` timing) runs without error
- HALT cancels the pending `.after()`; RESET restores `PC` to the reset
  vector and clears Port Monitor's display fields
- `test_harness.py`'s full 47-test suite still passes unchanged

**Not yet real:** Calculator and Memory Walker are still Phase 1
placeholders (next slices, per §4's sequencing) — Control Panel's manual
STEP/RUN is the only way to drive the CPU in this build until Memory
Walker's own step/breakpoint controls exist in tkinter.

---

## 8. Phase 2 part 2 — Calculator + DIYButton grid

Second content slice: the calculator itself, both the physical button
grid and the on/off-powered board it represents.

| File | Role |
|---|---|
| `panels/diy_button.py` | tkinter port of `beboputer_v7/tools/diy_button.py`'s two Qt *widgets* -- `DIYButton` (now a `tk.Button` subclass) and `ConfigureButtonAttributes` (now a `tk.Toplevel` dialog, right-click to open, only when the calculator is off). The file-format helpers underneath (`ButtonDef`, `load_defbuttons_file`, `save_defbuttons_file`, `COLORS`, `_color_index`, `_parse_code`, `_DEFBUTTONS_PATH`, `_BUTTONS_DIR`) have zero Qt dependency, so this module imports and reuses them directly from `beboputer_v7.tools.diy_button` rather than duplicating them -- one `Config/defbuttons.ini` format, shared by both builds. |
| `panels/calculator.py` | tkinter port of `beboputer_v7/tools/calculator.py` -- display, 6-LED top row, full digit/operator/trig button grid, On/Off + Reset/Step/Run bottom bar, defbuttons.ini load/save/Configure/Restore Defaults. |

**A discovery during the port, same shape as the DIYButton bug found
earlier this session:** the Qt `Calculator` class has its own
`.control()`/`.key_press()`/`.evaluate()`/`.trig_op()`/`.func_op()`
methods and a `_build_memory_row()` widget -- none of it is live code.
Tracing every call site shows the display is driven *only* by port
`$F031` (`write_display`, called from the CPU write hook `main_window.py`
wires up) and the 6 LEDs *only* by `$F032` (`write_leds`) -- every
calculator key, including the ones named `Clear`/`CE`/`Back`/`Enter`
that share a name with branches inside `.control()`, is actually a
`DIYButton` that writes its configured code to `$F011` and lets the
CPU-resident program decide what happens next. `.control()` itself is
only ever invoked by the four *non*-DIYButton bottom-bar buttons
(On/Off, Reset, Step, Run), so its Clear/CE/Back/Enter branches, the
whole expression-evaluator, and `_build_memory_row()` (defined but never
called, even in the Qt file) are unreachable. None of that dead code
was ported -- `panels/calculator.py`'s module docstring documents the
tracing that led to this conclusion, the same way `main_window.py`
already documents why `control_panel.py` was found dead in Phase 2 part 1.

`main_window.py` changes: constructs `Calculator(child.content,
host_main=self)` as real content the first time (and every time --
Calculator is a startup panel) the "calculator" `MdiChild` is built,
and wires the CPU's `$F031`/`$F032` write hooks to
`calculator.write_display`/`calculator.write_leds` at that point,
mirroring the Qt build's `_calc_win = Calculator(self)` +
`cpu._write_hooks[...]` pair. Also ports `_do_random_fill_ram()` /
`_do_power_off_ram()` / `_on_power_changed()` from
`beboputer_v7.main_window` unchanged in behaviour: real SRAM powers up
with random garbage, not zeros, so power-on fills `$4000`-`$FFFF` with
random bytes (ROM at `$0000`-`$3FFF` stays zeroed/defined) rather than
auto-running anything meaningful; power-off marks RAM "undefined" in
Memory Walker's sense without touching the underlying values.
`_do_reset()` now actually calls `calculator.blank_display()` when
`clear_calc_display=True`, completing the parameter that Phase 2 part 1
added to the signature but didn't yet act on.

**Verified** (headless, via Xvfb, calling the exact same callables a
click invokes):

- Calculator is real from startup (all 3 startup panels -- Calculator,
  Memory Walker placeholder, Message Display -- tile correctly as before)
- All 69 `DIYButton`s build and load their real codes from
  `Config/defbuttons.ini` (Sin `$3A`... consistent with the codes this
  session already verified against the live Qt app)
- Power-on shows the 24-dash boot placeholder and enables Reset/Step/Run;
  power-off blanks the display and disables them again
- Loading tutorial 17's `.ram` and driving real `DIYButton._execute()`
  calls (the literal left-click handler) writes the exact configured
  code to `$F011`; stepping the CPU afterward drives the display back
  through the real `$F031` write hook, confirming the full loop --
  DIYButton click -> CPU port -> program logic -> display port ->
  Calculator screen -- works end-to-end, not just each half in isolation
- `test_harness.py`'s full 47-test suite still passes unchanged

**Not yet real:** the right-click Configure Button Attributes dialog
opens correctly but wasn't driven through a full edit-and-persist cycle
in headless verification (no synthetic right-click event source under
Xvfb without a window manager) -- worth a manual check on real Windows.
Memory Walker is still the next slice.
