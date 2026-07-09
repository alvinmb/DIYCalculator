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
Beboputer 8-bit virtual CPU — instruction set aligned to das.py.

Opcode numbering matches Appendix A (Tables A-2a/A-2b) of The Official
DIY Calculator Data Book.

Addressing modes
----------------
  imm          opcode + 1-byte operand
               (BLDX/BLDSP/BLDIV use a 16-bit immediate -> 2-byte operand)
  dir (abs)    opcode + 16-bit big-endian address
  idx (abs-x)  opcode + 16-bit big-endian address  (effective = addr + IX)
  ind          opcode + 16-bit addr of pointer     (pointer is 16-bit BE in RAM)
  xind (x-ind) opcode + 16-bit addr of pointer      (pointer addr = addr + IX;
               i.e. IX is added BEFORE the pointer is fetched)
  indx (ind-x) opcode + 16-bit addr of pointer      (pointer = mem[addr];
               effective = pointer + IX; i.e. IX is added AFTER the
               pointer is fetched)

Registers
---------
  acc   8-bit  accumulator
  ix   16-bit  index register  (used by indexed / indirect-indexed modes)
  sp   16-bit  stack pointer   (descending; reset to $01FF)
  pc   16-bit  program counter (reset to RESET_VECTOR = $4000)
  flags 8-bit  C Z N V I (V displayed as "O" on the CPU panel)

Stack convention
----------------
  PUSH: write byte to mem[SP], then SP--
  POP:  SP++, then read byte from mem[SP]
  JSR pushes PC.high then PC.low; RTS pops in reverse.
