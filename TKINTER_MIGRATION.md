# Migrating PY-DIYCALCULATOR from PyQt5 to tkinter

**Status:** Phase 0 (spike/validation) complete. Not started: Phase 1 onward.
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
| Windows Hi-DPI scaling — no `AA_EnableHighDpiScaling` equivalent | **Spiked, needs real-hardware validation.** See §3.3 |
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

**Caveat — this is the one spike that couldn't be fully validated here.**
This sandbox is Linux with no real display DPI to test against. The
self-test confirms the module imports cleanly, the Windows-only code
paths no-op safely on other platforms, and `apply_dpi_scaling()` doesn't
raise against a real Tk root — but it **cannot** confirm the actual
visual result (crisp rendering at 125%/150%/200%, correct behavior when
dragging a window between monitors of different DPI). The Windows API
calls used are standard and well-documented, but this needs a real test
pass on your Windows hardware with a Hi-DPI display before being trusted.

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

1. **Phase 1 — infrastructure.** New `app.py` entry point: `Tk()` root +
   `dpi_awareness.py` wired in, `MdiArea` shell, menu bar/toolbar/status
   bar. CPU engine and assembler are reused unchanged.
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
3. **Phase 3 — platform validation.** Windows Hi-DPI real-hardware test
   pass (§3.3's open item), Raspberry Pi touchscreen validation (button
   sizes, small-screen layout fallback, touch-drag on `MdiChild` title
   bars), macOS if relevant.
4. **Phase 4 — regression pass.** `test_harness.py` and
   `tests/test_*.py` don't touch the GUI at all, so they stay green
   throughout — but every tutorial and `Data/*.asm` file needs a manual
   click-through against the new GUI. Rebuild both the `.deb` and the
   Windows installer (PyInstaller still bundles tkinter's Tcl/Tk runtime,
   so the release pipeline shape stays similar — output should be
   noticeably smaller than the current PyQt5 build).

---

## 5. Risks carried forward from Phase 0

1. **Printing** — real capability gap, no tkinter framework to build on.
   Needs a product decision (drop printing entirely / PDF-export-only /
   shell out to the OS print command) before Phase 2 reaches any panel
   that currently prints.
2. **MDI feel** — independent `Toplevel`-based `MdiChild` windows versus
   Qt's `QMdiSubWindow`; functionally equivalent per §3.1, worth a Pi
   touchscreen sanity check once real content is in the panels.
3. **Hi-DPI** — implemented per standard practice, **not yet verified
   visually** on real Windows hardware. Treat as the top item to test as
   soon as Phase 1 has a running window.
4. **Multi-monitor geometry** — no tkinter equivalent spiked yet for
   `QScreen.availableGeometry()`; needed for maximize/panel-layout
   parity with this session's Qt fixes.
5. **Sound** — no tkinter built-in; small gap, low effort either way
   (drop or shim).
