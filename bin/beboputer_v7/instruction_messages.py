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
# Derived from the [Message Section] in DIYCALC.INI and the das.py opcode table.
_OPCODE_MSG = {
    0x00: 43,   # NOP
    # LDA
    0x01: 42,   # LDA imm
    0x02: 41,   # LDA abs
    0x03: 186,  # LDA abs-x
    0x04: 187,  # LDA ind
    0x05: 189,  # LDA ind-x
    # STA
    0x06: 55,   # STA abs
    0x07: 62,   # STA abs-x
    0x08: 63,   # STA ind
    0x09: 65,   # STA ind-x
    # ADD / ADDC
    0x0A: 26,   # ADD imm
    0x0B: 25,   # ADD abs
    0x0C: 177,  # ADD abs-x
    0x0D: 28,   # ADDC imm
    0x0E: 27,   # ADDC abs
    0x0F: 127,  # ADDC abs-x
    # SUB / SUBC
    0x10: 57,   # SUB imm
    0x11: 56,   # SUB abs
    0x12: 128,  # SUB abs-x
    0x13: 59,   # SUBC imm
    0x14: 58,   # SUBC abs
    0x15: 129,  # SUBC abs-x
    # BCD arithmetic — no specific messages in INI; use "No Message"
    0x16: 12,   # DADD imm
    0x17: 12,   # DADD abs
    0x18: 12,   # DADD abs-x
    0x19: 12,   # DADDC imm
    0x1A: 12,   # DADDC abs
    0x1B: 12,   # DADDC abs-x
    0x1C: 12,   # DSUB imm
    0x1D: 12,   # DSUB abs
    0x1E: 12,   # DSUB abs-x
    0x1F: 12,   # DSUBC imm
    0x20: 12,   # DSUBC abs
    0x21: 12,   # DSUBC abs-x
    # CMPA
    0x22: 32,   # CMPA imm
    0x23: 31,   # CMPA abs
    0x24: 184,  # CMPA abs-x
    # AND / OR / XOR
    0x25: 30,   # AND imm
    0x26: 29,   # AND abs
    0x27: 181,  # AND abs-x
    0x28: 46,   # OR imm
    0x29: 45,   # OR abs
    0x2A: 182,  # OR abs-x
    0x2B: 61,   # XOR imm
    0x2C: 60,   # XOR abs
    0x2D: 183,  # XOR abs-x
    # Shifts / Rotates
    0x2E: 53,   # SHL
    0x2F: 54,   # SHR
    0x30: 49,   # ROLC
    0x31: 50,   # RORC
    # Inc / Dec
    0x32: 237,  # INCA
    0x33: 238,  # DECA
    0x34: 212,  # INCX
    0x35: 213,  # DECX
    # Interrupt mask
    0x36: 235,  # CLRIM
    0x37: 236,  # SETIM
    # Stack
    0x38: 48,   # PSHA / PUSHA
    0x39: 47,   # POPA
    0x3A: 24,   # PUSHSR
    0x3B: 23,   # POPSR
    # Control
    0x3C: 33,   # HALT
    0x3D: 51,   # RTI
    0x3E: 52,   # RTS
    # Index / SP / IV big loads & stores
    0x3F: 199,  # BLDX imm
    0x40: 200,  # BLDX abs
    0x41: 204,  # BSTX abs
    0x42: 197,  # BLDSP imm
    0x43: 203,  # BSTSP abs
    0x44: 202,  # BLDIV abs
    # Jumps
    0x45: 36,   # JMP abs
    0x46: 131,  # JMP ind
    0x47: 133,  # JMP ind-x
    0x48: 35,   # JC
    0x49: 37,   # JNC
    0x4A: 215,  # JN
    0x4B: 216,  # JNN
    0x4C: 40,   # JZ
    0x4D: 38,   # JNZ
    0x4E: 221,  # JO
    0x4F: 222,  # JNO
    # JSR
    0x50: 39,   # JSR abs
    0x51: 191,  # JSR ind
    0x52: 193,  # JSR ind-x
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
