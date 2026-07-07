# ================================================================
# 16n_lab3e_nested_subroutines.asm
# Beboputer Hands-On Tutorial — Lab 3e (nested subroutines)
#
# Display four fixed bytes as hex, using one subroutine that calls
# two more subroutines to do the actual work.
#
# What this program does
# -----------------------
#   On its own, with no keypad interaction at all, shows four
#   pre-loaded byte values ($23, $5A, $06, $4C) as hex digit pairs,
#   one after another, then stops.
#
# How it works
# -------------
#   The main body just loads each byte and calls one subroutine four
#   times:
#
#     LDA     [TEMP]     # Load 1st byte into ACC
#     JSR     [DISPBYTE] # Call display byte subroutine
#     LDA     [TEMP+1]   # Load 2nd byte into ACC
#     JSR     [DISPBYTE] # Call display byte subroutine
#     ... (and so on for TEMP+2, TEMP+3)
#     JMP     [$0000]    # Terminate the program
#
#   JSR/RTS were introduced back in exercise 12 for calling one
#   shared subroutine from three different places. This exercise
#   goes a step further: DISPBYTE isn't one flat block of code - it's
#   a short subroutine that itself calls two *more* subroutines:
#
#     DISPBYTE:  PUSHA              # Push a copy of ACC onto stack
#                JSR     [DISPMSN]  # Call sub for MS nybble
#                POPA               # Pop copy of original byte off stack
#                JSR     [DISPLSN]  # Call sub for LS nybble
#                RTS                # Return to calling location
#
#     DISPMSN:   SHR / SHR / SHR / SHR
#                AND     %00001111  # Clear MS 4 bits (not really necessary)
#                STA     [MAINDISP] # Copy result to main display
#                RTS                # Return to calling location
#
#     DISPLSN:   AND     %00001111  # Mask out (clear) MS nybble
#                STA     [MAINDISP] # Copy result to main display
#                RTS                # Return to calling location
#
#   DISPMSN's four SHRs are destructive - they consume the
#   accumulator's original value while pulling the high nybble down
#   (the same technique 16c uses). By the time DISPMSN returns, the
#   byte's original bits are gone from ACC. That's exactly why
#   DISPBYTE pushes a copy *before* calling DISPMSN, and pops it back
#   *after* - so the original, untouched byte is sitting in ACC again
#   when DISPLSN is called to extract the low nybble from it. Without
#   that PUSHA/POPA pair, DISPLSN would be masking whatever DISPMSN
#   left behind instead of the real byte.
#
#   Three levels of calling happen here: the main body calls
#   DISPBYTE, and DISPBYTE calls DISPMSN and then DISPLSN. Each JSR
#   pushes a return address on the stack (see exercise 12's note on
#   JSR/RTS), and each RTS pops the most recent one - so the calls
#   unwind in the reverse order they were made, same as any nested
#   function calls in a higher-level language.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - the display shows "23 5A 06 4C"
#   as it processes all four bytes (no separators between pairs,
#   since DISPBYTE never writes one - watch closely, or use Step, to
#   see each pair land).
#
# Watch it happen
# -----------------
#   Open Registers and watch the stack pointer drop by 2 on each JSR
#   and rise by 2 on each RTS, and by 1 more on each PUSHA/POPA -
#   Step through one full DISPBYTE call and count exactly how deep
#   the stack gets before it's all unwound back to where it started.
#
# Try this next
# ---------------
#   - See 16o for the same net result with DISPMSN and DISPLSN
#     folded directly into DISPBYTE as fall-through labels instead of
#     separately JSR'd subroutines - same output, different internal
#     structure.
# ================================================================

## Lab 3e using a nested subroutine

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
           JSR     [DISPMSN]  # Call sub for MS nybble
           POPA               # Pop copy of original byte off stack
           JSR     [DISPLSN]  # Call sub for LS nybble
           RTS                # Return to calling location

########## Subroutine to extract/display the MS nybble
DISPMSN:   SHR                # Shift right 1 bit (= 1 bit shift)
           SHR                # Shift right 1 bit (= 2 bit shift)
           SHR                # Shift right 1 bit (= 3 bit shift)
           SHR                # Shift right 1 bit (= 4 bit shift)
           AND     %00001111  # Clear MS 4 bits (not really necessary)
           STA     [MAINDISP] # Copy result to main display
           RTS                # Return to calling location

########## Extract and display the LS nybble
DISPLSN:   AND     %00001111  # Mask out (clear) MS nybble
           STA     [MAINDISP] # Copy result to main display
           RTS                # Return to calling location

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
