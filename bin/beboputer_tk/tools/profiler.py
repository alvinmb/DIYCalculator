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
profiler.py -- Code Profiler utility for Beboputer .asm programs.

Revives the "Code Profiler" tool pitched in Educators/more-tools-code-
profiler.ppt (colored text / bar-chart / "bird's eye" hotspot displays,
same *.pad-based idea as the sibling Code Coverage tool) for this Python
port. The pitch is the classic 80:20 rule: a program spends most of its
time in a small fraction of its code, so ranking source lines by how
often they actually executed tells you where "judicious tweaking" will
actually speed things up -- instead of guessing.

Beboputer has no variable-length instruction timing (cpu.py's step()
increments cycle_count by exactly 1 for every instruction, regardless of
which one), so "time spent" and "instructions executed" are the same
thing on this virtual CPU -- ranking by execution count *is* ranking by
time, with no separate cycle-cost model needed.

Architecture
------------
ProfileSession wraps a CoverageSession (beboputer_tk.tools.coverage,
same folder) rather than re-implementing address/line mapping and
hit-recording a second time -- profiling and coverage are the same
underlying data ("which addresses executed, how many times"), just
answered with a different question ("where did the time go" instead of
"was it touched at all"). No tkinter dependency of its own; consumed by
both a headless CLI (profiler_cli.py, same folder) and beboputer_tk's
Code Profiler panel (beboputer_tk/panels/profiler.py).

Lives under beboputer_tk/tools/ rather than beboputer_v7/tools/ for the
same reason coverage.py does -- see that module's docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .coverage import CoverageSession


def _source_text_for(source_lines: Optional[Sequence[str]], line_no: int) -> str:
    if source_lines and 1 <= line_no <= len(source_lines):
        return source_lines[line_no - 1].rstrip()
    return ""


@dataclass
class HotLine:
    """One executable source line's share of total execution."""
    line_no: int
    hits: int
    percent: float
    text: str


@dataclass
class ProfileReport:
    """Snapshot of a ProfileSession's results at the moment report() was
    called. `lines` covers every executable line (including ones never
    hit, at 0%), sorted hottest-first."""
    total_instructions: int
    lines: List[HotLine]
    unmapped_hits: int = 0   # instructions executed outside any known line

    def hottest(self, n: int = 10) -> List[HotLine]:
        """The top *n* lines that were actually executed at least once,
        hottest first (lines never hit are omitted, not just low-ranked --
        a 0%-forever list of the whole program isn't a "hot spots" list)."""
        return [ln for ln in self.lines if ln.hits > 0][:n]


class ProfileSession:
    """Ranks a Beboputer assembly program's source lines by how large a
    share of total execution they accounted for, across as many CPU runs
    as you like (hits accumulate until reset(), same as CoverageSession).
    """

    def __init__(self, listing_text: str, source_lines: Optional[Sequence[str]] = None):
        self._cov = CoverageSession(listing_text, source_lines)

    @classmethod
    def from_source(cls, source_text: str, source_path: Optional[str] = None) -> "ProfileSession":
        """Assemble *source_text* and build a session from the resulting
        listing. Raises RuntimeError (with the assembler's own messages)
        if it fails to assemble -- same contract as
        CoverageSession.from_source()."""
        session = cls.__new__(cls)
        session._cov = CoverageSession.from_source(source_text, source_path=source_path)
        return session

    # ---------------------------------------------------------- delegates --
    # Recording/attach/detach/run_headless/reset are exactly the same
    # mechanics as CoverageSession -- no reason to reimplement them.
    @property
    def line_map(self):
        return self._cov.line_map

    @property
    def source_lines(self):
        return self._cov.source_lines

    @property
    def attached(self) -> bool:
        return self._cov.attached

    def record(self, addr: int) -> None:
        self._cov.record(addr)

    def attach(self, cpu) -> None:
        self._cov.attach(cpu)

    def detach(self) -> None:
        self._cov.detach()

    def run_headless(self, cpu, max_steps: int = 200_000, stop_on_halt: bool = True) -> int:
        return self._cov.run_headless(cpu, max_steps=max_steps, stop_on_halt=stop_on_halt)

    def reset(self) -> None:
        self._cov.reset()

    # --------------------------------------------------------- reporting --
    def report(self) -> ProfileReport:
        cov_rep = self._cov.report()
        total = sum(cov_rep.line_hits.values())
        unmapped = sum(cov_rep.unmapped_addresses.values())

        lines: List[HotLine] = []
        for line_no in self.line_map.executable_lines:
            hits = cov_rep.line_hits.get(line_no, 0)
            pct = (100.0 * hits / total) if total else 0.0
            lines.append(HotLine(
                line_no=line_no, hits=hits, percent=pct,
                text=_source_text_for(self.source_lines, line_no),
            ))
        lines.sort(key=lambda ln: (-ln.hits, ln.line_no))
        return ProfileReport(total_instructions=total, lines=lines, unmapped_hits=unmapped)

    # ---------------------------------------------------------- render --
    @staticmethod
    def _bar(percent: float, width: int = 20) -> str:
        n = min(width, int(round(percent / 100.0 * width)))
        return "#" * n + "-" * (width - n)

    def render_text_report(self, title: Optional[str] = None, top_n: int = 15) -> str:
        """A gprof-flavoured summary: total instructions executed, then
        the hottest *top_n* lines with a percentage and an ASCII bar
        (the "vertical bar-chart type display" the original tool's own
        pitch deck describes) -- the thing that actually answers "where
        should I optimize"."""
        rep = self.report()
        out: List[str] = []
        if title:
            out.append(title)
            out.append("=" * len(title))
        out.append(f"Total instructions executed : {rep.total_instructions}")
        if rep.unmapped_hits:
            out.append(
                f"Executed outside any known source line: {rep.unmapped_hits} "
                f"instruction(s) -- possible runaway PC / jump into data."
            )
        hot = rep.hottest(top_n)
        if not hot:
            out.append("")
            out.append("No instructions have been executed yet.")
            return "\n".join(out)

        out.append("")
        out.append(f"Hottest {len(hot)} line(s) (80:20 rule -- start here):")
        out.append("")
        out.append(f"{'LINE':>6}  {'HITS':>8}  {'%':>6}  {'':22}  SOURCE")
        for ln in hot:
            bar = self._bar(ln.percent)
            out.append(f"{ln.line_no:6d}  {ln.hits:8d}  {ln.percent:5.1f}%  {bar}  {ln.text}")
        return "\n".join(out)

    def render_annotated_source(self) -> str:
        """One row per source line, prefixed with hit count + percentage
        of total execution -- executable lines never hit still show
        (as 0), non-executable lines (comments/blanks/labels/directives)
        are left unmarked."""
        if self.source_lines is None:
            raise RuntimeError(
                "render_annotated_source() needs source_lines -- construct "
                "via ProfileSession.from_source(), or pass source_lines= "
                "explicitly."
            )
        rep = self.report()
        by_line = {ln.line_no: ln for ln in rep.lines}
        out: List[str] = []
        for i, text in enumerate(self.source_lines, start=1):
            hot = by_line.get(i)
            if hot is None:
                out.append(f"{'':7} {'':7}  {i:5d}  {text}")
            else:
                out.append(f"{hot.hits:7d} {hot.percent:6.1f}%  {i:5d}  {text}")
        return "\n".join(out)
