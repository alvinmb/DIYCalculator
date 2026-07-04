# Copyright (c) 2026 Alvin Brown & Clive Maxfield
#
# test_cpu.py — Beboputer CPU test suite
#
# Run from the project root (Bebop_python/):
#   python -m pytest bin/beboputer_v7/test_cpu.py -v
# Or run standalone:
#   python bin/beboputer_v7/test_cpu.py
#
# No PyQt5 required — tests the CPU core only.
# ──────────────────────────────────────────────────────────────────

import sys
import os
import unittest

# ── path setup ────────────────────────────────────────────────────
# This file lives at  bin/beboputer_v7/test_cpu.py
# We need  bin/  on sys.path so  "from beboputer_v7.cpu import CPU"  works.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BIN  = os.path.dirname(_HERE)
if _BIN not in sys.path:
    sys.path.insert(0, _BIN)

from beboputer_v7.cpu import CPU
from beboputer_v7.constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I


# ── helpers ───────────────────────────────────────────────────────

def make_cpu(*prog):
    """Fresh CPU with prog loaded at $4000 (reset vector)."""
    cpu = CPU()
    cpu.reset()
    for i, b in enumerate(prog):
        cpu.ram[0x4000 + i] = b
    return cpu

def run(cpu, steps=1):
    """Step the CPU n times; return list of mnemonic strings."""
    return [cpu.step() for _ in range(steps)]

def addr(a):
    """Split a 16-bit address into (hi, lo) bytes."""
    return (a >> 8) & 0xFF, a & 0xFF


# ══════════════════════════════════════════════════════════════════
# Initialisation
# ══════════════════════════════════════════════════════════════════

class TestInit(unittest.TestCase):

    def test_ram_size(self):
        cpu = CPU()
        self.assertEqual(len(cpu.ram), 0x10000)

    def test_reset_vector(self):
        cpu = CPU()
        self.assertEqual(cpu.pc, 0x4000)

    def test_reset_registers(self):
        cpu = CPU()
        cpu.acc = 0xFF; cpu.ix = 0x1234; cpu.flags = 0xFF
        cpu.reset()
        self.assertEqual(cpu.acc, 0)
        self.assertEqual(cpu.ix,  0)
        self.assertEqual(cpu.sp,  0x01FF)
        self.assertEqual(cpu.pc,  0x4000)
        self.assertFalse(cpu.halted)

    def test_keyboard_sentinel(self):
        cpu = CPU()
        self.assertEqual(cpu.ram[0xF011], 0xFF)


# ══════════════════════════════════════════════════════════════════
# NOP
# ══════════════════════════════════════════════════════════════════

class TestNOP(unittest.TestCase):

    def test_nop_advances_pc(self):
        cpu = make_cpu(0x00)
        run(cpu)
        self.assertEqual(cpu.pc, 0x4001)

    def test_nop_leaves_acc(self):
        cpu = make_cpu(0x00)
        cpu.acc = 0x42
        run(cpu)
        self.assertEqual(cpu.acc, 0x42)


# ══════════════════════════════════════════════════════════════════
# LDA
# ══════════════════════════════════════════════════════════════════

class TestLDA(unittest.TestCase):

    def test_lda_imm(self):
        cpu = make_cpu(0x01, 0x7F)
        run(cpu)
        self.assertEqual(cpu.acc, 0x7F)
        self.assertFalse(cpu.flags & FLAG_Z)
        self.assertFalse(cpu.flags & FLAG_N)

    def test_lda_imm_zero_sets_Z(self):
        cpu = make_cpu(0x01, 0x00)
        run(cpu)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_lda_imm_negative_sets_N(self):
        cpu = make_cpu(0x01, 0x80)
        run(cpu)
        self.assertTrue(cpu.flags & FLAG_N)

    def test_lda_abs(self):
        cpu = make_cpu(0x02, 0x10, 0x00)   # LDA [$1000]
        cpu.ram[0x1000] = 0xAB
        run(cpu)
        self.assertEqual(cpu.acc, 0xAB)

    def test_lda_idx(self):
        cpu = make_cpu(0x03, 0x10, 0x00)   # LDA [$1000+X]
        cpu.ix = 5
        cpu.ram[0x1005] = 0xCD
        run(cpu)
        self.assertEqual(cpu.acc, 0xCD)

    def test_lda_ind(self):
        cpu = make_cpu(0x04, 0x20, 0x00)   # LDA [[$2000]]
        cpu.ram[0x2000] = 0x30             # pointer hi
        cpu.ram[0x2001] = 0x00             # pointer lo → $3000
        cpu.ram[0x3000] = 0xEF
        run(cpu)
        self.assertEqual(cpu.acc, 0xEF)

    def test_lda_ind_idx(self):
        cpu = make_cpu(0x05, 0x20, 0x00)   # LDA [[$2000+X]]
        cpu.ix = 2
        cpu.ram[0x2002] = 0x30             # pointer at $2000+2
        cpu.ram[0x2003] = 0x00
        cpu.ram[0x3000] = 0x55
        run(cpu)
        self.assertEqual(cpu.acc, 0x55)


