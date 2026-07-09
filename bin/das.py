#!/usr/bin/env python3
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
DAs - David's Assembler (Python port)
Assembles DIY Calculator assembly source (.asm) files into RAM image (.ram) files.

Usage:
    python das.py <input.asm> <output.ram>

Original DAs by David Venhoek. Python port preserves all behaviour.

---
DIY Calculator CPU Summary (from "How Computers Do Math" by Maxfield & Brown):
  - 8-bit accumulator (ACC)
  - 16-bit index register (X)
  - 16-bit stack pointer (SP)
  - Status register flags: Negative (N), Zero (Z), Carry (C), Overflow (O)
  - Memory: 16-bit address space
  - All instructions are 1, 2, or 3 bytes

Addressing modes (as used in source) — terminology and opcodes match
Appendix A ("Addressing Modes and Instruction Set"), Tables A-2a/A-2b,
of The Official DIY Calculator Data Book:
  LDA  $nn           - imm    immediate            (1-byte value)
  LDA  [addr]         - dir    absolute (abs)        (2-byte address)
  LDA  [addr,X]       - idx    absolute indexed (abs-x)
  LDA  [[addr]]       - ind    indirect
  LDA  [[addr,X]]     - xind   pre-indexed indirect (x-ind): X is added to
                                the address BEFORE the pointer is fetched.
  LDA  [[addr],X]     - indx   indirect post-indexed (ind-x): the pointer
                                is fetched from addr FIRST, then X is added
                                to the resulting address.

Directives:
  .ORG  <addr>       - set origin (program counter)
  .EQU  <label> <val>- define constant
  .BYTE <val/string> - emit byte(s)

Numbers:
  $FF   - hexadecimal
  %1010 - binary
  123   - decimal
