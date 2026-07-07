# ================================================================
# 15d_lab2d_keypad_echo_digits.asm
# Beboputer Hands-On Tutorial — Lab 2d
#
# Clear the display, then echo digit keys 0-9 to it - and quietly
# ignore everything else.
#
# What this program does
# -----------------------
#   Clears the display, then sits in a loop reading the keypad
#   port. Press a digit key (0-9) and it appears on the display.
#   Press anything else - an operator, Clear, a hex letter, Sin,
#   whatever - and nothing happens; the program just keeps waiting.
#
# How it works
# -------------
#   A busy-wait loop reading one port ($F011, the keypad), guarded
#   by two range checks before anything reaches the display:
#
#     LOOP:      LDA     [KEYPAD]   # Load the accumulator from the keypad
#                JN      [LOOP]     # Jump to LOOP if N flag is set
#                CMPA    $09        # Compare accumulator to code $09
#                JC      [LOOP]     # Jump to LOOP if C flag is set
#                STA     [MAINDISP] # ... else store accumulator to display
#                JMP     [LOOP]     # Jump to LOOP
#
#   First check - JN ("jump if Negative"): the keypad port sits at
#   $FF ("idle, nothing pressed") whenever no key is down, and $FF
#   has its top bit set, which LDA's N flag reports as "negative."
#   Any byte $80-$FF - not just $FF itself - trips this same check,
#   which conveniently also screens out any button whose code
#   happens to live up in that range, with one read and one branch.
#   As long as nothing is pressed, JN keeps firing and the loop just
#   spins on this line.
#
#   Second check - CMPA $09 then JC ("jump if Carry"): once a key
#   with its top bit clear gets through the first check, this one
#   asks "is it bigger than 9?" This CPU's Carry flag after CMPA
#   means "the accumulator is STRICTLY GREATER THAN the operand"
#   (see exercise 10 for the long version of this, and why it trips
#   up naive "is A >= B" tests elsewhere) - so JC firing means the
#   keypress was 10 or higher, and gets looped past just like an
#   idle read did. Digit and hex-letter buttons arrive as their raw
#   nibble value, 0-15 (see exercise 10's note on tools/diy_button.py)
#   - so this check is exactly what separates plain digits 0-9 from
#   hex letters A-F (10-15) and everything else, without needing to
#   list out ten separate values.
#
#   Only a keypress that survives both checks - not negative, and
#   not greater than 9 - reaches the STA that puts it on the
#   display. Because raw bytes $00-$09 show up as the digit
#   characters '0'-'9' on this display (the same convention Lab 2c
#   and every Calculator exercise relies on), whatever digit you
#   pressed appears exactly as itself.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, switch the Calculator on if it
#   isn't already, and press digit keys - each one appears on the
#   display. Press Clear, an operator, or a letter key and watch
#   nothing happen.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and watch $F011 as you press
#   different keys - notice it always briefly shows the byte you
#   pressed and then reverts to $FF (see exercise 05's note on this
#   read-clear-latch behavior), and that only digit keys make it to
#   $F031.
#
# Try this next
# ---------------
#   - Also accept hex letters A-F: change the second check to
#     compare against $0F instead of $09.
#   - Add a Clear-key check ($1B) that resets the display, the way
#     every later Calculator exercise's DO_CLEAR does.
# ================================================================

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
KEYPAD:   .EQU     $F011      # Address of input port for keypad
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
LOOP:      LDA     [KEYPAD]   # Load the accumulator from the keypad
           JN      [LOOP]     # Jump to LOOP if N flag is set
           CMPA    $09        # Compare accumulator to code $09
           JC      [LOOP]     # Jump to LOOP if C flag is set
           STA     [MAINDISP] # ... else store accumulator to display
           JMP     [LOOP]     # Jump to LOOP
          .END                # This is the end of the program
