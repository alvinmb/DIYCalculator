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
