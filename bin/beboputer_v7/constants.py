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
CPU flag bit positions and opcode mnemonic table.

Opcode numbering matches Appendix A (Tables A-2a/A-2b) of The Official
DIY Calculator Data Book, and mirrors the OPCODES table in bin/das.py.
DADD/DADDC/DSUB/DSUBC use the official opcodes from the "DIY Calculator:
BCD Instructions" appendix (Rev 1.0, 2005): $48-$4A / $68-$6A / $88-$8A /
$B8-$BA — see das.py's OPCODES comment for details.
"""

FLAG_C = 0x01
FLAG_Z = 0x02
FLAG_N = 0x04
FLAG_V = 0x08
FLAG_I = 0x10
FLAG_H = 0x20

OP = {
    0x00: "NOP",
    0x01: "HALT",
    0x08: "SETIM", 0x09: "CLRIM",
    0x10: "ADD",  0x11: "ADD",  0x12: "ADD",
    0x18: "ADDC", 0x19: "ADDC", 0x1A: "ADDC",
    0x20: "SUB",  0x21: "SUB",  0x22: "SUB",
    0x28: "SUBC", 0x29: "SUBC", 0x2A: "SUBC",
    0x30: "AND",  0x31: "AND",  0x32: "AND",
    0x38: "OR",   0x39: "OR",   0x3A: "OR",
    0x40: "XOR",  0x41: "XOR",  0x42: "XOR",
    0x48: "DADD",  0x49: "DADD",  0x4A: "DADD",
    0x50: "BLDSP", 0x51: "BLDSP",
    0x59: "BSTSP",
    0x60: "CMPA", 0x61: "CMPA", 0x62: "CMPA",
    0x68: "DADDC", 0x69: "DADDC", 0x6A: "DADDC",
    0x70: "SHL",  0x71: "SHR",
    0x78: "ROLC", 0x79: "RORC",
    0x80: "INCA", 0x81: "DECA", 0x82: "INCX", 0x83: "DECX",
    0x88: "DSUB",  0x89: "DSUB",  0x8A: "DSUB",
    0x90: "LDA",  0x91: "LDA",  0x92: "LDA",  0x93: "LDA",  0x94: "LDA",  0x95: "LDA",
    0x99: "STA",  0x9A: "STA",  0x9B: "STA",  0x9C: "STA",  0x9D: "STA",
    0xA0: "BLDX", 0xA1: "BLDX",
    0xA9: "BSTX",
    0xB0: "POPA", 0xB1: "POPSR", 0xB2: "PSHA", 0xB3: "PUSHSR",
    0xB8: "DSUBC", 0xB9: "DSUBC", 0xBA: "DSUBC",
    0xC1: "JMP",  0xC2: "JMP",  0xC3: "JMP",  0xC4: "JMP",  0xC5: "JMP",
    0xC7: "RTI",
    0xC9: "JSR",  0xCA: "JSR",  0xCB: "JSR",  0xCC: "JSR",  0xCD: "JSR",
    0xCF: "RTS",
    0xD1: "JZ",   0xD6: "JNZ",
    0xD9: "JN",   0xDE: "JNN",
    0xE1: "JC",   0xE6: "JNC",
    0xE9: "JO",   0xEE: "JNO",
    0xF0: "BLDIV", 0xF1: "BLDIV",
}

# Opcodes whose instruction is exactly 1 byte (no operand bytes).
_SIZE1 = frozenset({
    0x00, 0x01,
    0x08, 0x09,
    0x70, 0x71, 0x78, 0x79,
    0x80, 0x81, 0x82, 0x83,
    0xB0, 0xB1, 0xB2, 0xB3,
    0xC7, 0xCF,
})

# Opcodes whose instruction is exactly 2 bytes (opcode + 1-byte operand).
_SIZE2 = frozenset({
    0x10, 0x18,
    0x20, 0x28,
    0x30, 0x38, 0x40,
    0x48, 0x60, 0x68,
    0x88, 0xB8,
    0x90,
})

def instr_size(opcode):
    if opcode in _SIZE1: return 1
    if opcode in _SIZE2: return 2
    if opcode in OP:     return 3
    return 1

RUN_LIMIT = 500_000