# ══════════════════════════════════════════════════════════════════
# STA
# ══════════════════════════════════════════════════════════════════

class TestSTA(unittest.TestCase):

    def test_sta_abs(self):
        cpu = make_cpu(0x06, 0x10, 0x00)
        cpu.acc = 0x99
        run(cpu)
        self.assertEqual(cpu.ram[0x1000], 0x99)

    def test_sta_idx(self):
        cpu = make_cpu(0x07, 0x10, 0x00)
        cpu.acc = 0x77; cpu.ix = 3
        run(cpu)
        self.assertEqual(cpu.ram[0x1003], 0x77)

    def test_sta_ind(self):
        cpu = make_cpu(0x08, 0x20, 0x00)   # STA [[$2000]]
        cpu.ram[0x2000] = 0x30
        cpu.ram[0x2001] = 0x00
        cpu.acc = 0x11
        run(cpu)
        self.assertEqual(cpu.ram[0x3000], 0x11)

    def test_sta_ind_idx(self):
        cpu = make_cpu(0x09, 0x20, 0x00)   # STA [[$2000+X]]
        cpu.ix = 4
        cpu.ram[0x2004] = 0x30
        cpu.ram[0x2005] = 0x00
        cpu.acc = 0x22
        run(cpu)
        self.assertEqual(cpu.ram[0x3000], 0x22)


# ══════════════════════════════════════════════════════════════════
# ADD / SUB
# ══════════════════════════════════════════════════════════════════

class TestAddSub(unittest.TestCase):

    def test_add_imm_basic(self):
        cpu = make_cpu(0x01, 0x05,   # LDA #5
                       0x0A, 0x03)   # ADD #3
        run(cpu, 2)
        self.assertEqual(cpu.acc, 8)
        self.assertFalse(cpu.flags & FLAG_C)
        self.assertFalse(cpu.flags & FLAG_Z)

    def test_add_carry(self):
        cpu = make_cpu(0x01, 0xFF,
                       0x0A, 0x01)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_C)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_add_overflow(self):
        cpu = make_cpu(0x01, 0x7F,   # 127
                       0x0A, 0x01)   # + 1 = -128 (overflow)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x80)
        self.assertTrue(cpu.flags & FLAG_V)
        self.assertTrue(cpu.flags & FLAG_N)

    def test_sub_imm_basic(self):
        cpu = make_cpu(0x01, 0x0A,
                       0x10, 0x03)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 7)

    def test_sub_zero_sets_Z(self):
        cpu = make_cpu(0x01, 0x05,
                       0x10, 0x05)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_sub_carry_set_when_a_greater(self):
        cpu = make_cpu(0x01, 0x0A,
                       0x10, 0x03)
        run(cpu, 2)
        self.assertTrue(cpu.flags & FLAG_C)

    def test_sub_carry_clear_when_a_less(self):
        cpu = make_cpu(0x01, 0x03,
                       0x10, 0x0A)
        run(cpu, 2)
        self.assertFalse(cpu.flags & FLAG_C)

    def test_addc_uses_carry(self):
        # Set carry first with 0xFF+1, then ADDC
        cpu = make_cpu(0x01, 0xFF,
                       0x0A, 0x01,   # ADD #1 → carry=1, acc=0
                       0x0D, 0x00)   # ADDC #0 → acc = 0 + 0 + 1 = 1
        run(cpu, 3)
        self.assertEqual(cpu.acc, 1)

    def test_subc_uses_carry(self):
        # carry=1 means borrow; 5 - 3 - 1 = 1
        cpu = make_cpu(0x01, 0xFF,
                       0x0A, 0x01,   # ADD → carry=1
                       0x01, 0x05,   # LDA #5
                       0x13, 0x03)   # SUBC #3 → 5-3-1=1
        run(cpu, 4)
        self.assertEqual(cpu.acc, 1)

    def test_add_abs(self):
        cpu = make_cpu(0x01, 0x04,           # LDA #4
                       0x0B, 0x10, 0x00)     # ADD [$1000]
        cpu.ram[0x1000] = 6
        run(cpu, 2)
        self.assertEqual(cpu.acc, 10)

    def test_sub_abs(self):
        cpu = make_cpu(0x01, 0x0F,
                       0x11, 0x10, 0x00)
        cpu.ram[0x1000] = 5
        run(cpu, 2)
        self.assertEqual(cpu.acc, 10)


