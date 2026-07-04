###################################################################
# Name:     FMULT                                                 #
#                                                                 #
# Function: Multiplies two 8-bit unsigned numbers and returns an  #
#           8-bit unsigned result (MS byte of 2-byte result       #
#           is discarded)                                         #
#                                                                 #
# Entry:    Top of stack                                          #
#           Most-significant byte of return address               #
#           Least-significant byte of return address              #
#           Second 8-bit number (multiplicand)                    #
#           First 8-bit number (multiplier)                       #
#                                                                 #
# Exit:     Top of stack                                          #
#           Least-significant byte of result (product)            #
#                                                                 #
# Modifies: Accumulator                                           #
#           Index register                                        #
#                                                                 #
# Size:     Program = 63 bytes                                    #
#           Data    =  5 bytes                                    #
###################################################################

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

#---------------------------------------------------------------------#

