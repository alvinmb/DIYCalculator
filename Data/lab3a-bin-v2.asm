## Lab 3a binary display using the index (X) register

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

########## Wait for key to be pressed
GETKEY:    LDA     [KEYPAD]   # Load ACC with code from keypad
           JN      [GETKEY]   # Jump back if no key pressed
           STA     [TEMP8]    # Store key code in temp location

########## Prepare the main display
CLRDISP:   LDA     CLRCODE    # Load ACC with clear code
           STA     [MAINDISP] # Clear main display
DISPPERC:  LDA     $25        # Load ACC with ASCII code for '%'
           STA     [MAINDISP] # Write '%' to main display

########## Display the binary value
           BLDX    8          # Load X reg with number of bits
LOOP:      LDA     [TEMP8]    # Reload ACC with copy of key code
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP_1]   # If carry = 1, jump to display a 1
DISP_0:    LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [DISPDECX] # ... then go and decrement the X reg
DISP_1:    LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display
DISPDECX:  DECX               # Decrement the X reg
           JNZ     [LOOP]     # If not zero jump back for next bit

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

          .END
                # That's all folks
