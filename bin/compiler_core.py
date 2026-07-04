# Copyright (c) 2026 Alvin Brown & Clive Maxfield
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
compiler_core.py
================

Thin wrapper around `das.py` (David's Assembler, Python port) that exposes a
class-based API consumed by `beboputer_v4.py` and `QT_compile.py`.

Expected usage:

    from compiler_core import Compiler

    c = Compiler()
    result = c.compile_source(source_text)

    if result.success:
        ram_bytes = result.bytecode      # raw, contiguous byte-string
        for line in result.messages:
            print(line)
    else:
        for line in result.messages:
            print(line)

`result.bytecode` is the contiguous byte image starting at the program's
origin (`.ORG`) address.  The caller is responsible for placing the bytes
at the correct load address in the target RAM image (the Beboputer GUI
loads them at $4000).

This module must live in the same folder as `das.py`.
"""

from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Locate das.py.  It is expected to be in the same folder as this file.
# We add that folder to sys.path defensively in case the caller's cwd
# differs from where the modules actually live (e.g. when launched from
# the menu of a different working directory).
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    import das  # type: ignore
except Exception as exc:                       # pragma: no cover
    raise ImportError(
        f"compiler_core: failed to import 'das' from {_HERE!r}: {exc}"
    ) from exc


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class CompileResult:
    """Outcome of a single `Compiler.compile_source()` call."""
    success:    bool          = False
    bytecode:   Optional[bytes] = None   # contiguous image, origin..max
    origin:     Optional[int]   = None   # min address emitted (or None)
    end:        Optional[int]   = None   # max address emitted (or None)
    messages:   List[str]       = field(default_factory=list)

    # Convenience aliases used by some callers
    @property
    def ok(self) -> bool:
        return self.success


# ---------------------------------------------------------------------------
# Compiler facade
# ---------------------------------------------------------------------------
class Compiler:
    """Class-based facade around `das.assemble()`.

    The DAs engine is a pair of free functions that operate on a list of
    source lines and raise `das.AssemblerError` on failure.  This class
    converts that into a simple object-style API:

        Compiler().compile_source(text) -> CompileResult
    """

    # Exposed for callers that want to inspect the underlying engine.
    engine = das

    def __init__(self) -> None:
        # Nothing to configure today, but keeping __init__ means the
        # API stays stable if options are added later.
        pass

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------
    def compile_source(self, text: str) -> CompileResult:
        """Assemble `text` (full source as a single string) and return a
        `CompileResult`.

        The returned `bytecode` is a contiguous bytes object covering the
        range [origin, end] inclusive, with any gaps zero-filled.
        """
        result = CompileResult()

        if text is None:
            result.messages.append("No source provided.")
            return result

        # das.assemble() expects a list of lines (with no trailing newline).
        # splitlines() handles all line-ending variants and drops the
        # terminator, matching what `main()` in das.py does.
        source_lines = text.splitlines()

        try:
            memory = das.assemble(source_lines)
        except das.AssemblerError as exc:
            # AssemblerError already formats as "Error line N: ...".
            result.messages.append(str(exc))
            return result
        except Exception as exc:                      # pragma: no cover
            # Defensive: catch anything else from the engine so the GUI
            # gets a helpful message instead of a hard crash.
            result.messages.append(f"Internal assembler error: {exc}")
            result.messages.append(traceback.format_exc().rstrip())
            return result

        if not memory:
            result.messages.append(
                "Assembled OK, but no bytes were emitted "
                "(empty program or only directives)."
            )
            result.success = True
            result.bytecode = b""
            return result

        start_addr = min(memory.keys())
        end_addr   = max(memory.keys())

        # Build a contiguous byte image with gaps zero-filled.
        size = end_addr - start_addr + 1
        buf = bytearray(size)
        for addr, val in memory.items():
            buf[addr - start_addr] = val & 0xFF

        result.success   = True
        result.bytecode  = bytes(buf)
        result.origin    = start_addr
        result.end       = end_addr
        result.messages.append(
            f"Assembly successful. "
            f"Range: ${start_addr:04X} - ${end_addr:04X} "
            f"({size} byte{'s' if size != 1 else ''})."
        )
        return result

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def compile_file(self, path: str) -> CompileResult:
        """Assemble a source file on disk (utf-8, with latin-1 fallback)."""
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as exc:
            r = CompileResult()
            r.messages.append(f"Cannot open source file: {exc}")
            return r

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return self.compile_source(text)


# ---------------------------------------------------------------------------
# CLI smoke-test:  `python compiler_core.py foo.asm`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compiler_core.py <input.asm>")
        sys.exit(1)

    res = Compiler().compile_file(sys.argv[1])
    for m in res.messages:
        print(m)
    if res.success:
        print(f"  bytes: {len(res.bytecode or b'')}")
        sys.exit(0)
    sys.exit(1)
