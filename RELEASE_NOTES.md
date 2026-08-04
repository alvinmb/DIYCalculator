# PY-DIYCALCULATOR — Release Notes

## v10.1.4 — 2026-08-04

### Added

- **Code Coverage tool** (`beboputer_tk`, Tools > Code Coverage...)
  -- revives the Code Coverage utility pitched in
  `Educators/more-tools-code-coverage.ppt`. Load a `.asm` source, then
  either Run Program (fast headless burst) or Track Live (records real
  Step/Run/Memory Walker activity), and see which source lines actually
  executed vs. never ran, highlighted green/red, with a percentage
  summary and a saveable text report. Hits accumulate across runs until
  Reset Coverage is pressed. Also available headless via
  `bin/beboputer_tk/tools/coverage_cli.py`.
- **Code Profiler tool** (`beboputer_tk`, Tools > Code Profiler...)
  -- revives the Code Profiler utility pitched in
  `Educators/more-tools-code-profiler.ppt` (the 80:20 rule). Same
  Load Source / Run Program / Track Live workflow as Code Coverage,
  ranking source lines by share of total execution with a per-line
  ASCII bar chart and a 4-tier heat-map highlight, plus a "Hot Spots"
  summary of the busiest lines. Also available headless via
  `bin/beboputer_tk/tools/profiler_cli.py`.

## v10.0.4 — 2026-08-04

### Added

- **Vertical scrollbar on the Assembler's Messages panel** (`beboputer_tk`)
  -- previously only the Source editor had scrollbars; long compile output
  had no way to scroll.

### Changed

- **Assembler/Disassembler text backgrounds** now match the Calculator's
  own LCD color instead of plain white/grey.
- **Assembler "Assemble" / "Load -> CPU" buttons** are grey again, matching
  every other button in the app (they were rendering white).
- **Assembler Messages panel is now cleared on File > New and File > Open**
  -- previously only New cleared it, so opening a different source file
  left the prior file's stale compile messages on screen.
- **Tutorial 14 (Hex/Bin Conversion)**: the display is now cleared before
  the first digit/bit is echoed when starting a Hex or Bin entry, so the
  leftover boot-placeholder dashes no longer show up mixed in with the
  first conversion's result.

## v10.0.3 — 2026-08-03

### Added

- **File dialogs default to the app's workspace directory.** Open
  Project, Save Project As, Load RAM, and Save RAM previously opened
  wherever the OS felt like (often the install folder, which isn't
  writable once packaged). Now use the same cross-platform
  `default_open_dir()` / `default_save_dir()` convention already used by
  the compiler and calculator panels.
- **"Beboputer Databook" launch point in the About dialog**, plus an
  HTML edition of *The Official DIY Calculator Data Book* to open
  (`help/databook/`, converted from the original PDF with `pdftohtml` --
  one background image per page so the original schematics/pinout
  diagrams render exactly as before).
- **`help/` directory** — `beboputer_v7_help.html` and `databook/` now
  live together here (moved out of `bin/` and `Data/` respectively),
  bundled as a single folder in every build (source, `.deb`, and the
  frozen Windows/macOS PyInstaller build) so the help file's own
  relative links resolve identically everywhere.

### Changed

- **The Official DIY Calculator Data Book.pdf is no longer shipped** in
  any packaged build (Windows installer, `.deb`, macOS `.app`) -- fully
  superseded by the HTML edition above. `beboputer_v7_help.html`'s
  "detailed instruction description" link now points at the HTML
  edition instead of the PDF.
- **Purge RAM confirmation dialog** replaced the tiny stock
  `messagebox.askyesno` with a custom dialog at ~2x font size, sized to
  match, so it's actually legible.

## v10.0.2 — 2026-08-03

### Added

- **`tests/test_gui_smoke.py`** — a visual regression smoke test for the
  tkinter build. Every existing test (`test_cpu.py`,
  `test_compiler_core.py`, `test_asm_regression.py`, ...) exercises the
  CPU/assembler directly and never touches a single widget, so nothing
  in this repo previously caught a panel or dialog silently rendering
  blank, zero-sized, or raising on open. Drives every menu command that
  opens a panel/dialog (Calculator, Memory Walker, Message Display, CPU
  Registers, Terminal, Port Map Status, Disassembler, Keyboard,
  Workbench 1, Assembler/Editor, EPROM Burner, About, System Clock,
  Credits) and asserts each one actually renders; also writes best-effort
  screenshots to `tests/gui_screenshots/` (gitignored) for manual visual
  review. Requires a real or virtual (Xvfb) display -- skips cleanly if
  none is available.

### Fixed

- **`SevenSeg._cache` (Workbench 7-segment displays) held `PhotoImage`
  objects in a class-level dict shared across every instance**, but a
  `PhotoImage` belongs to whichever Tcl interpreter created it. A single
  real run of the app only ever has one `tk.Tk()` root for its whole
  lifetime, so this never affected actual usage -- it surfaced when the
  new GUI smoke test suite (above) created more than one root in the
  same process, reusing a cached image from a since-destroyed
  interpreter and raising `"image ... doesn't exist"`. Now validates a
  cached image is still alive before trusting it.
- **Startup panel layout could measure the window before the OS had
  actually resized it**, also caught by the new test suite (Message
  Display rendering at 1x100): `BebopMain.__init__` requested
  `zoomed`/`1200x800` and immediately built the menu bar and MDI area
  without giving the window manager's response a chance to land first,
  so `tile_children()`'s measurement of the MDI area's width could still
  reflect the pre-request size. Added one `root.update()` right after
  the geometry/state request.

## v10.0.1 — 2026-08-02

### Fixed

