# ================================================================
# 16e_lab3a_hex_nibbles_rolc.asm
# Beboputer Hands-On Tutorial — Lab 3a (hex display, ROLC version)
#
# The same most-significant nybble as 16c/16d - this time using
# ROLC, and still forcing bit 0 by hand rather than trusting ROLC's
# own carry-in.
#
# What this program does
# -----------------------
#   Identical behavior to 16c and 16d: wait for a key, show '$',
#   then show that key's raw code as two hex digits.
#
# How it works
# -------------
#   ROLC ("rotate left through carry") is built for exactly this
#   kind of bit recycling - it shifts the accumulator left, moves the
#   old top bit into Carry, and moves the *previous* Carry flag value
#   into the new bit 0, all in one instruction. That sounds like it
#   should make 16d's manual OR unnecessary. This version, though,
#   doesn't lean on that automatic bit-0 fill at all - it overrides
#   it explicitly every single time:
#
#     DISPMSN:   BLDX     4         # Load X reg with number of shifts
#                LDA     [TEMP8]    # Reload ACC with copy of key code
#     DISPMSNL:  ROLC               # Shift left 1 bit
#                JNC     [DISPMSN0] # Jump if carry flag = 0
#     DISPMNS1:  OR      %00000001  #   otherwise set LS bit to 1
#                JMP     [DISPDECX] #   then jump to decrement X reg
#     DISPMSN0:  AND     %11111110  # Clear LS bit to 0
#     DISPDECX:  DECX               # Decrement index register
#                JNZ     [DISPMSNL] # If X !=0 jump back and shift again
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#
#   The JNC test here is checking the *new* Carry flag that this
#   ROLC just produced - the bit that fell off the top - exactly the
#   same bit 16d's SHL produced. Whichever way that test comes out,
#   this code then forces bit 0 to match it by hand: OR to set it,
#   AND $FE to clear it. Whatever ROLC itself had already written
#   into bit 0 (from the Carry flag's value *before* this instruction
#   ran - old, stale information left over from some earlier
#   operation) gets stomped on and replaced immediately.
#
#   Put another way: this program uses ROLC only for the "shift left
#   and capture the bit that fell out in Carry" half of what ROLC
#   does, and throws away the "fill bit 0 from the old Carry" half by
#   overwriting it a line later. It ends up doing the exact same
#   work as 16d's SHL version, with one extra instruction (AND $FE)
#   in the path where the bit was a 0, since SHL already leaves
#   bit 0 at 0 for free while ROLC does not.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - results should
#   match 16c and 16d exactly for every key.
#
# Watch it happen
# -----------------
#   Step through DISPMSNL and compare the accumulator's bit 0 right
#   after ROLC executes against what it becomes right after the
#   following OR/AND - watch the explicit override happen in real
#   time in the Registers panel.
#
# Try this next
# ---------------
#   - Remove the OR/AND overrides and see what garbage turns up in
#     the displayed nybble - Carry's value going into the very first
#     ROLC is whatever was left over from CLRDISP's LDA/STA pair, not
#     necessarily 0, so the "automatic" bit-0 fill can't be trusted
#     here without first clearing Carry.
#   - Compare against 16f, which uses RORC and needs no bit-forcing
#     at all because the final AND mask cleans up any leftover
#     carry-chain bits regardless of what they were.
# ================================================================

## Lab 3a hex display using ROLC instructions

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
GETKEY:    LDA     [KEYPAD]   # Load ACC with code from keypad
           JN      [GETKEY]   # Jump back if no key pressed
           STA     [TEMP8]    # Store key code in temp location

########## Prepare the main display
CLRDISP:   LDA     CLRCODE    # Load ACC with clear code
           STA     [MAINDISP] # Clear main display
DISPDOLL:  LDA     $24        # Load ACC with ASCII code for '$'
           STA     [MAINDISP] # Write '$' to main display

########## Extract and display the most-significant nybble
DISPMSN:   BLDX     4         # Load X reg with number of shifts
           LDA     [TEMP8]    # Reload ACC with copy of key code
DISPMSNL:  ROLC               # Shift left 1 bit
           JNC     [DISPMSN0] # Jump if carry flag = 0
DISPMNS1:  OR      %00000001  #   otherwise set LS bit to 1
           JMP     [DISPDECX] #   then jump to decrement X reg
DISPMSN0:  AND     %11111110  # Clear LS bit to 0
DISPDECX:  DECX               # Decrement index register
           JNZ     [DISPMSNL] # If X !=0 jump back and shift again
           AND     %00001111  # Clear MS 4 bits (not really necessary)
           STA     [MAINDISP] # Copy result to main display

########## Extract and display the least-significant nybble
DISPLSN:   LDA     [TEMP8]    # Reload ACC with copy of key code
           AND     %00001111  # Mask out (clear) MS nybble
           STA     [MAINDISP] # Copy result to main display

########## Do it all again
DONE:      JMP     [GETKEY]   # Jump back and wait for new key

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
TEMP8:    .BYTE               # 8-bit temp location to store data
#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
