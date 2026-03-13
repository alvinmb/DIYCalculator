"""
compiler_core.py
~~~~~~~~~~~~~~~~
Provides the Compiler class used by QT_compile.py.

Internally delegates to the DAs assembler engine (das.py) to assemble
DIY Calculator assembly source (.asm) into a RAM image (.ram).

Expected interface (consumed by QT_compile.py):

    compiler = Compiler()
    result   = compiler.compile_source(source_text: str)

    result.success   -> bool
    result.messages  -> list[str]    human-readable lines for the Messages pane
    result.bytecode  -> bytes | None RAM image bytes on success, None on failure

RAM image layout (matches DAs / DIY Calculator emulator format):
    Bytes 0-1 : start address (big-endian 16-bit)
    Bytes 2-3 : end   address (big-endian 16-bit)
    Bytes 4.. : code/data from start_addr..end_addr inclusive
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Optional

from das import assemble, AssemblerError


@dataclass
class CompileResult:
    success:  bool
    messages: list[str]       = field(default_factory=list)
    bytecode: Optional[bytes] = None


class Compiler:
    def compile_source(self, source: str) -> CompileResult:
        messages: list[str] = []

        # Run the two-pass assembler
        try:
            memory = assemble(source.splitlines())
        except AssemblerError as exc:
            messages.append(str(exc))
            messages.append("Compilation FAILED.")
            return CompileResult(success=False, messages=messages)
        except Exception as exc:
            messages.append(f"Internal assembler error: {exc}")
            messages.append("Compilation FAILED.")
            return CompileResult(success=False, messages=messages)

        if not memory:
            messages.append("Warning: no bytes emitted (empty program).")
            return CompileResult(success=True, messages=messages, bytecode=b"")

        start_addr = min(memory.keys())
        end_addr   = max(memory.keys())
        span       = end_addr - start_addr + 1

        # Build RAM image: 4-byte header + raw code/data bytes
        # Header format used by the DIY Calculator emulator:
        #   [start_hi, start_lo, end_hi, end_lo]  (big-endian)
        header    = struct.pack(">HH", start_addr, end_addr)
        body      = bytes(memory.get(addr, 0x00)
                          for addr in range(start_addr, end_addr + 1))
        ram_image = header + body

        messages.append(
            f"Assembly successful. "
            f"Origin: ${start_addr:04X}  End: ${end_addr:04X}  ({span} bytes)"
        )
        return CompileResult(success=True, messages=messages, bytecode=ram_image)
