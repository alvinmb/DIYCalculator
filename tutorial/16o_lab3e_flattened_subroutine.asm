# ================================================================
# 16o_lab3e_flattened_subroutine.asm
# Beboputer Hands-On Tutorial — Lab 3e (one flattened subroutine)
#
# The same four-byte hex display as 16n - with DISPMSN and DISPLSN
# folded into DISPBYTE as fall-through labels instead of separately
# called subroutines.
#
# What this program does
# -----------------------
#   Identical behavior to 16n: shows four pre-loaded bytes ($23,
#   $5A, $06, $4C) as hex digit pairs, then stops. The main body
#   calling DISPBYTE four times is unchanged.
#
# How it works
# -------------
#   16n's DISPBYTE made two separate JSR calls, one to DISPMSN and
#   one to DISPLSN, each with its own RTS. This version keeps the
#   same three label names, but only one of them is a real "callable"
#   entry point anymore - the other two are just waypoints inside a
#   single subroutine that falls straight through from one to the
#   next:
#
#     DISPBYTE:  PUSHA              # Push a copy of ACC onto stack
#
#     DISPMSN:   SHR                # Shift right 1 bit (= 1 bit shift)
#                SHR                # Shift right 1 bit (= 2 bit shift)
#                SHR                # Shift right 1 bit (= 3 bit shift)
#                SHR                # Shift right 1 bit (= 4 bit shift)
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#
#     DISPLSN:   POPA               # Pop copy of original byte off stack
#                AND     %00001111  # Mask out (clear) MS nybble
#                STA     [MAINDISP] # Copy result to main display
#                RTS                # Return from subroutine
#
#   There's no JSR anywhere in this block, and no RTS until the very
#   end. DISPMSN and DISPLSN are still labels - useful for reading
#   the code and for referring to "the bit that handles the MS
#   nybble" versus "the bit that handles the LS nybble" - but nothing
#   ever jumps to them from outside DISPBYTE. Execution simply falls
#   from the last instruction under DISPBYTE straight into DISPMSN's
#   first instruction, and from DISPMSN's last instruction straight
#   into DISPLSN's, with no jump or call involved at either boundary.
#
#   This is the same PUSHA-before/POPA-after pattern 16n uses to
#   protect the original byte across the destructive SHR chain - the
#   *data flow* is identical between the two versions. What changed
#   is purely structural: 16n expresses "do the MS nybble, then do
#   the LS nybble" as two subroutine calls from a third subroutine;
#   this version expresses the exact same two steps as one
#   subroutine with internal signposts. Both compile down to running
#   the same instructions in the same order - the only difference is
#   whether DISPMSN and DISPLSN could, in principle, be called from
#   somewhere else too (16n's version, yes; this version, no - RTS
#   only appears once, at the very end).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - output should be identical to
#   16n's: "23 5A 06 4C".
#
# Watch it happen
# -----------------
#   Step through one call to DISPBYTE and watch the Program Counter
#   in the Registers panel - it moves smoothly from DISPBYTE's last
#   instruction into DISPMSN's first, and from DISPMSN's last into
#   DISPLSN's first, with no jump instruction executing at either
#   handoff (contrast this with 16n, where the PC visibly jumps to a
#   JSR target and back at each of those same two points).
#
# Try this next
# ---------------
#   - Try calling DISPMSN directly (JSR [DISPMSN]) from somewhere
#     else in a copy of this file and see what goes wrong - without
#     its own RTS, it will fall straight through into DISPLSN and pop
#     a stack value that was never pushed for it, rather than
#     returning to the caller.
# ================================================================

## Lab 3e using a simple subroutine

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
           BLDSP   $EFFF      # Load stack pointer with $EFFF
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

           LDA     [TEMP]     # Load 1st byte into ACC
           JSR     [DISPBYTE] # Call display byte subroutine
           LDA     [TEMP+1]   # Load 2nd byte into ACC
           JSR     [DISPBYTE] # Call display byte subroutine
           LDA     [TEMP+2]   # Load 3rd byte into ACC
           JSR     [DISPBYTE] # Call display byte subroutine
           LDA     [TEMP+3]   # Load 4th byte into ACC
           JSR     [DISPBYTE] # Call display byte subroutine
           JMP     [$0000]    # Terminate the program

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

########## Subroutine to extract/display MS and LS nybbles of byte
DISPBYTE:  PUSHA              # Push a copy of ACC onto stack

########## Extract and display the most-significant nybble
DISPMSN:   SHR                # Shift right 1 bit (= 1 bit shift)
           SHR                # Shift right 1 bit (= 2 bit shift)
           SHR                # Shift right 1 bit (= 3 bit shift)
           SHR                # Shift right 1 bit (= 4 bit shift)
           AND     %00001111  # Clear MS 4 bits (not really necessary)
           STA     [MAINDISP] # Copy result to main display

########## Extract and display the least-significant nybble
DISPLSN:   POPA               # Pop copy of original byte off stack
           AND     %00001111  # Mask out (clear) MS nybble
           STA     [MAINDISP] # Copy result to main display
           RTS                # Return from subroutine

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

TEMP:     .BYTE $23, $5A, $06, $4C  # Just some data to play with

#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
