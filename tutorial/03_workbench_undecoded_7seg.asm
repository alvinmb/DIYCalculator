# ================================================================
# 03_workbench_undecoded_7seg.asm
# Beboputer Hands-On Tutorial — Section 3.3 (Workbench 1)
#
# Drive the undecoded 7-segment display directly.
#
# What this program does
# -----------------------
#   $F021 is NOT decoded - each of its low 7 bits drives one
#   segment (a through g) directly. This program masks Switch
#   Bank 1 (port $F000) down to those 7 bits and writes them
#   straight to the undecoded 7-segment display.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, then flip switches and watch
#   individual segments turn on and off - most patterns will look
#   like nonsense digits, which is the point: this port has no
#   idea what a "digit" is, it just drives wires a-g.
# ================================================================

SW1:    .EQU    $F000
SEG1:   .EQU    $F021

        .ORG    $4000

LOOP:   LDA     [SW1]
        AND     $7F        # keep bits 0-6 (segments a-g)
        STA     [SEG1]
        JMP     [LOOP]

        .END    $4000
