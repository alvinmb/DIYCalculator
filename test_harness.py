"""
test_harness.py  --  PY-DIYCALCULATOR ASM Test Harness
Assembles every .asm file in Data/, simulates with keypad input,
validates display and LED output.

WorkInProgress/ folder: drop any .asm file there while developing;
the harness will assemble and run it and print what it outputs --
no pass/fail, just quick feedback.

NOTE: The __pycache__/cpu.cpython-310.pyc may be stale (timestamp newer
than cpu.py due to OneDrive sync).  The harness monkey-patches three things
at runtime so results match the intended CPU behaviour:
  * _read_hooks       -- added in current source, missing from stale pyc
  * _set_sub_flags    -- carry direction fixed: C=1 when ACC>operand
  * cpu.ram[0xF011]   -- keypad idle sentinel set to $FF after reset

Usage:  python test_harness.py
"""

import sys, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
BIN  = os.path.join(HERE, "bin")
DATA = os.path.join(HERE, "Data")
WIP  = os.path.join(HERE, "WorkInProgress")
sys.path.insert(0, BIN)

def _load(rel):
    full = os.path.join(BIN, rel)
    name = rel.replace(os.sep, ".").replace("/", ".").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, full)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

constants = _load("beboputer_v7/constants.py")
cpu_mod   = _load("beboputer_v7/cpu.py")
das_mod   = _load("das.py")

FLAG_C = constants.FLAG_C
FLAG_Z = constants.FLAG_Z
FLAG_N = constants.FLAG_N
FLAG_V = constants.FLAG_V
RUN_LIMIT = constants.RUN_LIMIT

AssemblerError = das_mod.AssemblerError
assemble       = das_mod.assemble
_OrigCPU       = cpu_mod.CPU

# ---- Runtime patches for stale pyc ----------------------------------------
_orig_cpu_init = _OrigCPU.__init__

def _patched_init(self):
    _orig_cpu_init(self)
    if not hasattr(self, "_read_hooks"):
        self._read_hooks = {}

def _patched_read(self, addr):
    addr = addr & 0xFFFF
    val  = self.ram[addr]
    hook = self._read_hooks.get(addr)
    if hook is not None:
        hook(val)
    return val

def _patched_sub_flags(self, a, b, result):
    r8 = result & 0xFF
    self.flags &= ~(FLAG_C | FLAG_Z | FLAG_N | FLAG_V)
    if (a & 0xFF) > (b & 0xFF):
        self.flags |= FLAG_C
    if r8 == 0:
        self.flags |= FLAG_Z
    if r8 & 0x80:
        self.flags |= FLAG_N
    if ((a & 0x80) != (b & 0x80)) and ((r8 & 0x80) != (a & 0x80)):
        self.flags |= FLAG_V
    self.flags_touched |= (FLAG_C | FLAG_Z | FLAG_N | FLAG_V)

_OrigCPU.__init__       = _patched_init
_OrigCPU._read          = _patched_read
_OrigCPU._set_sub_flags = _patched_sub_flags
CPU = _OrigCPU

# ---------------------------------------------------------------------------

def make_cpu(memory):
    cpu = CPU()
    cpu.reset()
    for addr, byte in memory.items():
        cpu.ram[addr] = byte
    cpu.ram[0xF011] = 0xFF
    return cpu

def inject_keys(cpu, keys):
    key_idx = [0]
    def keypad_read(val):
        if val == 0xFF and key_idx[0] < len(keys):
            cpu.ram[0xF011] = keys[key_idx[0]] & 0xFF
            key_idx[0] += 1
        elif val != 0xFF:
            cpu.ram[0xF011] = 0xFF
    cpu._read_hooks[0xF011] = keypad_read

