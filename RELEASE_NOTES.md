# PY-DIYCALCULATOR — Release Notes

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