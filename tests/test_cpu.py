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
test_cpu.py - Unit tests for the Beboputer CPU (cpu.py).

Run from the project root:
    pytest tests/

No Qt / GUI dependencies - pure headless Python.

Opcode numbering matches Appendix A (Tables A-2a/A-2b) of The Official
DIY Calculator Data Book (see bin/das.py's OPCODES table for the
canonical mapping).
"""

import sys
import os

# Make sure the package is importable when running from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

import pytest
from beboputer_v7.cpu import CPU
from beboputer_v7.constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def make_cpu(*program_bytes, base=0x4000):
    """Return a freshly reset CPU with program_bytes loaded at base."""
    cpu = CPU()
    cpu.reset()
    for i, b in enumerate(program_bytes):
        cpu.ram[base + i] = b
    cpu.pc = base
    return cpu


def step_n(cpu, n):
    """Step the CPU n times, return list of mnemonics."""
    return [cpu.step() for _ in range(n)]


# -----------------------------------------------------------------------------
# Reset
# -----------------------------------------------------------------------------

class TestReset:
    def test_pc_at_reset_vector(self):
        cpu = CPU()
        cpu.reset()
        assert cpu.pc == CPU.RESET_VECTOR

    def test_acc_zero(self):
        cpu = CPU()
        cpu.reset()
        assert cpu.acc == 0

    def test_flags_zero(self):
        cpu = CPU()
        cpu.reset()
        assert cpu.flags == 0

    def test_sp_initial(self):
        cpu = CPU()
        cpu.reset()
        assert cpu.sp == 0x01FF

    def test_not_halted(self):
        cpu = CPU()
        cpu.reset()
        assert not cpu.halted


# -----------------------------------------------------------------------------
# LDA - Load Accumulator
# -----------------------------------------------------------------------------

class TestLDA:
    def test_lda_immediate(self):
        cpu = make_cpu(0x90, 0x42)   # LDA $42
        cpu.step()
        assert cpu.acc == 0x42

    def test_lda_immediate_sets_zero_flag(self):
        cpu = make_cpu(0x90, 0x00)
        cpu.step()
        assert cpu.flags & FLAG_Z

    def test_lda_immediate_sets_negative_flag(self):
        cpu = make_cpu(0x90, 0x80)
        cpu.step()
        assert cpu.flags & FLAG_N

    def test_lda_immediate_clears_zero_flag(self):
        cpu = make_cpu(0x90, 0x01)
        cpu.step()
        assert not (cpu.flags & FLAG_Z)

    def test_lda_direct(self):
        cpu = make_cpu(0x91, 0x50, 0x00)   # LDA [$5000]
        cpu.ram[0x5000] = 0xAB
        cpu.step()
        assert cpu.acc == 0xAB

    def test_lda_indexed(self):
        cpu = make_cpu(0x92, 0x50, 0x00)   # LDA [$5000,X]
        cpu.ix = 0x0010
        cpu.ram[0x5010] = 0xCD
        cpu.step()
        assert cpu.acc == 0xCD

    def test_lda_indirect(self):
        cpu = make_cpu(0x93, 0x60, 0x00)   # LDA [[$6000]]
        cpu.ram[0x6000] = 0x70             # pointer high
        cpu.ram[0x6001] = 0x00             # pointer low -> $7000
        cpu.ram[0x7000] = 0x55
        cpu.step()
        assert cpu.acc == 0x55

    def test_lda_x_ind(self):
        cpu = make_cpu(0x94, 0x60, 0x00)   # LDA [[$6000,X]]  (x-ind: X added before dereference)
        cpu.ix = 0x0004
        cpu.ram[0x6004] = 0x70
        cpu.ram[0x6005] = 0x10             # -> $7010
        cpu.ram[0x7010] = 0x77
        cpu.step()
        assert cpu.acc == 0x77

    def test_lda_ind_x(self):
        cpu = make_cpu(0x95, 0x60, 0x00)   # LDA [[$6000],X]  (ind-x: dereference first, then add X)
        cpu.ix = 0x0004
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00             # pointer -> $7000; effective = $7000 + X
        cpu.ram[0x7004] = 0x99
        cpu.step()
        assert cpu.acc == 0x99


# -----------------------------------------------------------------------------
# STA - Store Accumulator
# -----------------------------------------------------------------------------

class TestSTA:
    def test_sta_direct(self):
        cpu = make_cpu(0x99, 0x50, 0x00)   # STA [$5000]
        cpu.acc = 0xBB
        cpu.step()
        assert cpu.ram[0x5000] == 0xBB

    def test_sta_indexed(self):
        cpu = make_cpu(0x9A, 0x50, 0x00)   # STA [$5000,X]
        cpu.acc = 0xCC
        cpu.ix = 0x0020
        cpu.step()
        assert cpu.ram[0x5020] == 0xCC

    def test_sta_indirect(self):
        cpu = make_cpu(0x9B, 0x60, 0x00)   # STA [[$6000]]
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00             # -> $7000
        cpu.acc = 0x11
        cpu.step()
        assert cpu.ram[0x7000] == 0x11

    def test_sta_x_ind(self):
        cpu = make_cpu(0x9C, 0x60, 0x00)   # STA [[$6000,X]]  (x-ind)
        cpu.ix = 0x0004
        cpu.ram[0x6004] = 0x70
        cpu.ram[0x6005] = 0x10             # -> $7010
        cpu.acc = 0x22
        cpu.step()
        assert cpu.ram[0x7010] == 0x22

    def test_sta_ind_x(self):
        cpu = make_cpu(0x9D, 0x60, 0x00)   # STA [[$6000],X]  (ind-x)
        cpu.ix = 0x0004
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00             # pointer -> $7000; effective = $7000 + X
        cpu.acc = 0x33
        cpu.step()
        assert cpu.ram[0x7004] == 0x33

    def test_sta_write_hook_fires(self):
        cpu = make_cpu(0x99, 0xF0, 0x31)   # STA [$F031]
        cpu.acc = 0x41
        received = []
        cpu._write_hooks[0xF031] = received.append
        cpu.step()
        assert received == [0x41]


# -----------------------------------------------------------------------------
# ADD / ADDC
# -----------------------------------------------------------------------------

class TestADD:
    def test_add_immediate_basic(self):
        cpu = make_cpu(0x10, 0x05)         # ADD $05
        cpu.acc = 3
        cpu.step()
        assert cpu.acc == 8

    def test_add_sets_carry_on_overflow(self):
        cpu = make_cpu(0x10, 0x01)
        cpu.acc = 0xFF
        cpu.step()
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_C
        assert cpu.flags & FLAG_Z

    def test_add_sets_negative(self):
        cpu = make_cpu(0x10, 0x01)
        cpu.acc = 0x7F
        cpu.step()
        assert cpu.flags & FLAG_N
        assert cpu.flags & FLAG_V      # signed overflow: +127 + 1 -> -128

    def test_add_direct(self):
        cpu = make_cpu(0x11, 0x50, 0x00)   # ADD [$5000]
        cpu.ram[0x5000] = 0x10
        cpu.acc = 0x05
        cpu.step()
        assert cpu.acc == 0x15

    def test_addc_uses_carry(self):
        cpu = make_cpu(0x18, 0x01)         # ADDC $01
        cpu.acc = 0x00
        cpu.flags = FLAG_C                 # carry = 1
        cpu.flags_touched = FLAG_C
        cpu.step()
        assert cpu.acc == 0x02            # 0 + 1 + carry(1) = 2


# -----------------------------------------------------------------------------
# SUB / SUBC
# -----------------------------------------------------------------------------

class TestSUB:
    def test_sub_immediate_basic(self):
        cpu = make_cpu(0x20, 0x03)         # SUB $03
        cpu.acc = 0x08
        cpu.step()
        assert cpu.acc == 0x05

    def test_sub_sets_zero_flag(self):
        cpu = make_cpu(0x20, 0x05)
        cpu.acc = 0x05
        cpu.step()
        assert cpu.flags & FLAG_Z

    def test_sub_wraps_without_carry_when_acc_less_than_operand(self):
        # Beboputer convention: SUB/CMPA set Carry only when ACC > operand,
        # not the traditional "carry = no borrow" rule most 8-bit CPUs use.
        # Here ACC (0x00) is not greater than the operand (0x01), so Carry
        # stays clear even though the result wraps around to 0xFF.
        cpu = make_cpu(0x20, 0x01)
        cpu.acc = 0x00
        cpu.step()
        assert cpu.acc == 0xFF
        assert not (cpu.flags & FLAG_C)

    def test_sub_sets_overflow(self):
        # -128 - 1 = -129, overflows signed byte
        cpu = make_cpu(0x20, 0x01)
        cpu.acc = 0x80                    # -128 in two's complement
        cpu.step()
        assert cpu.flags & FLAG_V

    def test_subc_uses_borrow(self):
        cpu = make_cpu(0x28, 0x01)         # SUBC $01
        cpu.acc = 0x05
        cpu.flags = FLAG_C                 # borrow = 1
        cpu.flags_touched = FLAG_C
        cpu.step()
        assert cpu.acc == 0x03            # 5 - 1 - borrow(1) = 3


# -----------------------------------------------------------------------------
# CMPA - Compare
# -----------------------------------------------------------------------------

class TestCMPA:
    def test_cmpa_equal_sets_zero(self):
        cpu = make_cpu(0x60, 0x07)         # CMPA $07
        cpu.acc = 0x07
        cpu.step()
        assert cpu.flags & FLAG_Z
        assert cpu.acc == 0x07            # ACC must be unchanged

    def test_cmpa_greater_sets_carry(self):
        # Beboputer convention: Carry is set when ACC > operand (the
        # opposite of the usual "carry = no borrow" rule).
        cpu = make_cpu(0x60, 0x03)
        cpu.acc = 0x07
        cpu.step()
        assert cpu.flags & FLAG_C

    def test_cmpa_less_clears_carry(self):
        # ACC (0x05) is not greater than the operand (0x0A), so Carry
        # stays clear under the Beboputer's greater-than convention.
        cpu = make_cpu(0x60, 0x0A)
        cpu.acc = 0x05
        cpu.step()
        assert not (cpu.flags & FLAG_C)


# -----------------------------------------------------------------------------
# Logical - AND / OR / XOR
# -----------------------------------------------------------------------------

class TestLogical:
    def test_and_masks_bits(self):
        cpu = make_cpu(0x30, 0x0F)
        cpu.acc = 0xFF
        cpu.step()
        assert cpu.acc == 0x0F

    def test_and_sets_zero(self):
        cpu = make_cpu(0x30, 0x00)
        cpu.acc = 0xFF
        cpu.step()
        assert cpu.flags & FLAG_Z

    def test_or_sets_bits(self):
        cpu = make_cpu(0x38, 0xF0)
        cpu.acc = 0x0F
        cpu.step()
        assert cpu.acc == 0xFF

    def test_xor_toggles_bits(self):
        cpu = make_cpu(0x40, 0xFF)
        cpu.acc = 0xFF
        cpu.step()
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_Z

    def test_xor_clears_self(self):
        cpu = make_cpu(0x40, 0xAA)
        cpu.acc = 0xAA
        cpu.step()
        assert cpu.acc == 0x00


# -----------------------------------------------------------------------------
# Shifts and Rotates
# -----------------------------------------------------------------------------

class TestShifts:
    def test_shl_shifts_left(self):
        cpu = make_cpu(0x70)               # SHL
        cpu.acc = 0x01
        cpu.step()
        assert cpu.acc == 0x02
        assert not (cpu.flags & FLAG_C)

    def test_shl_captures_carry(self):
        cpu = make_cpu(0x70)
        cpu.acc = 0x80
        cpu.step()
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_C

    def test_shr_shifts_right(self):
        cpu = make_cpu(0x71)               # SHR
        cpu.acc = 0x80
        cpu.step()
        assert cpu.acc == 0x40
        assert not (cpu.flags & FLAG_C)

    def test_shr_captures_carry(self):
        cpu = make_cpu(0x71)
        cpu.acc = 0x01
        cpu.step()
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_C

    def test_rolc_rotates_through_carry(self):
        cpu = make_cpu(0x78)               # ROLC
        cpu.acc = 0x80
        cpu.flags = FLAG_C                 # incoming carry = 1
        cpu.flags_touched = FLAG_C
        cpu.step()
        assert cpu.acc == 0x01            # old bit7(1) -> carry; carry(1) -> bit0
        assert cpu.flags & FLAG_C

    def test_rorc_rotates_through_carry(self):
        cpu = make_cpu(0x79)               # RORC
        cpu.acc = 0x01
        cpu.flags = FLAG_C
        cpu.flags_touched = FLAG_C
        cpu.step()
        assert cpu.acc == 0x80           # old bit0(1) -> carry; carry(1) -> bit7
        assert cpu.flags & FLAG_C


# -----------------------------------------------------------------------------
# INC / DEC
# -----------------------------------------------------------------------------

class TestIncDec:
    def test_inca(self):
        cpu = make_cpu(0x80)
        cpu.acc = 0x04
        cpu.step()
        assert cpu.acc == 0x05

    def test_inca_wraps(self):
        cpu = make_cpu(0x80)
        cpu.acc = 0xFF
        cpu.step()
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_Z

    def test_deca(self):
        cpu = make_cpu(0x81)
        cpu.acc = 0x05
        cpu.step()
        assert cpu.acc == 0x04

    def test_deca_wraps(self):
        cpu = make_cpu(0x81)
        cpu.acc = 0x00
        cpu.step()
        assert cpu.acc == 0xFF
        assert cpu.flags & FLAG_N

    def test_incx_no_flags(self):
        cpu = make_cpu(0x82)               # INCX
        cpu.ix = 0x00FF
        original_flags = cpu.flags
        cpu.step()
        assert cpu.ix == 0x0100
        assert cpu.flags == original_flags   # INCX does not touch flags

    def test_decx_wraps(self):
        cpu = make_cpu(0x83)               # DECX
        cpu.ix = 0x0000
        cpu.step()
        assert cpu.ix == 0xFFFF


# -----------------------------------------------------------------------------
# Interrupt mask
# -----------------------------------------------------------------------------

class TestInterruptMask:
    def test_setim_sets_flag(self):
        cpu = make_cpu(0x08)               # SETIM
        cpu.step()
        assert cpu.flags & FLAG_I

    def test_clrim_clears_flag(self):
        cpu = make_cpu(0x09)               # CLRIM
        cpu.flags = FLAG_I
        cpu.step()
        assert not (cpu.flags & FLAG_I)


# -----------------------------------------------------------------------------
# Stack - PSHA / POPA / PUSHSR / POPSR
# -----------------------------------------------------------------------------

class TestStack:
    def test_push_pop_roundtrip(self):
        cpu = make_cpu(0xB2, 0xB0)         # PSHA then POPA
        cpu.acc = 0xAB
        cpu.step()                         # PSHA
        assert cpu.acc == 0xAB
        saved_sp = cpu.sp
        cpu.acc = 0x00
        cpu.step()                         # POPA
        assert cpu.acc == 0xAB
        assert cpu.sp == saved_sp + 1      # net effect on SP is +1 after push then pop

    def test_push_decrements_sp(self):
        cpu = make_cpu(0xB2)               # PSHA
        sp_before = cpu.sp
        cpu.step()
        assert cpu.sp == sp_before - 1

    def test_pop_increments_sp(self):
        cpu = make_cpu(0xB2, 0xB0)
        sp_before = cpu.sp
        cpu.step()                         # PSHA
        cpu.step()                         # POPA
        assert cpu.sp == sp_before        # back to original

    def test_pushsr_popsr_roundtrip(self):
        cpu = make_cpu(0xB3, 0xB1)         # PUSHSR then POPSR
        cpu.flags = FLAG_C | FLAG_Z
        cpu.step()                         # PUSHSR
        cpu.flags = 0
        cpu.step()                         # POPSR
        assert cpu.flags == (FLAG_C | FLAG_Z)

    def test_multiple_pushes_lifo(self):
        # Push 3 values, pop them back in LIFO order
        cpu = make_cpu(
            0x90, 0x11,   # LDA $11
            0xB2,         # PSHA
            0x90, 0x22,   # LDA $22
            0xB2,         # PSHA
            0x90, 0x33,   # LDA $33
            0xB2,         # PSHA
            0xB0,         # POPA -> expect $33
            0xB0,         # POPA -> expect $22
            0xB0,         # POPA -> expect $11
        )
        step_n(cpu, 6)                    # load and push all three
        cpu.step(); assert cpu.acc == 0x33
        cpu.step(); assert cpu.acc == 0x22
        cpu.step(); assert cpu.acc == 0x11


# -----------------------------------------------------------------------------
# HALT
# -----------------------------------------------------------------------------

class TestHalt:
    def test_halt_stops_cpu(self):
        cpu = make_cpu(0x01)               # HALT
        cpu.step()
        assert cpu.halted

    def test_step_after_halt_returns_halt(self):
        cpu = make_cpu(0x01)
        cpu.step()
        result = cpu.step()
        assert result == "HALT"


# -----------------------------------------------------------------------------
# 16-bit register ops: BLDX / BSTX / BLDSP / BSTSP / BLDIV
# -----------------------------------------------------------------------------

class TestBigOps:
    def test_bldx_immediate(self):
        cpu = make_cpu(0xA0, 0x12, 0x34)   # BLDX $1234
        cpu.step()
        assert cpu.ix == 0x1234

    def test_bstx_stores_big_endian(self):
        cpu = make_cpu(0xA9, 0x50, 0x00)   # BSTX [$5000]
        cpu.ix = 0xABCD
        cpu.step()
        assert cpu.ram[0x5000] == 0xAB
        assert cpu.ram[0x5001] == 0xCD

    def test_bldsp_immediate(self):
        cpu = make_cpu(0x50, 0x02, 0x00)   # BLDSP $0200
        cpu.step()
        assert cpu.sp == 0x0200

    def test_bldsp_direct(self):
        cpu = make_cpu(0x51, 0x60, 0x00)   # BLDSP [$6000]
        cpu.ram[0x6000] = 0x03
        cpu.ram[0x6001] = 0x00
        cpu.step()
        assert cpu.sp == 0x0300

    def test_bstsp_stores(self):
        cpu = make_cpu(0x59, 0x50, 0x00)   # BSTSP [$5000]
        cpu.sp = 0x01FF
        cpu.step()
        assert cpu.ram[0x5000] == 0x01
        assert cpu.ram[0x5001] == 0xFF

    def test_bldiv_immediate(self):
        cpu = make_cpu(0xF0, 0xFF, 0xFE)   # BLDIV $FFFE
        cpu.step()
        assert cpu._intr_vector == 0xFFFE

    def test_bldiv_loads_vector(self):
        cpu = make_cpu(0xF1, 0x60, 0x00)   # BLDIV [$6000]
        cpu.ram[0x6000] = 0xFF
        cpu.ram[0x6001] = 0xFE
        cpu.step()
        assert cpu._intr_vector == 0xFFFE


# -----------------------------------------------------------------------------
# Jumps
# -----------------------------------------------------------------------------

class TestJumps:
    def test_jmp_direct(self):
        cpu = make_cpu(0xC1, 0x50, 0x00)   # JMP [$5000]
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jmp_indexed(self):
        cpu = make_cpu(0xC2, 0x50, 0x00)   # JMP [$5000,X]
        cpu.ix = 0x0010
        cpu.step()
        assert cpu.pc == 0x5010

    def test_jmp_indirect(self):
        cpu = make_cpu(0xC3, 0x60, 0x00)   # JMP [[$6000]]
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00
        cpu.step()
        assert cpu.pc == 0x7000

    def test_jmp_x_ind(self):
        cpu = make_cpu(0xC4, 0x60, 0x00)   # JMP [[$6000,X]]  (x-ind)
        cpu.ix = 0x0004
        cpu.ram[0x6004] = 0x70
        cpu.ram[0x6005] = 0x00
        cpu.step()
        assert cpu.pc == 0x7000

    def test_jmp_ind_x(self):
        cpu = make_cpu(0xC5, 0x60, 0x00)   # JMP [[$6000],X]  (ind-x)
        cpu.ix = 0x0004
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00             # pointer -> $7000; effective = $7000 + X
        cpu.step()
        assert cpu.pc == 0x7004

    def test_jc_taken(self):
        cpu = make_cpu(0xE1, 0x50, 0x00)   # JC [$5000]
        cpu.flags = FLAG_C
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jc_not_taken(self):
        cpu = make_cpu(0xE1, 0x50, 0x00)
        cpu.flags = 0
        cpu.step()
        assert cpu.pc != 0x5000

    def test_jnc_taken_when_no_carry(self):
        cpu = make_cpu(0xE6, 0x50, 0x00)   # JNC [$5000]
        cpu.flags = 0
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jz_taken(self):
        cpu = make_cpu(0xD1, 0x50, 0x00)   # JZ [$5000]
        cpu.flags = FLAG_Z
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jnz_taken_when_not_zero(self):
        cpu = make_cpu(0xD6, 0x50, 0x00)   # JNZ [$5000]
        cpu.flags = 0
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jn_taken(self):
        cpu = make_cpu(0xD9, 0x50, 0x00)   # JN [$5000]
        cpu.flags = FLAG_N
        cpu.step()
        assert cpu.pc == 0x5000

    def test_jo_taken(self):
        cpu = make_cpu(0xE9, 0x50, 0x00)   # JO [$5000]
        cpu.flags = FLAG_V
        cpu.step()
        assert cpu.pc == 0x5000


# -----------------------------------------------------------------------------
# JSR / RTS
# -----------------------------------------------------------------------------

class TestJSR_RTS:
    def test_jsr_pushes_return_address(self):
        cpu = make_cpu(0xC9, 0x50, 0x00)   # JSR [$5000]  at $4000
        sp_before = cpu.sp
        cpu.step()
        assert cpu.pc == 0x5000
        # return address = $4003 (opcode + 2 operand bytes)
        hi = cpu.ram[(sp_before)     & 0xFFFF]
        lo = cpu.ram[(sp_before - 1) & 0xFFFF]
        assert (hi << 8) | lo == 0x4003

    def test_jsr_indexed(self):
        cpu = make_cpu(0xCA, 0x50, 0x00)   # JSR [$5000,X]  at $4000
        cpu.ix = 0x0010
        cpu.step()
        assert cpu.pc == 0x5010

    def test_jsr_ind_x(self):
        cpu = make_cpu(0xCD, 0x60, 0x00)   # JSR [[$6000],X]  (ind-x) at $4000
        cpu.ix = 0x0004
        cpu.ram[0x6000] = 0x70
        cpu.ram[0x6001] = 0x00             # pointer -> $7000; effective = $7000 + X
        cpu.step()
        assert cpu.pc == 0x7004

    def test_rts_returns_to_caller(self):
        cpu = make_cpu(
            0xC9, 0x40, 0x04,    # JSR [$4004]  @$4000
            0x01,                # HALT         @$4003 (unreachable in this test)
            0xCF,                # RTS          @$4004
        )
        cpu.step()               # JSR - pc -> $4004, stack has $4003
        cpu.step()               # RTS - pc should return to $4003
        assert cpu.pc == 0x4003

    def test_nested_jsr_rts(self):
        """Two-level subroutine call/return via JSR + RTS.

        Layout:
          $4000: JSR [$4006]   main calls outer-sub; ret=$4003 pushed
          $4003: HALT           (not reached in test)
          $4004-$4005: pad
          $4006: JSR [$400C]   outer-sub calls inner-sub; ret=$4009 pushed
          $4009: RTS            outer-sub returns (not reached in test)
          $400A-$400B: pad
          $400C: RTS            inner-sub returns to outer-sub at $4009
        """
        cpu = make_cpu(
            0xC9, 0x40, 0x06,    # JSR [$4006]   @$4000 -> ret=$4003
            0x01,                # HALT          @$4003
            0x00, 0x00,          # padding       @$4004-$4005
            0xC9, 0x40, 0x0C,    # JSR [$400C]   @$4006 -> ret=$4009
            0xCF,                # RTS           @$4009
            0x00, 0x00,          # padding       @$400A-$400B
            0xCF,                # RTS           @$400C -> returns to $4009
        )
        cpu.step()               # JSR [$4006] main->outer
        cpu.step()               # JSR [$400C] outer->inner
        cpu.step()               # RTS inner->outer  pc=$4009
        assert cpu.pc == 0x4009
        cpu.step()               # RTS outer->main   pc=$4003
        assert cpu.pc == 0x4003


# -----------------------------------------------------------------------------
# BCD arithmetic
# -----------------------------------------------------------------------------

class TestBCD:
    def test_dadd_basic(self):
        cpu = make_cpu(0x48, 0x05)         # DADD $05
        cpu.acc = 0x09                     # BCD 09 + 05 = 14 -> $14
        cpu.step()
        assert cpu.acc == 0x14

    def test_dadd_carry(self):
        cpu = make_cpu(0x48, 0x05)
        cpu.acc = 0x99                     # BCD 99 + 05 -> 04 + carry
        cpu.step()
        assert cpu.acc == 0x04
        assert cpu.flags & FLAG_C

    def test_dsub_basic(self):
        cpu = make_cpu(0x88, 0x03)         # DSUB $03
        cpu.acc = 0x09                     # BCD 09 - 03 = 06
        cpu.step()
        assert cpu.acc == 0x06

    def test_dsub_borrow(self):
        cpu = make_cpu(0x88, 0x01)
        cpu.acc = 0x00                     # BCD 00 - 01 -> borrow
        cpu.step()
        assert cpu.flags & FLAG_C


# -----------------------------------------------------------------------------
# Memory helpers: _read16 / _write16
# -----------------------------------------------------------------------------

class TestMemoryHelpers:
    def test_write16_big_endian(self):
        cpu = CPU()
        cpu.reset()
        cpu._write16(0x1000, 0xABCD)
        assert cpu.ram[0x1000] == 0xAB
        assert cpu.ram[0x1001] == 0xCD

    def test_read16_big_endian(self):
        cpu = CPU()
        cpu.reset()
        cpu.ram[0x2000] = 0x12
        cpu.ram[0x2001] = 0x34
        assert cpu._read16(0x2000) == 0x1234

    def test_read16_wrap(self):
        cpu = CPU()
        cpu.reset()
        cpu.ram[0xFFFF] = 0xAB
        cpu.ram[0x0000] = 0xCD
        assert cpu._read16(0xFFFF) == 0xABCD


# -----------------------------------------------------------------------------
# Write hooks
# -----------------------------------------------------------------------------

class TestWriteHooks:
    def test_hook_called_on_write(self):
        cpu = CPU()
        cpu.reset()
        calls = []
        cpu._write_hooks[0x1234] = calls.append
        cpu._write(0x1234, 0x55)
        assert calls == [0x55]

    def test_hook_not_called_for_other_addr(self):
        cpu = CPU()
        cpu.reset()
        calls = []
        cpu._write_hooks[0x1234] = calls.append
        cpu._write(0x1235, 0x55)
        assert calls == []

    def test_hook_value_masked_to_byte(self):
        cpu = CPU()
        cpu.reset()
        calls = []
        cpu._write_hooks[0x0010] = calls.append
        cpu._write(0x0010, 0x1FF)          # only low byte written
        assert calls == [0xFF]


# -----------------------------------------------------------------------------
# Disassembler
# -----------------------------------------------------------------------------

class TestDisassembler:
    def test_disassemble_nop(self):
        cpu = make_cpu(0x00)               # NOP
        lines = cpu.disassemble_at(0x4000, 1)
        assert lines[0][2] == 'NOP'

    def test_disassemble_lda_imm(self):
        cpu = make_cpu(0x90, 0x42)
        lines = cpu.disassemble_at(0x4000, 1)
        assert lines[0][2] == 'LDA'
        assert lines[0][3] == '$42'

    def test_disassemble_advances_pc_correctly(self):
        cpu = make_cpu(0x90, 0x42, 0x00)   # LDA $42 then NOP
        lines = cpu.disassemble_at(0x4000, 2)
        assert lines[0][0] == 0x4000       # LDA at $4000
        assert lines[1][0] == 0x4002       # NOP at $4002 (LDA is 2 bytes)

    def test_disassemble_halt(self):
        cpu = make_cpu(0x01)
        lines = cpu.disassemble_at(0x4000, 1)
        assert lines[0][2] == 'HALT'


# -----------------------------------------------------------------------------
# Integration: short programs
# -----------------------------------------------------------------------------

class TestIntegration:
    def test_loop_counter(self):
        """Count from 5 down to 0, halt."""
        # LDA $05 / LOOP: DECA / JNZ [LOOP] / HALT
        cpu = make_cpu(
            0x90, 0x05,          # LDA $05       @$4000
            0x81,                # DECA          @$4002   <- LOOP
            0xD6, 0x40, 0x02,    # JNZ [$4002]   @$4003
            0x01,                # HALT          @$4006
        )
        for _ in range(100):     # safety limit
            if cpu.halted:
                break
            cpu.step()
        assert cpu.halted
        assert cpu.acc == 0x00
        assert cpu.flags & FLAG_Z

    def test_sum_via_memory(self):
        """Store two values, add them, write result."""
        cpu = make_cpu(
            0x90, 0x0A,          # LDA $0A (10)
            0x99, 0x50, 0x00,    # STA [$5000]
            0x90, 0x05,          # LDA $05 (5)
            0x11, 0x50, 0x00,    # ADD [$5000]
            0x99, 0x50, 0x01,    # STA [$5001]
            0x01,                # HALT
        )
        for _ in range(10):
            if cpu.halted:
                break
            cpu.step()
        assert cpu.ram[0x5001] == 15

    def test_subroutine_double(self):
        """Call a subroutine that doubles ACC."""
        # Main:    LDA $07 / JSR [DOUBLE] / HALT
        # DOUBLE:  STA [$5000], ADD [$5000], RTS
        cpu = make_cpu(
            0x90, 0x07,          # LDA $07           @$4000
            0xC9, 0x40, 0x08,    # JSR [$4008]        @$4002  -> ret=$4005
            0x01,                # HALT              @$4005
            0x00,                # NOP (padding)     @$4006
            0x00,                # NOP               @$4007
            # DOUBLE subroutine @$4008:
            0x99, 0x50, 0x00,    # STA [$5000]
            0x11, 0x50, 0x00,    # ADD [$5000]        ACC = ACC * 2
            0xCF,                # RTS
        )
        for _ in range(20):
            if cpu.halted:
                break
            cpu.step()
        assert cpu.halted
        assert cpu.acc == 14   # 7 * 2
