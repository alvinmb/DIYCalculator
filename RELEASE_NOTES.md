# PY-DIYCALCULATOR — Release Notes

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
 