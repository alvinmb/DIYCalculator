# ================================================================
# 02_workbench_switch_to_hex_digit.asm
# Beboputer Hands-On Tutorial — Section 3.2 (Workbench 1)
#
# Show a switch value as a hex digit.
#
# What this program does
# -----------------------
#   Masks Switch Bank 1 (port $F000) down to its low nibble and
#   shows it as a single hex digit (0-F) on the decoded 7-segment
#   display (port $F023).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, then flip the low four
#   switches of Switch Bank 1 and watch the decoded 7-segment
#   digit change.
# ================================================================

SW1:    .EQU    $F000
SEG2:   .EQU    $F023

        .ORG    $4000

LOOP:   LDA     [SW1]
        AND     $0F        # keep only the low nibble
        STA     [SEG2]
        JMP     [LOOP]

        .END    $4000
