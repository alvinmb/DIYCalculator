# ================================================================
# 16d_lab3a_hex_nibbles_shl.asm
# Beboputer Hands-On Tutorial — Lab 3a (hex display, SHL version)
#
# The same most-significant nybble as 16c - extracted with SHL and a
# manual carry reinsertion trick instead of plain SHR.
#
# What this program does
# -----------------------
#   Identical behavior to 16c: wait for a key, show '$', then show
#   that key's raw code as two hex digits.
#
# How it works
# -------------
#   The least-significant nybble (DISPLSN) is unchanged from 16c -
#   a single AND does the job. The most-significant nybble is where
#   this version does something less obvious:
#
#     DISPMSN:   BLDX     4         # Load X reg with number of shifts
#                LDA     [TEMP8]    # Reload ACC with copy of key code
#     DISPMSNL:  SHL                # Shift left 1 bit
#                JNC     [DISPMSN0] # Jump if carry flag = 0
#                OR      %00000001  #   otherwise set LS bit to 1
#     DISPMSN0:  DECX               # Decrement index register
#                JNZ     [DISPMSNL] # If X !=0 jump back and shift again
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#
#   SHL shifts left and drops the bit that falls off the top edge
#   into Carry - the opposite direction from what you'd want for
#   pulling a high nybble down to the bottom. The trick is what
#   happens right after each shift: whatever bit SHL just discarded
#   into Carry gets manually stuffed back in at the bottom via
#   JNC/OR. Trace it through with TEMP8 = $A7 (1010 0111) and this
#   becomes clear:
#
#       start:  1010 0111
#       SHL #1: 0100 1110, carry=1 -> OR sets bit0: 0100 1111
#       SHL #2: 1001 1110, carry=0 -> no OR:        1001 1110
#       SHL #3: 0011 1100, carry=1 -> OR sets bit0:  0011 1101
#       SHL #4: 0111 1010, carry=0 -> no OR:        0111 1010
#       AND $0F:                                    0000 1010  = $0A
#
#   $A7's top nybble is $A (1010) - and that's exactly what comes
#   out. Four rounds of "shift left, then immediately recycle the
#   bit that fell out back into the bottom" amounts to rotating the
#   whole byte left by four places, done one bit at a time with the
#   carry flag standing in for the "wraparound" a true rotate would
#   handle automatically. BLDX 4 / DECX / JNZ counts the four rounds,
#   the same loop-counting pattern 16b uses for its eight bits.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - results should
#   match 16c exactly for every key.
#
# Watch it happen
# -----------------
#   Step through DISPMSNL four times and watch both the accumulator
#   and the Carry flag in the Registers panel - each pass, whatever
#   bit lands in Carry gets folded straight back into bit 0.
#
# Try this next
# ---------------
#   - See 16e for the same "recycle the bit that fell out" idea done
#     with ROLC instead of a plain SHL, and 16f for the direction
#     (RORC) that needs no manual bit-recycling at all.
# ================================================================

## Lab 3a hex display using SHL instructions

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
DISPMSNL:  SHL                # Shift left 1 bit
           JNC     [DISPMSN0] # Jump if carry flag = 0
           OR      %00000001  #   otherwise set LS bit to 1
DISPMSN0:  DECX               # Decrement index register
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
