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
