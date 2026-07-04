## Lab 3a binary display one painful bit at a time

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
## Process bit 7
TEST7:     LDA     [TEMP8]    # Reload ACC with copy of key code
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP7_1]  # If carry = 1, jump to display a 1
DISP7_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST6]    # ... then go and deal with bit 6
DISP7_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 6
TEST6:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP6_1]  # If carry = 1, jump to display a 1
DISP6_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST5]    # ... then go and deal with bit 5
DISP6_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 5
TEST5:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP5_1]  # If carry = 1, jump to display a 1
DISP5_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST4]    # ... then go and deal with bit 4
DISP5_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 4
TEST4:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP4_1]  # If carry = 1, jump to display a 1
DISP4_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST3]    # ... then go and deal with bit 3
DISP4_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 3
TEST3:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP3_1]  # If carry = 1, jump to display a 1
DISP3_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST2]    # ... then go and deal with bit 2
DISP3_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 2
TEST2:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP2_1]  # If carry = 1, jump to display a 1
DISP2_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST1]    # ... then go and deal with bit 1
DISP2_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

## Process bit 1
TEST1:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP1_1]  # If carry = 1, jump to display a 1
DISP1_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [TEST0]    # ... then go and deal with bit 6
DISP1_1:   LDA     1          # Load acc with 0
           STA     [MAINDISP] # ... and store it to main display

## Process bit 0
TEST0:     LDA     [TEMP8]    # Reload ACC from temp location
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP0_1]  # If carry = 1, jump to display a 1
DISP0_0:   LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [DONE]     # ... then go and deal with bit 6
DISP0_1:   LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display

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