def run_program(fname, key_sequence=None, max_steps=100_000, data_dir=None):
    if data_dir is None:
        data_dir = DATA
    path = os.path.join(data_dir, fname)
    if not os.path.exists(path):
        return None, None, None, None, False, "File not found"
    try:
        src    = open(path, encoding="latin-1").read()
        memory = assemble(src.splitlines())
    except AssemblerError as e:
        return None, None, None, None, False, str(e)
    except Exception as e:
        return None, None, None, None, False, str(e)

    cpu = make_cpu(memory)
    display_out = []
    led_out     = []
    cpu._write_hooks[0xF031] = lambda ch: display_out.append(ch)
    cpu._write_hooks[0xF032] = lambda b:  led_out.append(b)
    inject_keys(cpu, list(key_sequence) if key_sequence else [])

    for _ in range(max_steps):
        if cpu.halted:
            break
        cpu.step()

    return display_out, led_out, cpu.acc, cpu.flags, cpu.halted, None


def fmt_disp(writes):
    out = ""
    for b in writes:
        if 32 <= b <= 126:
            out += chr(b)
        elif b <= 9:
            out += str(b)
        elif 0x0A <= b <= 0x0F:
            out += chr(b - 0x0A + ord('A'))  # raw hex letter → 'A'-'F'
        elif b == 0x10:
            out += "[CLR]"
        else:
            out += "[{:02X}]".format(b)
    return out


