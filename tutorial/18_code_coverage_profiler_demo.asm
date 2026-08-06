# ================================================================
# 18_code_coverage_profiler_demo.asm
# Beboputer Hands-On Tutorial — Code Coverage & Code Profiler Demo
#
# A small, self-contained program built specifically to demonstrate
# the two Tools-menu analysis utilities:
#
#   Tools -> Code Coverage...   -- which lines actually ran?
#   Tools -> Code Profiler...   -- which lines ate the most time?
#
# What this program does
# -----------------------
#   Adds the numbers 1 through 5 together in a loop (SUM = 15), then
#   checks whether SUM is even or odd and lights LED 0 for ODD or
#   LED 1 for EVEN (port $F032, the same six-LED port used by the
#   Lab 3 exercises).
#
#   Because the numbers being summed are hardcoded (always 1..5),
#   SUM is always 15 -- always odd. The EVEN branch is real,
#   assembled, sitting right there in the program... and can never
#   run. That is deliberate: it is the smallest possible example of
#   the scenario the Code Coverage tool exists to catch -- a branch
#   that looks fine sitting in the editor and would only reveal
#   itself as dead (or, in a less contrived program, as an
#   undiscovered bug) once someone actually points a coverage tool
#   at a real run.
#
#   The 8-line addition loop runs 5 times (40 of this program's 51
#   total instructions -- about 78%) while every other line runs
#   once. That is the Code Profiler's demo: a small fraction of the
#   program accounts for most of the execution, exactly the 80:20
#   rule the tool exists to surface.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run (or single-step with Memory
#   Walker if you want to watch SUM/N in RAM change on every pass
#   of the loop). It halts on its own -- no keypad input needed.
#
# Watch it happen
# -----------------
#   Open Tools -> Code Coverage..., click Load Source... and pick
#   this file, then Run Program. The SHOW_EVEN lines (LDA %00000010
#   / STA [SIXLEDS]) light up red -- executable, assembled, and
#   never executed. Everything else lights up green.
#
#   Open Tools -> Code Profiler... the same way. The eight LOOP:
#   lines dominate the Hot Spots box and the bar chart; the one-shot
#   setup/branch lines barely register by comparison.
#
#   (The SUM/N reservation lines at the bottom show up as
#   "uncovered" too, in both tools -- that is expected, not a bug in
#   the program or the tools: .BYTE just reserves a memory location,
#   the CPU's PC never fetches an instruction from there, so it can
#   never show up as "executed" the way real code does.)
#
# Try this next
# ---------------
#   - Change the starting N from 5 to 4 (SUM becomes 10, even) and
#     re-run -- now ODD is the branch that never executes instead
#     (still 23 executable lines total, but coverage drops slightly,
#     from 82.6% to 78.3% -- SHOW_ODD is one line longer than
#     SHOW_EVEN, thanks to its extra JMP [DONE], so missing it costs
#     one more line).
#   - Add a third branch (e.g. "is SUM a multiple of 5?") and see it
#     show up as its own uncovered line until you make it reachable.
#   - Change the loop to sum 1 through 20 instead of 1 through 5 and
#     watch the profiler's hit counts (and the loop's share of total
#     execution) climb accordingly.
# ================================================================
SIXLEDS:  .EQU   $F032        # six-LED output port (Lab 3's port)

        .ORG   $4000

        LDA    $00
        STA    [SUM]
        LDA    $05
        STA    [N]

# ---------------------------------------------------------------
# Hot loop: SUM = SUM + N, N = N - 1, repeat while N != 0.
# Runs 5 times -- the busiest lines in the whole program.
# ---------------------------------------------------------------
LOOP:   LDA    [SUM]
        ADD    [N]
        STA    [SUM]
        LDA    [N]
        DECA
        STA    [N]
        CMPA   $00
        JNZ    [LOOP]

# ---------------------------------------------------------------
# Branch: is SUM even or odd? SUM is always 15 here, so ODD always
# runs and EVEN never does -- see the header comment above.
# ---------------------------------------------------------------
        LDA    [SUM]
        AND    $01
        JZ     [SHOW_EVEN]

SHOW_ODD:
        LDA    %00000001     # LED 0
        STA    [SIXLEDS]
        JMP    [DONE]

SHOW_EVEN:
        LDA    %00000010     # LED 1 -- never reached with N starting at 5
        STA    [SIXLEDS]

DONE:   HALT

SUM:    .BYTE
N:      .BYTE

        .END   $4000
