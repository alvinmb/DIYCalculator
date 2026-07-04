# ================================================================
# 06_calculator_display_text.asm
# Beboputer Hands-On Tutorial — Section 4.2 (Calculator)
#
# Write text to the Calculator's own display.
#
# What this program does
# -----------------------
#   The Calculator's LCD is itself a memory-mapped output device
#   at $F031. Printable ASCII (32-126) appends a character to it;
#   codes $0D, $10, or $1B clear the display. This program clears
#   the display, then writes 'H' and 'I' to it one byte at a time.
#
# Try it
# -------
#   Assemble, Load -> CPU, then Step through it a few instructions
#   at a time (rather than Run) so you can watch each character
#   land on the display before moving to the next. Display ->
#   Port Map Status will show each character the instant STA
#   executes.
# ================================================================

DISP:   .EQU    $F031

        .ORG    $4000

        LDA     $1B        # clear code
        STA     [DISP]

        LDA     $48        # 'H'
        STA     [DISP]
        LDA     $49        # 'I'
        STA     [DISP]

        HALT

        .END    $4000