# ══════════════════════════════════════════════════════════════════
# BCD arithmetic
# ══════════════════════════════════════════════════════════════════

class TestBCD(unittest.TestCase):

    def test_dadd_basic(self):
        cpu = make_cpu(0x01, 0x09,   # LDA #$09
                       0x16, 0x01)   # DADD #$01 → should give $10
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x10)

    def test_dadd_carry(self):
        cpu = make_cpu(0x01, 0x99,
                       0x16, 0x01)   # $99 + $01 BCD → $00 carry=1
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_C)

    def test_dsub_basic(self):
        cpu = make_cpu(0x01, 0x20,
                       0x1C, 0x05)   # $20 - $05 BCD = $15
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x15)

    def test_dsub_borrow(self):
        cpu = make_cpu(0x01, 0x00,
                       0x1C, 0x01)   # $00 - $01 BCD → borrow
        run(cpu, 2)
        self.assertTrue(cpu.flags & FLAG_C)


# ══════════════════════════════════════════════════════════════════
# CMPA
# ══════════════════════════════════════════════════════════════════

class TestCMPA(unittest.TestCase):

    def test_cmpa_equal_sets_Z(self):
        cpu = make_cpu(0x01, 0x07,
                       0x22, 0x07)
        run(cpu, 2)
        self.assertTrue(cpu.flags & FLAG_Z)
        self.assertEqual(cpu.acc, 0x07)   # ACC unchanged

    def test_cmpa_greater_sets_C(self):
        cpu = make_cpu(0x01, 0x0A,
                       0x22, 0x07)   # 10 > 7 → C=1
        run(cpu, 2)
        self.assertTrue(cpu.flags & FLAG_C)
        self.assertFalse(cpu.flags & FLAG_Z)

    def test_cmpa_less_clears_C(self):
        cpu = make_cpu(0x01, 0x03,
                       0x22, 0x07)   # 3 < 7 → C=0
        run(cpu, 2)
        self.assertFalse(cpu.flags & FLAG_C)

    def test_cmpa_does_not_change_acc(self):
        cpu = make_cpu(0x01, 0x42,
                       0x22, 0xFF)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x42)

    def test_cmpa_abs(self):
        cpu = make_cpu(0x01, 0x0F,
                       0x23, 0x10, 0x00)
        cpu.ram[0x1000] = 0x09
        run(cpu, 2)
        self.assertTrue(cpu.flags & FLAG_C)   # 15 > 9


# ══════════════════════════════════════════════════════════════════
# Logic: AND / OR / XOR
# ══════════════════════════════════════════════════════════════════

class TestLogic(unittest.TestCase):

    def test_and_imm(self):
        cpu = make_cpu(0x01, 0xFF,
                       0x25, 0x0F)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x0F)

    def test_and_zero_sets_Z(self):
        cpu = make_cpu(0x01, 0xAA,
                       0x25, 0x55)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_or_imm(self):
        cpu = make_cpu(0x01, 0xF0,
                       0x28, 0x0F)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0xFF)

    def test_xor_imm(self):
        cpu = make_cpu(0x01, 0xFF,
                       0x2B, 0xFF)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_xor_toggle(self):
        cpu = make_cpu(0x01, 0xA5,
                       0x2B, 0xFF)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x5A)

    def test_and_abs(self):
        cpu = make_cpu(0x01, 0xFF,
                       0x26, 0x10, 0x00)
        cpu.ram[0x1000] = 0x3C
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x3C)

    def test_or_abs(self):
        cpu = make_cpu(0x01, 0x0F,
                       0x29, 0x10, 0x00)
        cpu.ram[0x1000] = 0xF0
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0xFF)


