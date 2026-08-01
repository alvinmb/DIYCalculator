# Migrating PY-DIYCALCULATOR from PyQt5 to tkinter

**Status:** Phase 0 (spike/validation) complete — all three spikes
verified working, including Hi-DPI on real Windows hardware. **Phase 1
(app shell) complete** — see §5. **Phase 2 is now feature-complete**
(parts 1-6) — every panel and dialog in the Qt app's menu structure now
has real tkinter content: CPU wiring, Message Display, Port Monitor,
Control Panel, Calculator + DIYButton grid, Memory Walker, CPU
Registers, Terminal, Disassembler, Assembler/Editor, Workbench 1,
Keyboard, EPROM Burner, System Clock, About — see §7-§12. Remaining
gaps are deliberate, tracked ones: printing, sound, Font dialog,
inline Memory Walker DATA-cell editing, multi-monitor geometry (all
already called out in §2/§6 and the per-part sections below). Not
started: Phase 3 (platform validation) and Phase 4 (regression pass).
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

---

## 9. Phase 2 part 3 — Memory Walker

Third content slice: the hardest panel per §4's sequencing, de-risked
ahead of time by the Phase 0 spike (§3.2).

| File | Role |
|---|---|
| `panels/memory_grid.py` | The 256-row BP/STEP/ADDRESS/DATA table widget, promoted from `prototypes/tkinter_migration/memory_grid.py` (same one `tk.Text` + per-substring color tags approach, verified at ~9.3ms/refresh in Phase 0). Two changes from the spike: breakpoints and the view's base address are no longer owned by the grid widget itself (that was a spike-only convenience) -- they're owned by `MemoryWalker` now, matching the Qt panel's `self._breakpoints`/`self._base`, so `main_window.py` can inspect `mem_walker._breakpoints` directly the same way the Qt build's `_run_tick()` does. Added `scroll_to_offset()`, matching Qt's `scrollToItem()` call that keeps the ▶ PC marker in view. |
| `panels/memory_walker.py` | tkinter port of `beboputer_v7/panels/memory_walker.py` -- Address/GO/Go to PC navigation, RUN to BP, Clear BPs, Walk 64K (continuous 64K auto-paging), status line, and the embedded grid. Same `_user_nav` flag semantics as Qt: manual navigation (GO or Walk) suspends PC-following until you step again or click Go to PC. Default breakpoint at `$0000` preserved (catches the `JMP [$0000]` NOP-sled idiom several tutorials use as an old-style HALT). |

`main_window.py` changes: builds a real `MemoryWalker(child.content,
self.cpu, on_step_executed=..., on_bp_hit=...)` the first time the
"mem_walker" panel is opened (it's one of the three startup panels, so
this happens immediately at launch, same as Calculator/Message
Display). `_refresh_all()` now also calls `mem_walker.highlight_pc()`
after every step/run, so the ▶ marker tracks the live PC regardless of
whether execution was driven from Control Panel, Memory Walker's own
STEP column, or a future Calculator Step click. `_run_tick()` (the
Control-Panel-driven Run loop) now checks `mem_walker._breakpoints`
inside its per-instruction loop and stops with a status message on a
hit -- previously (Phase 2 part 1) Run ignored breakpoints entirely,
the same gap the Qt build itself once had and fixed. Two new callbacks,
`_on_mem_walker_step`/`_on_mem_walker_bp_hit`, log to Message Display
and refresh other panels when Memory Walker's *own* controls (not
Control Panel) drive execution -- mirroring the Qt build's
`step_executed`/`bp_hit` signal connections.

**Verified** (headless, via Xvfb):

- Grid renders real addresses/data from cold construction (`$0000` shows
  `00`, not `XX`, since ROM is marked "known" even before power-on)
- Loading tutorial 17's `.ram` and single-stepping via Memory Walker's
  own `_do_step()` (the literal STEP-column click handler) advances the
  real CPU, updates the status line with the live mnemonic, and fires
  the `on_step_executed` callback
- Breakpoint toggle (the literal BP-column click handler,
  `_toggle_bp()`) sets and clears `_breakpoints` correctly
- `run_to_breakpoint()` genuinely stops exactly at a breakpoint address
  reached mid-program (verified by single-stepping 3 real instructions
  first to learn a real future PC, setting a breakpoint there, resetting,
  and confirming Run-to-BP halts at that exact address after exactly 3
  steps) -- not just "doesn't crash," an actual correct stop
- A longer `run_to_breakpoint()` run against an unreached breakpoint
  correctly terminates at the `RUN_LIMIT` (500,000) safety cap rather
  than hanging
