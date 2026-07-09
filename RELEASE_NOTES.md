# PY-DIYCALCULATOR — Release Notes

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
