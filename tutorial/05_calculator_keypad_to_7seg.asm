# ================================================================
# 05_calculator_keypad_to_7seg.asm
# Beboputer Hands-On Tutorial — Section 4.1 (Calculator)
#
# Show the last key pressed on a 7-segment display.
#
# What this program does
# -----------------------
#   Polls the keypad port ($F011) - shared by the Calculator and
#   the on-screen Keyboard - and, the moment a digit or hex key
#   (0-9, A-F) is pressed, shows its low nibble on the Workbench's
#   decoded 7-segment display ($F023).
#
# How it works
# -------------
#   Port $F011 is a read-clear latch: the moment your program
#   reads a non-$FF value, the underlying byte snaps back to $FF
#   so the same keypress is never processed twice. The LDA still
#   gets the real key value in the Accumulator before that happens
#   - only the copy in RAM is cleared.
#
# Try it
# -------
#   Open Workbench 1 as well as the Calculator, assemble, Load ->
#   CPU, click Run, then press any digit or hex key (0-9, A-F) on
#   the Calculator.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise; its
#   $F011 box shows the current and previous key code, which makes
#   the read-clear behaviour easy to see in real time.
# ================================================================

KEY:    .EQU    $F011
SEG2:   .EQU    $F023

        .ORG    $4000

WAIT:   LDA     [KEY]      # read the keypad port
        CMPA    $FF        # $FF means idle - no key waiting
        JZ      [WAIT]     # keep waiting
        AND     $0F        # keep the low nibble (0-9, A-F)
        STA     [SEG2]     # show it
        JMP     [WAIT]

        .END    $4000