- **Tkinter Windows installer was bundling all of PyQt5/Qt5** despite
  `beboputer_tk` never importing it -- two panel modules
  (`panels/compiler.py`, `panels/diy_button.py`) imported "pure logic"
  pieces (`AssemblerRunner`, `ButtonDef` and the `defbuttons.ini`
  helpers) from `beboputer_v7` files that also had unconditional
  top-level `PyQt5` imports for unrelated Qt UI classes living in the
  same file, so PyInstaller's dependency analysis pulled in the whole
  Qt5 runtime. Split the Qt-free logic out into two new modules with
  no PyQt5 import (`beboputer_v7/tools/button_defs.py`,
  `beboputer_v7/tools/assembler_runner.py`); the Qt build's own files
  re-export the same names unchanged.
- **Main window opened stuck at its default size, centered on screen,
  and couldn't be dragged** on a Raspberry Pi 5 -- some Linux window
  managers accept the startup `root.state("zoomed")` request without
  error but never actually resize the window, and treat it as
  "maximized" regardless, refusing to let it move. Now verified after
  the window is fully built and falls back to sizing it to the screen
  manually if "zoomed" didn't really take effect.
- **Top-level menu dropdowns (File/Setup/Display/Memory/Tools/Help, and
  the Assembler/Editor panel's own File/Edit/Insert row) stopped
  responding to clicks** on the same Pi -- `tk.Menubutton`'s built-in
  auto-post mechanism only ever posted the first menu in a bar.
  Switched to posting each menu manually via `tk_popup()`, letting Tk
  manage its own grab/ungrab internally rather than pairing it with an
  extra manual `grab_release()` (an earlier attempt at this fix, which
  caused the entire app -- not just menus -- to stop responding to any
  click at all).
- Removed the always-visible scrollbar track around the Calculator
  panel -- the panel auto-sizes to its exact content on open, so the
  scrollbars never actually had anything to scroll; the canvas/mouse
  wheel fallback stays in place invisibly for the rare case a window
  manager can't honor the full requested size.

### Changed

- Removed the Control Panel tool (RUN/STEP/HALT/RESET + bus readout +
  manual switches) from the tkinter build -- redundant with controls
  already available on the Calculator (Step/Run buttons) and Memory
  Walker (RUN to BP / STEP), so it added a panel without adding any
  capability.
- New splash artwork (`bin/splash.png`, `bin/splash_about.png`) with a
  red "PYTHON / VERSION" banner; the previous artwork is kept at
  `bin/oldsplash.png`.
- `bin/beboputer_v7_help.html` (the in-app Help document, shared by
  both builds) now documents the Setup menu (System Clock, Interrupt,
  Load/Save Button File, Restore Defaults) and corrects the File Menu
  section, which had Project (`.prj`, the whole session) and Load/Save
  RAM (`.rom`/`.ram`, RAM only) backwards.

## v10.0.0 — 2026-08-01

### Changed

- **The tkinter rebuild (`beboputer_tk`, `run_beboputer_tk.py`) is now
  the primary, actively developed build** — a from-scratch port of
  every panel and dialog in the original PyQt5 app (Calculator,
  Memory Walker, CPU Registers, Port Monitor, Disassembler, Assembler/
  Editor, Terminal, Keyboard, Workbench, EPROM Burner, System Clock,
  Control Panel, Message Display, and File > Project save/restore),
  followed by an extensive UI-polish pass across nearly every panel:
  consistent font sizing and matching between related panels/dialogs,
  auto-fit-then-lock panel sizing (no more clipped or oversized
  windows), the Memory Walker grid gained real column/row grid lines
  and rectangular buttons, the Workbench's 7-segment displays now use
  real bitmap art instead of vector approximations with correctly
  aligned LEDs, the Interrupt feature was ported over from Qt's
  toolbar, and the About dialog now shows the splash artwork. This is
  a MAJOR version bump because the tkinter build is now the intended
  installation target going forward, superseding the PyQt5 build
  (`beboputer_v7`, `run_beboputer_v7.py`) as the primary distributed
  app — PyQt5's licensing (GPL/commercial dual license) makes it
  unsuitable to keep carrying forward as a distributed build, whereas
  tkinter ships with the Python standard library under the PSF
  license, with no separate licensing terms to track. The Qt build's
  source remains in the repo for reference but will not receive
  further installer/package releases.
- **New Windows installer and .deb build scripts for the tkinter
  build**, under `bin/beboputer_tk/`: `beboputer_tk.spec`
  (PyInstaller), `build_installer.bat` + `beboputer_tk_setup.iss`
  (Inno Setup installer, must be run on Windows), and
  `RPI_INSTALL/build_deb.sh` + `build_deb.bat` (Debian/Raspberry Pi
  package, depends on `python3-tk` instead of `python3-pyqt5`).
  Mirror the existing `beboputer_v7` build scripts structurally; all
  read the version from the same single source of truth
  (`bin/beboputer_v7/__init__.py`'s `__version__`, which `beboputer_tk`
  re-exports unchanged) so there's one version number for the app
  regardless of which UI build is packaged.

## v9.0.29 — 2026-07-31

### Fixed

- **`DIYButton._execute()` silently corrupted any non-digit button whose
  `Code=` value fell in the ASCII digit/hex-letter ranges `$30`-`$39` or
  `$41`-`$46`**: a leftover translation step (meant to turn ASCII '0'-'9'
  / 'A'-'F' into raw nibbles 0-15) rewrote those bytes down before they
  reached the CPU port, even though every digit/hex button in the current
  `Config/defbuttons.ini` already stores its raw nibble code directly and
  never needed the translation. This silently broke `Cos` (`$39`→`$09`),
  `Tan` (`$38`→`$08`), `Log` (`$37`→`$07`), and `n!` (`$36`→`$06`) — each
  landed on the CPU as a plain digit instead of its real function code,
  so any program reading the keypad for one of those keys (e.g.
  `tutorial/17_bcd_scientific_calculator.asm`'s Cos/Tan/n!) never saw it
  pressed. `Sin` (`$3A`) escaped only by being one byte outside the
  range. Fixed by removing the translation entirely — `_execute()` now
  writes `self._defn.value` to the port unchanged.
- **`tutorial/17_bcd_scientific_calculator.asm` didn't clear the display
  on start**, so the exercise could open showing whatever the previously
  run program last left on screen. `START` now writes the clear code
  first.

## v9.0.28 — 2026-07-30

### Fixed

- **`Config/defbuttons.ini`'s operator row was scrambled**: `+`/`-`/`*`/`/`
  had their Annotations and Codes rotated relative to their own
  Description fields, and two buttons both claimed `Code= $17`
  (annotated `*`, described "Subtract" and "Multiply"). Corrected to
  `+`=`$16`, `-`=`$17`, `*`=`$18`, `/`=`$19`, matching the dispatch
  table already used by `Data/2funcal.asm` and `Data/lab5a`-`e.asm`
  (which needed no code changes as a result — their table was right
  all along). Also fixed `Mod` (was `$1C`, colliding with `Pi`) to
  `$1D`, and swapped the `Mod`/`=` buttons' Description fields back
  to match their own Annotation ("Equals" had drifted onto `Mod`,
  and `=`'s description read "Display remainder of division").
- **5 tutorial files used stale keypad codes** predating the current
  `Config/defbuttons.ini` scheme: `tutorial/10, 11, 12, 13, 14`
  checked Clear as `$1B`/CE as `$7F` (now `$10`/`$11`), and 10 + 13
  additionally checked `+/-/*//` as `$2B/$2D/$2A/$2F`, `=` as `$3D`,
  and Enter as `$0D` (now `$16/$17/$18/$19`, `$1A`, `$13`). Fixing
  the operator codes also required translating the raw keypad code
  to its ASCII glyph before echoing it to the display in `10` and
  `13` — the new codes ($16-$19) aren't in the ranges `write_display()`
  recognizes as characters, unlike the old scheme where the keypad
  code and the display glyph happened to be the same byte. `12` also
  had its own separate Sin/Cos/Tan code mismatch (was `$73/$63/$74`
  from `_BUTTON_DEFAULTS`, corrected to `$3A/$39/$38` from the ini).
  All 5 files re-verified against the CPU simulator after the fix.

## v9.0.27 — 2026-07-30

### Fixed

- **Clear and CE button codes were swapped in `Config/defbuttons.ini`.**
  `Clear` was `Code= $11` and `CE` was `Code= $10`; corrected to
  `Clear = $10` / `CE = $11`. Both codes already triggered the same
  display-clear side effect in `main_window.py` (`if val in (0x10,
  0x11)`), so this didn't affect that behavior, but any example
  program distinguishing between the two keys needed them the right
  way round.

## v9.0.26 — 2026-07-30

### Fixed

- **The packaged `Config/defbuttons.ini` is now actually loaded.**
  Previously, on first run (no per-user button file yet), the app
  seeded buttons purely from `_BUTTON_DEFAULTS` -- an in-code table
  keyed by button label, which only covers labeled buttons. Many
  buttons have no label but a real, meaningful `Code=` value in the
  shipped `defbuttons.ini` (e.g. Button 1: no Annotation, `Code= $40`)
  -- those silently came up as `Code= $00`/"Unassigned" on a fresh
  install, which is enough to make some example `.asm` programs fail.
  `Calculator` now loads the packaged `Config/defbuttons.ini` (via
  `resource_path()`, so this works correctly in a source run, the
  Windows PyInstaller build, and the `.deb`'s `/usr/share/beboputer/`
  layout) as the real seed on first run, then saves that as the active
  per-user file exactly as before -- Load Button File / Configure
  Button Attributes / Save As all still work unchanged, so a user's
  own customizations still fully override this.
- **"Restore Defaults" now restores the real per-button Code, not just
  Color.** Same root cause as the color bug fixed in v9.0.25: the
  `_BUTTON_DEFAULTS` fallback it used doesn't cover unlabeled buttons,
  so restoring used to reset their codes to $00 too. It now restores
  every button from the same packaged `defbuttons.ini`, falling back
  to the old label-keyed behavior only for a button index that file
  doesn't cover.

## v9.0.25 — 2026-07-30

### Fixed

- **"Restore Defaults" turned every calculator button black.**
  `Calculator._restore_defaults()` hardcoded `color_index = 0` (Black)
  for every button regardless of its real default color, instead of
  restoring each button's actual built-in color. Reported as "all
  calculator buttons come in black" on a Raspberry Pi install — the
  app reads button colors from a per-user file
  (`~/PY-DIYCALCULATOR/Config/defbuttons.ini` on Linux/Pi,
  `%APPDATA%\PY-DIYCALCULATOR\Config\defbuttons.ini` on Windows, not
  the file shipped in the install folder), and once that per-user file
  gets written with all-black colors — by this bug, via Restore
  Defaults — every future launch loads the corrupted data. `_diy()`
  now snapshots each button's real construction-time color
  (`self._original_colors`), and `_restore_defaults()` uses that
  instead of a hardcoded value.
- **`Config/defbuttons.ini` in the repo/installers restored** to its
  correct default colors — it had been accidentally flattened to
  all-black (likely by the same bug during a dev/test session) and
  swept into the v9.0.24 commit alongside unrelated changes. Note:
  this file isn't actually read at runtime (the app uses the per-user
  path above), so this is a correctness/hygiene fix, not a functional
  one — if your buttons are still black after updating, delete your
  per-user `defbuttons.ini` (see above) so it reseeds from the
  now-fixed defaults.

## v9.0.24 — 2026-07-30

### Fixed

- **Maximize-on-launch no longer under-fills the screen.** On Windows,
  a display running above 100% scaling made Qt compute the maximized
  window geometry against the wrong DPI reference, so the window
  reported itself as maximized but visibly left a border. Fixed by
  enabling `Qt.AA_EnableHighDpiScaling` / `AA_UseHighDpiPixmaps`
  before `QApplication` is constructed (`app.py`), plus a new
  `_reassert_maximized()` helper (`main_window.py`) that explicitly
  sizes the window to `QApplication.primaryScreen().availableGeometry()`
  before calling `showMaximized()` — covers the same failure mode on
  Debian/Linux window managers that report "maximized" without
  actually resizing to the real screen.
- **Startup panel overlap (Calculator / Memory Walker / Message
  Display).** These were positioned using stale hand-guessed widths
  (calculator assumed 720px, actually ~800px; Memory Walker assumed
  260px, actually table-width-dependent), so Memory Walker silently
  overlapped the Calculator. Positions are now computed from each
  panel's real on-screen size, and the whole arrangement is
  screen-size aware: side-by-side on a normal monitor, a two-row
  layout (Calculator + Memory Walker on top, Message Display below)
  on mid-size screens, or a fully stacked column as a last resort on
  very small displays (e.g. the project's 7"/10" Pi touchscreen
  targets) — see `_layout_startup_panels()` in `main_window.py`.

### Changed

- **Memory Walker**: `RUN to BP`, `Clear BPs`, and `Walk 64K` moved to
  their own second button row, separate from the Address/GO/Go to PC
  row. Added `ideal_width()`, which sizes the panel to exactly fit its
  four columns (BP/STEP/ADDRESS/DATA) plus scrollbar, with no dead
  space to the right of DATA.

## v9.0.23 — 2026-07-29

### Changed

- **New "Setup" menu**, between File and Display: System Clock (moved
  from Tools) plus Load Button File / Save Button File / Restore
  Defaults (moved from File, where they were the last group before
  Exit). Menu bar order is now File, Setup, Display, Memory, Tools,
  Help.

### Fixed

- **Loading a `.ram`/`.rom` program no longer touches the calculator
  display.** Previously `_load_file()` (File > Open ROM/RAM) and the
  Compiler's "Load -> CPU" swapped in the boot-style dash placeholder
  (or, in the Compiler's case, fully blanked the screen) as soon as the
  file loaded — before Run was ever pressed. Both paths now reset
  without touching the display at all, so nothing changes on screen
  until the program actually runs.
- **Button-file edits now write back to whichever file is active.**
  Configure Button Attributes' Apply, and Restore Defaults, used to
  always save to the default `Config/defbuttons.ini` even after
  loading a different button file via Load Button File. The Calculator
  now tracks an "active" button file (default `defbuttons.ini` unless
  the user loads or saves-as a different one) and every edit is
  persisted there instead.
- **Button `Color=` now accepts color names, not just numeric index or
  hex.** A hand-edited file using a name from the file's own header
  convention (`#COLOR 5 = MAGENTA`), e.g. `Color= Magenta`, used to
  silently fall back to Black because the parser only recognized a
  digit index or a `#rrggbb` hex string. Names are now matched
  case-insensitively alongside both of those.

## v9.0.22 — 2026-07-25

### Changed

- **Removed the temporary subwindow-state diagnostic added in 9.0.19**
  (`_debug_dump_subwindows()` and its `aboutToShow`/`aboutToHide` hooks
  on every menu). It served its purpose: the printed state confirmed
  every subwindow's `isVisible`/`isHidden`/`isMinimized` flags stayed
  correct across menu use, which is what pointed at a repaint/backing-
  store gap rather than a Qt state bug. No behavior change.
- Also fixed the main window sometimes opening small instead of
  maximized (manual maximize always worked -- a startup timing issue,
  not the WM refusing maximize outright). `showEvent()` now re-asserts
  the maximize once more when the window is actually about to be shown,
  on top of the two existing safety nets in `__init__()`.
- CPU Register Display and I/O Ports Display no longer clip/overlap
  their own labels and fields -- `_sub()`'s fixed-size panels now use
  whichever is bigger, the caller's requested size or the panel's own
  minimum layout size, instead of locking to the requested size
  verbatim.
- Memory Walker and the Assembler/Editor are resizable again (with a
  working maximize button); every other panel/tool stays fixed-size
  with no minimize/maximize, and the Calculator remains the one
  panel/tool that can't be closed.

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_9.0.22_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.

## v9.0.21 — 2026-07-25

### Fixed

- **Memory Walker and the Assembler/Editor were wrongly locked to a
  fixed size by v9.0.20.** Both have genuinely variable-length content
  (Memory Walker's table, the code editor) that benefits from more
  room, unlike the mostly fixed-layout panels/tools. They're now
  resizable with a working maximize button (`_sub(..., resizable=True)`
  for Memory Walker; `_show_compiler()` updated directly). Minimize
  stays off everywhere, including these two -- with everything embedded
  in one MDI area, minimizing just leaves a useless icon strip. Every
  other panel/tool, and the Calculator's non-closability, are unchanged
  from v9.0.20.

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_9.0.21_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.

## v9.0.20 — 2026-07-25

### Fixed

- **Every panel/tool subwindow had minimize, maximize, and close buttons
  by default**, since embedding them all as `QMdiSubWindow`s (see
  `_PanelSubWindow`) never set title-bar hints, leaving Qt's defaults in
  place. Minimize/maximize/resize made no sense for any of them (most
  are fixed-size widgets, and the MDI area already keeps everything
  laid out and visible), and the Calculator -- the app's always-on
  centerpiece -- shouldn't be closable at all. Every panel/tool is now
  fixed-size with no minimize/maximize/resize; the Calculator additionally
  has no close button, while every other panel/tool keeps one (`_sub()`
  and the individual `_show_*` methods now call the new
  `_set_subwindow_buttons()` helper and `setFixedSize()`).

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_9.0.20_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.

## v9.0.19 — 2026-07-25 (diagnostic build)

### Diagnostic

- **Temporary, purely observational debug logging added to
  `_build_menu()`.** The panels-go-blank-after-menu report on
  Raspberry Pi persisted after switching from Wayfire/Wayland to X11,
  which rules out the wlroots compositor theory from v9.0.17/v9.0.18 --
  this is happening regardless of display server. Rather than guess at
  another fix blind, every top-level menu now prints each panel's
  actual Qt state (`isVisible`, `isMinimized`, `isMaximized`,
  `isHidden`, geometry) to the terminal on open and close, so the next
  fix can be based on what's actually happening to the widgets instead
  of another theory. No behavior changes -- safe to install regardless
  of outcome. Remove this logging once the root cause is found.

## v9.0.18 — 2026-07-25

### Fixed

- **Reverted the v9.0.17 menu-repaint hook.** It made things markedly
  worse on Raspberry Pi OS: opening *any* top-level menu (including
  File, which only that hook touched -- confirming it was the cause)
  detached every panel/tool subwindow, showing them as minimized
  icon+title strips at the top of the screen instead of embedded in
  the MDI area. Back to plain `build_menus(self)` with no repaint
  hook. The original report this was trying to fix (panels reading as
  blank/grey after using a menu) is still open and needs a different,
  better-tested approach.

## v9.0.17 — 2026-07-25

### Fixed

- **Opening a top menu on Raspberry Pi OS could leave Calculator,
  Memory Walker, Message Display, etc. reading as blank/grey**, with
  only the panel/tool selected from the menu (e.g. Tools -> Workbench)
  showing correctly. This looks like a repaint/backing-store gap under
  the closed menu on X11 without a compositor -- the widgets underneath
  hadn't actually disappeared, they just weren't being repainted, while
  a freshly-opened panel paints correctly regardless since that's a
  genuinely new paint rather than a repaint of already-drawn content.
  Every top-level menu (File/Memory/Display/Tools/Help) now forces the
  MDI area and all its subwindows to repaint the instant it closes,
  which papers over the gap; harmless on platforms where it wasn't
  happening.

## v9.0.16 — 2026-07-25

### Fixed

- **Main window could not be resized or un-maximized on Windows.**
  `changeEvent()` forcibly snapped the window straight back to
  maximized on every resize/restore/minimize -- necessary back when
  every panel/tool was a separate floating top-level window positioned
  in absolute screen coordinates, since shrinking, moving, or
  minimizing the main window would otherwise scatter or strand them.
  Now that they're all MDI subwindows embedded inside this one
  (v9.0.14), that risk is gone, so the override has been removed
  entirely. The window still starts maximized, but the user can now
  freely resize, restore, or minimize it like any ordinary window on
  any platform.

## v9.0.15 — 2026-07-25

### Fixed

- **Main window opened at ~1/4 of the screen on Linux, with no
  minimize/maximize/close buttons to fix it manually.** `__init__`
  stripped the maximize/minimize/close title-bar button hints on the
  theory that `changeEvent()` would keep the window maximized
  regardless. Several Linux/X11 window managers instead read "no
  maximize button hint" as "this window doesn't support being
  maximized" (it clears the corresponding Motif/EWMH capability
  hints) and refuse maximize requests outright, falling back to
  whatever small default size that WM uses for non-maximizable
  windows -- with the button also gone, there was no manual way to
  fix it either. The title-bar buttons are back to normal now, so the
  WM treats this as an ordinary maximizable window and `showMaximized()`
  actually works, with a manual fallback available either way;
  `changeEvent()` still keeps it maximized and auto-recovers from
  minimizing exactly as before. Also re-asserts maximized once after
  the initial show completes, since some window managers ignore a
  maximize request made before the window is first mapped.

## v9.0.14 — 2026-07-25

### Changed

- **Replaced the free-floating-window layout with a real Qt MDI area.**
  v9.0.12/v9.0.13 tried to patch around Linux window managers burying
  floating panels/tool windows behind the main window (raise/lower
  tricks), but that kept failing because every panel and tool
  (Calculator, Memory Walker, Message Display, CPU Registers, Terminal,
  Disassembler, Port Monitor, Keyboard, Workbench, Assembler/Editor,
  EPROM Burner) was still its own independent top-level OS window, and
  different window managers handle owned-window stacking differently
  (or not at all) -- there was no patch that could reliably win against
  all of them. They're now embedded as subwindows inside a single
  `QMdiArea` in the main window, so there's only one real top-level
  window in the whole app; Qt itself owns all panel/tool stacking
  deterministically and no window manager is involved any more, which
  removes this entire bug class rather than working around one more
  symptom of it. Verified with an automated repro (open on launch,
  Display -> CPU Registers, then re-raise other tools) confirming
  nothing gets buried or vanishes.

## v9.0.13 — 2026-07-25

### Fixed

- **Fixed floating panels and tool windows vanishing behind the main
  window on Linux** (e.g. clicking Display -> CPU Registers made the
  Calculator, Memory Walker, Message Display, etc. disappear). The
  main window is a full-screen grey backdrop with every panel/tool
  window floating above it as a separate top-level window; on Windows
  an owned window is guaranteed to stay above its owner, but several
  Linux/X11 window managers instead raise the *owner* right along with
  any one floating dialog that gets raised or activated, burying every
  OTHER floating window that wasn't part of that particular raise —
  they were still open, just hidden behind the now-topmost backdrop.
  Every place that raises/activates a panel or tool window (Display
  menu items, Calculator, Keyboard, Workbench, Assembler/Editor, EPROM
  Burner, and the v9.0.12 minimize-recovery path) now explicitly sinks
  the main window back below the floaters afterward, which — unlike
  re-raising every other floater one at a time — isn't itself subject
  to the same WM quirk and reliably keeps all of them visible.

## v9.0.12 — 2026-07-25

### Fixed

- **Fixed main window and Calculator getting "lost" on Linux, leaving
  orphaned tool windows on screen.** Both windows hide their
  minimize button, but that only removes the title-bar control — a
  Linux window manager can still minimize them via a keyboard
  shortcut, system menu, or "show desktop." The main window's
  recovery check only looked for "not maximized," but on Linux/X11
  minimizing a maximized window keeps *both* the Minimized and
  Maximized state bits set (Windows clears Maximized on minimize), so
  the check never fired and the window was left stuck hidden with no
  way back — while its floating panels and standalone tool windows
  (Calculator, Keyboard, Workbench, Compiler) stayed on screen with no
  visible owner, since Linux doesn't minimize/restore transient
  windows together with their parent the way Windows does. Both
  windows now explicitly detect the Minimized bit and immediately
  restore themselves.

## v9.0.11 — 2026-07-24

Packaging refresh — no functional changes since v9.0.10.

## v9.0.10 — 2026-07-24

### Added

- **New `tests/test_asm_regression.py` regression suite** — every
  `.asm` file under `Data/`, `tutorial/`, `article/`, `Compiler/`, and
  `bin/` is now discovered automatically, assembled, and (for full
  programs) run for a bounded number of CPU steps as part of `pytest`,
  catching assembler/CPU regressions across the whole sample library
  instead of just the curated subset `test_harness.py` exercises.

### Changed

- **Removed the empty `databook/` folder** and the now-redundant
  references to it in `Beboputer.spec`, `beboputer.spec`,
  `beboputer_mac.spec`, `install_linux.sh`, `install_rpi.sh`,
  `build_deb.sh`, and `check_deb.bat`. *The Official DIY Calculator
  Data Book.pdf* now lives in `bin/`, next to the help file that links
  to it, and is picked up automatically wherever `bin/` is already
  bundled.

## v9.0.9 — 2026-07-24

### Fixed

- **Corrected the source book title** shown in the About dialog and the
  Help file — both wrongly credited *Bebop Bytes Back* instead of
  *How Computers Do Math* by Clive "Max" Maxfield & Alvin Brown.
- **I/O Ports Display value fields enlarged to match the register
  display.** The hex/binary/annotation readouts were noticeably smaller
  (11pt) than the CPU register panel's LCD boxes (14pt); they now share
  the same 14pt bold Courier New styling and box sizing.

## v9.0.8 — 2026-07-21

### Fixed

- **The Assembler / Editor's "Load -> CPU" button now refuses to load
  while the calculator is off**, showing the same "Calculator Off"
  warning used by File -> Open ROM/RAM instead of silently loading —
  previously it had no power check at all.
- **The EPROM Burner's "Load ROM" button now has the identical gate.**
  Load RAM (File -> Open ROM/RAM), the Assembler's Load -> CPU, and the
  EPROM Burner's Load ROM all now behave the same way: calculator off
  means an explicit warning, not a silent load.

## v9.0.7 — 2026-07-21

### Fixed

- **The Workbench 1 window can no longer be resized.** Every switch,
  LED, and 7-segment widget inside it is already fixed-size, so
  dragging the window's edges previously just left dead space or
  clipped content instead of doing anything useful. It now locks to
  its natural content size on open.
- **Removed the OS minimise button from the Calculator window.** The
  Calculator is a fixed-size tool window with no menu path back to it
  once minimised; it now matches the main window, which already hides
  this button for the same reason.

## v9.0.6 — 2026-07-20

### Added

- **Two new hands-on tutorial exercises**, merged into the combined
  article/tutorial document right before the Circumference Button
  exercise: building a 4-function (+ - * /) calculator from scratch,
  and a second version of the same calculator that stores every number
  as packed BCD instead of plain binary.
- **Every exercise's complete `.asm` source listing now lives in
  `article/`** alongside the write-up (`01_workbench_switches_to_leds.asm`
  through `13_bcd_math_routines.asm`), so the article folder is
  self-contained and matches exactly what's printed in the document.

### Changed

- **Removed all manually-typed section numbers** (`1.`, `8.3.1`,
  `A.2.1`, `Exercise N`) from the tutorial's headings, so new exercises
  can be inserted without renumbering everything that follows.
- **Added numbered captions and in-text references for every figure and
  table** in the document (`Figure 1`… `Figure 10`, `Table 1`…
  `Table 24`).

### Fixed

- **Power-off now immediately halts CPU execution.** Previously the run
  timer kept ticking after the On/Off button was clicked off, so the
  CPU kept silently executing until something else happened to stop it
  (e.g. the next power-on).
- **`RUN_LIMIT` corrected from 50,000 to 500,000.** A missing zero was
  silently capping how many instructions a program could run.
- `build_deb.sh`'s post-build install instructions now print in full
  (previously truncated mid-line).

## v9.0.3 — 2026-07-10

### Fixed

- **Power-off no longer purges RAM to a deterministic `$00`.** The
  On/Off button's power-off path used to call the same code as the
  explicit "Purge RAM" menu action (zero every byte and mark it
  "known"), showing the misleading message "Ram purged" and a memory
  map full of `$00`. Power-off now marks the RAM region
  (`$4000`-`$FFFF`) undefined (`$XX`) again instead, matching the same
  "we don't know what's there once the board is off" reasoning already
  used for the power-on random-garbage fill. `$0000`-`$3FFF` (ROM)
  stays defined either way, and the message now reads "Power off."
- **Run now keeps the Message Display and Memory Walker's `▶` pointer
  live while it's ticking.** Previously `_run_tick` only refreshed the
  CPU panel and port monitor, so clicking Run looked like nothing was
  happening — the CPU was actually executing the whole time, but the
  pointer stayed frozen wherever it was when Run was clicked and the
  Message Display showed nothing until you clicked Step or Reset
  afterward.

## v9.0.2 — 2026-07-10

### Added

- **Memory Walker: "Walk 64K" button.** Continuously pages through the
  full 64K address space in 256-byte increments, wrapping from `$FFFF`
  back to `$0000`, so you can watch the whole memory map cycle by
  without manually clicking GO over and over.
- **Memory Walker: "Go to PC" button.** Jumps the view straight back
  to wherever the Program Counter currently is and resumes live
  PC-following — the fix for losing track of PC after navigating away
  with GO or Walk 64K.
- **Loading a program now shows the boot-style dash placeholder**
  (`------------------------`) on the calculator display instead of
  blanking it, matching the existing power-on boot sequence.

### Fixed

- **Memory outside a loaded program's actual footprint now correctly
  shows `$XX` (undefined) instead of `$00`.** Root cause: the Compiler
  wrote every `.ram` file as a padded 65536-byte image, and
  `_load_file()` / `load_into_cpu()` marked the *entire* file as
  "known" on load. Real assembled programs are typically only a
  handful of bytes — the other ~64KB of incidental zero-padding was
  showing as defined `$00` instead of undefined. The Compiler now
  writes compact `.ram` files (just the real bytecode) and marks only
  the actual program bytes as touched.
- **`$0000`-`$3FFF` (ROM) is now always shown as defined (`$00`), never
  `$XX`.** Real ROM contents are fixed at fabrication and don't have an
  "undefined" state the way blank RAM does. This also means the
  power-on random-garbage RAM fill (and other RAM-wide operations) now
  correctly leave ROM alone instead of randomizing it too.
- **Regenerated 15 shipped tutorial/test `.ram` files** (`lab2a.ram`,
  `lab2b.ram`, `lab2c.ram`, `lab3a-bin-v1.ram`, `lab3a-hex-rolc.ram`,
  `lab3a-hex-shr.ram`, `lab3b.ram`, `lab3c-bin-v2.ram`,
  `lab3c-hex-forward.ram`, `lab4e-add.ram`, `lab5e.ram`,
  `optest-dadd-dsub.ram`, `optest-psha.ram`,
  `workbench1_seg7test.ram`, `workbench_exercise.ram`) as compact files
  matching the new format, verified byte-for-byte against a fresh
  recompile of each `.asm` source.

## v9.0.1 — 2026-07-10

### Fixed

- **Removed the placeholder demo program loaded at startup.** `CPU.__init__`
  no longer calls a `_load_default_program()` step that wrote a small
  LDA/ADD/STA/... demo snippet to `$4000` on every launch. RAM now starts
  genuinely empty (undefined), matching real hardware power-on behavior.
- **Memory Walker shows `$XX` (undefined) for all RAM at cold start.**
  Previously a handful of bytes could appear as defined `$00` on first
  launch even though nothing had written to them yet.
- **Memory Walker now refreshes correctly after loading a `.ram`/`.rom`
  file**, whether loaded via File > Open, the EPROM Burner's Load ROM
  function, or the Assembler's "Load -> CPU" button. Loaded bytes are now
  marked "known" (`ram_touched`) and a refresh is triggered in all three
  code paths, so the Walker immediately shows the real loaded data instead
  of stale `$XX` placeholders.
- **Disassembler panel now follows the live PC** the same way Memory
  Walker does — synced on every Step/Run/Reset/Halt and Memory
  Walker-driven step/breakpoint event, not just the main toolbar buttons.

### Changed

- Startup boot messages reworded: `"PY-DIYCALCULATOR ready."` is now just
  `"PY-DIYCALCULATOR"`, and the closing line now reads "Switch calculator
  on (click on/off) button" / "Load a .RAM file" instead of the old
  combined ROM/Memory-Walker/RUN/STEP instruction line.

## v9.0.0 — 2026-07-09

### Breaking changes

- **DADD/DADDC/DSUB/DSUBC now use their official Data Book opcodes.**
  These four BCD instructions previously sat on provisional placeholder
  opcodes ($02-$04/$05-$07/$0A-$0C/$1C-$1E) because v8.0.0's renumbering
  pass didn't have the BCD appendix available. With "DIY Calculator: BCD
  Instructions" (Rev 1.0, 2005, Maxfield & Brown) now in hand, all four
  instructions have been moved to their official byte values:
  - `DADD`  — `$48` imm / `$49` abs / `$4A` abs-x
  - `DADDC` — `$68` imm / `$69` abs / `$6A` abs-x
  - `DSUB`  — `$88` imm / `$89` abs / `$8A` abs-x
  - `DSUBC` — `$B8` imm / `$B9` abs / `$BA` abs-x

  This is a breaking change to the `.ram` binary format for any program
  using these instructions: **`.ram`/`.lst` files built with 8.0.0 or
  earlier that use DADD/DADDC/DSUB/DSUBC will not run correctly on 9.0.0
  and must be re-assembled.** `Data/optest-dadd-dsub.ram`, the only
  shipped sample affected, has been re-assembled.
- **DADD/DADDC/DSUB/DSUBC now compute correct N and V flags.** Per the
  BCD appendix, N reflects the tens-complement sign of the result (set
  when the result is >= $50, not merely bit 7), and V (overflow) is now
  actually computed from the two operands' tens-complement signs instead
  of never being touched. Previously N used a plain bit-7 test and V was
  always left at whatever it happened to be from a prior instruction.
- **DSUB/DSUBC's Carry flag intentionally keeps its existing polarity.**
  The BCD appendix describes Carry as "borrow-not" (1 = no borrow, 0 = a
  borrow occurred). This emulator instead keeps the "honest borrow"
  convention already established by tutorial 13 and the test suite
  (1 = a borrow was needed) — a deliberate deviation, documented in
  `cpu.py`, `das.py`, and `tutorial/13_bcd_math_routines.asm`.

### Verification

- The full test suite (145 tests) passes, including updated BCD opcode
  and flag coverage in `tests/test_cpu.py`.
- `test_harness.py`'s BCD sample programs pass with corrected N/V flag
  expectations (47/47 tests passing).

### Upgrading

- **Re-assemble any of your own `.asm` programs that use DADD, DADDC,
  DSUB, or DSUBC** before loading them under 9.0.0.

## v8.0.0 — 2026-07-09

### Breaking changes

- **Opcode numbering now matches the official Data Book.** Every instruction's
  opcode byte has been renumbered to match Appendix A (Tables A-2a/A-2b,
  pages A-11/A-12) of *The Official DIY Calculator Data Book*, instead of
  the emulator's own ad-hoc numbering. This is a breaking change to the
  `.ram` binary format: **any `.ram`/`.lst` file assembled with a version
  older than 8.0.0 will not run correctly on 8.0.0 and must be
  re-assembled from its `.asm` source.** All sample programs shipped in
  `Data/` have been re-assembled and are up to date.
- **New addressing mode: indirect post-indexed (`ind-x`).** The Data Book
  documents a sixth addressing mode — `LDA [[addr],X]` — where the pointer
  is fetched first and X is added to the *result* (as opposed to the
  existing pre-indexed-indirect `x-ind` mode, `LDA [[addr,X]]`, where X is
  added to the address *before* the pointer is fetched). This mode is now
  fully implemented in the assembler (`das.py`) and CPU emulator (`cpu.py`)
  for LDA, STA, JMP, and JSR. The pre-existing `x-ind` mode was previously
  written internally as `iix`; it's been renamed to `xind` for clarity
  alongside the new `indx` mode.
- **JMP and JSR gained an absolute-indexed (`abs-x`) mode** (`JMP
  [addr,X]` / `JSR [addr,X]`), matching the Data Book's instruction table.
- **BLDSP gained an absolute (`abs`) mode** (`BLDSP [addr]`) alongside its
  existing 16-bit immediate mode, and **BLDIV gained a 16-bit immediate
  mode** (`BLDIV $nnnn`) alongside its existing absolute mode — both per
  the Data Book.
- Fixed a pre-existing mislabeling in the CPU-panel message text where the
  `x-ind` and `ind-x` addressing-mode descriptions were swapped for LDA,
  STA, JMP, and JSR.
- **DADD/DADDC/DSUBC opcodes are provisional placeholders.** The Data Book
  pages consulted for this release (55-56) don't cover the BCD
  instructions' opcodes, and the official byte values would have collided
  with the newly-assigned ADDC/SUB opcodes. These three instructions have
  been moved to unused opcode slots ($02-$04 / $05-$07 / $0A-$0C) pending
  the official BCD appendix. DSUB is unaffected and keeps its original
  opcodes ($1C-$1E).

### Verification

- The full test suite (145 tests) was updated for the new opcode numbers
  and passes.
- The new assembler's output was cross-checked byte-for-byte against
  `Data/2funcal.lst`/`.ram` — the original vendor-supplied reference
  listing from the 2005 "DIY Calculator Assembler V2.0" tool — and matches
  exactly, confirming the new numbering is correct.

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_8.0.0_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.
- **Re-assemble any of your own `.asm` programs** with the new assembler
  before loading them — `.ram`/`.lst` files built with 7.x or earlier will
  not execute correctly under 8.0.0.

## v7.0.2 — 2026-07-09

### Fixes

- **Memory Walker: view no longer goes blank partway down the table.**
  The table widget was created with 500 rows, but only the first 256 were
  ever populated on each refresh — rows past that point had no address
  and no data, which looked like the display "stopped" partway through
  memory. The table now has exactly 256 rows, matching the visible
  address window the view actually fills.
- **Memory Walker: power-on / Purge RAM now correctly reset the "undefined
  memory" ($XX) markers.** Filling RAM with random bytes on power-on (added
  in 7.0.1) wrote new byte values but never cleared the "touched" flag, so
  addresses touched in an *earlier* power cycle (e.g. the default program
  at $4000-$400C, or the I/O sentinel bytes around $F000) kept showing
  their stale "known" status — displaying the fresh random garbage as if
  it were a real value instead of `$XX`. Power-on now clears every
  address's touched flag before re-marking only the I/O sentinels as
  known; Purge RAM now marks all of RAM as known (`$00`), since a purge
  is a deliberate, deterministic clear.

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_7.0.2_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.

## v7.0.1 — 2026-07-09

### New features

- **Assembler listing files (.lst)** — assemb