# ══════════════════════════════════════════════════════════════════
# Shifts and Rotates
# ══════════════════════════════════════════════════════════════════

class TestShifts(unittest.TestCase):

    def test_shl_basic(self):
        cpu = make_cpu(0x01, 0x01,
                       0x2E)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x02)
        self.assertFalse(cpu.flags & FLAG_C)

    def test_shl_carry(self):
        cpu = make_cpu(0x01, 0x80,
                       0x2E)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_C)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_shr_basic(self):
        cpu = make_cpu(0x01, 0x80,
                       0x2F)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x40)
        self.assertFalse(cpu.flags & FLAG_C)

    def test_shr_carry(self):
        cpu = make_cpu(0x01, 0x01,
                       0x2F)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_C)

    def test_rolc_no_carry_in(self):
        cpu = make_cpu(0x01, 0x40,
                       0x30)          # ROLC, carry=0 → 0x80
        cpu.flags &= ~FLAG_C
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x80)
        self.assertFalse(cpu.flags & FLAG_C)

    def test_rolc_with_carry_in(self):
        cpu = make_cpu(0x01, 0x40,
                       0x30)          # ROLC, carry=1 → 0x81
        run(cpu)
        cpu.flags |= FLAG_C
        cpu.step()
        self.assertEqual(cpu.acc, 0x81)

    def test_rorc_no_carry_in(self):
        cpu = make_cpu(0x01, 0x02,
                       0x31)          # RORC, carry=0 → 0x01
        cpu.flags &= ~FLAG_C
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x01)

    def test_rorc_with_carry_in(self):
        cpu = make_cpu(0x01, 0x02,
                       0x31)          # RORC, carry=1 → 0x81
        run(cpu)
        cpu.flags |= FLAG_C
        cpu.step()
        self.assertEqual(cpu.acc, 0x81)


# ══════════════════════════════════════════════════════════════════
# INCA / DECA / INCX / DECX
# ══════════════════════════════════════════════════════════════════

class TestIncrDecr(unittest.TestCase):

    def test_inca(self):
        cpu = make_cpu(0x01, 0x05, 0x32)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 6)

    def test_inca_wraps(self):
        cpu = make_cpu(0x01, 0xFF, 0x32)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0x00)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_deca(self):
        cpu = make_cpu(0x01, 0x05, 0x33)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 4)

    def test_deca_wraps(self):
        cpu = make_cpu(0x01, 0x00, 0x33)
        run(cpu, 2)
        self.assertEqual(cpu.acc, 0xFF)
        self.assertTrue(cpu.flags & FLAG_N)

    def test_incx(self):
        cpu = make_cpu(0x34)
        cpu.ix = 0x00FF
        run(cpu)
        self.assertEqual(cpu.ix, 0x0100)

    def test_decx(self):
        cpu = make_cpu(0x35)
        cpu.ix = 0x0001
        run(cpu)
        self.assertEqual(cpu.ix, 0x0000)
        self.assertTrue(cpu.flags & FLAG_Z)


# ══════════════════════════════════════════════════════════════════
# Stack: PSHA / POPA / PUSHSR / POPSR
# ══════════════════════════════════════════════════════════════════

class TestStack(unittest.TestCase):

    def test_push_pop(self):
        cpu = make_cpu(0x01, 0xAB,   # LDA #$AB
                       0x38,          # PSHA
                       0x01, 0x00,   # LDA #0
                       0x39)          # POPA
        run(cpu, 4)
        self.assertEqual(cpu.acc, 0xAB)

    def test_push_decrements_sp(self):
        cpu = make_cpu(0x01, 0x01, 0x38)
        sp_before = cpu.sp
        run(cpu, 2)
        self.assertEqual(cpu.sp, sp_before - 1)

    def test_pop_increments_sp(self):
        cpu = make_cpu(0x01, 0x01, 0x38, 0x39)
        run(cpu, 2)
        sp_after_push = cpu.sp
        run(cpu)
        self.assertEqual(cpu.sp, sp_after_push + 1)

    def test_pushsr_popsr(self):
        cpu = make_cpu(0x01, 0xFF,   # LDA #$FF
                       0x0A, 0x01,   # ADD #1 → carry + zero
                       0x3A,          # PUSHSR
                       0x36,          # CLRIM (modify flags)
                       0x3B)          # POPSR (restore)
        run(cpu, 5)
        # After POPSR, flags should be restored to post-ADD state
        self.assertTrue(cpu.flags & FLAG_C)
        self.assertTrue(cpu.flags & FLAG_Z)

    def test_multiple_pushes(self):
        cpu = make_cpu(0x01, 0x01, 0x38,
                       0x01, 0x02, 0x38,
                       0x39,
                       0x39)
        run(cpu, 6)
        self.assertEqual(cpu.acc, 1)


