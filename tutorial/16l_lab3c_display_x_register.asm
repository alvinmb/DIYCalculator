# ================================================================
# 16l_lab3c_display_x_register.asm
# Beboputer Hands-On Tutorial — Lab 3c (display the Index register
# itself)
#
# Count hex-digit keypresses with the Index register, then display
# the register's own numeric value - as 4 hex digits - instead of
# the keys that were typed.
#
# What this program does
# -----------------------
#   Reads hex-digit keys ($00-$0F, same acceptance test as 16j/16k)
#   and counts them using the Index register - but never stores the
#   individual key values anywhere. The moment a non-hex key is
#   pressed, it shows the *count* of hex digits that were typed, as
#   a 4-digit hex number after a '$'.
#
# How it works
# -------------
#   The fill phase looks almost identical to 16k's, with one telling
#   difference - notice there's no STA [STORE,X] anywhere:
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
#   The keys still get written into STORE (this file borrows the
#   fill loop unchanged), but nothing ever reads STORE back out -
#   this program only cares about X's final count, not the values it
#   counted. That count can run past 255, since the Index register is
#   16 bits wide - something a plain 8-bit accumulator or TEMP8 byte
#   could never hold - and this exercise is specifically about
#   getting that 16-bit value onto an 8-bit-wide display:
#
#     DISPSTUF:  BSTX    [TEMP16]    # Store X reg into 2-byte temp location
#                LDA     $24         # Load ACC with ASCII code for '$'
#                STA     [MAINDISP]  # Write '$' to main display
#
#     DSMSNMSB:  LDA     [TEMP16]    # Load ACC with MS byte from X reg
#                SHR / SHR / SHR / SHR
#                AND     %00001111   # Clear MS 4 bits
#                STA     [MAINDISP]  # Copy result to main display
#
#     DSLSNMSB:  LDA     [TEMP16]    # Reload ACC with MS byte from X reg
#                AND     %00001111   # Mask out (clear) MS nybble
#                STA     [MAINDISP]  # Copy result to main display
#
#   BSTX ("store X register") is the write counterpart to BLDX - it
#   copies the 16-bit Index register out to a 2-byte memory location
#   in one instruction, here TEMP16. From there, showing the count as
#   hex is exactly the SHR + AND nybble-splitting technique 16c uses,
#   just repeated four times instead of twice: once each for the
#   MS and LS nybbles of TEMP16's high byte (DSMSNMSB/DSLSNMSB), then
#   again for TEMP16+1, its low byte (DSMSNLSB/DSLSNLSB) - four
#   nybbles, four hex digits, one 16-bit number.
#
#   Compare this directly against 16k: both programs count typed hex
#   keys with the exact same fill loop, but 16k displays *what* was
#   typed (in reverse), while this one displays *how many* keys were
#   typed (as a 4-digit hex count) - the same raw ingredients, put
#   to two very different uses.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, switch to Hex mode, type a
#   dozen or so hex digits, then press an operator key - the display
#   shows something like "$000C" (12 in hex), the count of digits
#   you typed, not the digits themselves.
#
# Watch it happen
# -----------------
#   Open Registers and watch the Index register count up while
#   typing, then open Memory and watch TEMP16 receive that same
#   16-bit value in one step when BSTX executes.
#
# Try this next
# ---------------
#   - Type more than 255 hex digits before stopping and confirm the
#     4-digit hex count correctly shows a value like $0105 - something
#     an 8-bit BSTX target never could have held.
# ================================================================

## Lab 3c - Demo of how to display contents of the index (X) register

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

########## Display the value in the index register
DISPSTUF:  BSTX    [TEMP16]    # Store X reg into 2-byte temp location
           LDA     $24         # Load ACC with ASCII code for '$'
           STA     [MAINDISP]  # Write '$' to main display

########## Extract/display MS nybble of MS byte
DSMSNMSB:  LDA     [TEMP16]    # Load ACC with MS byte from X reg
           SHR                 # Shift right 1 bit (= 1 bit shift)
           SHR                 # Shift right 1 bit (= 2 bit shift)
           SHR                 # Shift right 1 bit (= 3 bit shift)
           SHR                 # Shift right 1 bit (= 4 bit shift)
           AND     %00001111   # Clear MS 4 bits
           STA     [MAINDISP]  # Copy result to main display

########## Extract/display LS nybble of MS byte
DSLSNMSB:  LDA     [TEMP16]    # Reload ACC with MS byte from X reg
           AND     %00001111   # Mask out (clear) MS nybble
           STA     [MAINDISP]  # Copy result to main display

########## Extract/display MS nybble of LS byte
DSMSNLSB:  LDA     [TEMP16+1]  # Load ACC with LS byte from X reg
           SHR                 # Shift right 1 bit (= 1 bit shift)
           SHR                 # Shift right 1 bit (= 2 bit shift)
           SHR                 # Shift right 1 bit (= 3 bit shift)
           SHR                 # Shift right 1 bit (= 4 bit shift)
           AND     %00001111   # Clear MS 4 bits
           STA     [MAINDISP]  # Copy result to main display

########## Extract/display LS nybble of LS byte
DSLSNLSB:  LDA     [TEMP16+1]  # Reload ACC with LS byte from X reg
           AND     %00001111   # Mask out (clear) MS nybble
           STA     [MAINDISP]  # Copy result to main display

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
