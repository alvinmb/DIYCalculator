## Lab 3d - Display hex chars in reverse order using the stack

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

########## Initialize the stack pointer
           BLDSP   $EFFF       # Load stack pointer with $EFFF

########## Wait for key to be pressed
GETKEY:    NOP                 # “No operation” - see notes
LOOP:      LDA     [KEYPAD]    # Load ACC from the keypad
           JN      [LOOP]      # Jump back if no key pressed
           CMPA    $0F         # Compare ACC to $0F
           JC      [DISPSTUF]  # Jump if ACC is bigger
           PUSHA               # ... else push ACC onto the stack
           JMP     [GETKEY]    # Go and wait for another key

########## Display a number
DISPSTUF:  POPA                # Pop ACC off the stack
           STA     [MAINDISP]  # Store it to the main display
           JMP     [GETKEY]    # Go and wait for another key

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

#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