# ══════════════════════════════════════════════════════════════════
# Branches
# ══════════════════════════════════════════════════════════════════

class TestBranches(unittest.TestCase):

    def _branch_taken(self, set_flag_op, branch_op, flag_bit):
        """Helper: set a flag via an instruction, then verify branch is taken."""
        hi, lo = addr(0x4020)
        cpu = make_cpu(set_flag_op, branch_op, hi, lo)
        run(cpu, 2)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jmp_abs(self):
        hi, lo = addr(0x5000)
        cpu = make_cpu(0x45, hi, lo)
        run(cpu)
        self.assertEqual(cpu.pc, 0x5000)

    def test_jmp_ind(self):
        cpu = make_cpu(0x46, 0x20, 0x00)  # JMP [$2000]
        cpu.ram[0x2000] = 0x50
        cpu.ram[0x2001] = 0x00
        run(cpu)
        self.assertEqual(cpu.pc, 0x5000)

    def test_jmp_idx(self):
        cpu = make_cpu(0x47, 0x20, 0x00)  # JMP [$2000+X]
        cpu.ix = 2
        cpu.ram[0x2002] = 0x60
        cpu.ram[0x2003] = 0x00
        run(cpu)
        self.assertEqual(cpu.pc, 0x6000)

    def test_jc_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0xFF, 0x0A, 0x01,   # ADD sets C=1
                       0x48, hi, lo)               # JC
        run(cpu, 3)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jc_not_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x01, 0x0A, 0x01,   # ADD, no carry
                       0x48, hi, lo)
        run(cpu, 3)
        self.assertEqual(cpu.pc, 0x4007)   # past the JC instruction

    def test_jnc_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x01, 0x0A, 0x01,   # no carry
                       0x49, hi, lo)
        run(cpu, 3)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jz_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x00,       # LDA #0 → Z=1
                       0x4C, hi, lo)
        run(cpu, 2)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jnz_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x01,
                       0x4D, hi, lo)
        run(cpu, 2)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jn_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x80,       # N=1
                       0x4A, hi, lo)
        run(cpu, 2)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jnn_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x01,
                       0x4B, hi, lo)
        run(cpu, 2)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jo_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x7F, 0x0A, 0x01,   # overflow
                       0x4E, hi, lo)
        run(cpu, 3)
        self.assertEqual(cpu.pc, 0x4020)

    def test_jno_taken(self):
        hi, lo = addr(0x4020)
        cpu = make_cpu(0x01, 0x01, 0x0A, 0x01,   # no overflow
                       0x4F, hi, lo)
        run(cpu, 3)
        self.assertEqual(cpu.pc, 0x4020)


# ══════════════════════════════════════════════════════════════════
# JSR / RTS
# ══════════════════════════════════════════════════════════════════

class TestJSR_RTS(unittest.TestCase):

    def test_jsr_rts(self):
        # Program at $4000: JSR $4010
        # Subroutine at $4010: LDA #$42, RTS
        cpu = make_cpu(
            0x50, 0x40, 0x10,    # $4000: JSR $4010
            0x3C,                 # $4003: HALT
        )
        # Subroutine at $4010
        cpu.ram[0x4010] = 0x01   # LDA #$42
        cpu.ram[0x4011] = 0x42
        cpu.ram[0x4012] = 0x3E   # RTS

        run(cpu)                  # JSR — jumps to $4010
        self.assertEqual(cpu.pc, 0x4010)

        run(cpu, 2)               # LDA then RTS
        self.assertEqual(cpu.acc, 0x42)
        self.assertEqual(cpu.pc, 0x4003)   # returned past JSR

    def test_jsr_pushes_return_addr(self):
        hi, lo = addr(0x5000)
        cpu = make_cpu(0x50, hi, lo)
        sp_before = cpu.sp
        run(cpu)
        # JSR pushes PC.hi then PC.lo → sp decremented by 2
        self.assertEqual(cpu.sp, sp_before - 2)

    def test_jsr_indirect(self):
        cpu = make_cpu(0x51, 0x20, 0x00)   # JSR [$2000]
        cpu.ram[0x2000] = 0x50
        cpu.ram[0x2001] = 0x00
        run(cpu)
        self.assertEqual(cpu.pc, 0x5000)


