# ================================================================
# 16i_lab3c_bin_display_nibble_dash.asm
# Beboputer Hands-On Tutorial — Lab 3c (binary display, nybble
# groups with a dash separator)
#
# Show a key's raw code as two groups of 4 binary digits with a
# '-' between them, instead of 8 digits running together.
#
# What this program does
# -----------------------
#   Waits for a key, clears the display, shows '%', then shows the
#   key's raw code as "XXXX-XXXX" - four binary digits, a dash, then
#   four more - instead of 16h's unbroken run of eight digits.
#
# How it works
# -------------
#   This takes 16h's single 8-count loop and splits it into two
#   separate 4-count loops with a dash written in between:
#
#     LOADXA:    BLDX    4           # Load X reg with 4
#     LOOPA:     LDA     [TEMP8]     # Reload ACC from temp location
#                SHL                 # Shift left 1 bit
#                STA     [TEMP8]     # Store new value in temp location
#                JC      [DISP_1A]   # If carry = 1, jump to display a 1
#     DISP_0A:   LDA     0           # ... otherwise load acc with 0
#                STA     [MAINDISP]  # ... and store it to main display
#                JMP     [DEALWXA]   # ... then go and deal with the X reg
#     DISP_1A:   LDA     1           # Load acc with 1
#                STA     [MAINDISP]  # ... and store it to main display
#     DEALWXA:   DECX                # Decrement the index register
#                JNZ     [LOOPA]     # If X not zero then do next bit
#
#     DISPDASH:  LDA     $2D         # Load ACC with ASCII code for '-'
#                STA     [MAINDISP]  # ... and store it to main display
#
#   ... followed by a second, near-identical loop (LOOPB/DEALWXB)
#   that displays the remaining 4 bits the same way. TEMP8 is shared
#   between both halves - it isn't reset in between - so LOOPA
#   naturally consumes the top 4 bits (shifting them out via SHL just
#   like every earlier version in this series) and LOOPB picks up
#   exactly where LOOPA left off, displaying the bottom 4 bits.
#
#   Notice LOOPA and LOOPB are two separate copies of the same
#   four-line loop body, each with its own labels (the 'A' and 'B'
#   suffixes) - a small, deliberate bit of duplication rather than
#   one shared loop, presumably because writing the dash needs to
#   happen exactly once, in between the two halves, rather than
#   being something a single unified loop could express cleanly with
#   just a counter. It's a reasonable trade: two copies of a short
#   loop instead of one loop with an awkward "am I halfway done yet"
#   check bolted on.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - the display shows
#   the same 8 bits as 16h/16b would, but grouped as "XXXX-XXXX".
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and watch $F031 receive four
#   digits, then $2D (the dash), then four more digits - compare the
#   timing against 16h, which writes eight digits with no pause.
#
# Try this next
# ---------------
#   - Try merging LOOPA and LOOPB into one loop that runs 8 times and
#     writes a dash exactly when the counter reaches 4 - is the
#     result shorter or longer than keeping two separate loops?
# ================================================================

## Lab 3c - New version of binary display using index (X) reg
##          Also display '-' between MS and LS nybbles

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

## Display MS Nybble
LOADXA:    BLDX    4           # Load X reg with 4
LOOPA:     LDA     [TEMP8]     # Reload ACC from temp location
           SHL                 # Shift left 1 bit
           STA     [TEMP8]     # Store new value in temp location
           JC      [DISP_1A]   # If carry = 1, jump to display a 1
DISP_0A:   LDA     0           # ... otherwise load acc with 0
           STA     [MAINDISP]  # ... and store it to main display
           JMP     [DEALWXA]   # ... then go and deal with the X reg
DISP_1A:   LDA     1           # Load acc with 1
           STA     [MAINDISP]  # ... and store it to main display
DEALWXA:   DECX                # Decrement the index register
           JNZ     [LOOPA]     # If X not zero then do next bit

## Display a dash character
DISPDASH:  LDA     $2D         # Load ACC with ASCII code for '-'
           STA     [MAINDISP]  # ... and store it to main display

## Display MS Nybble
LOADXB:    BLDX    4           # Load X reg with 4
LOOPB:     LDA     [TEMP8]     # Reload ACC from temp location
           SHL                 # Shift left 1 bit
           STA     [TEMP8]     # Store new value in temp location
           JC      [DISP_1B]   # If carry = 1, jump to display a 1
DISP_0B:   LDA     0           # ... otherwise load acc with 0
           STA     [MAINDISP]  # ... and store it to main display
           JMP     [DEALWXB]   # ... then go and deal with the X reg
DISP_1B:   LDA     1           # Load acc with 1
           STA     [MAINDISP]  # ... and store it to main display
DEALWXB:   DECX                # Decrement the index register
           JNZ     [LOOPB]     # If X not zero then do next bit

## Do it all again
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

          .END
                # That's all folks
