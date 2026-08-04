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
coverage.py -- Code Coverage utility for Beboputer .asm programs.

Revives the "Code Coverage" tool described in Educators/more-tools-code-
coverage.ppt (a *.pad/processed-assembly-dump-based utility in the
original Windows DIY Calculator) for this Python port. The idea, per
that deck and the project's own pitch for the feature: run a program,
then find out which source lines actually executed and which didn't --
so a bug hiding in a branch you never exercised during your own testing
(the "it worked every time I tried it, then it crashed and burned in
front of a friend" scenario) shows up as an uncovered line before you
ship or demo, instead of after.

Architecture
------------
LineCoverageMap  -- maps CPU program-counter addresses back to Beboputer
                    assembly *source line numbers*, built from the .lst
                    listing text `das.generate_listing()` already
                    produces (see Data/2funcal.lst for a real example).
                    No Qt/tkinter dependency.
CoverageSession  -- accumulates which addresses were actually fetched
                    across one or more CPU runs (attach() to a live CPU,
                    or run_headless() for a bounded batch run), and
                    turns that into a per-line report. No tkinter
                    dependency itself -- consumed by both a headless CLI
                    (coverage_cli.py, same folder) and beboputer_tk's
                    Code Coverage panel (beboputer_tk/panels/coverage.py),
                    same "pure logic" split as AssemblerRunner in
                    beboputer_v7/tools/assembler_runner.py.

This module lives under beboputer_tk/tools/ (the actively developed
build -- see README.md's "Which build?" note) rather than
beboputer_v7/tools/, even though it has no tkinter dependency of its
own: beboputer_v7 is discontinued and receives no further code changes
of any kind, so new tools belong with the build that's actually
maintained, not alongside the legacy Qt one.

Why parse the .lst listing instead of adding line numbers to the
assembler's own output?  compiler_core.Compiler already exposes a
generate_listing() that reuses the exact same instruction-encoding path
as compile_source() (see das.py's module docstring), so a listing and
its .ram can never disagree about what bytes a source line assembled
to. Piggy-backing on that text (rather than inventing a second,
parallel address-map data structure inside das.py that could drift out
of sync with the real listing) keeps this module a thin, independent
consumer of an interface the project already maintains and tests
against real reference listings (Data/*.lst).
"""

from __future__ import annotations

import bisect
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set

# compiler_core + das.py live two levels up in bin/ -- same defensive
# sys.path dance as beboputer_v7/tools/assembler_runner.py, so
# CoverageSession.from_source() works whether this module is imported via
# `beboputer_tk.tools.coverage` (normal app usage) or run standalone.
_BIN_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BIN_DIR))

try:
    from compiler_core import Compiler as _AsmCompiler
    _COMPILER_AVAILABLE = True
    _COMPILER_IMPORT_ERROR: Optional[str] = None
except Exception as _exc:                          # pragma: no cover
    _AsmCompiler = None
    _COMPILER_AVAILABLE = False
    _COMPILER_IMPORT_ERROR = str(_exc)


# ---------------------------------------------------------------------------
# .lst listing -> per-line address map
# ---------------------------------------------------------------------------

# Matches the fixed-width prefix `das.generate_listing()` writes for every
# row that corresponds to a real source line (see das.py's _format_row()):
#   f"{line_num:05d} {addr_field} {data_field}  {label_field} ..."
# addr_field is exactly 4 characters: either an uppercase hex address, or
# four spaces for a line that emits no bytes of its own (comments, blank
# lines, bare labels, .EQU/.ORG/.END directives). Continuation rows for a
# >3-byte .BYTE/.4BYTE line (wrapped data with no line number at all) and
# plain comment/blank rows (`f"{line_num:05d}" + " " + raw_text`, no
# fixed-width addr field) don't match this pattern and are correctly
# skipped -- verified against the real reference listings in Data/*.lst.
_ROW_RE = re.compile(r'^(?P<line>\d{5}) (?P<addr>[0-9A-Fa-f]{4}|\s{4}) ')


@dataclass(frozen=True)
class ListingLine:
    """One source line's entry from a .lst listing."""
    line_no: int
    addr: Optional[int]   # starting address of the bytes this line emits, or None


def parse_listing(listing_text: str) -> List[ListingLine]:
    """Extract (line_no -> starting address) for every row in *listing_text*
    that has one. Lines with no emitted bytes (comments, blank lines,
    bare labels, .EQU/.ORG/.END) come back with addr=None."""
    rows: List[ListingLine] = []
    for raw in listing_text.splitlines():
        m = _ROW_RE.match(raw)
        if not m:
            continue
        line_no = int(m.group('line'))
        addr_s = m.group('addr')
        addr = int(addr_s, 16) if addr_s.strip() else None
        rows.append(ListingLine(line_no, addr))
    return rows


class LineCoverageMap:
    """Maps CPU addresses to the source line that emitted the byte at that
    address, built from a parsed .lst listing."""

    def __init__(self, rows: Sequence[ListingLine]):
        self._line_addr: Dict[int, int] = {
            r.line_no: r.addr for r in rows if r.addr is not None
        }
        breaks = sorted((addr, line_no) for line_no, addr in self._line_addr.items())
        self._break_addrs: List[int] = [a for a, _ in breaks]
        self._break_lines: List[int] = [ln for _, ln in breaks]

    @property
    def executable_lines(self) -> Set[int]:
        """Source line numbers that emit at least one byte -- the
        denominator for a coverage percentage."""
        return set(self._line_addr)

    def address_for_line(self, line_no: int) -> Optional[int]:
        return self._line_addr.get(line_no)

    def line_for_address(self, addr: int) -> Optional[int]:
        """The source line that owns *addr*, i.e. the executable line
        whose own starting address is the greatest one <= addr (so
        continuation bytes of a multi-byte .BYTE/.4BYTE line, and the
        2nd/3rd byte of a multi-byte instruction, still resolve to the
        line that emitted them). Returns None if *addr* precedes every
        known line (e.g. it's in ROM/unassembled RAM, not this
        program)."""
        i = bisect.bisect_right(self._break_addrs, addr) - 1
        if i < 0:
            return None
        return self._break_lines[i]


# ---------------------------------------------------------------------------
# Coverage session -- accumulates hits across one or more CPU runs
# ---------------------------------------------------------------------------

@dataclass
class CoverageReport:
    """Snapshot of a CoverageSession's results at the moment report() was
    called."""
    total_executable: int
    covered: Set[int]
    uncovered: Set[int]
    line_hits: Dict[int, int]              # line_no -> total instructions executed
    unmapped_addresses: Dict[int, int] = field(default_factory=dict)  # addr -> hit count, outside any known line

    @property
    def percent(self) -> float:
        if not self.total_executable:
            return 100.0
        return 100.0 * len(self.covered) / self.total_executable


class CoverageSession:
    """Tracks which source lines of one Beboputer assembly program have
    been executed, across as many CPU runs as you like -- run the
    program several times (different keys pressed, different branches
    taken) and the hit set keeps accumulating until reset() is called,
    same as the "does everything actually get exercised" question this
    tool exists to answer.
    """

    def __init__(self, listing_text: str, source_lines: Optional[Sequence[str]] = None):
        self.line_map = LineCoverageMap(parse_listing(listing_text))
        self.source_lines: Optional[List[str]] = (
            list(source_lines) if source_lines is not None else None
        )
        self._addr_hits: "Counter[int]" = Counter()
        self._attached_cpu = None
        self._orig_step: Optional[Callable] = None

    # ------------------------------------------------------------ setup --
    @classmethod
    def from_source(cls, source_text: str, source_path: Optional[str] = None) -> "CoverageSession":
        """Assemble *source_text* with the shared compiler_core.Compiler
        and build a session from the resulting listing. Raises
        RuntimeError (with the assembler's own messages) if it fails to
        assemble."""
        if not _COMPILER_AVAILABLE:
            raise RuntimeError(
                f"compiler_core / das.py not available: {_COMPILER_IMPORT_ERROR}"
            )
        compiler = _AsmCompiler()
        listing = compiler.generate_listing(source_text, source_path=source_path)
        if not listing.success:
            raise RuntimeError(
                "Could not assemble source for coverage: " + "; ".join(listing.messages)
            )
        return cls(listing.text, source_text.splitlines())

    # -------------------------------------------------------- recording --
    def record(self, addr: int) -> None:
        """Note that the instruction at *addr* was fetched. Safe to call
        directly (e.g. from a custom run loop) without attach()."""
        self._addr_hits[addr & 0xFFFF] += 1

    def attach(self, cpu) -> None:
        """Transparently record every instruction *cpu* fetches from now
        on, by wrapping its step(). Works no matter what drives
        cpu.step() -- the GUI's own Run/Step buttons, Memory Walker's
        Run-to-BP, or a headless loop -- since they all end up calling
        cpu.step(). Call detach() to stop (e.g. when the panel closes or
        a different program is loaded)."""
        if self._attached_cpu is not None:
            self.detach()
        orig_step = cpu.step

        def _tracked_step(_orig=orig_step, _cpu=cpu):
            self.record(_cpu.pc)
            return _orig()

        cpu.step = _tracked_step
        self._attached_cpu = cpu
        self._orig_step = orig_step

    def detach(self) -> None:
        """Undo attach(), restoring the CPU's original step()."""
        if self._attached_cpu is not None and self._orig_step is not None:
            self._attached_cpu.step = self._orig_step
        self._attached_cpu = None
        self._orig_step = None

    @property
    def attached(self) -> bool:
        return self._attached_cpu is not None

    def run_headless(self, cpu, max_steps: int = 200_000, stop_on_halt: bool = True) -> int:
        """Single-step *cpu* up to *max_steps* times, recording coverage
        as it goes -- no attach()/detach() needed. Mirrors the bounded
        run loop tests/test_asm_regression.py uses for crash-smoke
        testing (SMOKE_STEPS), just recording addresses along the way.
        Returns the number of instructions actually executed."""
        executed = 0
        for _ in range(max_steps):
            if stop_on_halt and cpu.halted:
                break
            self.record(cpu.pc)
            cpu.step()
            executed += 1
        return executed

    def reset(self) -> None:
        """Clear accumulated hits (does not touch any attached CPU)."""
        self._addr_hits.clear()

    # --------------------------------------------------------- reporting --
    def report(self) -> CoverageReport:
        executable = self.line_map.executable_lines
        line_hits: Dict[int, int] = defaultdict(int)
        unmapped: Dict[int, int] = {}
        for addr, n in self._addr_hits.items():
            ln = self.line_map.line_for_address(addr)
            if ln is not None:
                line_hits[ln] += n
            else:
                unmapped[addr] = n
        covered = set(line_hits) & executable
        uncovered = executable - covered
        return CoverageReport(
            total_executable=len(executable),
            covered=covered,
            uncovered=uncovered,
            line_hits=dict(line_hits),
            unmapped_addresses=unmapped,
        )

    # ---------------------------------------------------------- render --
    def _source_text_for(self, line_no: int) -> str:
        if self.source_lines and 1 <= line_no <= len(self.source_lines):
            return self.source_lines[line_no - 1].rstrip()
        return ""

    def render_text_report(self, title: Optional[str] = None) -> str:
        """A short, human-readable summary -- coverage percentage plus
        the uncovered lines (with source text, when available) -- the
        thing you actually want to read after a test run."""
        rep = self.report()
        out: List[str] = []
        if title:
            out.append(title)
            out.append("=" * len(title))
        out.append(f"Executable lines : {rep.total_executable}")
        out.append(f"Covered          : {len(rep.covered)}")
        out.append(f"Uncovered        : {len(rep.uncovered)}")
        out.append(f"Coverage         : {rep.percent:.1f}%")
        if rep.unmapped_addresses:
            total_unmapped_hits = sum(rep.unmapped_addresses.values())
            out.append(
                f"Executed outside any known source line: "
                f"{len(rep.unmapped_addresses)} address(es), "
                f"{total_unmapped_hits} hit(s) -- possible runaway PC / "
                f"jump into data."
            )
        if rep.uncovered:
            out.append("")
            out.append("Uncovered lines:")
            for ln in sorted(rep.uncovered):
                text = self._source_text_for(ln)
                out.append(f"  {ln:5d}  {text}")
        return "\n".join(out)

    def render_annotated_source(self) -> str:
        """One row per source line, prefixed with a coverage marker:
        '+' executed, '!' executable but never executed, ' ' not an
        executable line at all (comment/blank/label/directive) -- same
        idea as gcov's ``.gcov`` annotation. Needs source_lines (set
        automatically by from_source(), or pass them to the
        constructor)."""
        if self.source_lines is None:
            raise RuntimeError(
                "render_annotated_source() needs source_lines -- construct "
                "via CoverageSession.from_source(), or pass source_lines= "
                "explicitly."
            )
        rep = self.report()
        out: List[str] = []
        for i, text in enumerate(self.source_lines, start=1):
            if i in rep.covered:
                marker = "+"
            elif i in rep.uncovered:
                marker = "!"
            else:
                marker = " "
            out.append(f"{marker} {i:5d}  {text}")
        return "\n".join(out)
