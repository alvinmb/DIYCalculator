# PY-DIYCALCULATOR — Release Notes

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
  before loading them