"""

import sys
import re
import datetime

# ---------------------------------------------------------------------------
# Opcode table
#
# Opcodes below match Appendix A, Tables A-2a/A-2b of The Official DIY
# Calculator Data Book (pages A-11/A-12). Each entry: opcode_base, total
# instruction size in bytes.
#
# Modes:
#   'imm'   = immediate:               LDA $FF        -> 1-byte operand
#             (BLDX/BLDSP/BLDIV use a 16-bit immediate -> 2-byte operand)
#   'dir'   = absolute (abs):          LDA [addr]      -> 2-byte address
#   'idx'   = absolute indexed (abs-x):LDA [addr,X]    -> 2-byte address
#   'ind'   = indirect:                LDA [[addr]]    -> 2-byte address
#   'xind'  = pre-indexed indirect (x-ind):
#             LDA [[addr,X]]  -> 2-byte address; X added to addr BEFORE
#             the pointer is fetched.
#   'indx'  = indirect post-indexed (ind-x):
#             LDA [[addr],X]  -> 2-byte address; pointer fetched from addr
#             FIRST, then X is added to the resulting address.
#   'none'  = no operand:              NOP
#
# DADD/DADDC/DSUBC opcodes below are PROVISIONAL placeholders — the
# official databook opcodes for these BCD instructions reassign bytes
# also used by ADDC/SUB in the new table, so they've been relocated to
# unused slots ($02-$04 / $05-$07 / $0A-$0C) pending the official BCD
# appendix. DSUB keeps its original opcodes ($1C-$1E); those don't
# collide with anything in the new table.
# ---------------------------------------------------------------------------

# fmt: off
OPCODES = {
    # Mnemonic : { mode: (opcode_byte, total_instruction_bytes) }
    'NOP'   : { 'none': (0x00, 1) },
    'HALT'  : { 'none': (0x01, 1) },
    'DADD'  : { 'imm':  (0x02, 2),   # provisional — pending official BCD appendix
                'dir':  (0x03, 3),
                'idx':  (0x04, 3) },
    'DADDC' : { 'imm':  (0x05, 2),   # provisional
                'dir':  (0x06, 3),
                'idx':  (0x07, 3) },
    'SETIM' : { 'none': (0x08, 1) },
    'CLRIM' : { 'none': (0x09, 1) },
    'DSUBC' : { 'imm':  (0x0A, 2),   # provisional
                'dir':  (0x0B, 3),
                'idx':  (0x0C, 3) },
    'ADD'   : { 'imm':  (0x10, 2),
                'dir':  (0x11, 3),
                'idx':  (0x12, 3) },
    'ADDC'  : { 'imm':  (0x18, 2),
                'dir':  (0x19, 3),
                'idx':  (0x1A, 3) },
    'DSUB'  : { 'imm':  (0x1C, 2),   # provisional — unchanged, no collision
                'dir':  (0x1D, 3),
                'idx':  (0x1E, 3) },
    'SUB'   : { 'imm':  (0x20, 2),
                'dir':  (0x21, 3),
                'idx':  (0x22, 3) },
    'SUBC'  : { 'imm':  (0x28, 2),
                'dir':  (0x29, 3),
                'idx':  (0x2A, 3) },
    'AND'   : { 'imm':  (0x30, 2),
                'dir':  (0x31, 3),
                'idx':  (0x32, 3) },
    'OR'    : { 'imm':  (0x38, 2),
                'dir':  (0x39, 3),
                'idx':  (0x3A, 3) },
    'XOR'   : { 'imm':  (0x40, 2),
                'dir':  (0x41, 3),
                'idx':  (0x42, 3) },
    'BLDSP' : { 'imm':  (0x50, 3),   # 16-bit immediate
                'dir':  (0x51, 3) },
    'BSTSP' : { 'dir':  (0x59, 3) },
    'CMPA'  : { 'imm':  (0x60, 2),
                'dir':  (0x61, 3),
                'idx':  (0x62, 3) },
    'SHL'   : { 'none': (0x70, 1) },
    'SHR'   : { 'none': (0x71, 1) },
    'ROLC'  : { 'none': (0x78, 1) },
    'RORC'  : { 'none': (0x79, 1) },
    'INCA'  : { 'none': (0x80, 1) },
    'DECA'  : { 'none': (0x81, 1) },
    'INCX'  : { 'none': (0x82, 1) },
    'DECX'  : { 'none': (0x83, 1) },
    'LDA'   : { 'imm':  (0x90, 2),
                'dir':  (0x91, 3),
                'idx':  (0x92, 3),
                'ind':  (0x93, 3),
                'xind': (0x94, 3),
                'indx': (0x95, 3) },
    'STA'   : { 'dir':  (0x99, 3),
                'idx':  (0x9A, 3),
                'ind':  (0x9B, 3),
                'xind': (0x9C, 3),
                'indx': (0x9D, 3) },
    'BLDX'  : { 'imm':  (0xA0, 3),   # BLDX is always 16-bit immediate
                'dir':  (0xA1, 3) },
    'BSTX'  : { 'dir':  (0xA9, 3) },
    'POPA'  : { 'none': (0xB0, 1) },
    'POPSR' : { 'none': (0xB1, 1) },
    'PSHA'  : { 'none': (0xB2, 1) },  # also named PUSHA
    'PUSHA' : { 'none': (0xB2, 1) },
    'PUSHSR': { 'none': (0xB3, 1) },
    'JMP'   : { 'dir':  (0xC1, 3),
                'idx':  (0xC2, 3),
                'ind':  (0xC3, 3),
                'xind': (0xC4, 3),
                'indx': (0xC5, 3) },
    'RTI'   : { 'none': (0xC7, 1) },
    'JSR'   : { 'dir':  (0xC9, 3),
                'idx':  (0xCA, 3),
                'ind':  (0xCB, 3),
                'xind': (0xCC, 3),
                'indx': (0xCD, 3) },
    'RTS'   : { 'none': (0xCF, 1) },
    'JZ'    : { 'dir':  (0xD1, 3) },
    'JNZ'   : { 'dir':  (0xD6, 3) },
    'JN'    : { 'dir':  (0xD9, 3) },
    'JNN'   : { 'dir':  (0xDE, 3) },
    'JC'    : { 'dir':  (0xE1, 3) },
    'JNC'   : { 'dir':  (0xE6, 3) },
    'JO'    : { 'dir':  (0xE9, 3) },
    'JNO'   : { 'dir':  (0xEE, 3) },
    'BLDIV' : { 'imm':  (0xF0, 3),   # 16-bit immediate
                'dir':  (0xF1, 3) },
}
# fmt: on


class AssemblerError(Exception):
    def __init__(self, line_num, message):
        self.line_num = line_num
        super().__init__(f"Error line {line_num}: {message}")


def parse_number(token, line_num):
    """Parse $hex, %binary, or decimal integer. Raises AssemblerError on bad input."""
    token = token.strip()
    if not token:
        raise AssemblerError(line_num, f"Expected a number, got empty string.")
    try:
        if token.startswith('$'):
            return int(token[1:], 16)
        elif token.startswith('%'):
            return int(token[1:], 2)
        else:
            return int(token, 10)
    except ValueError:
        raise AssemblerError(line_num, f"Invalid number: '{token}'")


def tokenize_line(raw_line):
    """
    Strip comments (# ...) and return (label, mnemonic, operand_string).
    Labels end with ':' OR are the first token on a line before a known directive/mnemonic.
    Comments start with #.
    """
    # Remove comment
    comment_idx = raw_line.find('#')
    if comment_idx != -1:
        raw_line = raw_line[:comment_idx]

    line = raw_line.strip()
    if not line:
        return None, None, None

    label = None
    mnemonic = None
    operand = None

    # Check for label: a token ending in ':' at the start
    # OR a leading token that is not a directive/mnemonic (legacy format)
    parts = line.split(None, 2)  # split into at most 3 parts

    if not parts:
        return None, None, None

    # Detect label: first token ends with ':'
    if parts[0].endswith(':'):
        label = parts[0][:-1]
        parts = parts[1:]  # consume the label token

    if not parts:
        return label, None, None

    mnemonic = parts[0].upper()
    # Reconstruct operand from remainder of line (everything after mnemonic)
    mnemonic_end = line.index(parts[0]) + len(parts[0])
    operand = line[mnemonic_end:].strip() if len(parts) > 1 else None

    return label, mnemonic, operand


def parse_operand(operand_str, labels, line_num, pass_num, on_label_used=None):
    """
    Parse an operand string and return (mode, value_16bit).
    Handles:
      $nn / %nn / decimal           -> 'imm', value
      [addr]                        -> 'dir', address
      [addr,X]                      -> 'idx', address
      [[addr]]                      -> 'ind', address
      [[addr,X]]                    -> 'xind', address   (pre-indexed indirect / x-ind)
      [[addr],X]                    -> 'indx', address   (indirect post-indexed / ind-x)
    'addr' can be a label, a number, or label+offset (label+N or label-N).

    `on_label_used`, if given, is called as `on_label_used(name, line_num)`
    each time a label reference is actually resolved (pass 2 only). This is
    an optional hook used by the listing generator to build the label
    cross-reference tables; it has no effect on assembly output.
    """
    if operand_str is None:
        return 'none', 0

    s = operand_str.strip()

    def resolve_addr(token):
        """Resolve a token that may be label, label+N, label-N, or a plain number."""
        token = token.strip()
        # Try label+offset or label-offset
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*([+\-])\s*(.+)$', token)
        if m:
            lbl, op_sign, offset_str = m.group(1), m.group(2), m.group(3)
            base = resolve_label(lbl)
            offset = parse_number(offset_str, line_num)
            return (base + offset) if op_sign == '+' else (base - offset)
        # Plain label?
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', token):
            return resolve_label(token)
        # Plain number
        return parse_number(token, line_num)

    def resolve_label(name):
        if pass_num == 1:
            return 0  # placeholder during pass 1
        if name not in labels:
            raise AssemblerError(line_num, f"Label doesn't exist: '{name}'")
        if on_label_used is not None:
            on_label_used(name, line_num)
        return labels[name]

    # Indirect post-indexed: [[addr],X]   (dereference addr, THEN add X)
    m = re.match(r'^\[\[(.+)\]\s*,\s*X\s*\]$', s, re.IGNORECASE)
    if m:
        return 'indx', resolve_addr(m.group(1)) & 0xFFFF

    # Pre-indexed indirect: [[addr,X]]   (add X to addr, THEN dereference)
    m = re.match(r'^\[\[(.+),\s*X\s*\]\]$', s, re.IGNORECASE)
    if m:
        return 'xind', resolve_addr(m.group(1)) & 0xFFFF

    # Indirect: [[addr]]
    m = re.match(r'^\[\[(.+)\]\]$', s)
    if m:
        return 'ind', resolve_addr(m.group(1)) & 0xFFFF

    # Indexed: [addr,X]
    m = re.match(r'^\[(.+),\s*X\s*\]$', s, re.IGNORECASE)
    if m:
        return 'idx', resolve_addr(m.group(1)) & 0xFFFF

    # Direct: [addr]
    m = re.match(r'^\[(.+)\]$', s)
    if m:
        return 'dir', resolve_addr(m.group(1)) & 0xFFFF

    # Immediate (plain number or label treated as immediate)
    return 'imm', resolve_addr(s) & 0xFFFF


def assemble(source_lines):
    """
    Two-pass assembler.
    Returns a dict: { address: byte_value } for all emitted bytes.
    """
    labels = {}    # label -> address
    equates = {}   # .EQU label -> value (merged into labels)

    def do_pass(pass_num):
        memory = {}   # address -> byte
        pc = 0        # program counter
        origin_set = False

        for raw_line_num, raw_line in enumerate(source_lines):
            line_num = raw_line_num  # DAs numbers from 0

            # Decode bytes if needed
            if isinstance(raw_line, bytes):
                raw_line = raw_line.decode('latin-1')

            label, mnemonic, operand = tokenize_line(raw_line)

            # Register label in pass 1
            # Skip PC-based registration for .EQU lines — the .EQU handler
            # will register the label with the correct constant value instead.
            if label is not None and (mnemonic or '').upper() != '.EQU':
                if pass_num == 1:
                    if label in labels:
                        raise AssemblerError(line_num, f"Duplicate label: '{label}'")
                    labels[label] = pc

            if mnemonic is None:
                continue

            # ---- Directives ----

            if mnemonic == '.ORG':
                if operand is None:
                    raise AssemblerError(line_num, ".ORG requires an address operand.")
                pc = parse_number(operand, line_num)
                # Update label to real address if label was on same line
                if label is not None and pass_num == 1:
                    labels[label] = pc
                if not origin_set:
                    origin_set = True
                continue

            if mnemonic == '.EQU':
                # Accepts two styles:
                #   Colon-label:   MAINDISP: .EQU $F031
                #   Traditional:   .EQU MAINDISP $F031
                if label is not None:
                    # Colon-label style — label already parsed, operand is the value
                    if operand is None:
                        raise AssemblerError(line_num, ".EQU requires a value operand.")
                    eq_label = label
                    eq_val_str = operand.strip()
                else:
                    # Traditional style — operand contains "LABELNAME value"
                    if operand is None:
                        raise AssemblerError(line_num, ".EQU requires label and value.")
                    parts = operand.split(None, 1)
                    if len(parts) < 2:
                        raise AssemblerError(line_num, ".EQU requires label and value.")
                    eq_label, eq_val_str = parts[0], parts[1].strip()
                eq_val = parse_number(eq_val_str, line_num)
                if pass_num == 1:
                    if eq_label in labels:
                        raise AssemblerError(line_num, f"Duplicate label: '{eq_label}'")
                    labels[eq_label] = eq_val
                continue

            if not origin_set:
                raise AssemblerError(line_num, "Commentary or .ORG expected.")

            if mnemonic == '.END':
                break

            if mnemonic in ('.2BYTE', '.4BYTE'):
                count = 2 if mnemonic == '.2BYTE' else 4
                if operand and operand.strip():
                    # Use parse_operand to handle labels
                    _, val = parse_operand(operand.strip(), labels, line_num, pass_num)
                    for shift in range((count - 1) * 8, -1, -8):
                        if pass_num == 2:
                            memory[pc] = (val >> shift) & 0xFF
                        pc += 1
                else:
                    for _ in range(count):
                        if pass_num == 2:
                            memory[pc] = 0x00
                        pc += 1
                continue

            if mnemonic == '.BYTE':
                if operand is None or operand.strip() == '':
                    # Reserve 1 byte (uninitialized storage)
                    if pass_num == 2:
                        memory[pc] = 0x00
                    pc += 1
                    continue
                # .BYTE *N  -> reserve N bytes
                if operand.strip().startswith('*'):
                    count = parse_number(operand.strip()[1:], line_num)
                    for _ in range(count):
                        if pass_num == 2:
                            memory[pc] = 0x00
                        pc += 1
                    continue
                # String: "Hello World"
                if operand.startswith('"'):
                    # Find closing quote
                    end = operand.rfind('"')
                    if end <= 0:
                        raise AssemblerError(line_num, "Unterminated string in .BYTE.")
                    text = operand[1:end]
                    for ch in text:
                        if pass_num == 2:
                            memory[pc] = ord(ch) & 0xFF
                        pc += 1
                else:
                    # Possibly comma-separated byte values
                    for val_str in operand.split(','):
                        val_str = val_str.strip()
                        if val_str:
                            val = parse_number(val_str, line_num)
                            if pass_num == 2:
                                memory[pc] = val & 0xFF
                            pc += 1
                continue

            # ---- Instructions ----

            if mnemonic not in OPCODES:
                raise AssemblerError(line_num, f"Unknown mnemonic: '{mnemonic}'")

            mode_table = OPCODES[mnemonic]

            # Determine addressing mode and value
            mode, value = parse_operand(operand, labels, line_num, pass_num)

            # Special case: BLDX and BLDSP with immediate are always 16-bit (3 bytes)
            # They use 'imm' mode but encode as 16-bit. Already handled via opcode table.

            # For instructions that only support 'none', ensure no operand confusion
            if mode == 'none' and 'none' not in mode_table:
                raise AssemblerError(line_num, f"Mode Not Supported for {mnemonic}.")

            if mode not in mode_table:
                # Try fallback: some mnemonics treat plain labels/numbers as 'dir'
                if mode == 'imm' and 'dir' in mode_table:
                    mode = 'dir'
                elif mode == 'imm' and 'none' in mode_table:
                    mode = 'none'
                else:
                    raise AssemblerError(line_num,
                        f"Mode Not Supported for {mnemonic} (mode={mode}).")

            opcode, size = mode_table[mode]

            if pass_num == 2:
                memory[pc] = opcode
                if size == 2:
                    # 1-byte operand (immediate)
                    memory[pc + 1] = value & 0xFF
                elif size == 3:
                    # 2-byte operand (address or 16-bit immediate) — big-endian (MSB first)
                    memory[pc + 1] = (value >> 8) & 0xFF
                    memory[pc + 2] = value & 0xFF

            pc += size

        return memory

    # Pass 1: collect labels
    do_pass(1)
    # Pass 2: emit code
    memory = do_pass(2)
    return memory


# ---------------------------------------------------------------------------
# Listing (.lst) generation
#
# Reproduces the "DIY Calculator Assembler V2.0" listing format used by the
# original tool (see Data/2funcal.lst for a real reference listing, paired
# with its source at Data/2funcal.asm). This is a second, independent
# two-pass walk over the same source — it does not reuse assemble()'s
# do_pass() closures, because it needs to retain far more per-line detail
# (addresses, emitted bytes, and label cross-reference usage) than the flat
# {address: byte} map assemble() returns. Instruction encoding is still
# driven by the same OPCODES table, so a listing and its .ram will never
# disagree about what bytes an instruction assembles to.
# ---------------------------------------------------------------------------

def _fmt_data_bytes(byte_list):
    return " ".join(f"{b:02X}" for b in byte_list)


def _split_chunks(byte_list, size=3):
    if not byte_list:
        return [[]]
    return [byte_list[i:i + size] for i in range(0, len(byte_list), size)]


def _format_row(line_num, addr, data_chunk, label, opcode, operand):
    addr_field = f"{addr:04X}" if addr is not None else "    "
    data_field = _fmt_data_bytes(data_chunk).ljust(8)
    label_field = (f"{label}:" if label else "").ljust(9)
    opcode_field = (opcode or "").ljust(6)
    row = f"{line_num:05d} {addr_field} {data_field}  {label_field} {opcode_field} "
    if operand:
        row += f"{operand} "
    return row


def _format_line_rows(line_num, start_addr, data, label, opcode, operand):
    """Build the main row plus any continuation rows (>3 data bytes wrap)."""
    chunks = _split_chunks(data, 3)
    out = [_format_row(line_num, start_addr, chunks[0], label, opcode, operand)]
    if start_addr is not None:
        addr = start_addr + len(chunks[0])
        for chunk in chunks[1:]:
            out.append(f"      {addr:04X} {_fmt_data_bytes(chunk)} ")
            addr += len(chunk)
    return out


def _render_header(source_path, inst_bytes, data_bytes, generated_by, when=None):
    stamp = (when or datetime.datetime.now()).strftime("%b %d %H:%M:%S %Y")
    src = source_path if source_path else "(unsaved)"
    return [
        "# FILE TYPE: DIY Calculator List (*.lst) file",
        f"# GENERATED: {generated_by}",
        f"# DATE-TIME: {stamp}",
        f"# SOURCEWAS: {src}",
        "",
        f"INSTBYTES: {inst_bytes}",
        f"DATABYTES: {data_bytes}",
        "",
        "LINE  ADDR   DATA      LABEL   OPCODE OPERAND",
        "----- ---- --------  --------- ------ -------",
    ]


def _render_xref_table(title, entries, value_fmt):
    out = [
        "", "", "",
        title,
        "",
        "  NAME     VALUE   LINE NUMBERS WHERE USED (* INDICATES DECLARATION)",
        "-------- --------- ---------------------------------------------------",
    ]
    for name, value, uses in sorted(entries, key=lambda e: e[0]):
        merged = {}
        for ln, is_decl in uses:
            merged[ln] = merged.get(ln, False) or is_decl
        entry_strs = [f"{ln:05d}{'*' if d else ' '} " for ln, d in sorted(merged.items())]
        value_str = value_fmt(value)
        if not entry_strs:
            out.append(f"{name:<8} {value_str}  ")
            continue
        for i in range(0, len(entry_strs), 7):
            chunk = "".join(entry_strs[i:i + 7])
            if i == 0:
                out.append(f"{name:<8} {value_str}  {chunk}")
            else:
                out.append(f"{'':19}{chunk}")
    return out


def generate_listing(source_lines, source_path=None,
                      generated_by="DIY Calculator Assembler V2.0",
                      when=None):
    """
    Assemble `source_lines` and return a formatted .lst listing (str),
    matching the DIY Calculator Assembler V2.0 format. Raises
    AssemblerError under the same conditions as `assemble()`.
    """
    labels = {}          # name -> value (address or .EQU constant)
    label_kind = {}       # name -> 'equ' | 'addr'
    label_decl_line = {}  # name -> 1-based source line number
    label_uses = {}       # name -> [(line_num, is_decl), ...]

    def note_use(name, line_num, is_decl=False):
        label_uses.setdefault(name, []).append((line_num, is_decl))

    # ---- Pass 1: collect labels (mirrors assemble()'s pass 1) ----
    pc = 0
    origin_set = False
    for raw_line_num, raw_line in enumerate(source_lines):
        line_num = raw_line_num + 1
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode('latin-1')
        label, mnemonic, operand = tokenize_line(raw_line)

        if label is not None and (mnemonic or '').upper() != '.EQU':
            if label in labels:
                raise AssemblerError(raw_line_num, f"Duplicate label: '{label}'")
            labels[label] = pc
            label_kind[label] = 'addr'
            label_decl_line[label] = line_num

        if mnemonic is None:
            continue

        if mnemonic == '.ORG':
            if operand is None:
                raise AssemblerError(raw_line_num, ".ORG requires an address operand.")
            pc = parse_number(operand, raw_line_num)
            if label is not None:
                labels[label] = pc
            origin_set = True
            continue

        if mnemonic == '.EQU':
            if label is not None:
                if operand is None:
                    raise AssemblerError(raw_line_num, ".EQU requires a value operand.")
                eq_label, eq_val_str = label, operand.strip()
            else:
                if operand is None:
                    raise AssemblerError(raw_line_num, ".EQU requires label and value.")
                parts = operand.split(None, 1)
                if len(parts) < 2:
                    raise AssemblerError(raw_line_num, ".EQU requires label and value.")
                eq_label, eq_val_str = parts[0], parts[1].strip()
            eq_val = parse_number(eq_val_str, raw_line_num)
            if eq_label in labels:
                raise AssemblerError(raw_line_num, f"Duplicate label: '{eq_label}'")
            labels[eq_label] = eq_val
            label_kind[eq_label] = 'equ'
            label_decl_line[eq_label] = line_num
            continue

        if not origin_set:
            raise AssemblerError(raw_line_num, "Commentary or .ORG expected.")

        if mnemonic == '.END':
            break

        if mnemonic in ('.2BYTE', '.4BYTE'):
            pc += 2 if mnemonic == '.2BYTE' else 4
            continue

        if mnemonic == '.BYTE':
            if operand is None or operand.strip() == '':
                pc += 1
            elif operand.strip().startswith('*'):
                pc += parse_number(operand.strip()[1:], raw_line_num)
            elif operand.startswith('"'):
                end = operand.rfind('"')
                if end <= 0:
                    raise AssemblerError(raw_line_num, "Unterminated string in .BYTE.")
                pc += len(operand[1:end])
            else:
                pc += len([v for v in operand.split(',') if v.strip()])
            continue

        if mnemonic not in OPCODES:
            raise AssemblerError(raw_line_num, f"Unknown mnemonic: '{mnemonic}'")

        mode_table = OPCODES[mnemonic]
        mode, _ = parse_operand(operand, labels, raw_line_num, 1)
        if mode == 'none' and 'none' not in mode_table:
            raise AssemblerError(raw_line_num, f"Mode Not Supported for {mnemonic}.")
        if mode not in mode_table:
            if mode == 'imm' and 'dir' in mode_table:
                mode = 'dir'
            elif mode == 'imm' and 'none' in mode_table:
                mode = 'none'
            else:
                raise AssemblerError(raw_line_num,
                    f"Mode Not Supported for {mnemonic} (mode={mode}).")
        _, size = mode_table[mode]
        pc += size

    # ---- Pass 2: build listing rows + label usage ----
    rows = []
    inst_bytes = 0
    data_bytes = 0
    pc = 0
    origin_set = False

    for raw_line_num, raw_line in enumerate(source_lines):
        line_num = raw_line_num + 1
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode('latin-1')
        label, mnemonic, operand = tokenize_line(raw_line)

        if label is not None and label_decl_line.get(label) == line_num:
            note_use(label, line_num, is_decl=True)

        if mnemonic is None:
            if label is not None:
                rows.extend(_format_line_rows(line_num, None, [], label, None, None))
            else:
                text = raw_line if raw_line.strip() != '' else ''
                rows.append(f"{line_num:05d}" + (f" {text}" if text else ""))
            continue

        if mnemonic == '.ORG':
            pc = parse_number(operand, raw_line_num)
            origin_set = True
            rows.extend(_format_line_rows(line_num, None, [], label, mnemonic, operand))
            continue

        if mnemonic == '.EQU':
            if label is not None:
                eq_label, eq_val_str = label, operand.strip()
            else:
                parts = operand.split(None, 1)
                eq_label, eq_val_str = parts[0], parts[1].strip()
            rows.extend(_format_line_rows(line_num, None, [], eq_label, mnemonic, eq_val_str))
            continue

        if not origin_set:
            raise AssemblerError(raw_line_num, "Commentary or .ORG expected.")

        if mnemonic == '.END':
            rows.extend(_format_line_rows(line_num, None, [], label, mnemonic, None))
            break

        if mnemonic in ('.2BYTE', '.4BYTE'):
            count = 2 if mnemonic == '.2BYTE' else 4
            start = pc
            if operand and operand.strip():
                _, val = parse_operand(operand.strip(), labels, line_num, 2,
                                        on_label_used=note_use)
                data = [(val >> shift) & 0xFF for shift in range((count - 1) * 8, -1, -8)]
            else:
                data = [0] * count
            data_bytes += len(data)
            pc += count
            rows.extend(_format_line_rows(line_num, start, data, label, mnemonic, operand))
            continue

        if mnemonic == '.BYTE':
            start = pc
            if operand is None or operand.strip() == '':
                data = [0]
            elif operand.strip().startswith('*'):
                data = [0] * parse_number(operand.strip()[1:], raw_line_num)
            elif operand.startswith('"'):
                end = operand.rfind('"')
                text = operand[1:end]
                data = [ord(ch) & 0xFF for ch in text]
            else:
                data = [parse_number(v.strip(), raw_line_num) & 0xFF
                        for v in operand.split(',') if v.strip()]
            data_bytes += len(data)
            pc += len(data)
            rows.extend(_format_line_rows(line_num, start, data, label, mnemonic, operand))
            continue

        # ---- Instructions ----
        mode_table = OPCODES[mnemonic]
        mode, value = parse_operand(operand, labels, line_num, 2, on_label_used=note_use)
        if mode == 'none' and 'none' not in mode_table:
            raise AssemblerError(raw_line_num, f"Mode Not Supported for {mnemonic}.")
        if mode not in mode_table:
            if mode == 'imm' and 'dir' in mode_table:
                mode = 'dir'
            elif mode == 'imm' and 'none' in mode_table:
                mode = 'none'
            else:
                raise AssemblerError(raw_line_num,
                    f"Mode Not Supported for {mnemonic} (mode={mode}).")
        opcode, size = mode_table[mode]

        start = pc
        if size == 1:
            data = [opcode]
        elif size == 2:
            data = [opcode, value & 0xFF]
        else:
            data = [opcode, (value >> 8) & 0xFF, value & 0xFF]
        inst_bytes += size
        pc += size
        rows.extend(_format_line_rows(line_num, start, data, label, mnemonic, operand))

    out = []
    out.extend(_render_header(source_path, inst_bytes, data_bytes, generated_by, when))
    out.extend(rows)
    out.extend(_render_xref_table(
        "CONSTANT LABELS CROSS-REFERENCE",
        [(name, labels[name], label_uses.get(name, []))
         for name in label_kind if label_kind[name] == 'equ'],
        value_fmt=lambda v: f"{v & 0xFFFFFFFF:08X}"))
    out.extend(_render_xref_table(
        "ADDRESS LABELS CROSS-REFERENCE",
        [(name, labels[name], label_uses.get(name, []))
         for name in label_kind if label_kind[name] == 'addr'],
        value_fmt=lambda v: f"....{v & 0xFFFF:04X}"))

    return "\n".join(out) + "\n"


def write_ram(memory, output_path):
    """
    Write the assembled memory to a .ram file.
    The RAM file format used by the DIY Calculator emulator is:
      - First 2 bytes: start address (big-endian)
      - Next 2 bytes:  end address   (big-endian)
      - Followed by the raw bytes from start..end inclusive
    If memory is empty, write an empty file.
    """
    if not memory:
        with open(output_path, 'wb') as f:
            pass
        return

    start_addr = min(memory.keys())
    end_addr   = max(memory.keys())

    with open(output_path, 'wb') as f:
        # Write header: start address and end address (big-endian 16-bit each)
        f.write(bytes([(start_addr >> 8) & 0xFF, start_addr & 0xFF]))
        f.write(bytes([(end_addr   >> 8) & 0xFF, end_addr   & 0xFF]))
        # Write memory contents (fill gaps with 0x00)
        for addr in range(start_addr, end_addr + 1):
            f.write(bytes([memory.get(addr, 0x00)]))


def main():
    if len(sys.argv) != 3:
        print("Usage: python das.py <input.asm> <output.ram>")
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2]

    try:
        with open(input_path, 'rb') as f:
            raw = f.read()
    except OSError:
        print("Error: Cannot Open Input/Output File.")
        sys.exit(1)

    # Decode: try UTF-8 first, fall back to latin-1
    try:
        source = raw.decode('utf-8')
    except UnicodeDecodeError:
        source = raw.decode('latin-1')

    source_lines = source.splitlines()

    try:
        memory = assemble(source_lines)
    except AssemblerError as e:
        print(e)
        sys.exit(1)

    try:
        write_ram(memory, output_path)
    except OSError:
        print("Error: Cannot Open Input/Output File.")
        sys.exit(1)

    print(f"Assembly successful. Output written to: {output_path}")
    if memory:
        start = min(memory.keys())
        end   = max(memory.keys())
        print(f"  Address range: ${start:04X} - ${end:04X}  ({end - start + 1} bytes)")


if __name__ == '__main__':
    main()
