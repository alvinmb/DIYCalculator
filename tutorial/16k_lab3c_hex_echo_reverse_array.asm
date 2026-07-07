# ================================================================
# 16k_lab3c_hex_echo_reverse_array.asm
# Beboputer Hands-On Tutorial — Lab 3c (hex echo, reverse order via
# an indexed array)
#
# Collect a sequence of hex-digit keys, then play them back in
# reverse order - the last key typed appears first.
#
# What this program does
# -----------------------
#   Reads hex-digit keys ($00-$0F, same acceptance test as 16j) and
#   stores each one instead of displaying it immediately. The moment
#   any other key is pressed (an operator, Clear, Sin - anything with
#   a raw code above $0F), the program stops collecting and instead
#   plays back everything that was typed, last-typed-first, then
#   terminates.
#
# How it works
# -------------
#   Two phases, both built around the Index register, and a small
#   fixed-size array to hold what's been typed:
#
#     BLDX    $0000       # Load index register with zero
#     GETKEY:    LDA     [KEYPAD]    # Load ACC from the keypad
#                JN      [GETKEY]    # Jump back if no key pressed
#                CMPA    $0F         # Compare ACC to $0F
#                JC      [DISPSTUF]  # Jump if ACC is bigger
#                STA     [STORE,X]   # ... else store ACC to memory
#                INCX                # ... and increment the index reg
#                JMP     [GETKEY]    # Go and wait for another key
#
#   [STORE,X] is indexed addressing (the same technique exercise 09
#   and Lab 2f's message table use for reading): "write to the byte
#   at STORE's address, plus whatever X currently holds." Each
#   accepted key gets written to STORE[0], then STORE[1], then
#   STORE[2], and so on, with INCX advancing to the next slot each
#   time. By the time a non-hex key ends this phase, X holds the
#   *count* of keys that were typed - not their sum or their last
#   value, just how many there were - and STORE[0..X-1] holds them
#   in the order they arrived.
#
#   The playback phase reuses that same count to walk backward:
#
#     DISPSTUF:  LDA     [STORE-1,X] # Load ACC with a key code
#                STA     [MAINDISP]  # Store it to the main display
#                DECX                # Decrement the index register
#                JNZ     [DISPSTUF]  # If index reg not 0 get next code
#                JMP     [$0000]     # Terminate the program
#
#   [STORE-1,X] is indexed addressing with a label-arithmetic offset
#   folded into the operand: the effective address is (STORE - 1) + X.
#   Since X still holds the count from the fill phase, the very first
#   read here lands on (STORE - 1) + count = STORE[count - 1] - the
#   *last* slot that got filled, i.e. the last key typed. DECX then
#   walks that same expression backward one slot at a time - count-2,
#   count-3, ... down to slot 0 - so the whole sequence plays back in
#   the exact opposite order from how it went in.
#
#   One edge case worth knowing about: if the very first key pressed
#   is a non-hex key (so X is still 0 when DISPSTUF begins), this
#   loop reads one byte *before* STORE, displays whatever garbage
#   happens to sit there, and then DECX takes a 16-bit X register
#   from 0 down to $FFFF - not zero, so JNZ loops again, walking
#   backward through memory indefinitely. The lab exercises in this
#   project are teaching tools rather than hardened production code,
#   and this is a good example of the kind of boundary case worth
#   noticing rather than a bug worth "fixing" in the original file -
#   simply always type at least one hex digit before pressing a
#   non-hex key to stay clear of it.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, switch to Hex mode, type a
#   short sequence like 1-2-3-A, then press any operator key - the
#   display shows A-3-2-1, the reverse of what you typed.
#
# Watch it happen
# -----------------
#   Open Registers and watch X count up 1, 2, 3, 4 while typing, then
#   count back down 4, 3, 2, 1, 0 during playback - and open Memory
#   to watch the STORE array fill up in typed order during the first
#   phase.
#
# Try this next
# ---------------
#   - Compare this array-based approach against 16m, which gets the
#     exact same last-in-first-out reversal using PUSHA/POPA and the
#     stack instead of a hand-rolled array and index arithmetic.
#   - Add a bounds check against STORE's 10-byte capacity so a very
#     long sequence can't silently run past the reserved area.
# ================================================================

## Lab 3c - Display '0' thru 'F' keys in the reverse order to that in
##          which they are entered using the index (X) register

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

########## Initialize the index register
           BLDX    $0000       # Load index register with zero

########## Wait for key to be pressed
GETKEY:    LDA     [KEYPAD]    # Load ACC from the keypad
           JN      [GETKEY]    # Jump back if no key pressed
           CMPA    $0F         # Compare ACC to $0F
           JC      [DISPSTUF]  # Jump if ACC is bigger
           STA     [STORE,X]   # ... else store ACC to memory
           INCX                # ... and increment the index reg
           JMP     [GETKEY]    # Go and wait for another key

########## Display the numbers
DISPSTUF:  LDA     [STORE-1,X] # Load ACC with a key code
           STA     [MAINDISP]  # Store it to the main display
           DECX                # Decrement the index register
           JNZ     [DISPSTUF]  # If index reg not 0 get next code
           JMP     [$0000]     # Terminate the program

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

TEMP8:    .BYTE               # Temp  8-bit (1-byte) location
TEMP16:   .2BYTE              # Temp 16-bit (2-byte) location
STORE:    .BYTE    *10        # Reserve 10 x 1-byte locations

#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