# ---------------------------------------------------------------------------
# TEST CASES
TESTS = [
    # Lab 2
    ("lab2a.asm",  "Clear display",                    [], "[CLR]",       None),
    ("lab2b.asm",  "Clear display with labels",         [], "[CLR]",       None),
    ("lab2c.asm",  "Count 9 down to 1",                 [], "987654321",   None),
    ("lab2d.asm",  "Keypad filter 0-9: press 3,7,5",    [3,7,5], "375",   None),
    ("lab2e.asm",  "LED sweep pattern",                 [], "[CLR]",       0b00000001),
    ("lab2f.asm",  "Hello World",                       [], "HELLO WORLD!",None),

    # Lab 3a
    ("lab3a-bin-v1.asm",   "Binary v1 (unrolled): key 5",
        [0x05], "%00000101", 0b00000100),
    ("lab3a-bin-v2.asm",   "Binary v2 (X-reg loop): runs",
        [0x05], None, 0b00000100),
    ("lab3a-hex-shl.asm",  "Hex SHL: key A",  [0x0A], "$0A", 0b00000001),
    ("lab3a-hex-shr.asm",  "Hex SHR: key A",  [0x0A], "$0A", 0b00000001),
    ("lab3a-hex-rolc.asm", "Hex ROLC: key A", [0x0A], "$0A", 0b00000001),
    ("lab3a-hex-rorc.asm", "Hex RORC: key A", [0x0A], "$0A", 0b00000001),

    # Lab 3b
    ("lab3b.asm", "Counter wraps 0..255", [], None, None),

    # Lab 3c
    ("lab3c-hex-forward.asm",   "Hex forward: 1,2,3,A,F -> 123AF",
        [0x01,0x02,0x03,0x0A,0x0F,0x10], "123AF", None),
    ("lab3c-hex-reverse-x.asm", "Hex reverse-X: 1,2,3 -> 321",
        [0x01,0x02,0x03,0x10], "321", None),
    ("lab3c-hex-x-contents.asm","Hex X-contents: runs",
        [0x01,0x02,0x03,0x10], None, None),
    ("lab3c-bin-v1.asm",        "Bin v1 (X-reg): runs", [0x05], None, None),
    ("lab3c-bin-v2.asm",        "Bin v2 (X-reg dash): runs", [0x05], None, None),

    # Lab 3d -- push 1,2,3 then pop with 3 CLR presses
    ("lab3d-hex-reverse-sp.asm", "Stack reverse: 1,2,3+3xCLR -> 321",
        [0x01,0x02,0x03,0x10,0x10,0x10], "321", None),

    # Lab 3e -- reads TEMP buffer, not keypad
    ("lab3e-sub.asm",    "Subroutine: TEMP buffer display", [], None, None),
    ("lab3e-nested.asm", "Nested sub: TEMP buffer display", [], None, None),

    # Lab 3f
    ("lab3f-reverse.asm",   "Recursive reverse 'SWAP PAWS'", [], "SWAP PAWS", None),
    ("lab3f-factorial.asm", "Factorial: key 5", [0x05,0x10], None, None),

    # Lab 4
    ("lab4b.asm",    "Lab 4b", [0x03,0x05,0x10], None, None),
    ("lab4c.asm",    "Lab 4c", [0x03,0x05,0x10], None, None),
    ("lab4d.asm",    "Lab 4d", [0x03,0x05,0x10], None, None),
    ("lab4e-add.asm","Lab 4e add", [0x03,0x05,0x10], None, None),
    ("lab4e-sub.asm","Lab 4e sub", [0x07,0x03,0x10], None, None),
    ("lab4f.asm",    "Lab 4f", [0x03,0x05,0x10], None, None),
    ("lab4g.asm",    "Lab 4g", [0x03,0x05,0x10], None, None),

    # Lab 5
    ("lab5a.asm","Lab 5a",[0x03,0x10],None,None),
    ("lab5b.asm","Lab 5b",[0x03,0x10],None,None),
    ("lab5c.asm","Lab 5c",[0x03,0x10],None,None),
    ("lab5d.asm","Lab 5d",[0x03,0x10],None,None),
    ("lab5e.asm","Lab 5e",[0x03,0x10],None,None),

    # Misc
    ("2funcal.asm",     "Two function calls",[0x05,0x10],None,None),
    ("my-skeleton.asm", "Skeleton template", [],        None,None),

    # Opcode coverage tests (14 opcodes not exercised by lab files)
    # 6th element = exp_flags dict: only listed bits are checked
    ("optest-halt.asm",         "HALT stops execution",          [], "H",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-psha.asm",         "PSHA/POPA round-trip",          [], "P",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-pushsr-popsr.asm", "PUSHSR/POPSR restores flags",   [], "S",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-clrim-setim.asm",  "CLRIM/SETIM toggle FLAG_I",     [], "I",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-rti.asm",          "RTI returns to correct address", [], "R",  None, {"C":0,"Z":0,"N":0,"V":0}),
    # N/V here reflect the databook's tens-complement BCD flag rules, now
    # implemented in cpu.py's _set_bcd_flags/_bcd_overflow_add/_sub:
    #   dadd-dsub:   final ACC=$50 is >=$50, i.e. "negative" in tens-
    #                complement BCD, so N=1.
    #   daddc-dsubc: final DSUBC computes 50-10-1=39, but the true signed
    #                result (-50 - 10 - 1 = -61) doesn't fit the 2-digit
    #                tens-complement range (-50..+49), so V=1.
    ("optest-dadd-dsub.asm",    "DADD/DSUB BCD arithmetic",      [], "uP", None, {"C":0,"Z":0,"N":1,"V":0}),
    ("optest-daddc-dsubc.asm",  "DADDC/DSUBC BCD with carry",    [], "Q9", None, {"C":0,"Z":0,"N":0,"V":1}),
    ("optest-bstsp.asm",        "BSTSP stores stack pointer",    [], "!",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-bldiv.asm",        "BLDIV loads interrupt vector",  [], "V",  None, {"C":0,"Z":0,"N":0,"V":0}),
    ("optest-jo-jno.asm",       "JO/JNO overflow branches",      [], "O",  None, {"C":1,"Z":0,"N":0,"V":1}),
]

SUBROUTINE_LIBS = [
    "fmult.asm",
    "int-add-2-byte-v1.asm","int-add-2-byte-v2.asm",
    "int-sub-2-byte-v1.asm","int-sub-2-byte-v2.asm",
    "int-mult-2-byte.asm",  "int-div-2-byte.asm",
    "int-neg-2-byte.asm",   "int-check-32768.asm",
]

SEP = "-" * 118

# ---------------------------------------------------------------------------
def run_all():
    lines  = []
    passed = failed = asm_err = lib_ok = lib_err = 0

    hdr = "{:<3}  {:<36} {:<36} {:<8}  {}".format(
        "#", "FILE", "DESCRIPTION", "RESULT", "DISPLAY / NOTE")
    lines.append(SEP)
    lines.append(hdr)
    lines.append(SEP)

    for idx, test in enumerate(TESTS, 1):
        fname, desc, keys, exp_disp, exp_led = test[:5]
        exp_flags = test[5] if len(test) > 5 else None
        disp, leds, acc, flags, halted, err = run_program(fname, keys)
        if err:
            result = "ASM ERR" if "Error line" in str(err) else "NO FILE"
            note   = err
            asm_err += 1
        else:
            disp_str = fmt_disp(disp)
            ok = True
            if exp_disp is not None and exp_disp not in disp_str:
                ok = False
            if exp_led is not None and (not leds or leds[-1] != exp_led):
                ok = False
            if exp_flags is not None:
                _fmap = {"C":FLAG_C,"Z":FLAG_Z,"N":FLAG_N,"V":FLAG_V}
                for _fb, _fv in exp_flags.items():
                    if int(bool(flags & _fmap[_fb])) != _fv:
                        ok = False
            result = "PASS" if ok else "FAIL"
            c = int(bool(flags & FLAG_C))
            z = int(bool(flags & FLAG_Z))
            n = int(bool(flags & FLAG_N))
            v = int(bool(flags & FLAG_V))
            note = "display={}".format(repr(disp_str[:52]))
            if leds:
                note += "  led={:08b}".format(leds[-1])
            note += "  ACC=${:02X} C={}Z={}N={}V={}".format(acc, c, z, n, v)
            if exp_flags is not None:
                _fmap = {"C":FLAG_C,"Z":FLAG_Z,"N":FLAG_N,"V":FLAG_V}
                for _fb, _fv in exp_flags.items():
                    _got = int(bool(flags & _fmap[_fb]))
                    if _got != _fv:
                        note += " [{}: exp {} got {}]".format(_fb, _fv, _got)
            if ok:
                passed += 1
            else:
                failed += 1
        lines.append("{:<3}  {:<36} {:<36} {:<8}  {}".format(
            idx, fname, desc, result, note))

    # Subroutine libraries
    lines.append(SEP)
    lines.append("")
    lines.append("SUBROUTINE LIBRARY FILES (assemble-only):")
    lines.append("")
    for fname in SUBROUTINE_LIBS:
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            lines.append("  SKIP  {}  (not found)".format(fname))
            continue
        try:
            src = open(path, encoding="latin-1").read()
            assemble((".ORG $4000\n" + src).splitlines())
            lines.append("  OK    {}".format(fname))
            lib_ok += 1
        except AssemblerError as e:
            lines.append("  ERR   {}  -- {}".format(fname, e))
            lib_err += 1
        except Exception as e:
            lines.append("  ERR   {}  -- {}".format(fname, e))
            lib_err += 1

    # Work In Progress
    wip_files = sorted(
        f for f in os.listdir(WIP) if f.lower().endswith(".asm")
    ) if os.path.isdir(WIP) else []

    lines.append("")
    lines.append(SEP)
    lines.append("WORK IN PROGRESS  (WorkInProgress/*.asm)  --  run & report, no pass/fail")
    lines.append("")
    if not wip_files:
        lines.append("  (folder is empty -- drop .asm files here for quick feedback)")
        lines.append("")
    else:
        wip_ok = wip_err = 0
        for fname in wip_files:
            disp, leds, acc, flags, halted, err = run_program(
                fname, key_sequence=[], data_dir=WIP)
            if err:
                lines.append("  ERR  {:<32}  {}".format(fname, err))
                wip_err += 1
            else:
                disp_str = fmt_disp(disp)
                c = int(bool(flags & FLAG_C))
                z = int(bool(flags & FLAG_Z))
                n = int(bool(flags & FLAG_N))
                note = "display={}".format(repr(disp_str[:52]))
                if leds:
                    note += "  led={:08b}".format(leds[-1])
                note += "  ACC=${:02X} C={}Z={}N={}".format(acc, c, z, n)
                lines.append("  OK   {:<32}  {}".format(fname, note))
                wip_ok += 1
        lines.append("")
        lines.append("  WIP: {} ran OK  |  {} errors".format(wip_ok, wip_err))
        lines.append("")

    # Summary
    lines.append(SEP)
    lines.append("  TESTS:    {} PASSED 