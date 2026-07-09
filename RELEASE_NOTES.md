# PY-DIYCALCULATOR — Release Notes

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

- **Assembler listing files (.lst)** — assembling a program now writes a
  `.lst` listing alongside the `.ram` image, in the original "DIY Calculator
  Assembler V2.0" format: line-by-line address/bytes/label/opcode/operand
  columns, plus constant and address label cross-reference tables.

### Fixes

- **Assembler/Editor: column-aligned source no longer breaks on load** —
  the editor was word-wrapping long lines, which visually mangled
  column-aligned `.asm` files. Word wrap is now disabled.
- **Calculator: top-row LEDs now turn on when the calculator is powered
  on**, and turn off when powered off — matching real hardware.
- **Calculator: pressing Reset now blanks the top-row LEDs.**
- **Calculator: RAM is now filled with random bytes on power-on**, instead
  of being zeroed. Real SRAM powers up with unpredictable garbage, not a
  tidy `$00` in every location — the emulator now matches that behavior.
  (Power-off still zeroes RAM deterministically, since there's no "real
  hardware" state to emulate once the board is off.)

### Other

- **Versioning is now single-sourced.** The app version lives in one place
  (`bin/beboputer_v7/__init__.py`) and is automatically picked up by the
  About dialog, window title, Windows installer, Debian package, and macOS
  build — no more hunting down hardcoded version strings across build
  scripts.

### Upgrading

- Debian/Raspberry Pi: `sudo dpkg -i beboputer_7.0.1_all.deb && sudo apt-get install -f`
- Windows: run the new `BeboputerSetup.exe` installer.