# ══════════════════════════════════════════════════════════════════
# HALT
# ══════════════════════════════════════════════════════════════════

class TestHALT(unittest.TestCase):

    def test_halt_sets_halted(self):
        cpu = make_cpu(0x3C)
        run(cpu)
        self.assertTrue(cpu.halted)

    def test_halt_returns_halt_string(self):
        cpu = make_cpu(0x3C)
        r = cpu.step()
        self.assertEqual(r, "HALT")

    def test_step_after_halt_returns_halt(self):
        cpu = make_cpu(0x3C)
        run(cpu)
        r = cpu.step()
        self.assertEqual(r, "HALT")

    def test_reset_clears_halted(self):
        cpu = make_cpu(0x3C)
        run(cpu)
        cpu.reset()
        self.assertFalse(cpu.halted)


# ══════════════════════════════════════════════════════════════════
# Index register: BLDX / BSTX / BLDSP / BSTSP
# ══════════════════════════════════════════════════════════════════

class TestIndexReg(unittest.TestCase):

    def test_bldx_imm(self):
        cpu = make_cpu(0x3F, 0x12, 0x34)   # BLDX #$1234
        run(cpu)
        self.assertEqual(cpu.ix, 0x1234)

    def test_bldx_abs(self):
        cpu = make_cpu(0x40, 0x10, 0x00)   # BLDX [$1000]
        cpu.ram[0x1000] = 0xAB
        cpu.ram[0x1001] = 0xCD
        run(cpu)
        self.assertEqual(cpu.ix, 0xABCD)

    def test_bstx(self):
        cpu = make_cpu(0x41, 0x10, 0x00)   # BSTX [$1000]
        cpu.ix = 0x5678
        run(cpu)
        self.assertEqual(cpu.ram[0x1000], 0x56)
        self.assertEqual(cpu.ram[0x1001], 0x78)

    def test_bldsp(self):
        cpu = make_cpu(0x42, 0x02, 0x00)   # BLDSP #$0200
        run(cpu)
        self.assertEqual(cpu.sp, 0x0200)

    def test_bstsp(self):
        cpu = make_cpu(0x43, 0x10, 0x00)   # BSTSP [$1000]
        cpu.sp = 0x01EF
        run(cpu)
        self.assertEqual(cpu.ram[0x1000], 0x01)
        self.assertEqual(cpu.ram[0x1001], 0xEF)


# ══════════════════════════════════════════════════════════════════
# Interrupt mask: CLRIM / SETIM
# ══════════════════════════════════════════════════════════════════

class TestInterruptMask(unittest.TestCase):

    def test_setim(self):
        cpu = make_cpu(0x37)
        run(cpu)
        self.assertTrue(cpu.flags & FLAG_I)

    def test_clrim(self):
        cpu = make_cpu(0x37, 0x36)
        run(cpu, 2)
        self.assertFalse(cpu.flags & FLAG_I)


# ══════════════════════════════════════════════════════════════════
# Memory wrap-around
# ══════════════════════════════════════════════════════════════════

class TestMemoryWrap(unittest.TestCase):

    def test_read_wraps_at_64k(self):
        cpu = CPU()
        cpu.ram[0x0000] = 0x42
        val = cpu._read(0x10000)   # should wrap to $0000
        self.assertEqual(val, 0x42)

    def test_write_wraps_at_64k(self):
        cpu = CPU()
        cpu._write(0x10001, 0x99)   # should wrap to $0001
        self.assertEqual(cpu.ram[0x0001], 0x99)

    def test_pc_wraps(self):
        cpu = CPU()
        cpu.pc = 0xFFFF
        cpu.ram[0xFFFF] = 0x00     # NOP
        cpu.step()
        self.assertEqual(cpu.pc, 0x0000)


# ══════════════════════════════════════════════════════════════════
# Write / Read hooks (I/O ports)
# ══════════════════════════════════════════════════════════════════

