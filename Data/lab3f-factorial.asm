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
           BLDSP    $EFFF     # Initialize stack pointer

########## Wait for a key between 1 and 5
GETNUM:    LDA     [KEYPAD]   # Load ACC from keypad
           CMPA     $00       # Compare to 0
           JZ      [GETNUM]   # Jump back if key = 0
           CMPA     $05       # Compare to 5
           JC      [GETNUM]   # Jump back if key > 5
           JSR     [FACTOR]   #   else call FACTOR subroutine
           JSR     [DISPBYTE] #   then display value in ACC

########## Now wait for any key, then clear display and do it again  
WAIT:      LDA     [KEYPAD]   # Load ACC from keypad
           JN      [WAIT]     # Jump if no key pressed
CLEAR:     LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Write clear code to main display
           JMP     [GETNUM]   # Jump back and wait for next number

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

########## This is the recursive subroutine called FACTOR
FACTOR:    PUSHA              # Push copy of ACC onto stack
           CMPA     $01       # Compare ACC to 1 
           JNC     [COMEOUT]  # If ACC not > 1 start to come out
           DECA               #   else decrement ACC
           JSR     [FACTOR]   #   then this routine calls itself

COMEOUT:   PUSHA              # Push copy of ACC onto stack
           JSR     [FMULT]    # Multiply two bytes on top of stack
           POPA               # Retrieve 8-bit result
           RTS                # End this instantiation of the routine 
########## End of FACTOR
#---------------------------------------------------------------------#


#######################################################################
# Name:     FMULT                                                     #
#                                                                     #
# Function: Multiplies two 8-bit unsigned numbers and returns 8-bit   #
#           unsigned result (MS byte of 2-byte result is discarded.   #
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Second 8-bit number (multiplicand)                        #
#           First 8-bit number (multiplier)                           #
#                                                                     #
# Exit:     Top of stack                                              #
#           Least-significant byte of result (product)                #
#                                                                     #
# Modifies: Accumulator                                               #
#           Index register                                            #
#                                                                     #
# Size:     Program = 63 bytes                                        #
#           Data    =  5 bytes                                        #
#######################################################################

########## Store return address
FMULT:     POPA               # Retrieve MS byte of return
           STA  [_FM_RADD]    # address from stack and store it
           POPA               # Retrieve LS byte of return
           STA  [_FM_RADD+1]  # address from stack and store it

           POPA               # Retrieve multiplicand from stack
           STA  [_FM_MAND]    # and store it
           POPA               # Retrieve multiplier from stack
           STA  [_FM_RES+1]   # and store it in LS byte of result
           LDA   0            # Load the accumulator with 0 and
           STA  [_FM_RES]     # store it in the MS byte of result

########## Perform housekeeping tasks and get ready to multiply
_FM_INIT:  BLDX  9            # Load X reg no. of cycles + 1
           ADD   0            # Dummy inst. to set C flag to 0

########## Do the main multiplication loop
_FM_LOOP:  LDA  [_FM_RES]     # Load MS byte of the result
                              #   This doesn't affect the carry flag
           JNC  [_FM_SHFT]    # If carry=0, perform shift
           ADD  [_FM_MAND]    #   .. else add the multiplicand

########## Shift (using rotates) 2-byte result 1 bit to the right
_FM_SHFT:  RORC               # Rotate MS byte of result 1-bit right
           STA  [_FM_RES]     #   and store it
           LDA  [_FM_RES+1]   # Load LS byte of result
           RORC               # Rotate LS byte of result 1-bit right. 
           STA  [_FM_RES+1]   #   and store it

########## Test for end of multiplication
_FM_TST:   DECX               # Decrement the X register
           JNZ  [_FM_LOOP]    # Jump if X reg isn’t 0

########## Store LS byte of result on stack (discard MS byte) 
_FM_SRES:  LDA  [_FM_RES+1]   # Load ACC with LS byte of result
           PUSHA              #   and store it on the stack

########## Retrieve return address and exit routine
_FM_GRET:  LDA  [_FM_RADD+1]  # Load ACC with LS return address
           PUSHA              #   and store it on the stack
           LDA  [_FM_RADD]    # Load ACC with MS return address
           PUSHA              #   and store it on the stack
           RTS                # That’s all folks (exit the routine)

########## Temp storage loactions for thsi routine
_FM_RADD: .2BYTE              # 2-byte location for return address
_FM_MAND: .BYTE               # 1-byte temp location for multiplicand
_FM_RES:  .2BYTE              # 2-byte temp location for result

########## End of FMULT
#---------------------------------------------------------------------#


########## Subroutine to extract/display MS and LS nybbles of byte
DISPBYTE:  PUSHA              # Push a copy of ACC onto stack

########## Display a dollar character
DISPDOL:   LDA   $24          # Load ACC with ASCII code for '$'
           STA  [MAINDISP]    # Load ACC with MS return address

########## Extract and display the most-significant nybble
DISPMSN:   POPA               # Retrieve copy of ACC from stack
           PUSHA              # And push a copy back for later
           SHR                # Shift right 1 bit (= 1 bit shift)
           SHR                # Shift right 1 bit (= 2 bit shift)
           SHR                # Shift right 1 bit (= 3 bit shift)
           SHR                # Shift right 1 bit (= 4 bit shift)
           AND     %00001111  # Clear MS 4 bits (not really necessary)
           STA     [MAINDISP] # Copy result to main display

########## Extract and display the least-significant nybble
DISPLSN:   POPA               # Pop copy of original byte off stack
           AND     %00001111  # Mask out (clear) MS nybble
           STA     [MAINDISP] # Copy result to main display
           RTS                # Return from subroutine

########## End of DISPBYTE
#---------------------------------------------------------------------#

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
