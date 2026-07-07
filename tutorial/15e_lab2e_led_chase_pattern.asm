# ================================================================
# 15e_lab2e_led_chase_pattern.asm
# Beboputer Hands-On Tutorial — Lab 2e
#
# Walk a single lit LED across the Calculator's six-LED row, one
# position at a time, forever.
#
# What this program does
# -----------------------
#   Clears the display, then lights the leftmost LED alone, then
#   the next one, then the next, all the way to the rightmost -
#   then starts over from the left again. A classic "chase" or
#   "scanner" pattern, built from one instruction most exercises
#   before this one haven't needed yet: SHR.
#
# How it works
# -------------
#   Exercise 07 showed that $F032 lights the six LEDs directly from
#   the bits of whatever byte you store there - bit 5 is the
#   leftmost LED, bit 0 the rightmost. This program starts with only
#   bit 5 set and shifts that single lit bit rightward one place
#   per trip through the inner loop:
#
#     LOOPA:     LDA     $20        # Load accumulator with $20
#     LOOPB:     STA     [SIXLEDS]  # Store accumulator to six LEDs
#                SHR                # Shift accumulator 1 bit to the right
#                JNZ     [LOOPB]    # Jump to LOOPB if Z flag not set
#                JMP     [LOOPA]    # ..else jump to LOOPA
#
#   $20 is 00100000 in binary - bit 5 set, every other bit clear.
#   SHR shifts every bit one place to the right, discarding whatever
#   falls off the bottom and filling the new top bit with 0. Watch
#   what that does across six passes through LOOPB:
#
#       $20 = 00100000   (leftmost LED)
#       $10 = 00010000
#       $08 = 00001000
#       $04 = 00000100
#       $02 = 00000010
#       $01 = 00000001   (rightmost LED)
#       $00 = 00000000   <- SHR of $01 - the bit finally shifts off
#                            the end entirely, and nothing replaces it
#
#   Each of those six values gets written to SIXLEDS and shown
#   before the next SHR runs, so the lit LED visibly walks from left
#   to right. The moment the shift produces $00, JNZ ("jump if Z
#   flag not set") stops firing - SHR sets the Zero flag exactly
#   when its result is zero, the same flag every other instruction
#   in this project sets on a zero result - so the loop falls
#   through to JMP [LOOPA], which reloads $20 and starts the whole
#   sweep over from the left again. The result is a lit LED that
#   walks all the way across and then jumps back to the start,
#   repeating forever (there is no exit condition in this program -
#   Stop or Power Off on the Calculator is the only way out).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, and watch the LED row - one
#   LED lit at a time, sweeping left to right, restarting at the
#   left each time it reaches the far right.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and watch $F032's value cycle
#   through $20, $10, $08, $04, $02, $01, then jump back to $20 -
#   Step through slowly to see SHR's effect on the accumulator in
#   the Registers panel one bit at a time.
#
# Try this next
# ---------------
#   - Make it bounce instead of restart: once you reach $01, switch
#     to SHL and walk back up to $20 before switching back to SHR,
#     instead of jumping straight back to LOOPA.
#   - Light two LEDs at once (e.g. start at $22 = 00100010) and
#     watch both march across in step.
#   - Slow it down: exercise 15c's note on adding a delay loop
#     applies here too - without one, the sweep runs faster than the
#     eye can separate each individual step at full emulator speed.
# ================================================================

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
SIXLEDS:  .EQU     $F032      # Address of output port for six LEDs
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
LOOPA:     LDA     $20        # Load accumulator with $20
LOOPB:     STA     [SIXLEDS]  # Store accumulator to six LEDs
           SHR                # Shift accumulator 1 bit to the right
           JNZ     [LOOPB]    # Jump to LOOPB if Z flag not set
           JMP     [LOOPA]    # ..else jump to LOOPA
          .END                # This is the end of the program