class TestHooks(unittest.TestCase):

    def test_write_hook_fires(self):
        cpu = make_cpu(0x01, 0xAB,
                       0x06, 0xF0, 0x31)   # STA [$F031]
        received = []
        cpu._write_hooks[0xF031] = lambda v: received.append(v)
        run(cpu, 2)
        self.assertEqual(received, [0xAB])

    def test_read_hook_fires(self):
        cpu = make_cpu(0x02, 0xF0, 0x11)   # LDA [$F011]
        cpu.ram[0xF011] = 0x41
        seen = []
        cpu._read_hooks[0xF011] = lambda v: seen.append(v)
        run(cpu)
        self.assertEqual(seen, [0x41])

    def test_write_hook_does_not_prevent_write(self):
        cpu = make_cpu(0x01, 0x55,
                       0x06, 0x10, 0x00)
        cpu._write_hooks[0x1000] = lambda v: None
        run(cpu, 2)
        self.assertEqual(cpu.ram[0x1000], 0x55)

    def test_multiple_hooks(self):
        cpu = make_cpu(0x01, 0x01, 0x06, 0x10, 0x00,
                       0x01, 0x02, 0x06, 0x10, 0x01)
        calls = []
        cpu._write_hooks[0x1000] = lambda v: calls.append(('A', v))
        cpu._write_hooks[0x1001] = lambda v: calls.append(('B', v))
        run(cpu, 4)
        self.assertIn(('A', 0x01), calls)
        self.assertIn(('B', 0x02), calls)


# ══════════════════════════════════════════════════════════════════
# Disassembler
# ══════════════════════════════════════════════════════════════════

class TestDisassembler(unittest.TestCase):

    def test_basic_disassembly(self):
        cpu = make_cpu(0x01, 0x42,   # LDA #$42
                       0x3C)          # HALT
        lines = cpu.disassemble_at(0x4000, 2)
        self.assertEqual(lines[0][2], 'LDA')
        self.assertEqual(lines[1][2], 'HALT')

    def test_disassembly_returns_address(self):
        cpu = make_cpu(0x00, 0x00)
        lines = cpu.disassemble_at(0x4000, 1)
        self.assertEqual(lines[0][0], 0x4000)

    def test_disassembly_operand(self):
        cpu = make_cpu(0x01, 0xFF)
        lines = cpu.disassemble_at(0x4000, 1)
        self.assertIn('FF', lines[0][3].upper())

    def test_disassembly_advances_correctly(self):
        # 2-byte instruction then 3-byte instruction
        cpu = make_cpu(0x01, 0x42,         # LDA imm (2 bytes)
                       0x06, 0x10, 0x00)   # STA abs (3 bytes)
        lines = cpu.disassemble_at(0x4000, 2)
        self.assertEqual(lines[0][0], 0x4000)
        self.assertEqual(lines[1][0], 0x4002)

    def test_unknown_opcode(self):
        cpu = CPU()
        cpu.ram[0x4000] = 0xFF   # illegal
        lines = cpu.disassemble_at(0x4000, 1)
        self.assertEqual(lines[0][2], '???')


# ══════════════════════════════════════════════════════════════════
# Indexed addressing integration
# ══════════════════════════════════════════════════════════════════

class TestIndexedAddressing(unittest.TestCase):

    def test_lda_idx_add_loop(self):
        """Sum 4 bytes from a table using IX."""
        # Table at $1000: 1, 2, 3, 4
        cpu = CPU()
        cpu.reset()
        table = [1, 2, 3, 4]
        for i, v in enumerate(table):
            cpu.ram[0x1000 + i] = v

        # Program: sum = 0; for ix in 0..3: sum += table[ix]
        prog = [
            0x3F, 0x00, 0x00,   # $4000 BLDX #0
            0x01, 0x00,          # $4003 LDA #0  (accumulator = sum)
        ]
        # loop: ADD [$1000+X]; INCX; CMPA? just loop 4 times with JNZ trick
        # simpler: unroll
        for _ in range(4):
            prog += [0x0C, 0x10, 0x00,   # ADD [$1000+X]
                     0x34]                 # INCX
        prog.append(0x3C)                 # HALT
        for i, b in enumerate(prog):
            cpu.ram[0x4000 + i] = b

        # Execute: BLDX + LDA + 4*(ADD+INCX) + HALT = 2+4*2+1 = 11 steps
        for _ in range(11):
            r = cpu.step()
            if r == "HALT":
                break
        self.assertEqual(cpu.acc, 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
