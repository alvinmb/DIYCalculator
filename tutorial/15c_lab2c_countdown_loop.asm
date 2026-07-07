# ================================================================
# 15c_lab2c_countdown_loop.asm
# Beboputer Hands-On Tutorial — Lab 2c
#
# Clear the display, then count down from 9 to 1 on it.
#
# What this program does
# -----------------------
#   Clears the display (as in Labs 2a/2b), then shows 9, 8, 7, 6,
#   5, 4, 3, 2, 1 in quick succession before stopping - too fast to
#   read each digit individually at full speed, but easy to follow
#   with Step.
#
# How it works
# -------------
#   The first loop this series introduces - decrement-and-test,
#   the same shape almost every later exercise's loops are built
#   from:
#
#     LDA     $09        # Load the accumulator with $09
#     LOOP:      STA     [MAINDISP] # Store accumulator to the main display
#                DECA               # Decrement the accumulator
#                JNZ     [LOOP]     # Jump to LOOP if ACC isn't zero
#
#   ACC starts at 9. Each pass through LOOP shows the CURRENT value
#   before decrementing it, so the display sees 9 first, then 8,
#   then 7, and so on. DECA subtracts 1 and sets the Zero flag when
#   the result lands on exactly 0; JNZ ("jump if not zero") keeps
#   the loop going for every value except that last one. So the
#   sequence is: show 9, decrement to 8, still nonzero, loop; show
#   8, decrement to 7, loop; ...; show 1, decrement to 0, Zero flag
#   set, JNZ does NOT jump - the loop ends right after 1 was shown,
#   which is exactly the "9 downto 1" the header promises (0 is
#   never displayed, since the loop stops as soon as ACC reaches it,
#   before another STA can run).
#
#   $09 down to $01 are raw values, not ASCII text - but they show
#   up as the digit characters "9" through "1" anyway, because the
#   display port has a special case for exactly this range: raw
#   bytes $00-$09 are shown as the digit characters '0'-'9' (see
#   tools/calculator.py's write_display), on top of its normal
#   handling of printable ASCII. This is the same convention every
#   Calculator exercise relies on when it echoes a keypad digit
#   straight to the display without converting it to ASCII first.
#
#   Like Lab 2a, this program ends with JMP [$0000] rather than
#   HALT - see 15a's note for why that works.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - the display flashes through
#   9 down to 1 almost instantly. Switch to Step instead of Run to
#   watch each digit land one at a time, and watch the accumulator
#   count down in the Registers panel in lockstep.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and Step through the program -
#   you'll see $F031 receive 9, then 8, then 7, ... down to 1, one
#   value per trip through LOOP.
#
# Try this next
# ---------------
#   - Count up instead of down: start ACC at $01, INCA instead of
#     DECA, and stop the loop once ACC passes 9 (CMPA $09 then a
#     conditional jump, the way later exercises test ranges).
#   - Insert a delay loop between the STA and the DECA so each digit
#     is visible for a moment instead of flashing past - Lab 2e's
#     inner SHR loop is a good model for a simple busy-wait.
# ================================================================

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
           LDA     $09        # Load the accumulator with $09
LOOP:      STA     [MAINDISP] # Store accumulator to the main display
           DECA               # Decrement the accumulator
           JNZ     [LOOP]     # Jump to LOOP if ACC isn't zero
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program
