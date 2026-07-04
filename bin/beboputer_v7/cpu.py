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

Addressing modes
----------------
  imm          opcode + 1-byte operand
  dir          opcode + 16-bit big-endian address
  idx          opcode + 16-bit big-endian address  (effective = addr + IX)
  ind          opcode + 16-bit addr of pointer     (pointer is 16-bit BE in RAM)
  iix          opcode + 16-bit addr of pointer     (pointer addr = addr + IX)

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
        self.ram       = bytearray(self.RAM_SIZE)
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

    def _load_default_program(self):
        prog = [
            0x01, 0x05,
            0x0A, 0x03,
            0x06, 0x40, 0x50,
            0x01, 0x0A,
            0x10, 0x05,
            0x32,
            0x3C,
        ]
        for i, b in enumerate(prog):
            self.ram[self.RESET_VECTOR + i] = b

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

            elif op == 0x01: self.acc = self._fetch();               self._set_nz(self.acc)
            elif op == 0x02: self.acc = self._read(self._fetch16()); self._set_nz(self.acc)
            elif op == 0x03: self.acc = self._read((self._fetch16() + self.ix) & 0xFFFF);  self._set_nz(self.acc)
            elif op == 0x04: self.acc = self._read(self._read16(self._fetch16()));          self._set_nz(self.acc)
            elif op == 0x05: self.acc = self._read(self._read16((self._fetch16() + self.ix) & 0xFFFF)); self._set_nz(self.acc)

            elif op == 0x06: self._write(self._fetch16(), self.acc)
            elif op == 0x07: self._write((self._fetch16() + self.ix) & 0xFFFF, self.acc)
            elif op == 0x08: self._write(self._read16(self._fetch16()), self.acc)
            elif op == 0x09: self._write(self._read16((self._fetch16() + self.ix) & 0xFFFF), self.acc)

            elif op == 0x0A:
                n = self._fetch();  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x0B:
                n = self._read(self._fetch16());  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x0C:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  r = self.acc + n;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF

            elif op == 0x0D:
                n = self._fetch();  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x0E:
                n = self._read(self._fetch16());  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x0F:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  c = 1 if (self.flags & FLAG_C) else 0
                r = self.acc + n + c;  self._set_add_flags(self.acc, n, r);  self.acc = r & 0xFF

            elif op == 0x10:
                n = self._fetch();  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x11:
                n = self._read(self._fetch16());  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x12:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  r = self.acc - n;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF

            elif op == 0x13:
                n = self._fetch();  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x14:
                n = self._read(self._fetch16());  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF
            elif op == 0x15:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  bw = 1 if (self.flags & FLAG_C) else 0
                r = self.acc - n - bw;  self._set_sub_flags(self.acc, n, r);  self.acc = r & 0xFF

            elif op == 0x16:
                n = self._fetch();  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x17:
                n = self._read(self._fetch16());  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x18:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  res, c = self._bcd_add(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, c)

            elif op == 0x19:
                n = self._fetch();  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x1A:
                n = self._read(self._fetch16());  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)
            elif op == 0x1B:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  c_in = 1 if (self.flags & FLAG_C) else 0
                res, c = self._bcd_add(self.acc, n, c_in);  self.acc = res;  self._set_bcd_flags(res, c)

            elif op == 0x1C:
                n = self._fetch();  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x1D:
                n = self._read(self._fetch16());  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x1E:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  res, bw = self._bcd_sub(self.acc, n);  self.acc = res;  self._set_bcd_flags(res, bw)

            elif op == 0x1F:
                n = self._fetch();  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x20:
                n = self._read(self._fetch16());  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)
            elif op == 0x21:
                n = self._read((self._fetch16() + self.ix) & 0xFFFF);  bw_in = 1 if (self.flags & FLAG_C) else 0
                res, bw = self._bcd_sub(self.acc, n, bw_in);  self.acc = res;  self._set_bcd_flags(res, bw)

            elif op == 0x22: n = self._fetch();                                           self._set_sub_flags(self.acc, n, self.acc - n)
            elif op == 0x23: n = self._read(self._fetch16());                             self._set_sub_flags(self.acc, n, self.acc - n)
            elif op == 0x24: n = self._read((self._fetch16() + self.ix) & 0xFFFF);        self._set_sub_flags(self.acc, n, self.acc - n)

            elif op == 0x25: self.acc &= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x26: self.acc &= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x27: self.acc &= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            elif op == 0x28: self.acc |= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x29: self.acc |= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x2A: self.acc |= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            elif op == 0x2B: self.acc ^= self._fetch();                                   self._set_nz(self.acc)
            elif op == 0x2C: self.acc ^= self._read(self._fetch16());                     self._set_nz(self.acc)
            elif op == 0x2D: self.acc ^= self._read((self._fetch16() + self.ix) & 0xFFFF); self._set_nz(self.acc)

            elif op == 0x2E:
                c = (self.acc >> 7) & 1;  self.acc = (self.acc << 1) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x2F:
                c = self.acc & 1;  self.acc = (self.acc >> 1) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x30:
                old_c = 1 if (self.flags & FLAG_C) else 0;  new_c = (self.acc >> 7) & 1
                self.acc = ((self.acc << 1) | old_c) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | new_c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)
            elif op == 0x31:
                old_c = 1 if (self.flags & FLAG_C) else 0;  new_c = self.acc & 1
                self.acc = ((self.acc >> 1) | (old_c << 7)) & 0xFF
                self.flags = (self.flags & ~FLAG_C) | new_c;  self.flags_touched |= FLAG_C;  self._set_nz(self.acc)

            elif op == 0x32: self.acc = (self.acc + 1) & 0xFF;  self._set_nz(self.acc)
            elif op == 0x33: self.acc = (self.acc - 1) & 0xFF;  self._set_nz(self.acc)
            elif op == 0x34: self.ix = (self.ix + 1) & 0xFFFF; self._set_nz(self.ix)
            elif op == 0x35: self.ix = (self.ix - 1) & 0xFFFF; self._set_nz(self.ix)

            elif op == 0x36: self.flags &= ~FLAG_I;  self.flags_touched |= FLAG_I
            elif op == 0x37: self.flags |=  FLAG_I;  self.flags_touched |= FLAG_I

            elif op == 0x38: self._push(self.acc)
            elif op == 0x39: self.acc = self._pop();  self._set_nz(self.acc)
            elif op == 0x3A: self._push(self.flags)
            elif op == 0x3B: self.flags = self._pop();  self.flags_touched = 0xFF

            elif op == 0x3C: self.halted = True
            elif op == 0x3D:
                lo = self._pop();  hi = self._pop()
                self.pc    = (hi << 8) | lo
                self.flags = self._pop();  self.flags_touched = 0xFF
            elif op == 0x3E:
                lo = self._pop();  hi = self._pop()
                self.pc = (hi << 8) | lo

            elif op == 0x3F: self.ix = self._fetch16()
            elif op == 0x40: self.ix = self._read16(self._fetch16())
            elif op == 0x41: self._write16(self._fetch16(), self.ix)
            elif op == 0x42: self.sp = self._fetch16()
            elif op == 0x43: self._write16(self._fetch16(), self.sp)
            elif op == 0x44: self._intr_vector = self._read16(self._fetch16())

            elif op == 0x45: self.pc = self._fetch16()
            elif op == 0x46: self.pc = self._read16(self._fetch16())
            elif op == 0x47: self.pc = self._read16((self._fetch16() + self.ix) & 0xFFFF)
            elif op == 0x48: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_C) else None)
            elif op == 0x49: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_C) else None)
            elif op == 0x4A: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_N) else None)
            elif op == 0x4B: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_N) else None)
            elif op == 0x4C: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_Z) else None)
            elif op == 0x4D: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_Z) else None)
            elif op == 0x4E: addr = self._fetch16(); (setattr(self, 'pc', addr) if (self.flags & FLAG_V) else None)
            elif op == 0x4F: addr = self._fetch16(); (setattr(self, 'pc', addr) if not (self.flags & FLAG_V) else None)

            elif op == 0x50:
                addr = self._fetch16()
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0x51:
                addr = self._read16(self._fetch16())
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr
            elif op == 0x52:
                addr = self._read16((self._fetch16() + self.ix) & 0xFFFF)
                self._push((self.pc >> 8) & 0xFF);  self._push(self.pc & 0xFF);  self.pc = addr

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
