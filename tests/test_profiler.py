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

"""test_profiler.py -- beboputer_tk.tools.profiler (Code Profiler utility).

A 5-iteration DECX/JNZ loop gives a clean, deterministic 80:20-style
split: the loop body should dominate the hit count while the one-shot
setup/teardown lines (BLDX, LDA, HALT) stay at the bottom.
"""

import pytest

from beboputer_v7.cpu import CPU
from beboputer_tk.tools.profiler import ProfileSession
from compiler_core import Compiler

# DECX sets flags from IX; JNZ checks them immediately (nothing in
# between to clobber the Z flag) -- 5 trips round the loop, then falls
# through to LDA/HALT once each.
LOOP_SRC = """.ORG $4000
        BLDX   $0005
LOOP:   DECX
        JNZ    [LOOP]
        LDA    $01
        HALT
"""


def _load(cpu, compiled):
    cpu.reset()
    for i, b in enumerate(compiled.bytecode):
        cpu.ram[(compiled.origin + i) & 0xFFFF] = b
    cpu.pc = compiled.origin
    cpu.ram[0xF011] = 0xFF


def test_profile_ranks_loop_body_hottest():
    session = ProfileSession.from_source(LOOP_SRC, source_path="loop.asm")
    compiled = Compiler().compile_source(LOOP_SRC)
    cpu = CPU()
    _load(cpu, compiled)

    executed = session.run_headless(cpu, max_steps=1000)
    assert cpu.halted
    assert executed == 13   # BLDX(1) + 5*(DECX+JNZ) + LDA(1) + HALT(1)

    rep = session.report()
    assert rep.total_instructions == 13
    assert rep.unmapped_hits == 0

    by_line = {ln.line_no: ln for ln in rep.lines}
    assert by_line[3].hits == 5   # DECX
    assert by_line[4].hits == 5   # JNZ
    assert by_line[2].hits == 1   # BLDX
    assert by_line[5].hits == 1   # LDA
    assert by_line[6].hits == 1   # HALT
    assert by_line[3].percent == pytest.approx(5 / 13 * 100)

    # Sorted hottest-first, ties broken by line number.
    hottest = rep.hottest(2)
    assert [ln.line_no for ln in hottest] == [3, 4]
    assert all(ln.hits == 5 for ln in hottest)


def test_hottest_omits_never_executed_lines():
    session = ProfileSession.from_source(LOOP_SRC)
    compiled = Compiler().compile_source(LOOP_SRC)
    cpu = CPU()
    _load(cpu, compiled)
    session.run_headless(cpu, max_steps=1000)

    rep = session.report()
    # Every executable line in this program does execute at least once,
    # so hottest(100) should return all 5 -- not pad with 0-hit entries.
    assert len(rep.hottest(100)) == 5
    assert all(ln.hits > 0 for ln in rep.hottest(100))


def test_render_text_report_contains_bar_and_source():
    session = ProfileSession.from_source(LOOP_SRC)
    compiled = Compiler().compile_source(LOOP_SRC)
    cpu = CPU()
    _load(cpu, compiled)
    session.run_headless(cpu, max_steps=1000)

    text = session.render_text_report(title="Loop", top_n=3)
    assert "Loop" in text
    assert "Total instructions executed : 13" in text
    assert "DECX" in text
    assert "#" in text   # the ASCII bar chart


def test_render_text_report_before_any_run():
    session = ProfileSession.from_source(LOOP_SRC)
    text = session.render_text_report()
    assert "No instructions have been executed yet." in text


def test_profile_accumulates_across_runs_until_reset():
    session = ProfileSession.from_source(LOOP_SRC)
    compiled = Compiler().compile_source(LOOP_SRC)

    cpu1 = CPU()
    _load(cpu1, compiled)
    session.run_headless(cpu1, max_steps=1000)

    cpu2 = CPU()
    _load(cpu2, compiled)
    session.run_headless(cpu2, max_steps=1000)

    rep = session.report()
    assert rep.total_instructions == 26   # two full runs
    by_line = {ln.line_no: ln for ln in rep.lines}
    assert by_line[3].hits == 10

    session.reset()
    rep_after = session.report()
    assert rep_after.total_instructions == 0
    assert all(ln.hits == 0 for ln in rep_after.lines)


def test_attach_tracks_live_execution():
    session = ProfileSession.from_source(LOOP_SRC)
    compiled = Compiler().compile_source(LOOP_SRC)
    cpu = CPU()
    _load(cpu, compiled)

    session.attach(cpu)
    assert session.attached
    while not cpu.halted:
        cpu.step()
    session.detach()
    assert not session.attached

    rep = session.report()
    assert rep.total_instructions == 13


def test_render_annotated_source_requires_source_lines():
    listing = Compiler().generate_listing(LOOP_SRC).text
    session = ProfileSession(listing)   # no source_lines
    with pytest.raises(RuntimeError):
        session.render_annotated_source()


def test_from_source_raises_on_bad_assembly():
    with pytest.raises(RuntimeError):
        ProfileSession.from_source(".ORG $4000\n        NOTAREALMNEMONIC\n")
