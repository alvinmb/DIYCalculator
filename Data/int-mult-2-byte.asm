#######################################################################
# Name:     _MULT                                                     #
#                                                                     #
# Function: Multiply two 16-bit signed binary numbers together and    #
#           return a 16-bit result in the range -32,767 to +32,767    #
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Most-significant byte of second number  (multiplicand)    #
#           Least-significant byte of second number (multiplicand)    #
#           Most-significant byte of first number   (multiplier)      #
#           Least-significant byte of first number  (multiplier)      #
#                                                                     #
# Exit:     Top of stack                                              #
#           Most-significant byte of result         (product)         #
#           Least-significant byte of result        (product)         #
#                                                                     #
# Modifies: Accumulator and Index Register                            #
#                                                                     #
# Size:     Program = 211 bytes                                       #
#           Data    =   9 bytes                                       #
#######################################################################

########## Get return address from stack and store it
_MULT:     POPA                 # Retrieve MS byte of return
           STA     [_ML_RADD+0] #   address from stack and store it
           POPA                 # Retrieve LS byte of return
           STA     [_ML_RADD+1] #   address from stack and store it

########## Get multiplicand from stack and store it
_ML_GMAN:  POPA                 # Retrieve MS byte of multiplicand
           STA     [_ML_MAND+0] #   from stack and store it
           POPA                 # Retrieve LS byte of multiplicand
           STA     [_ML_MAND+1] #   from stack and store it

########## Get multiplier from stack and store it
_ML_GMUL:  LDA      $00         # Load ACC with 0 and save it to
           STA     [_ML_RES+0]  #   the two MS bytes of the
           STA     [_ML_RES+1]  #   4-byte result
           POPA                 # Retrieve MS byte of multiplier
           STA     [_ML_RES+2]  #   from stack and store it
           POPA                 # Retrieve LS byte of multiplier
           STA     [_ML_RES+3]  #   from stack and store it

########## Invert multiplicand if necessary (store sign in flag)
_ML_IMAN:  LDA     [_ML_MAND+0] # Load ACC with MS multiplicand
           STA     [_ML_FLAG]   #   and store a copy in the flag
           JNN     [_ML_IMUL]   # If positive value, jump to next test
                                #   ... otherwise ...
           LDA      $00         # Load ACC with 0
           SUB     [_ML_MAND+1] #   Subtract (no carry) LS byte of 
           STA     [_ML_MAND+1] #   multiplicand and store the result
           LDA      $00         # Load ACC with 0
           SUBC    [_ML_MAND+0] #   Subtract (with carry) MS byte of 
           STA     [_ML_MAND+0] #   multiplicand and store the result

########## Invert multiplier if necessary (XOR sign in flag)
_ML_IMUL:  LDA     [_ML_FLAG]   # Load the flag
           XOR     [_ML_RES+2]  #   XOR it with MS byte of multiplier
           AND      %10000000   #   Clear bits (except sign) to 0
           STA     [_ML_FLAG]   #   Store the flag away again
           LDA     [_ML_RES+2]  # Load ACC with MS multiplier
           JNN     [_ML_DUMY]   # If positive value, jump to next part
                                #   ... otherwise ...
           LDA      $00         # Load ACC with 0
           SUB     [_ML_RES+3]  #   Subtract (no carry) LS byte of 
           STA     [_ML_RES+3]  #   multiplier and store the result
           LDA      $00         # Load ACC with 0
           SUBC    [_ML_RES+2]  #   Subtract (with carry) MS byte of 
           STA     [_ML_RES+2]  #   multiplier and store the result

########## Dummy instruction to ensure the carry flag contains 0
_ML_DUMY:  ADD      $00         # Add 0 to ACC (will clear C to 0)

########## Hold tight - this is the start of the multiplication loop
           BLDX      17         # Load index reg with the number of
                                # times we want to go around loop + 1
_ML_DOIT:  JNC     [_ML_ROT]    # If carry = 0, jump to next rotate
           LDA     [_ML_RES+1]  #   otherwise add the 16-bit  
           ADD     [_ML_MAND+1] #   multiplicand to the MS 16-bits
           STA     [_ML_RES+1]  #   of the result
           LDA     [_ML_RES+0]  #    :
           ADDC    [_ML_MAND+0] #    :
           STA     [_ML_RES+0]  #    :

_ML_ROT:   LDA     [_ML_RES+0]  # Rotate the 4-byte (32-bit) result
           RORC                 #   one bit to the right. Start with
           STA     [_ML_RES+0]  #   the MS byte: _ML_RES+0
           LDA     [_ML_RES+1]  # Now do _ML_RES+1
           RORC                 #    :
           STA     [_ML_RES+1]  #    :
           LDA     [_ML_RES+2]  # Now do _ML_RES+2
           RORC                 #    :
           STA     [_ML_RES+2]  #    :
           LDA     [_ML_RES+3]  # Now do _ML_RES+3
           RORC                 #    :
           STA     [_ML_RES+3]  #    :

_ML_ELUP:  DECX                 # Decrement the index register
           JNZ     [_ML_DOIT]   # If not zero, then do another loop

########## Check that the result is less than/equal to 32,767
_ML_CHK:   LDA     [_ML_RES+0]  # Load MS byte of result
           JNZ     [_ML_ERR]    #   If not zero, jump to display error
           LDA     [_ML_RES+1]  # Load next byte of result
           JNZ     [_ML_ERR]    #   If not zero, jump to display error
           LDA     [_ML_RES+2]  # Load next byte of result
           JNN     [_ML_SIGN]   #   Jump if MS bit = 0

_ML_ERR:   BLDX     MSG_005     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine
                                # (which terminates the program)

########## Check the flag to see if we have to negate the result
_ML_SIGN:  LDA     [_ML_FLAG]   # Load the flag byte
           JNN     [_ML_SAVE]   # Jump if MS bit = 0
           LDA      $00         #   Otherwise invert LS two bytes
           SUB     [_ML_RES+3]  #   of the result by subtracting
           STA     [_ML_RES+3]  #   them from zero
           LDA      $00         #    :
           SUBC    [_ML_RES+2]  #    :
           STA     [_ML_RES+2]  #    :

########## Save the LS two bytes of the 4-byte result on the stack
_ML_SAVE:  LDA     [_ML_RES+3]  # Load ACC with LS byte of 2-byte
           PUSHA                #   result and push it onto the stack
           LDA     [_ML_RES+2]  # Load ACC with MS byte of 2-byte
           PUSHA                #   result and push it onto the stack

########## Return to main program
_ML_RET:   LDA     [_ML_RADD+1] # Load ACC with LS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           LDA     [_ML_RADD]   # Load ACC with MS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           RTS                  # That's it, exit the subroutine

########## Reserve temp locations for this subroutine
_ML_RADD: .2BYTE                # Reserve 2-byte temp location for
                                #   the return address
_ML_MAND: .2BYTE                # Reserve 2-byte temp location for
                                #   the multiplicand
_ML_RES:  .4BYTE                # Reserve 4-byte temp location for
                                #   the result (product)
_ML_FLAG: .BYTE                 # Reserve 1-byte to use as a flag
########## This is the end of the _MULT subroutine

#---------------------------------------------------------------------#
