# ================================================================
# 16m_lab3d_hex_echo_reverse_stack.asm
# Beboputer Hands-On Tutorial — Lab 3d (hex echo, reverse order via
# the stack)
#
# The same last-typed-first reversal as 16k - this time using
# PUSHA/POPA and the CPU's stack instead of a hand-built array.
#
# What this program does
# -----------------------
#   Behaves like 16k: type a run of hex-digit keys, press any other
#   key, and the digits play back in reverse - last typed, first
#   shown. Unlike 16k, this one never stops - after playing a
#   sequence back, it's ready to collect and reverse another one.
#
# How it works
# -------------
#   16k needed a fixed-size array (STORE) and index arithmetic
#   ([STORE-1,X]) to walk backward through what was typed. This
#   version reaches for the stack instead, using PUSHA to remember
#   each digit and POPA to retrieve them - which comes back out in
#   the opposite order automatically, with no array or index math
#   needed at all:
#
#     BLDSP   $EFFF       # Load stack pointer with $EFFF
#
#     GETKEY:    NOP                 # a harmless one-cycle delay - see notes
#     LOOP:      LDA     [KEYPAD]    # Load ACC from the keypad
#                JN      [LOOP]      # Jump back if no key pressed
#                CMPA    $0F         # Compare ACC to $0F
#                JC      [DISPSTUF]  # Jump if ACC is bigger
#                PUSHA               # ... else push ACC onto the stack
#                JMP     [GETKEY]    # Go and wait for another key
#
#     DISPSTUF:  POPA                # Pop ACC off the stack
#                STA     [MAINDISP]  # Store it to the main display
#                JMP     [GETKEY]    # Go and wait for another key
#
#   BLDSP sets up the stack pointer before anything else runs, the
#   same way BLDX sets up the Index register in earlier exercises -
#   this project's stack grows downward from $EFFF. Every accepted
#   hex digit gets PUSHA'd - laid on top of whatever's already
#   there. The stack is naturally Last-In-First-Out: the most
#   recently pushed byte is always the first one a POPA retrieves.
#   So the moment a non-hex key breaks the typing loop, DISPSTUF's
#   POPA hands back the *last* digit that was typed - no counting,
#   no indexed addressing, no [STORE-1,X] arithmetic required.
#
#   And notice DISPSTUF only pops and shows *one* digit, then jumps
#   straight back to GETKEY to wait for the next key - rather than
#   looping through every pushed byte at once the way 16k's DISPSTUF
#   loop does. Practically, that means: type a run of digits, press
#   a non-digit key, and one digit (the last one typed) appears; type
#   more digits, press a non-digit key again, and the *next-most*
#   recently typed digit comes back - the stack keeps handing back
#   whatever's currently on top, one POPA at a time, for as long as
#   there's anything left on it to pop.
#
#   The leading NOP on GETKEY does nothing to the program's behavior
#   - it just burns one CPU cycle before looping back to LOOP each
#   time. The source labels it "see notes" without further comment
#   in this file; harmless either way, and left in place exactly as
#   found. (The original source's comment used curly typographic
#   quotes saved in a Windows text encoding, which don't render
#   correctly as plain UTF-8 - normalized to straight quotes here for
#   readability; the instruction itself, and everything the CPU
#   actually does, is unaffected either way.)
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, switch to Hex mode, type 1-2-3,
#   then press an operator key - '3' appears (the last digit typed).
#   Press the operator key again and nothing more appears (the stack
#   for that run is now empty); type more digits and repeat.
#
# Watch it happen
# -----------------
#   Open Registers and watch the stack pointer (SP) count down by one
#   with every PUSHA and back up by one with every POPA - and compare
#   that against 16k's Index register, which does the equivalent
#   counting job with INCX/DECX instead.
#
# Try this next
# ---------------
#   - Change DISPSTUF to loop (POPA/STA/JNZ-style, checking for an
#     empty-stack condition) so an entire typed run reverses in one
#     shot the way 16k's does, instead of one digit per non-hex
#     keypress.
#   - Compare this file directly against 16k: both reverse a typed
#     sequence, but one leans on the stack's built-in LIFO order and
#     the other builds that same ordering by hand with an array and
#     index arithmetic.
# ================================================================

## Lab 3d - Display hex chars in reverse order using the stack

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

########## Initialize the stack pointer
           BLDSP   $EFFF       # Load stack pointer with $EFFF

########## Wait for key to be pressed
GETKEY:    NOP                 # "No operation" - see notes
LOOP:      LDA     [KEYPAD]    # Load ACC from the keypad
           JN      [LOOP]      # Jump back if no key pressed
           CMPA    $0F         # Compare ACC to $0F
           JC      [DISPSTUF]  # Jump if ACC is bigger
           PUSHA               # ... else push ACC onto the stack
           JMP     [GETKEY]    # Go and wait for another key

########## Display a number
DISPSTUF:  POPA                # Pop ACC off the stack
           STA     [MAINDISP]  # Store it to the main display
           JMP     [GETKEY]    # Go and wait for another key

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
