# ================================================================
# 16h_lab3c_bin_display_restructured.asm
# Beboputer Hands-On Tutorial — Lab 3c (binary display, restructured)
#
# The same 8-bit binary display as 16b - relabeled and reorganized,
# with the exact same logic underneath.
#
# What this program does
# -----------------------
#   Behaves identically to 16b: wait for a key, clear the display,
#   show '%', then show that key's raw code as eight binary digits.
#
# How it works
# -------------
#   Put this side by side with 16b and the two are almost the same
#   program - the same BLDX/SHL/JC/DECX/JNZ loop, the same overall
#   shape:
#
#     LOADX:     BLDX    8           # Load X reg with 8
#     LOOP:      LDA     [TEMP8]     # Reload ACC from temp location
#                SHL                 # Shift left 1 bit
#                STA     [TEMP8]     # Store new value in temp location
#                JC      [DISP_1]    # If carry = 1, jump to display a 1
#     DISP_0:    LDA     0           # ... otherwise load acc with 0
#                STA     [MAINDISP]  # ... and store it to main display
#                JMP     [DEALWX]    # ... then go and deal with the X reg
#     DISP_1:    LDA     1           # Load acc with 1
#                STA     [MAINDISP]  # ... and store it to main display
#     DEALWX:    DECX                # Decrement the index register
#                JNZ     [LOOP]      # If X not zero then do next bit
#                JMP     [GETKEY]    # Go back and wait for new key
#
#   Compare this to 16b's version of the same loop and the only real
#   differences are cosmetic: labels renamed (LOADX/DEALWX here vs
#   BLDX's bare instruction and DISPDECX in 16b), and the "go back to
#   GETKEY" jump moved to the bottom of the loop body instead of
#   living under its own DONE label. Every instruction that actually
#   runs, and the order it runs in, is identical.
#
#   This file is a good exercise in reading assembly for behavior
#   rather than appearance: two source files that don't look alike
#   line-for-line can still assemble to functionally (and here,
#   almost byte-for-byte) identical programs. Worth comparing labels
#   and structure against 16b directly to see exactly what changed
#   and what didn't.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - the display should
#   look identical to 16b's for every key you try.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and compare a Step-through of
#   this file against 16b's - the sequence of port writes to $F031
#   should match exactly, key for key.
#
# Try this next
# ---------------
#   - See 16i for this same loop split into two 4-bit passes with a
#     '-' separator in between, grouping the output as "XXXX-XXXX"
#     instead of one unbroken run of 8 digits.
# ================================================================

## Lab 3c - New version of binary display using index (X) reg

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
           LDA     BINMODE    # Load accumulator with bin mode code
           STA     [SIXLEDS]  # Write to port driving six LEDs
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

########## Get and display key codes in binary
## Wait for a key to be pressed
GETKEY:    LDA     [KEYPAD]    # Load ACC from the keypad
           JN      [GETKEY]    # Jump back if no key pressed
           STA     [TEMP8]     # Store ACC in temp location

## Clear display then display the '%' character
CLRDISP:   LDA     CLRCODE     # Load ACC with clear code
           STA     [MAINDISP]  # Clear main display
DISPPERC:  LDA     $25         # Load ACC with ASCII code for '%'
           STA     [MAINDISP]  # Write '%' to main display

## Initialize index register
LOADX:     BLDX    8           # Load X reg with 8

## Loop around writing
LOOP:      LDA     [TEMP8]     # Reload ACC from temp location
           SHL                 # Shift left 1 bit
           STA     [TEMP8]     # Store new value in temp location
           JC      [DISP_1]    # If carry = 1, jump to display a 1
DISP_0:    LDA     0           # ... otherwise load acc with 0
           STA     [MAINDISP]  # ... and store it to main display
           JMP     [DEALWX]    # ... then go and deal with the X reg
DISP_1:    LDA     1           # Load acc with 1
           STA     [MAINDISP]  # ... and store it to main display
DEALWX:    DECX                # Decrement the index register
           JNZ     [LOOP]      # If X not zero then do next bit
           JMP     [GETKEY]    # Go back and wait for new key

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

TEMP8:    .BYTE                # Temp  8-bit (1-byte) location

#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
