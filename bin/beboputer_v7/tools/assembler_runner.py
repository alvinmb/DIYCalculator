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

"""AssemblerRunner -- pure logic, no Qt dependency.

Split out of compiler.py (2026-08-02): that module's own docstring already
called AssemblerRunner "pure logic... no Qt dependency", but it lived in the
same file as CompilerWindow(QMainWindow) behind an unconditional top-level
``from PyQt5.QtCore import ...`` etc. Importing AssemblerRunner from that
file therefore still required PyQt5 to be installed and pulled the whole
package into PyInstaller's dependency graph -- including for the tkinter
build, which imports AssemblerRunner (via beboputer_tk.panels.compiler) but
never touches Qt itself. That's why the "tkinter" Windows installer kept
bundling PyQt5/Qt5 DLLs.

compiler.py re-exports AssemblerRunner unchanged, so existing
``from .compiler import AssemblerRunner`` / instantiation inside
CompilerWindow keeps working without edits.
"""

from __future__ import annotations

import sys
from pathlib import Path

# compiler_core + das.py live two levels up in bin/
_BIN_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BIN_DIR))

try:
    from compiler_core import Compiler as _AsmCompiler
    _COMPILER_AVAILABLE = True
    _COMPILER_IMPORT_ERROR = None
except Exception as _exc:
    _AsmCompiler = None
    _COMPILER_AVAILABLE = False
    _COMPILER_IMPORT_ERROR = str(_exc)


class AssemblerRunner:
    """Compile assembly source, write RAM images, and load into a CPU.

    This class holds no Qt state and can be used (and tested) without a
    display.  :class:`~beboputer_v7.tools.compiler.CompilerWindow` owns one
    instance and delegates all compile/load operations to it; the tkinter
    build's Assembler/Editor panel does the same.
    """

    LOAD_ADDR = 0x4000
    RAM_SIZE  = 0x10000

    def __init__(self):
        self._compiler = _AsmCompiler() if _COMPILER_AVAILABLE else None
        self.available = _COMPILER_AVAILABLE
        self.import_error = _COMPILER_IMPORT_ERROR

    # ------------------------------------------------------------------

    def compile(self, source: str):
        """Assemble *source* and return the :class:`compiler_core.CompileResult`.

        Returns ``None`` if the back-end is not available.
        """
        if self._compiler is None:
            return None
        return self._compiler.compile_source(source)

    def generate_listing(self, source: str, source_path=None):
        """Assemble *source* and return the :class:`compiler_core.ListingResult`
        containing the formatted .lst text. Returns ``None`` if the
        back-end is not available.
        """
        if self._compiler is None:
            return None
        return self._compiler.generate_listing(source, source_path=source_path)

    def build_image(self, bytecode: bytes) -> bytes:
        """Return the raw assembled *bytecode*, trimmed to fit in RAM.

        Previously this padded the bytecode out to a full 64KB image
        starting at LOAD_ADDR. That made every compiled .ram file a
        65536-byte blob, which in turn made _load_file() treat the
        *entire* file as "known" -- Memory Walker showed $00 for every
        address the program never touched, instead of the undefined
        placeholder ($XX). A compact file (just the real bytes) lets
        _load_file()'s existing chunked-copy path mark only the actual
        program bytes as touched, which is what we want.
        """
        max_bytes = self.RAM_SIZE - self.LOAD_ADDR
        return bytes(bytecode[:max_bytes])

    def write_ram(self, bytecode: bytes, out_path: Path) -> None:
        """Write the compact assembled bytecode to *out_path* (.ram file).

        The file holds only the real program bytes (loaded at LOAD_ADDR
        on read-back) -- not a padded 64KB image. See build_image().
        """
        out_path.write_bytes(self.build_image(bytecode))

    def load_into_cpu(self, bytecode: bytes, cpu) -> int:
        """Load *bytecode* into *cpu* RAM at LOAD_ADDR.

        Writes in-place so MemoryWalker and other holders of cpu.ram keep
        their reference to the same bytearray object.
        Returns the number of bytes loaded.
        """
        max_bytes = cpu.RAM_SIZE - self.LOAD_ADDR
        data = bytecode[:max_bytes]
        cpu.ram[self.LOAD_ADDR : self.LOAD_ADDR + len(data)] = data
        # Mark only the actual program bytes as known -- NOT the whole
        # $4000-$FFFF range. Previously this zeroed and marked the
        # entire remaining RAM as "touched", so Memory Walker showed
        # $00 everywhere past the program instead of the undefined
        # placeholder ($XX). Same bookkeeping as _load_file()/
        # EpromBurner._load_rom(), which only mark the bytes they
        # actually supply.
        if hasattr(cpu, "ram_touched"):
            cpu.ram_touched[self.LOAD_ADDR : self.LOAD_ADDR + len(data)] = \
                b"\x01" * len(data)
        return len(data)