- Control-Panel-driven `_run_tick()` (500 ticks / 5,000 instructions)
  runs without error with Memory Walker's breakpoint check wired into
  the loop
- `test_harness.py`'s full 47-test suite still passes unchanged

**Not yet real:** double-click-to-edit a DATA cell in place (Qt's
`QTableWidget` supports inline cell editing; the `Text`-based grid would
need a floating-`Entry`-on-click overlay to match -- real UI work, not a
mechanical port). RAM can still be changed via File > Load RAM in the
meantime. `ideal_width()` (Qt-only exact-pixel subwindow sizing) has no
tkinter equivalent need since `MdiChild` panels are already sized via
`PanelSpec`/`tile_children()`.

---

## 10. Phase 2 part 4 — CPU Registers, Terminal, Disassembler

Three smaller panels, ported together since each is a direct,
mechanical port with no dead-code surprises this time.

| File | Role |
|---|---|
| `panels/cpu_panel.py` | tkinter port of `beboputer_v7/panels/cpu_panel.py` -- the 6-register LCD-style grid (Accumulator, PC, Instruction Reg, Index Reg, Interrupt Vector, Stack Pointer) plus the 5-flag Status Reg row (I/O/N/Z/C). Also ports the two small display widgets it depends on (`beboputer_v7/widgets/leds.py`'s `LEDDisplay`/`FlagLight`) as local `tk.Label` subclasses inside the same file, since nothing else uses them yet. Untouched flags render as italic grey `x` (never-written) vs. `0`/`1`, same three-state design as Qt. |
| `panels/terminal.py` | tkinter port of `beboputer_v7/panels/terminal.py` -- the `$F028`-driven CRT-style output device, raised/sunken bevel frame, black-screen-when-off / white-screen-when-on styling tied to Calculator power state. |
| `panels/disassembler.py` | tkinter port of `beboputer_v7/panels/disassembler.py` -- From/Disassemble text output. `cpu.disassemble_at()` does all the real decoding and has zero Qt dependency, so it's reused completely unchanged; this panel is just the address-box + text-output wrapper around it. |

**A third dead-code trace, same pattern as the DIYButton and Calculator
findings:** `beboputer_v7.main_window._check_port_output()` forwards
`cpu.ports_out[1]` to the terminal on every refresh -- but nothing in
`cpu.py` ever writes to `ports_out[1]`; it's leftover from an older
port-based I/O model that predates the `$F028` memory-mapped write hook
actually in use. Not ported here (the real `$F028` hook is, and does
the actual work) -- documented in `panels/terminal.py`'s module
docstring.

`main_window.py` changes: builds real content for "cpu", "terminal",
and "disassembler" the first time each is opened from the Display menu
(all three are Phase 1 placeholders until then, same lazy-build pattern
as Port Monitor/Control Panel). Wires the `$F028` write hook to
`terminal.write_char` at that point. `_refresh_all()` now also calls
`cpu_panel.refresh()` and `disassembler.refresh_at_pc()` when those
panels are open. `_do_reset()` now calls `terminal.clear()`.
`_on_power_changed()` now calls `terminal.set_power(on)`, so the
terminal screen goes black/white in step with the calculator exactly
as in Qt.

**Verified** (headless, via Xvfb, through the real menu-handler and
CPU-hook call paths):

- CPU Registers panel shows the live PC and correctly renders
  never-written flags as `x`
- Terminal silently discards writes while powered off, then renders
  characters correctly once powered on (via Calculator's On/Off), and
  a direct `cpu._write(0xF028, ...)` -- the same path a real `STORE
  ($F028), A` instruction takes -- reaches the screen
- Disassembler shows real decoded instructions starting at `$4000`
  after loading tutorial 17's `.ram`, and stays in sync with the live
  PC after a step (via `_refresh_all()`)
- Reset clears the terminal screen
- `test_harness.py`'s full 47-test suite still passes unchanged

---

## 11. Phase 2 part 5 — Assembler / Editor

The full source-editing workflow: write/edit `.asm`, assemble it, load
the result straight into the running CPU.

| File | Role |
|---|---|
| `panels/compiler.py` | tkinter port of `beboputer_v7/tools/compiler.py`'s `CompilerWindow`. `AssemblerRunner` (compile / write-`.ram` / write-`.lst` / load-into-CPU) has zero Qt dependency and is imported straight from `beboputer_v7.tools.compiler` rather than duplicated -- same reuse pattern as `diy_button.py`'s file-format helpers. |

**A real gap, not a dead-code trace this time:** tkinter's `Menu`
widget can only attach to a `Toplevel`/`Tk` root, not to an arbitrary
`Frame` -- so a `CompilerPanel` living inside an `MdiChild` can't have
a true attached menu bar the way the Qt `CompilerWindow` (a real
`QMainWindow` with its own `menuBar()`) does. Built File/Edit/Insert as
a row of `tk.Menubutton` + `tk.Menu` dropdowns instead -- functionally
identical (click it, a menu drops down, same items), visually a button
row rather than a native strip. Keyboard accelerators (Ctrl+N/O/S,
F5, Ctrl+F, F3, Ctrl+G) are bound to the editor widget specifically,
not `bind_all()`, so they don't leak into other text widgets elsewhere
in the app if more than one Compiler panel is ever open at once.

Ported: New / Open / Save / Save As, Assemble, Load -> CPU (with the
same "calculator must be powered on" gate as the Qt version), Find /
Find Next / Go to Line, Insert Directive/Instruction snippets, Insert
String, Insert File. Also added `MdiChild.set_title()` (a small,
generically useful addition to `mdi.py`) so the panel can update its
own title bar to show the current filename, matching Qt's
`setWindowTitle()` calls on Open/Save/New.

**Not ported:** Font... (`QFontDialog` has no tkinter built-in --
already flagged as a low-priority gap in §2's table) and Printer
Setup/Print (no tkinter printing framework -- the same gap §6 already
carries forward from Phase 0, still unresolved and now hit for real by
a second panel).

**Verified** (headless, via Xvfb, through the real menu/button
handlers): opening the panel via the Tools menu; loading tutorial 17's
actual `.asm` source into the editor and running the real `on_compile()`
-- confirmed it assembles to the exact same 1,020 bytes verified earlier
this session, and writes real `.ram`/`.lst` files to disk; `on_load_into_cpu()`
(gated on calculator power, same as Qt) writes the compiled bytecode into
the live CPU's RAM at `$4000`; `Find` selects real matched text in the
editor via `tag_add("sel", ...)`; line navigation moves the insertion
cursor to a real target line; `New` correctly resets editor/state.
`test_harness.py`'s full 47-test suite still passes unchanged.

---

## 12. Phase 2 part 6 — Workbench 1, Keyboard, EPROM Burner, System Clock, About

The last slice: everything remaining in the Qt app's Setup/Tools/Help
menus.

| File | Role |
|---|---|
| `panels/workbench.py` | tkinter port of `beboputer_v7/tools/workbench.py` -- 2× 8-bit switch banks (`$F000`/`$F001`), an 8-LED bar and three 7-segment displays driven by CPU write hooks (`$F022` LEDs, `$F021` un-decoded 7-seg, `$F023` decoded 7-seg, `$F024` dual decoded 7-seg -- see the visual-simplification and constant-mismatch notes below). Inert until the calculator powers on, same as Qt. |
| `panels/keyboard.py` | tkinter port of `beboputer_v7/tools/keyboard.py` -- full on-screen keyboard (ESC row through bottom row), CAPS/SHIFT case toggling, hex readout of the last key sent to `$F011`, optional terminal-echo callback. |
| `dialogs/eprom_burner.py` | tkinter port of `beboputer_v7/dialogs/eprom_burner.py` -- Browse/Burn ROM/Load ROM/Swap ROMs against a CPU RAM address range, same "calculator must be on" gate as Load RAM. A fresh dialog every time it's opened, matching Qt. |
| `dialogs/system_clock.py` | tkinter port of `beboputer_v7/dialogs/system_clock.py` -- Hz entry with 1-10,000 range validation. Qt's blocking `exec_()` has no single tkinter widget equivalent, so `ask_hz()` reproduces the same blocking-modal call shape via the standard `grab_set()` + `wait_window()` pattern. |
| `dialogs/about.py` | tkinter port of `beboputer_v7/dialogs/about.py`. |

**A real visual simplification, not a dead-code trace:** the Qt
Workbench's un-decoded and decoded 7-segment displays are rendered
from photographic `BITMAPS/USEGn.BMP`/`DSEGn.BMP` assets via `QPixmap`.
tkinter's `PhotoImage` has no built-in BMP decoder (GIF/PGM/PPM/PNG
only, without adding a Pillow dependency this migration hasn't needed
anywhere else), so all three segment displays are drawn as vector
polygons on a `tk.Canvas` instead -- same segment-bit truth table
(`_DIGITS`), same on/off colors and blank-vs-lit-zero distinction, just
line-drawn rather than photorealistic. Also not ported: the switch-click
`.wav` sound (`QSound`, no tkinter equivalent -- same already-flagged
Sound gap).

**A genuine pre-existing discrepancy, left as-is:** `workbench.py`'s
module docstring documents the port map as `$F020`/`$F021`/`$F022`/`$F023`,
but the actual `ADDR_*` constants the working code uses are
`$F000`/`$F001`/`$F022`/`$F021`/`$F023`/`$F024`. This mismatch already
existed in the Qt source (not introduced by this port) -- the tkinter
port uses the real, working constants (copied from the code, not the
stale comment) and flags the discrepancy in its own docstring rather
than silently "fixing" behavior that wasn't asked about.

`main_window.py` changes: `_show_eprom()` now constructs a real,
fresh `EpromBurner` Toplevel each time (matching Qt's per-open
construction) instead of routing through the placeholder-panel
machinery. `_set_clock()` calls the real blocking `ask_hz()` and
updates `self._clock_hz`. `_load_button_file()`/`_save_button_file()`/
`_restore_defaults()` -- previously `_not_yet()` stubs even though
`Calculator` has fully implemented these methods since Phase 2 part
2 -- now delegate to the calculator, matching Qt's own
`BebopMain._load_button_file()`-style delegation. `_show_about()` now
opens the real dialog instead of a plain `messagebox`. Workbench
follows calculator power state and syncs from RAM when opened; Reset
now also resets Workbench's switches/outputs.

**Verified** (headless, via Xvfb, through real widget/hook call
paths): Workbench switch-bank writes reach `$F000`; all three CPU
write hooks (`$F021`/`$F022`/`$F023`/`$F024`) drive their real
Workbench widgets; Keyboard's case handling and hex readout are
correct for a real keypress; EPROM Burner's Burn ROM writes an actual
`.rom` file from a real CPU RAM range and Load ROM reads it back
correctly; System Clock's dialog validates in-range/out-of-range
input correctly (real logic, not just "doesn't crash"); About opens.
`test_harness.py`'s full 47-test suite still passes unchanged.

---

## 13. Menu / form review pass

After Phase 2 reached feature-complete, did a dedicated pass over
every menu handler and form in `bin/beboputer_tk/` looking for wiring
bugs -- not new content, just correctness of what's already there.

Found and fixed three menu items left as `_not_yet()` stubs despite
their Qt equivalents being fully real, working features (not
placeholders) -- worth calling out since it would've been easy to
assume "stub" meant "nothing to port" without actually checking:

- **New/Save/Save As Project, Save RAM** -- Qt's versions really do
  clear all RAM + reset the CPU (New), and really do write a full
  64KB `.rom` dump of `cpu.ram` to a chosen file (Save/Save As/Save
  RAM are all the same handler in Qt too). Ported faithfully,
  including a quirk worth knowing about: New Project resets
  `cpu.ram` to a fresh all-zero `bytearray` but does *not* reset
  `ram_touched`, so Memory Walker can briefly show stale "touched"
  flags against the new zeroed data -- Qt's real behavior, kept as-is
  rather than "fixed" mid-port.
- **Purge RAM** -- really zeroes all 64KB and marks it all "known"
  (distinct from New Project, which leaves `ram_touched` alone).
- **Find Address** -- removed from the Memory menu; Memory Walker's
  own Address field + GO button already do the identical
  `_user_nav`-locks-the-view jump, so the separate dialog was a
  redundant second entry point to the same behavior.
- **Help / DIY Calculator on the web / Credits** -- Help opens the
  bundled `beboputer_v7_help.html` in the system browser (same
  source/bundle path resolution as Qt); the web link opens the same
  external URL; Credits shows the same message. All three use
  `webbrowser.open()`, stdlib and Qt-free.

Verified via a full headless sweep (`xvfb-run`) calling every single
menu handler once -- Display menu panel opens (including re-opening
an already-open panel, confirming raise-not-duplicate), File/Setup,
Memory, Help, and CPU ops (Step/Run/Halt/Reset against a real loaded
program) -- with blocking dialogs (file pickers, `messagebox`, the
System Clock modal) neutered so the sweep runs unattended; every
handler completed with no exception. Followed by targeted checks
*not* covered by the blanket sweep (since it mocks dialog return
values to empty/None): Save Project writes a real, correctly-sized
RAM dump with the right byte at the right offset, and New Project
actually zeroes `cpu.ram`. `test_harness.py`'s full 47-test suite
still passes unchanged. (Find Address was later removed from the
Memory menu -- see note above -- so it's no longer part of this
sweep.)

Remaining `_not_yet()` fallbacks (Load/Save Button File, Restore
Defaults) are defensive-only: they delegate to the Calculator
instance and only trigger in the unreachable-in-practice case where
the Calculator startup panel has been closed.
