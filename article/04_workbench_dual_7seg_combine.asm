# ================================================================
# 04_workbench_dual_7seg_combine.asm
# Beboputer Hands-On Tutorial — Section 3.4 (Workbench 1)
#
# Combine both switch banks on the dual 7-segment display.
#
# What this program does
# -----------------------
#   Builds a single byte where the low nibble of Switch Bank 1
#   ($F000) becomes the LEFT digit and the low nibble of Switch
#   Bank 2 ($F001) becomes the RIGHT digit of the dual decoded
#   7-segment display ($F024). Four SHL instructions move the
#   first nibble into the high position before combining the two
#   with OR.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, then flip the low four
#   switches on each bank independently and watch each digit of
#   the dual display track its own switch bank.
#
# Debug it
# ---------
#   Use the Memory Walker's GO field to jump to the TEMP label's
#   address and watch the intermediate shifted value land there
#   on every pass of the loop.
# ================================================================

SW1:    .EQU    $F000
SW2:    .EQU    $F001
SEG3:   .EQU    $F024

        .ORG    $4000

LOOP:   LDA     [SW1]
        AND     $0F        # low nibble of bank 1 -> left digit
        SHL
        SHL
        SHL
        SHL                # shift it into the high nibble
        STA     [TEMP]
        LDA     [SW2]
        AND     $0F        # low nibble of bank 2 -> right digit
        OR      [TEMP]     # combine hi(bank1) | lo(bank2)
        STA     [SEG3]
        JMP     [LOOP]

TEMP:   .BYTE   $00         # scratch byte (never executed - JMP always skips it)

        .END    $4000
