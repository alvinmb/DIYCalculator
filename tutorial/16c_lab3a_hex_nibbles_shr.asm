# ================================================================
# 16c_lab3a_hex_nibbles_shr.asm
# Beboputer Hands-On Tutorial — Lab 3a (hex display, SHR version)
#
# Display a key's raw code as two hex digits, extracting the
# most-significant nybble with four SHR instructions.
#
# What this program does
# -----------------------
#   Waits for any key, clears the display, writes a '$' (this
#   project's convention for "what follows is hex," the same one
#   tutorial 14 uses), then shows that key's raw code as two hex
#   digit characters. Then it waits for the next key and repeats.
#
# How it works
# -------------
#   Two nybbles, two ways of getting them - and this version's most
#   significant nybble extraction is about as simple as it gets:
#
#     DISPMSN:   LDA     [TEMP8]    # Reload ACC with copy of key code
#                SHR                # Shift right 1 bit (= 1 bit shift)
#                SHR                # Shift right 1 bit (= 2 bit shift)
#                SHR                # Shift right 1 bit (= 3 bit shift)
#                SHR                # Shift right 1 bit (= 4 bit shift)
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#
#   SHR shifts every bit right one place and fills the vacated top
#   bit with 0 - do that four times and the byte's top nybble has
#   slid down into the bottom nybble, with zeros above it. The
#   trailing AND $0F is (as the comment admits) not strictly needed
#   here, since four SHRs on an 8-bit byte already leave the top
#   nybble as zero - but it's cheap insurance, and it matches the
#   pattern used for the least-significant nybble right below it:
#
#     DISPLSN:   LDA     [TEMP8]    # Reload ACC with copy of key code
#                AND     %00001111  # Mask out (clear) MS nybble
#                STA     [MAINDISP] # Copy result to main display
#
#   No shifting needed for the low nybble - it's already sitting in
#   the bottom 4 bits, so a single AND is enough to blank out the top
#   nybble before displaying it. This exact SHR + AND nybble-split is
#   the same technique tutorial 14's hex/bin conversion tutorial uses
#   to turn a 4-bit binary value back into a hex digit character.
#
#   This tutorial and the next three (16d, 16e, 16f) all extract the
#   exact same most-significant nybble, from the exact same byte,
#   and display the exact same result - only the instruction used to
#   do the shifting changes. Compare them side by side to see how
#   much (or how little) extra bookkeeping each approach costs.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press any key - its raw code
#   appears as two hex digits after a '$'.
#
# Watch it happen
# -----------------
#   Step through DISPMSN and watch the accumulator in the Registers
#   panel shift right one nybble's worth over the four SHRs.
#
# Try this next
# ---------------
#   - Compare against 16d (SHL + manual carry reinsertion), 16e
#     (ROLC + explicit bit0 override), and 16f (RORC, no manual
#     bit-forcing needed at all) - four different roads to the same
#     nybble.
# ================================================================

## Lab 3a hex display using SHR instructions

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
           SHR                # Shift right 1 bit (= 1 bit shift)
           SHR                # Shift right 1 bit (= 2 bit shift)
           SHR                # Shift right 1 bit (= 3 bit shift)
           SHR                # Shift right 1 bit (= 4 bit shift)
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
