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

           BLDX    0          # Load index register with 0
           BLDSP   $EFFF      # Load stack pointer with $EFFF
OUTSIDE:   JSR     [REVERSE]  # Call the subroutine
FINISH:    JMP     [$0000]    # Terminate the program

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

########## Recursive subroutine to display string in reverse order
REVERSE:   LDA     [PHRASE,X] # Load ACC with a character
           JNZ     [GOIN]     # If it's not NUL jump to GO_IN
RETURN1:   RTS                # Otherwise return from subroutine

########## Store the character on the stack and go further in
GOIN:      PUSHA              # Push the character onto the stack
           INCX               # Increment the index register
INSIDE:    JSR     [REVERSE]  # The subroutine calls itself recursively

########## Retrieve and display a character and come out
COMEOUT:   POPA               # Pop a character off the stack
           STA     [MAINDISP] # Copy to main display
RETURN2:   RTS                # Return from subroutine

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

PHRASE:   .BYTE $53, $57, $41, $50, $20
           #      S    W    A    P  SPACE

          .BYTE $50, $41, $57, $53, $00
           #      P    A    W    S  NUL

#######################################################################
## End of global data                                                ##
#######################################################################

          .END
                # That's all folks
