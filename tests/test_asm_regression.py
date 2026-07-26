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
test_asm_regression.py — every shipped .asm source file must assemble,
and every full program must run for a bounded number of steps without
the CPU faulting.

Scope: all ``*.asm`` files directly inside ``Data/``, ``tutorial/``,
``article/``, ``Compiler/``, and the top-level ``bin/`` folder.
``RPI_INSTALL/`` and ``MAC_INSTALL/`` are packaging trees, not program
sources, and ``WorkInProgress/`` is scratch space already covered
ad-hoc by ``test_harness.py`` — both are excluded here.

Two things are checked, split into two parametrized tests so a broken
file shows up under its own name in the pytest report:

  * ``test_asm_file_assembles`` — the file assembles cleanly. Files
    that start with ``.ORG`` are assembled as-is; files without one
    are subroutine-library fragments meant to be pasted into a larger
    program, so they're assembled wrapped in a synthetic
    ``.ORG $4000`` header instead (same trick ``test_harness.py`` uses
    for its ``SUBROUTINE_LIBS`` list).

  * ``test_asm_file_runs`` — full programs only (the fragments are
    never executed standalone: they typically end in ``RTS`` with
    nothing on the call stack). Assembles, loads the image at its
    origin, then single-steps the CPU for up to ``SMOKE_STEPS``
    instructions or until ``HALT``. This is a crash-detection smoke
    test, not an output check — ``cpu.step()`` never raises, it
    catches internal errors and returns ``"FAULT: ..."``, so that's
    what's asserted against. For expected-output checks on a curated
    subset of ``Data/*.asm`` (display text, LED pattern, flags), see
    ``test_harness.py`` at the project root.

A handful of the ``int-*-2-byte`` library fragments reference message
labels (``MSG_001`` etc.) that only exist in the full program they are
normally embedded in, so they fail to assemble even wrapped. This is a
pre-existing, documented condition — ``test_harness.py`` has reported
the same files as ``ERR`` in its "assemble-only" section since before
this suite existed (see ``test_harness_results.txt``) — so they are
marked ``xfail`` here rather than treated as a new regression.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

from compiler_core import Compiler
from beboputer_v7.cpu import CPU

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

# Directories that hold real program/library sources.
ASM_DIRS = ['Data', 'tutorial', 'article', 'Compiler', 'bin']

# Library fragments that cannot assemble standalone, even wrapped in a
# synthetic .ORG -- they reference MSG_nnn labels defined only in the
# full program they're normally pasted into. Not a bug introduced by
# this suite; test_harness.py has reported these same files as ERR
# in its subroutine-library check for as long as that harness existed.
KNOWN_UNRESOLVED_LABELS = {
    'Data/int-add-2-byte-v1.asm',
    'Data/int-add-2-byte-v2.asm',
    'Data/int-sub-2-byte-v1.asm',
    'Data/int-sub-2-byte-v2.asm',
    'Data/int-mult-2-byte.asm',
    'Data/int-div-2-byte.asm',
    'Data/int-check-32768.asm',
}

# Bound on how many instructions a "run" test will single-step. This is
# a smoke test for crashes, not a wait for HALT -- programs that idle
# on keypad input (never supplied here) will just spin harmlessly for
# the full budget. Deliberately smaller than the app's own RUN_LIMIT
# (500,000 in constants.py) to keep the suite fast.
SMOKE_STEPS = 50_000


def _discover_asm_files():
    found = []
    for d in ASM_DIRS:
        full = os.path.join(PROJECT_ROOT, d)
        if not os.path.isdir(full):
            continue
        for f in sorted(os.listdir(full)):
            if f.lower().endswith('.asm'):
                found.append(f"{d}/{f}")
    return found


ASM_FILES = _discover_asm_files()


def _read(rel_path):
    path = os.path.join(PROJECT_ROOT, *rel_path.split('/'))
    with open(path, encoding='latin-1') as fh:
        return fh.read()


def _has_org(src):
    """True if this looks like a full program (defines its own origin)
    rather than a subroutine-library fragment meant to be pasted into
    one."""
    return '.ORG' in src.upper()


# Full programs only -- used by test_asm_file_runs. Computed once at
# collection time so pytest can show each file as its own test id.
FULL_PROGRAMS = [
    f for f in ASM_FILES
    if f not in KNOWN_UNRESOLVED_LABELS and _has_org(_read(f))
]


@pytest.mark.parametrize('rel_path', ASM_FILES)
def test_asm_file_assembles(rel_path):
    src = _read(rel_path)
    result = Compiler().compile_source(src)
    if result.ok:
        return

    if rel_path in KNOWN_UNRESOLVED_LABELS:
        pytest.xfail(f"library fragment needs labels from its caller: {result.messages[:1]}")

    # No .ORG of its own -- retry as a library fragment wrapped in a
    # synthetic origin (mirrors test_harness.py's SUBROUTINE_LIBS check).
    wrapped = Compiler().compile_source(".ORG $4000\n" + src)
    assert wrapped.ok, (
        f"{rel_path} failed to assemble both standalone and wrapped in a "
        f"synthetic .ORG:\n"
        f"  standalone: {result.messages}\n"
        f"  wrapped:    {wrapped.messages}"
    )


@pytest.mark.parametrize('rel_path', FULL_PROGRAMS)
def test_asm_file_runs(rel_path):
    src = _read(rel_path)
    result = Compiler().compile_source(src)
    assert result.ok, f"{rel_path} failed to assemble: {result.messages}"

    cpu = CPU()
    cpu.reset()
    for i, b in enumerate(result.bytecode):
        cpu.ram[(result.origin + i) & 0xFFFF] = b
    cpu.pc = result.origin
    cpu.ram[0xF011] = 0xFF  # idle keypad sentinel, matches the app's reset state

    for _ in range(SMOKE_STEPS):
        if cpu.halted:
            break
        mnemonic_or_fault = cpu.step()
        assert not mnemonic_or_fault.startswith("FAULT:"), (
            f"{rel_path} faulted at PC=${cpu.pc:04X}: {mnemonic_or_fault}"
        )
