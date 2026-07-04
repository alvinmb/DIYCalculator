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
"""

FLAG_C = 0x01
FLAG_Z = 0x02
FLAG_N = 0x04
FLAG_V = 0x08
FLAG_I = 0x10
FLAG_H = 0x20

OP = {
    0x00: "NOP",
    0x01: "LDA",  0x02: "LDA",  0x03: "LDA",  0x04: "LDA",  0x05: "LDA",
    0x06: "STA",  0x07: "STA",  0x08: "STA",  0x09: "STA",
    0x0A: "ADD",  0x0B: "ADD",  0x0C: "ADD",
    0x0D: "ADDC", 0x0E: "ADDC", 0x0F: "ADDC",
    0x10: "SUB",  0x11: "SUB",  0x12: "SUB",
    0x13: "SUBC", 0x14: "SUBC", 0x15: "SUBC",
    0x16: "DADD",  0x17: "DADD",  0x18: "DADD",
    0x19: "DADDC", 0x1A: "DADDC", 0x1B: "DADDC",
    0x1C: "DSUB",  0x1D: "DSUB",  0x1E: "DSUB",
    0x1F: "DSUBC", 0x20: "DSUBC", 0x21: "DSUBC",
    0x22: "CMPA", 0x23: "CMPA", 0x24: "CMPA",
    0x25: "AND",  0x26: "AND",  0x27: "AND",
    0x28: "OR",   0x29: "OR",   0x2A: "OR",
    0x2B: "XOR",  0x2C: "XOR",  0x2D: "XOR",
    0x2E: "SHL",  0x2F: "SHR",  0x30: "ROLC", 0x31: "RORC",
    0x32: "INCA", 0x33: "DECA", 0x34: "INCX", 0x35: "DECX",
    0x36: "CLRIM", 0x37: "SETIM",
    0x38: "PSHA",  0x39: "POPA",  0x3A: "PUSHSR", 0x3B: "POPSR",
    0x3C: "HALT",  0x3D: "RTI",   0x3E: "RTS",
    0x3F: "BLDX",  0x40: "BLDX",  0x41: "BSTX",
    0x42: "BLDSP", 0x43: "BSTSP", 0x44: "BLDIV",
    0x45: "JMP",  0x46: "JMP",  0x47: "JMP",
    0x48: "JC",   0x49: "JNC",  0x4A: "JN",  0x4B: "JNN",
    0x4C: "JZ",   0x4D: "JNZ", 0x4E: "JO",  0x4F: "JNO",
    0x50: "JSR",  0x51: "JSR",  0x52: "JSR",
}

_SIZE1 = frozenset({
    0x00,
    0x2E, 0x2F, 0x30, 0x31,
    0x32, 0x33, 0x34, 0x35,
    0x36, 0x37,
    0x38, 0x39, 0x3A, 0x3B,
    0x3C, 0x3D, 0x3E,
})

_SIZE2 = frozenset({
    0x01,
    0x0A, 0x0D,
    0x10, 0x13,
    0x16, 0x19, 0x1C, 0x1F,
    0x22,
    0x25, 0x28, 0x2B,
})

def instr_size(opcode):
    if opcode in _SIZE1: return 1
    if opcode in _SIZE2: return 2
    if opcode in OP:     return 3
    return 1

RUN_LIMIT = 500_000
