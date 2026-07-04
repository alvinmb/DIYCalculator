# ================================================================
# 07_calculator_leds.asm
# Beboputer Hands-On Tutorial — Section 4.3 (Calculator)
#
# Light up the Calculator's LEDs.
#
# What this program does
# -----------------------
#   $F032 drives the Calculator's six indicator LEDs - bit 5 is
#   the leftmost, bit 0 the rightmost. This program writes
#   00101010 (an alternating on/off pattern) to that port.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run (or Step), and watch the
#   Calculator's LED row light every other LED.
# ================================================================

LEDS:   .EQU    $F032

        .ORG    $4000

        LDA     $2A        # 00101010 -> alternating LEDs on
        STA     [LEDS]

        HALT

        .END    $4000
