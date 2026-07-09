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
instruction_messages.py
-----------------------
Loads the human-readable instruction messages from DIYCALC.INI and
maps each CPU opcode to the appropriate message text.

Usage
-----
    from .instruction_messages import InstructionMessages
    msgs = InstructionMessages()           # loads INI once
    line = msgs.describe(cpu)              # call after cpu.step()
"""

import re

from .constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I
from .paths import resource_path

# ── Default path to DIYCALC.INI — resolved for source and PyInstaller bundle ──
_DEFAULT_INI = resource_path('Config', 'DIYCALC.INI')

# ── Opcode → Message_Field index  ─────────────────────────────────────────────
# Derived from the [Message Section] in DIYCALC.INI and the das.py opcode
# table (opcode numbering matches Appendix A, Tables A-2a/A-2b of The
# Official DIY Calculator Data Book).
#
# Note: message IDs 188/189 in the INI are labelled "[x-ind]"/"[ind-x]"
# respectively (likewise 64/65, 132/133, 192/193) — this corrects a
# pre-existing mislabeling where the x-ind (pre-indexed indirect) opcode
# was wired to the "ind-x" message and vice versa.
_OPCODE_MSG = {
    0x00: 43,   # NOP
    0x01: 33,   # HALT
    # DADD — provisional placeholder opcodes; no dedicated INI message
    0x02: 12, 0x03: 12, 0x04: 12,
    # DADDC — provisional placeholder opcodes; no dedicated INI message
    0x05: 12, 0x06: 12, 0x07: 12,
    0x08: 236,  # SETIM
    0x09: 235,  # CLRIM
    # DSUBC — provisional placeholder opcodes; no dedicated INI message
    0x0A: 12, 0x0B: 12, 0x0C: 12,
    # ADD
    0x10: 26,   # ADD imm
    0x11: 25,   # ADD abs
    0x12: 177,  # ADD abs-x
    # ADDC
    0x18: 28,   # ADDC imm
    0x19: 27,   # ADDC abs
    0x1A: 127,  # ADDC abs-x
    # DSUB — unchanged opcodes, no dedicated INI message
    0x1C: 12, 0x1D: 12, 0x1E: 12,
    # SUB
    0x20: 57,   # SUB imm
    0x21: 56,   # SUB abs
    0x22: 128,  # SUB abs-x
    # SUBC
    0x28: 59,   # SUBC imm
    0x29: 58,   # SUBC abs
    0x2A: 129,  # SUBC abs-x
    # AND
    0x30: 30,   # AND imm
    0x31: 29,   # AND abs
    0x32: 181,  # AND abs-x
    # OR
    0x38: 46,   # OR imm
    0x39: 45,   # OR abs
    0x3A: 182,  # OR abs-x
    # XOR
    0x40: 61,   # XOR imm
    0x41: 60,   # XOR abs
    0x42: 183,  # XOR abs-x
    # BLDSP / BSTSP
    0x50: 197,  # BLDSP imm
    0x51: 198,  # BLDSP abs
    0x59: 203,  # BSTSP abs
    # CMPA
    0x60: 32,   # CMPA imm
    0x61: 31,   # CMPA abs
    0x62: 184,  # CMPA abs-x
    # Shifts / Rotates
    0x70: 53,   # SHL
    0x71: 54,   # SHR
    0x78: 49,   # ROLC
    0x79: 50,   # RORC
    # Inc / Dec
    0x80: 237,  # INCA
    0x81: 238,  # DECA
    0x82: 212,  # INCX
    0x83: 213,  # DECX
    # LDA
    0x90: 42,   # LDA imm
    0x91: 41,   # LDA abs
    0x92: 186,  # LDA abs-x
    0x93: 187,  # LDA ind
    0x94: 188,  # LDA x-ind
    0x95: 189,  # LDA ind-x
    # STA
    0x99: 55,   # STA abs
    0x9A: 62,   # STA abs-x
    0x9B: 63,   # STA ind
    0x9C: 64,   # STA x-ind
    0x9D: 65,   # STA ind-x
    # BLDX / BSTX
    0xA0: 199,  # BLDX imm
    0xA1: 200,  # BLDX abs
    0xA9: 204,  # BSTX abs
    # Stack
    0xB0: 47,   # POPA
    0xB1: 23,   # POPSR
    0xB2: 48,   # PSHA / PUSHA
    0xB3: 24,   # PUSHSR
    # JMP
    0xC1: 36,   # JMP abs
    0xC2: 130,  # JMP abs-x
    0xC3: 131,  # JMP ind
    0xC4: 132,  # JMP x-ind
    0xC5: 133,  # JMP ind-x
    0xC7: 51,   # RTI
    # JSR
    0xC9: 39,   # JSR abs
    0xCA: 190,  # JSR abs-x
    0xCB: 191,  # JSR ind
    0xCC: 192,  # JSR x-ind
    0xCD: 193,  # JSR ind-x
    0xCF: 52,   # RTS
    # Conditional jumps
    0xD1: 40,   # JZ
    0xD6: 38,   # JNZ
    0xD9: 215,  # JN
    0xDE: 216,  # JNN
    0xE1: 35,   # JC
    0xE6: 37,   # JNC
    0xE9: 221,  # JO
    0xEE: 222,  # JNO
    # BLDIV
    0xF0: 201,  # BLDIV imm
    0xF1: 202,  # BLDIV abs
}

# ── Supplementary state message appended after the instruction name  ──────────
# Message 120: "I=%i O=%o N=%n Z=%z C=%c"
_STATE_MSG_ID = 120


class InstructionMessages:
    """Loads DIYCALC.INI once and formats per-instruction messages."""

    def __init__(self, ini_path: str = _DEFAULT_INI):
        self._messages: dict[int, str] = {}
        self._load(ini_path)

    # ── INI loader ────────────────────────────────────────────────────────────

    def _load(self, path: str):
        """Parse Message_Field_N="text" entries from the INI file."""
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except OSError:
            return

        pattern = re.compile(
            r'Message_Field_(\d+)\s*=\s*"([^"]*)"', re.IGNORECASE
        )
        for m in pattern.finditer(content):
            idx  = int(m.group(1))
            text = m.group(2)
            # Fix Windows-1252 mojibake that appears in some entries
            text = text.replace('�', "'").replace('’', "'")
            self._messages[idx] = text

    # ── Public API ────────────────────────────────────────────────────────────

    def describe(self, cpu) -> str:
        """Return a formatted message for the instruction cpu just executed.

        Call this immediately after cpu.step() so cpu.instr, cpu.acc,
        cpu.pc, cpu.flags etc. reflect the post-execution state.
        """
        opcode  = cpu.instr & 0xFF
        msg_id  = _OPCODE_MSG.get(opcode, 34)   # 34 = "INVALID opcode"
        instr_line = self._fmt(self._messages.get(msg_id, ""), cpu, opcode)

        state_line = self._fmt(
            self._messages.get(_STATE_MSG_ID, ""), cpu, opcode
        )
        acc_line = (
            f"  ACC=${cpu.acc:02X} ({cpu.acc:3d})  "
            f"PC=${cpu.pc:04X}  "
            f"SP=${cpu.sp:04X}  "
            f"IX=${cpu.ix:04X}"
        )

        return f"{instr_line}\n{acc_line}\n  {state_line}"

    # ── Formatter ─────────────────────────────────────────────────────────────

    def _fmt(self, text: str, cpu, opcode: int) -> str:
        """Substitute %X format tokens with live CPU values."""
        f = cpu.flags
        text = text.replace('%t', f'${opcode:02X}')
        text = text.replace('%d', str(cpu.acc))
        text = text.replace('%a', f'${cpu.pc:04X}')
        text = text.replace('%x', f'${cpu.ix:04X}')
        text = text.replace('%i', str(1 if f & FLAG_I else 0))
        text = text.replace('%o', str(1 if f & FLAG_V else 0))
        text = text.replace('%n', str(1 if f & FLAG_N else 0))
        text = text.replace('%z', str(1 if f & FLAG_Z else 0))
        text = text.replace('%c', str(1 if f & FLAG_C else 0))
        return text
