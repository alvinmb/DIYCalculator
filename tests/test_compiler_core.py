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
test_compiler_core.py — Tests for the assembler back-end (compiler_core.py).

The assembler syntax uses das.py conventions:
  - Immediate:  LDA $42       (no # prefix)
  - Direct:     LDA [$1234]
  - Indexed:    LDA [$1234,X]
  - All programs need a .ORG directive as the first statement.

CompileResult fields:  ok (bool), bytecode (bytes), origin (int), messages (list)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

import pytest

try:
    from compiler_core import Compiler
    COMPILER_AVAILABLE = True
except Exception as e:
    COMPILER_AVAILABLE = False
    _IMPORT_ERROR = str(e)

skip_if_no_compiler = pytest.mark.skipif(
    not COMPILER_AVAILABLE,
    reason="compiler_core not importable"
)

ORG = "        .ORG    $4000\n"


def assemble(body: str) -> bytes:
    """Wrap body in .ORG header, assemble, return bytecode. Raises on failure."""
    c = Compiler()
    src = ORG + body + "\n"
    r = c.compile_source(src)
    if not r.ok:
        raise AssertionError(f"Assembler failed:\n{src}\nMessages: {r.messages}")
    return bytes(r.bytecode)


# ─────────────────────────────────────────────────────────────────────────────
# Basic instruction encoding
# ─────────────────────────────────────────────────────────────────────────────

@skip_if_no_compiler
class TestBasicEncoding:
    def test_nop_encodes(self):
        code = assemble("        NOP\n        HALT")
        assert code[0] == 0x00

    def test_halt_encodes(self):
        code = assemble("        HALT")
        assert code[0] == 0x3C

    def test_lda_immediate(self):
        code = assemble("        LDA     $42\n        HALT")
        assert code[0] == 0x01
        assert code[1] == 0x42

    def test_lda_direct(self):
        code = assemble("        LDA     [$1234]\n        HALT")
        assert code[0] == 0x02
        assert code[1] == 0x12
        assert code[2] == 0x34

    def test_sta_direct(self):
        code = assemble("        STA     [$5000]\n        HALT")
        assert code[0] == 0x06

    def test_add_immediate(self):
        code = assemble("        ADD     $05\n        HALT")
        assert code[0] == 0x0A
        assert code[1] == 0x05

    def test_sub_immediate(self):
        code = assemble("        SUB     $03\n        HALT")
        assert code[0] == 0x10
        assert code[1] == 0x03

    def test_jmp_direct(self):
        code = assemble("        JMP     [$4000]\n        HALT")
        assert code[0] == 0x45

    def test_jsr_direct(self):
        code = assemble("        JSR     [$4010]\n        HALT")
        assert code[0] == 0x50

    def test_rts_encodes(self):
        code = assemble("        RTS\n        HALT")
        assert code[0] == 0x3E

    def test_inca_encodes(self):
        code = assemble("        INCA\n        HALT")
        assert code[0] == 0x32

    def test_deca_encodes(self):
        code = assemble("        DECA\n        HALT")
        assert code[0] == 0x33


@skip_if_no_compiler
class TestDirectives:
    def test_org_sets_origin(self):
        c = Compiler()
        r = c.compile_source("        .ORG    $4000\n        NOP\n        HALT\n")
        assert r.ok
        assert r.origin == 0x4000

    def test_equ_substitution(self):
        src = (ORG +
               "PORT:   .EQU    $F031\n"
               "        LDA     $41\n"
               "        STA     [PORT]\n"
               "        HALT\n")
        code = assemble(src.replace(ORG, ""))  # ORG already included above
        # STA opcode = 0x06, followed by $F0, $31
        c = Compiler()
        r = c.compile_source(src)
        assert r.ok, r.messages
        bc = bytes(r.bytecode)
        idx = list(bc).index(0x06)
        assert bc[idx + 1] == 0xF0
        assert bc[idx + 2] == 0x31

    def test_label_resolves(self):
        src = (ORG +
               "START:  NOP\n"
               "        JMP     [START]\n"
               "        HALT\n")
        c = Compiler()
        r = c.compile_source(src)
        assert r.ok, r.messages
        bc = bytes(r.bytecode)
        assert 0x45 in bc   # JMP opcode


@skip_if_no_compiler
class TestRoundTrip:
    def test_program_produces_correct_bytes(self):
        """LDA $05, ADD $03, HALT — byte-for-byte check."""
        src = (ORG +
               "        LDA     $05\n"
               "        ADD     $03\n"
               "        HALT\n")
        c = Compiler()
        r = c.compile_source(src)
        assert r.ok, r.messages
        code = bytes(r.bytecode)
        assert code[0] == 0x01   # LDA imm
        assert code[1] == 0x05
        assert code[2] == 0x0A   # ADD imm
        assert code[3] == 0x03
        assert code[4] == 0x3C   # HALT

    def test_loop_program(self):
        src = (ORG +
               "        LDA     $05\n"
               "LOOP:   DECA\n"
               "        JNZ     [LOOP]\n"
               "        HALT\n")
        c = Compiler()
        r = c.compile_source(src)
        assert r.ok, r.messages
        assert len(r.bytecode) > 0

    def test_compile_result_has_origin(self):
        c = Compiler()
        r = c.compile_source(ORG + "        NOP\n        HALT\n")
        assert r.ok
        assert r.origin == 0x4000

    def test_invalid_source_returns_failure(self):
        c = Compiler()
        r = c.compile_source("GARBAGE NONSENSE\n")
        assert not r.ok
        assert len(r.messages) > 0
