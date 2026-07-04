## Lab 3c - Display '0' thru 'F' keys in the reverse order to that in 
##          which they are entered using the index (X) register

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

########## Display the numbers
DISPSTUF:  LDA     [STORE-1,X] # Load ACC with a key code
           STA     [MAINDISP]  # Store it to the main display
           DECX                # Decrement the index register
           JNZ     [DISPSTUF]  # If index reg not 0 get next code
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
