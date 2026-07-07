# ================================================================
# 16j_lab3c_hex_echo_forward.asm
# Beboputer Hands-On Tutorial — Lab 3c (hex echo, forward order)
#
# Echo hex digit keys 0-F to the display, in the order they're
# pressed - the baseline this tutorial's next two files build on.
#
# What this program does
# -----------------------
#   Sits in a loop reading the keypad. Press any key with a raw code
#   of $0F or less - digits 0-9 or hex letters A-F - and it appears
#   on the display immediately, right after whatever was already
#   there. Press anything else (an operator, Clear, Sin, etc.) and
#   nothing happens.
#
# How it works
# -------------
#   This is Lab 2d's digit-only echo (exercise 15d) with one number
#   changed:
#
#     GETKEY:    LDA     [KEYPAD]   # Load ACC from the keypad
#                JN      [GETKEY]   # Jump back if no key pressed
#                CMPA    $0F        # Compare ACC to $0F
#                JC      [GETKEY]   # Jump back if ACC is bigger
#                STA     [MAINDISP] # ... else store ACC to display
#                JMP     [GETKEY]   # Go and wait for another key
#
#   15d's version compared against $09 to accept only plain digits.
#   This version compares against $0F instead, which - since digit
#   and hex-letter buttons both arrive as their raw nibble value,
#   0-15 (see exercise 10's note on tools/diy_button.py) - lets every
#   value from $00 through $0F through, meaning both the digit keys
#   (0-9) and the hex-letter keys (A-F) get displayed. Raw bytes
#   $00-$09 render as '0'-'9' and $0A-$0F render as 'A'-'F' on this
#   display (the same convention every Calculator exercise in this
#   project relies on), so no ASCII conversion step is needed - the
#   raw nibble value already *is* the character to show.
#
#   Each accepted key just gets appended to whatever's already on
#   the display - there's no clearing, no counting, no memory of
#   what came before. That simplicity is exactly why this file
#   exists: 16k and 16l both build on this same "accept 0-F, do
#   something with it" keypad loop, adding memory (an array, or the
#   Index register's own value) on top of it.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, switch to Hex mode, and type a
#   sequence like 1-2-3-A-B - the display fills up left to right in
#   exactly the order you typed, one character per keypress.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and watch $F011 as you press
#   digit and hex-letter keys - both kinds pass the CMPA $0F/JC test
#   and reach $F031, while an operator or Clear key's higher raw code
#   gets looped past.
#
# Try this next
# ---------------
#   - See 16k for the reverse-order version of this same idea (built
#     using an array and the Index register), and 16m for a second,
#     very different way of getting the exact same reversal using
#     the stack instead.
# ================================================================

## Lab 3c - Display '0' thru 'F' keys in the order they are entered

#######################################################################
## Start of constant declarations                                    ##
#######################################################################
MAINDISP: .EQU     $F031      # Address of output port for main display
SIXLEDS:  .EQU     $F032      # Address of output port for six LEDs
KEYPAD:   .EQU     $F011      # Address of input port for keypad
CLRCODE:  .EQU     $10        # Special code to clear the main display
BINMODE:  .EQU     %00000100  # LED code to indicate binary mode
DECMODE:  .EQU     %00000010  # LED code to indicate decimal mode
HEXMODE:  .EQU     %00000001  # LED code to indicate hexadecimal mode
#######################################################################
## End of constant declarations                                      ##
#######################################################################

          .ORG     $4000      # Set program origin

#######################################################################
## Start of initialization                                           ##
#######################################################################
INIT:      LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Write clear code to main display
           LDA     HEXMODE    # Load accumulator with hex mode code
           STA     [SIXLEDS]  # Write to port driving six LEDs
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

########## Wait for key to be pressed
GETKEY:    LDA     [KEYPAD]   # Load ACC from the keypad
           JN      [GETKEY]   # Jump back if no key pressed
           CMPA    $0F        # Compare ACC to $0F
           JC      [GETKEY]   # Jump back if ACC is bigger
           STA     [MAINDISP] # ... else store ACC to display
           JMP     [GETKEY]   # Go and wait for another key

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
