# Beboputer v7 — Cleanup & Refactoring Notes

## Test Suite

Run with:
```
cd Bebop_python
python -m pytest          # uses pytest.ini — runs all 135 tests
python -m pytest -k cpu   # CPU tests only
python -m pytest -v       # verbose per-test output
```

### Coverage (135 tests, 0 failures)

| File | Tests | What it covers |
|------|-------|----------------|
| `tests/test_cpu.py` | 92 | CPU reset, all addressing modes, ALU, BCD, shifts, stack, jumps, JSR/RTS, disassembler, integration loops |
| `tests/test_instruction_messages.py` | 17 | INI loading, `describe()`, format tokens `%d %a %t %x`, opcode coverage |
| `tests/test_paths.py` | 9 | `resource_path()` in source mode, BITMAPS/Config dirs, INI file |
| `tests/test_compiler_core.py` | 17 | Assembler encoding, `.EQU`, labels, round-trip byte verification |

---

## 1. Delete Legacy / Orphan Files

These files pre-date the v7 refactor and are no longer used by anything:

| File | Lines | Reason to delete |
|------|-------|-----------------|
| `bin/QT_compile.py` | 203 | Superseded by `tools/compiler.py` (merged + improved) |
| `bin/main_calc.py` | 312 | Pre-v7 entry point; replaced by `run_beboputer_v7.py` |
| `bin/calc.py` | 289 | Pre-v7 standalone calculator; replaced by `tools/calculator.py` |

**How to delete safely:** Run the test suite after each deletion — none of them are imported by v7 code.

---

## 2. Wire or Remove Orphaned Panels

Two panels exist in `panels/` but are never opened from `main_window.py`:

### `panels/control_panel.py` (104 lines)
- Classic "RUN / STEP / RESET" button bar
- **Option A:** Wire it into `main_window.py` under the Tools menu — gives users a floating control strip
- **Option B:** Delete — all controls are already in the main window's menu bar

### `panels/disassembler.py` (59 lines)
- Shows a live disassembly view of RAM around the PC
- **Recommended:** Wire it in — the Memory Walker shows raw hex; a mnemonic disassembly view is genuinely useful
- Add to Display menu: `self._sub(DisassemblerPanel(self.cpu), "Disassembler", ...)`

---

## 3. Refactor Large Files

### `tools/compiler.py` (598 lines) — HIGH PRIORITY
The assembler GUI is one monolithic class. Split into:
- `CompilerWindow` — the QDialog UI shell (file open/save/run buttons, editor widget)
- `AssemblerRunner` — the logic that calls `compiler_core.Compiler`, formats results, and loads ROM into CPU RAM

This makes it possible to write tests for the load-ROM logic without a Qt display.

### `tools/workbench.py` (542 lines) — MEDIUM
The I/O Workbench mixes widget layout, bitmap loading, and CPU port wiring. Split into:
- `WorkbenchUI` — builds the Qt layout, holds button/display widgets
- `WorkbenchIO` — maps port addresses to widget callbacks (testable without Qt)

### `tools/diy_button.py` (371 lines) — LOW
A single custom Qt widget class. Long but cohesive. Consider splitting the paint/style code into a separate `DIYButtonStyle` dataclass so button appearances can be unit-tested without rendering.

### `panels/memory_walker.py` (320 lines) — LOW
Well-structured already. The one improvement worth making: extract `_refresh()` into a `MemoryViewModel` that can be tested without Qt (it currently requires a `QTableWidget`).

---

## 4. CPU `step()` — Dispatch Table (Optional)

`cpu.py` `step()` is a long `if/elif` chain (≈ 90 branches). It works correctly and is fast enough for this use case, but it can be refactored to a dispatch table for readability:

```python
# In __init__:
self._dispatch = {
    0x00: self._op_nop,
    0x01: self._op_lda_imm,
    0x02: self._op_lda_dir,
    # ...
}

# In step():
handler = self._dispatch.get(op)
if handler:
    handler()
else:
    return f"ILLEGAL ${op:02X}"
```

**Trade-off:** Dispatch tables are faster to scan visually but add method call overhead (negligible at emulation speeds). The current flat chain is fine for this project — flag this as a future improvement only.

---

## 5. `main_window.py` — Reduce Fat Controller

`main_window.py` (370 lines) does too much: menu building, window layout, CPU wiring, panel lifecycle, help, and about dialogs. Suggested splits:

- Extract `_build_menus()` into a `MenuBuilder` helper — this alone cuts ~80 lines from the class
- Move `_show_help()`, `_show_about()`, `_show_credits()` into a `HelpActions` mixin
- Consider a `PanelRegistry` dict `{name: dialog}` instead of separate `self.mem_walker`, `self.port_mon`, etc. attributes — makes show/hide loops trivial

---

## 6. Quick Wins (Do These First)

| Item | Effort | Benefit |
|------|--------|---------|
| Delete `QT_compile.py`, `main_calc.py`, `calc.py` | 5 min | Removes 800 lines of dead code |
| Add `__all__` to `beboputer_v7/__init__.py` | 10 min | Clarifies public API |
| Move `make_test_calc.py` to `tools/` or `tests/` | 2 min | Clutter-free `bin/` root |
| Add `conftest.py` session fixture that creates one CPU per class | 30 min | Faster tests (avoids re-init per method) |
| Wire `DisassemblerPanel` into Display menu | 20 min | Surfaces already-written feature |

---

## 7. Suggested Refactoring Order

1. **Delete the three legacy files** — zero risk, instant gain
2. **Wire `DisassemblerPanel`** — already written, just needs a menu entry
3. **Split `CompilerWindow`** — enables assembler integration tests
4. **Split `WorkbenchUI`/`WorkbenchIO`** — enables port-wiring tests
5. **`main_window.py` menu extraction** — cosmetic but makes future changes much easier

After each step: run `python -m pytest` and confirm 135 tests still pass.