"""

from .constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I, OP, instr_size


class CPU:
    """Beboputer 8-bit virtual CPU."""

    RESET_VECTOR = 0x4000   # code loaded by the Assembler starts at $4000
    RAM_SIZE     = 0x10000  # 64 KB

    def __init__(self):
        self.ram         = bytearray(self.RAM_SIZE)
        # Real RAM chips power up with indeterminate contents — every
        # location is "undefined" ($XX) until something actually writes
        # to it. This flag array lets the UI (Memory Walker) show "XX"
        # for bytes the program hasn't touched yet, instead of a
        # misleading $00. It is only reset on power-on (here), not on
        # every CPU Reset, since RAM contents survive a reset in
        # real hardware.
        self.ram_touched = bytearray(self.RAM_SIZE)
        self.ports_in  = bytearray(16)
        self.ports_out = bytearray(16)
        self._write_hooks: dict = {}
        self._read_hooks:  dict = {}
        self.reset()
        self._load_default_program()

    def reset(self):
        self.acc           = 0
        self.pc            = self.RESET_VECTOR
        self.sp            = 0x01FF
        self.ix            = 0
        self.instr         = 0
        self.flags         = 0
        self.flags_touched = 0
        self._intr_vector  = 0xFFFE
        self.halted        = False
        self.running       = False
        self.cycle_count   = 0
        self.ram[0xF011]   = 0xFF  # keypad idle sentinel (no key pressed)
        self.ram[0xF031]   = 0x00  # clear display port
        self.ram[0xF032]   = 0x00  # clear LED port
        for addr in (0xF011, 0xF031, 0xF032):
            self.ram_touched[addr] = 1

    def _load_default_program(self):
        prog = [
            0x90, 0x05,        # LDA  $05
            0x10, 0x03,        # ADD  $03
            0x99, 0x40, 0x50,  # STA  [$4050]
            0x90, 0x0A,        # LDA  $0A
            0x20, 0x05,        # SUB  $05
            0x80,              # INCA
            0x01,              # HALT
        ]
        for i, b in enumerate(prog):
            self.ram[self.RESET_VECTOR + i] = b
            self.ram_touched[self.RESET_VECTOR + i] = 1

    def _read(self, addr):
        addr &= 0xFFFF
        val  = self.ram[addr]
        hook = self._read_hooks.get(addr)
        if hook is not None:
            hook(val)
        return val

    def _write(self, addr, val):
        addr &= 0xFFFF
        val  &= 0xFF
        self.ram[addr] = val
        self.ram_touched[addr] = 1
        hook = self._write_hooks.get(addr)
        if hook is not None:
            hook(val)

    def _fetch(self):
        b = self._read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return b

    def _fetch16(self):
        hi = self._fetch()
        lo = self._fetch()
        return (hi << 8) | lo

    def _read16(self, addr):
        hi = self._read(addr)
        lo = self._read((addr + 1) & 0xFFFF)
        return (hi << 8) | lo

    def _write16(self, addr, val):
        self._write(addr,                (val >> 8) & 0xFF)
        self._write((addr + 1) & 0xFFFF, val        & 0xFF)

    def _push(self, val):
        self._write(self.sp, val & 0xFF)
        self.sp = (self.sp - 1) & 0xFFFF

    def _pop(self):
        self.sp = (self.sp + 1) & 0xFFFF
        return self._read(self.sp)

    def _set_nz(self, val):
        self.flags &= ~(FLAG_Z | FLAG_N)
        if val == 0:    self.flags |= FLAG_Z
        if val & 0x80:  self.flags |= FLAG_N
        self.flags_touched |= (FLAG_Z | FLAG_N)

    def _set_add_flags(self, a, b, result):
        r8 = result & 0xFF
        self.flags &= ~(FLAG_C | FLAG_Z | FLAG_N | FLAG_V)
        if result > 0xFF:                                           self.flags |= FLAG_C
        if r8 == 0:                                                 self.flags |= FLAG_Z
        if r8 & 0x80:                                               self.flags |= FLAG_N
        if (not (a & 0x80) and not (b & 0x80) and (r8 & 0x80)) or \
           ((a & 0x80) and (b & 0x80) and not (r8 & 0x80)):        self.flags |= FLAG_V
        self.flags_touched |= (FLAG_C | FLAG_Z | FLAG_N | FLAG_V)

    def _set_sub_flags(self, a, b, result):
        r8 = result & 0xFF
        self.flags &= ~(FLAG_C | FLAG_Z | FLAG_N | FLAG_V)
        if (a & 0xFF) > (b & 0xFF):                                 self.flags |= FLAG_C
        if r8 == 0:                                                  self.flags |= FLAG_Z
        if r8 & 0x80:                                                self.flags |= FLAG_N
        if ((a & 0x80) != (b & 0x80)) and ((r8 & 0x80) != (a & 0x80)): self.flags |= FLAG_V
        self.flags_touched |= (FLAG_C | FLAG_Z | FLAG_N | FLAG_V)

    def _bcd_add(self, a, b, carry=0):
        lo = (a & 0x0F) + (b & 0x0F) + carry
        hi = (a >> 4)   + (b >> 4)
        if lo > 9:  lo -= 10; hi += 1
        if hi > 9:  hi -= 10; c_out = 1
        else:       c_out = 0
        return ((hi & 0x0F) << 4) | (lo & 0x0F), c_out

    def _bcd_sub(self, a, b, borrow=0):
        lo = (a & 0x0F) - (b & 0x0F) - borrow
        hi = (a >> 4)   - (b >> 4)
        if lo < 0:  lo += 10; hi -= 1
        if hi < 0:  hi += 10; b_out = 1
        else:       b_out = 0
        return ((hi & 0x0F) << 4) | (lo & 0x0F), b_out

    def _set_bcd_flags(self, result, carry):
        self.flags &= ~(FLAG_C | FLAG_Z | FLAG_N)
        if carry:         self.flags |= FLAG_C
        if result == 0:   self.flags |= FLAG_Z
        if result & 0x80: self.flags |= FLAG_N
        self.flags_touched |= (FLAG_C | FLAG_Z | FLAG_N)

    def step(self):
        """Execute one instruction. Returns mnemonic string or error."""
        if self.halted:
            return "HALT"
        try:
            self.instr = self._fetch()
            self.cycle_count += 1
            op = self.instr

            if   op == 0x00: pass                                                          # NOP
            elif op == 0x01: self.halted = True                                            # HALT

            # DADD  (BCD add) — provisional placeholder opcodes
            elif op == 0x02:
                n = self._fetch();  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x03:
                n = self._read(self._fetch16());  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x04:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)

            # DADDC (BCD add with carry) — provisional placeholder opcodes
            elif op == 0x05:
                n = self._fetch();  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x06:
                n = self._read(self._fetch16());  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x07:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)

            elif op == 0x08: self.flags |=  FLAG_I;  self.flags_touched |= FLAG_I           # SETIM
            elif op == 0x09: self.flags &= ~FLAG_I;  self.flags_touched |= FLAG_I           # CLRIM

            # DSUBC (BCD subtract with borrow) — provisional placeholder opcodes
            elif op == 0x0A:
                n = self._fetch();  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x0B:
                n = self._read(self._fetch16());  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x0C:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)

            # ADD
            elif op == 0x10:
                n = self._fetch();  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x11:
                n = self._read(self._fetch16());  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x12:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF

            # ADDC
            elif op == 0x18:
                n = self._fetch();  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x19:
                n = self._read(self._fetch16());  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x1A:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF

            # DSUB (BCD subtract) — unchanged opcodes, provisional semantics
            elif op == 0x1C:
                n = self._fetch();  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x1D:
                n = self._read(self._fetch16());  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x1E:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)

            # SUB
            elif op == 0x20:
                n = self._fetch();  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x21:
                n = self._read(self._fetch16());  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x22:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF

            # SUBC
            elif op == 0x28:
                n = self._fetch();  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x29:
                n = self._read(self._fetch16());  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x2A:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF

            # AND
            elif op == 0x30: self.acc &= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x31: self.acc &= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x32: self.acc &= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            # OR
            elif op == 0x38: self.acc |= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x39: self.acc |= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x3A: self.acc |= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            # XOR
            elif op == 0x40: self.acc ^= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x41: self.acc ^= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x42: self.acc ^= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            # BLDSP  (big load stack pointer)
            elif op == 0x50: self.sp = self._fetch16()
            elif op == 0x51: self.sp = self._read16(self._fetch16())
            # BSTSP  (big store stack pointer)
            elif op == 0x59: self._write16(self._fetch16(), self.sp)

            # CMPA (compare — subtract without storing result)
            elif op == 0x60: n = self._fetch();                                           self._set_sub_flags(self.acc, n, self.acc - n)
            elif op == 0x61: n = self._read(self._fetch16());                             self._set_sub_flags(self.acc, n, self.acc - n)
            elif op == 0x62: n = self._read((self._fetch16() + self.ix) & 0xFFFF);        self._set_sub_flags(self.acc, n, self.acc - n)

            elif op == 0x70:
                c = (self.acc >> 7) & 1;  self.acc = (self.acc << 1) & 0xFF               # SHL
                self.flags = (self.flags & ~FLAG_C) | c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x71:
                c = self.acc & 1;  self.acc = (self.acc >> 1) & 0xFF                      # SHR
                self.flags = (self.flags & ~FLAG_C) | c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x78:
                old_c = 1 if (self.flags & FLAG_C) else 0;  new_c = (self.acc >> 7) & 1   # ROLC
                self.acc = ((self.acc << 1) | old_c) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | new_c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x79:
                old_c = 1 if (self.flags & FLAG_C) else 0;  new_c = self.acc & 1          # RORC
                self.acc = ((self.acc >> 1) | (old_c << 7)) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | new_c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)

            elif op == 0x80: self.acc = (self.acc + 1) & 0xFF;  self._set_nz(self.acc)     # INCA
            elif op == 0x81: self.acc = (self.acc - 1) & 0xFF;  self._set_nz(self.acc)     # DECA
            elif op == 0x82: self.ix  = (self.ix + 1) & 0xFFFF; self._set_nz(self.ix)      # INCX
            elif op == 0x83: self.ix  = (self.ix - 1) & 0xFFFF; self._set_nz(self.ix)      # DECX

            # LDA — imm / dir / idx / ind / xind (x-ind) / indx (ind-x)
            elif op == 0x90: self.acc = self._fetch();               self._set_nz(self.acc)
            elif op == 0x91: self.acc = self._read(self._fetch16()); self._set_nz(self.acc)
            elif op == 0x92: self.acc = self._read((self._fetch16() + self.ix) & 0xFFFF);  self._set_nz(self.acc)
            elif op == 0x93: self.acc = self._read(self._read16(self._fetch16()));          self._set_nz(self.acc)
            elif op == 0x94: self.acc = self._read(self._read16((self._fetch16() + self.ix) & 0xFFFF)); self._set_nz(self.acc)
            elif op == 0x95: self.acc = self._read((self._read16(self._fetch16()) + self.ix) & 0xFFFF); self._set_nz(self.acc)

            # STA — dir / idx / ind / xind (x-ind) / indx (ind-x)
            elif op == 0x99: self._write(self._fetch16(), self.acc)
            elif op == 0x9A: self._write((self._fetch16() + self.ix) & 0xFFFF, self.acc)
            elif op == 0x9B: self._write(self._read16(self._fetch16()), self.acc)
            elif op == 0x9C: self._write(self._read16((self._fetch16() + self.ix) & 0xFFFF), self.acc)
            elif op == 0x9D: self._write((self._read16(self._fetch16()) + self.ix) & 0xFFFF, self.acc)

            # BLDX (big load index register) / BSTX (big store index register)
            elif op == 0xA0: self.ix = self._fetch16()
            elif op == 0xA1: self.ix = self._read16(self._fetch16())
            elif op == 0xA9: self._write16(self._fetch16(), self.ix)

            elif op == 0xB0: self.acc = self._pop();  self._set_nz(self.acc)               # POPA
            elif op == 0xB1: self.flags = self._pop();  self.flags_touched = 0xFF          # POPSR
            elif op == 0xB2: self._push(self.acc)                                          # PSHA / PUSHA
            elif op == 0xB3: self._push(self.flags)                                        # PUSHSR

            # JMP — dir / idx / ind / xind (x-ind) / indx (ind-x)
            elif op == 0xC1: self.pc = self._fetch16()
            elif op == 0xC2: self.pc = (self._fetch16() + self.ix) & 0xFFFF
            elif op == 0xC3: self.pc = self._read16(self._fetch16())
            elif op == 0xC4: self.pc = self._read16((self._fetch16() + self.ix) & 0xFFFF)
            elif op == 0xC5: self.pc = (self._read16(self._fetch16()) + self.ix) & 0xFFFF

            elif op == 0xC7:                                                               # RTI
                lo = self._pop();  hi = self._pop()
                self.pc    = (hi << 8) | lo
                self.flags = self._pop();  self.flags_touched = 0xFF

            # JSR — dir / idx / ind / xind (x-ind) / indx (ind-x)
            elif op == 0xC9:
                addr = self._fetch16()
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0xCA:
                addr = (self._fetch16() + self.ix) & 0xFFFF
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0xCB:
                addr = self._read16(self._fetch16())
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0xCC:
                addr = self._read16((self._fetch16() + self.ix) & 0xFFFF)
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0xCD:
                addr = (self._read16(self._fetch16()) + self.ix) & 0xFFFF
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr

            elif op == 0xCF:                                                               # RTS
                lo = self._pop();  hi = self._pop()
                self.pc = (hi << 8) | lo

            # Conditional jumps (dir only)
            elif op == 0xD1: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_Z) else None)       # JZ
            elif op == 0xD6: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_Z) else None)   # JNZ
            elif op == 0xD9: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_N) else None)       # JN
            elif op == 0xDE: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_N) else None)   # JNN
            elif op == 0xE1: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_C) else None)       # JC
            elif op == 0xE6: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_C) else None)   # JNC
            elif op == 0xE9: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_V) else None)       # JO
            elif op == 0xEE: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_V) else None)   # JNO

            # BLDIV (big load interrupt vector)
            elif op == 0xF0: self._intr_vector = self._fetch16()
            elif op == 0xF1: self._intr_vector = self._read16(self._fetch16())

            else:
                return f"ILLEGAL ${op:02X}"

            return OP.get(op, f"${op:02X}")

        except Exception as e:
            return f"FAULT: {e}"

    def disassemble_at(self, addr, count=16):
        lines = []
        pc = addr & 0xFFFF
        for _ in range(count):
            if pc >= self.RAM_SIZE:
                break
            op   = self.ram[pc]
            mnem = OP.get(op, "???")
            size = instr_size(op)
            if size == 1:
                operand = ""
            elif size == 2:
                operand = f"${self.ram[(pc + 1) & 0xFFFF]:02X}"
            else:
                hi = self.ram[(pc + 1) & 0xFFFF]
                lo = self.ram[(pc + 2) & 0xFFFF]
                operand = f"${hi:02X}{lo:02X}"
            lines.append((pc, op, mnem, operand))
            pc = (pc + size) & 0xFFFF
        return lines
