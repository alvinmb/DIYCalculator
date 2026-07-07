# ================================================================
# 16f_lab3a_hex_nibbles_rorc.asm
# Beboputer Hands-On Tutorial — Lab 3a (hex display, RORC version)
#
# The same most-significant nybble as 16c/16d/16e - four plain RORCs
# and a trailing mask, no bit-forcing needed anywhere.
#
# What this program does
# -----------------------
#   Identical behavior to the other three hex-display versions: wait
#   for a key, show '$', then show that key's raw code as two hex
#   digits.
#
# How it works
# -------------
#   Where 16e's ROLC needed explicit AND/OR overrides to control what
#   landed in bit 0 each pass, this version just runs RORC four times
#   in a row and masks off whatever's left afterward:
#
#     DISPMSN:   LDA     [TEMP8]    # Reload ACC with copy of key code
#                RORC               # Shift right 1 bit (= 1 bit shift)
#                RORC               # Shift right 1 bit (= 2 bit shift)
#                RORC               # Shift right 1 bit (= 3 bit shift)
#                RORC               # Shift right 1 bit (= 4 bit shift)
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#
#   RORC ("rotate right through carry") shifts every bit right one
#   place, moves the old bit 0 into Carry, and fills the new top bit
#   (bit 7) from whatever Carry held *before* this instruction ran.
#   That incoming Carry value is unpredictable here - it's whatever
#   was left over from earlier arithmetic, not something this code
#   bothers to clear first. So after four RORCs, the top nybble of
#   the result may have genuine leftover carry-chain bits mixed into
#   it, not necessarily zeros.
#
#   Unlike 16e, this version doesn't care. The AND $0F at the end
#   throws away the entire top nybble regardless of what ended up
#   there, keeping only the bottom nybble - which, after four
#   right-shifts, correctly holds the original top nybble of TEMP8.
#   Whatever RORC put in the bits the mask discards simply never
#   matters. That's the whole difference between this version and
#   16e's: 16e controls bit 0 on every pass because it needs the
#   *final* top nybble to already be clean; this version lets bit 7
#   be whatever it wants to be on every pass, because the final AND
#   cleans up after all four passes at once instead of after each one.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - results should
#   match 16c, 16d, and 16e exactly for every key, despite RORC's
#   top-bit fill being unpredictable along the way.
#
# Watch it happen
# -----------------
#   Step through all four RORCs and watch the accumulator's top
#   nybble in the Registers panel end up different-looking after
#   each pass depending on Carry's incoming state - then watch the
#   final AND $0F erase all of that regardless.
#
# Try this next
# ---------------
#   - Deliberately set Carry to 1 before DISPMSN runs (e.g. add a
#     CMPA that's guaranteed to set it) and confirm the displayed
#     nybble is unaffected - proof that AND $0F really does discard
#     whatever landed in the top nybble.
#   - Compare the byte count of all four hex-nybble versions (16c
#     through 16f) - SHR is the shortest, needing no loop and no
#     bit-forcing at all.
# ================================================================

## Lab 3a hex display using RORC instructions

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
DISPMSN:   LDA     [TEMP8]    # Reload ACC with copy of key code
           RORC               # Shift right 1 bit (= 1 bit shift)
           RORC               # Shift right 1 bit (= 2 bit shift)
           RORC               # Shift right 1 bit (= 3 bit shift)
           RORC               # Shift right 1 bit (= 4 bit shift)
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
