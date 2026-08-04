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
profiler_cli.py -- headless Code Profiler utility for Beboputer .asm programs.

Assembles a program, runs it on a fresh virtual CPU with no GUI attached
(up to a step cap or until it HALTs), and reports which source lines
accounted for the largest share of total execution -- the 80:20 rule:
find the 20% of the code eating 80% of the time before you spend an
afternoon "optimizing" a line that barely ever runs.

Usage
-----
    python profiler_cli.py PROGRAM.asm
    python profiler_cli.py PROGRAM.asm --steps 500000 --top 20 --out profile.txt --annotated PROGRAM.prof

See coverage_cli.py's module docstring for the same "no keypad input is
simulated" caveat -- it applies here too, since both tools share the
same headless run loop.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BIN_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BIN_DIR) not in sys.path:
    sys.path.insert(0, str(_BIN_DIR))

from beboputer_v7.cpu import CPU                        # noqa: E402  -- shared CPU engine, reused by beboputer_tk itself
from beboputer_tk.tools.profiler import ProfileSession  # noqa: E402
from compiler_core import Compiler                       # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Beboputer Code Profiler utility -- assemble, run, and "
                    "report which source lines accounted for the most execution time."
    )
    ap.add_argument("source", help="path to a .asm source file")
    ap.add_argument(
        "--steps", type=int, default=200_000,
        help="max instructions to execute before giving up (default: 200000)",
    )
    ap.add_argument(
        "--top", type=int, default=15,
        help="how many hottest lines to list (default: 15)",
    )
    ap.add_argument(
        "--out", metavar="FILE",
        help="write the text profile report to FILE (in addition to stdout)",
    )
    ap.add_argument(
        "--annotated", metavar="FILE",
        help="write a full source listing annotated with hit counts/percentages to FILE",
    )
    args = ap.parse_args(argv)

    src_path = Path(args.source)
    try:
        source_text = src_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Cannot read {src_path}: {exc}", file=sys.stderr)
        return 2

    compiler = Compiler()
    compiled = compiler.compile_source(source_text)
    if not compiled.ok:
        print(f"Assembly failed for {src_path}:", file=sys.stderr)
        for msg in compiled.messages:
            print(f"  {msg}", file=sys.stderr)
        return 1

    listing = compiler.generate_listing(source_text, source_path=str(src_path))
    if not listing.ok:
        print(f"Could not generate a listing for {src_path}:", file=sys.stderr)
        for msg in listing.messages:
            print(f"  {msg}", file=sys.stderr)
        return 1

    session = ProfileSession(listing.text, source_text.splitlines())

    cpu = CPU()
    cpu.reset()
    origin = compiled.origin if compiled.origin is not None else CPU.RESET_VECTOR
    for i, b in enumerate(compiled.bytecode or b""):
        cpu.ram[(origin + i) & 0xFFFF] = b
    cpu.pc = origin
    cpu.ram[0xF011] = 0xFF  # idle keypad sentinel -- matches the GUI's own reset state

    executed = session.run_headless(cpu, max_steps=args.steps)

    status = "HALTed" if cpu.halted else f"stopped after {executed} instructions (step limit reached)"
    header = f"Profile for {src_path.name}  --  {status}"
    report_text = session.render_text_report(title=header, top_n=args.top)
    print(report_text)

    if args.out:
        Path(args.out).write_text(report_text + "\n", encoding="utf-8")
        print(f"\nReport written to: {args.out}")

    if args.annotated:
        Path(args.annotated).write_text(session.render_annotated_source() + "\n", encoding="utf-8")
        print(f"Annotated source written to: {args.annotated}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
