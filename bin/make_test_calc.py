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
make_test_calc.py
=================
Generates  test_calc.rom  — a binary ROM image that runs on the
updated cpu.py (now aligned to das.py instruction set).

  Usage:  python make_test_calc.py
  Then:   File > Open Project -> test_calc.rom
          Press Reset, then Run (or Step to trace)

Opcodes used (das.py / cpu.py aligned)
  0x01  LDA $nn      load immediate
  0x06  STA [aa]     store direct  (big-endian address)
  0x0A  ADD $nn      add immediate
  0x10  SUB $nn      subtract immediate
  0x32  INCA         increment accumulator
  0x3C  HALT

Ports tested
  $F031  Calculator display  — ASCII chars appended; ESC ($1B) clears
  $F032  Calculator LED strip — bits 5..0 = LEDs left-to-right

Program starts at $4000 (RESET_VECTOR).

Expected result after HALT
  Display  : HELLO
  LEDs     : all 6 bright red
  ACC      : $0D  (13 decimal)
  Z=0  N=0  C=0
"""

from pathlib import Path


# ── Instruction builders (das.py / cpu.py opcodes) ────────────────────────────

def LDA(val: int):          # 0x01  load immediate
    return [0x01, val & 0xFF]

def STA(addr: int):         # 0x06  store direct  — big-endian address
    return [0x06, (addr >> 8) & 0xFF, addr & 0xFF]

def ADD(val: int):          # 0x0A  add immediate
    return [0x0A, val & 0xFF]

def SUB(val: int):          # 0x10  subtract immediate
    return [0x10, val & 0xFF]

def INCA():                 # 0x32  increment accumulator
    return [0x32]

def HALT():                 # 0x3C  halt
    return [0x3C]


# ── Port addresses ─────────────────────────────────────────────────────────────

CALCDSP = 0xF031   # calculator display
CALCLED = 0xF032   # calculator LED strip


# ── Program ────────────────────────────────────────────────────────────────────

program = (
    # Step 1: clear display (ESC = $1B)
    LDA(0x1B)          + STA(CALCDSP) +

    # Step 2: write "HELLO"
    LDA(ord('H'))      + STA(CALCDSP) +
    LDA(ord('E'))      + STA(CALCDSP) +
    LDA(ord('L'))      + STA(CALCDSP) +
    LDA(ord('L'))      + STA(CALCDSP) +
    LDA(ord('O'))      + STA(CALCDSP) +

    # Step 3: all 6 LEDs on  (%00111111 = $3F)
    LDA(0x3F)          + STA(CALCLED) +

    # Step 4: arithmetic — ACC ends up at 13 ($0D)
    LDA(0x0A)          +   # A = 10
    ADD(0x05)          +   # A = 15   C=0 Z=0 N=0
    SUB(0x03)          +   # A = 12
    INCA()             +   # A = 13

    HALT()
)


# ── Build 64 KB image and write ────────────────────────────────────────────────

RESET_VECTOR = 0x4000
ROM_SIZE     = 0x10000

rom = bytearray(ROM_SIZE)
for i, byte in enumerate(program):
    rom[RESET_VECTOR + i] = byte

out_path = Path(__file__).parent / "test_calc.rom"
out_path.write_bytes(bytes(rom))

print(f"Written {len(program)} bytes at ${RESET_VECTOR:04X}  ->  {out_path}")
print()
print("Instruction trace:")
addr = RESET_VECTOR
i = 0
while i < len(program):
    op = program[i]
    if op == 0x01:
        print(f"  ${addr:04X}:  {op:02X} {program[i+1]:02X}        LDA  ${program[i+1]:02X}")
        addr += 2;  i += 2
    elif op == 0x06:
        print(f"  ${addr:04X}:  {op:02X} {program[i+1]:02X} {program[i+2]:02X}     STA  [${program[i+1]:02X}{program[i+2]:02X}]")
        addr += 3;  i += 3
    elif op == 0x0A:
        print(f"  ${addr:04X}:  {op:02X} {program[i+1]:02X}        ADD  ${program[i+1]:02X}")
        addr += 2;  i += 2
    elif op == 0x10:
        print(f"  ${addr:04X}:  {op:02X} {program[i+1]:02X}        SUB  ${program[i+1]:02X}")
        addr += 2;  i += 2
    elif op == 0x32:
        print(f"  ${addr:04X}:  {op:02X}           INCA")
        addr += 1;  i += 1
    elif op == 0x3C:
        print(f"  ${addr:04X}:  {op:02X}           HALT")
        addr += 1;  i += 1
    else:
        print(f"  ${addr:04X}:  {op:02X}")
        addr += 1;  i += 1
print()
print("Load in Beboputer:  File > Open Project > test_calc.rom")
print("Press Reset then Run (or Step to trace instruction by instruction).")
print()
print("Expected display : HELLO")
print("Expected LEDs    : all 6 bright red")
print("Expected ACC     : $0D  (13 decimal)   Z=0  N=0  C=0")
