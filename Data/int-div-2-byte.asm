#######################################################################
# Name:     _DIV                                                      #
#                                                                     #
# Function: Divide one 16-bit signed binary number by another and     #
#           return a 16-bit result in the range -32,767 to +32,767    #
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Most-significant byte of second number  (Divisor)         #
#           Least-significant byte of second number (Divisor)         #
#           Most-significant byte of first number   (Dividend)        #
#           Least-significant byte of first number  (Dividend)        #
#                                                                     #
# Exit:     Top of stack                                              #
#           Most-significant byte of result         (Quotient)        #
#           Least-significant byte of result        (Quotient)        #
#                                                                     #
# Modifies: Accumulator and Index Register                            #
#                                                                     #
# Size:     Program = 298 bytes                                       #
#           Data    =   9 bytes                                       #
#######################################################################

########## Get return address from stack and store it
_DIV:      POPA                 # Retrieve MS byte of return
           STA     [_DV_RADD+0] #   address from stack and store it
           POPA                 # Retrieve LS byte of return
           STA     [_DV_RADD+1] #   address from stack and store it

########## Get divisor from stack and store it
_DV_GDIV:  POPA                 # Retrieve MS byte of divisor
           STA     [_DV_DIV+0]  #   from stack and store it
           POPA                 # Retrieve LS byte of divisor
           STA     [_DV_DIV+1]  #   from stack and store it

########## Check that we're not trying to divide by zero
_DV_CHKZ:  OR      [_DV_DIV+0]  # OR ACC with MS byte of divisor
           JNZ     [_DV_GDND]   # If non-zero, carry on ...
_DV_ERRZ:  BLDX     MSG_007     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine
                                # (which terminates the program)

########## Get dividend from stack and store it
_DV_GDND:  LDA      $00         # Load ACC with 0 and save it to
           STA     [_DV_RES+0]  #   the two MS bytes of the
           STA     [_DV_RES+1]  #   4-byte result
           POPA                 # Retrieve MS byte of dividend
           STA     [_DV_RES+2]  #   from stack and store it
           POPA                 # Retrieve LS byte of dividend
           STA     [_DV_RES+3]  #   from stack and store it

########## Invert divisor if necessary (store sign in flag)
_DV_IDIV:  LDA     [_DV_DIV+0]  # Load ACC with MS divisor
           STA     [_DV_FLAG]   #   and store a copy in the flag
           JNN     [_DV_IDND]   # If positive value, jump to next test
                                #   ... otherwise ...
           LDA      $00         # Load ACC with 0
           SUB     [_DV_DIV+1]  #   Subtract (no carry) LS byte of 
           STA     [_DV_DIV+1]  #   divisor and store the result
           LDA      $00         # Load ACC with 0
           SUBC    [_DV_DIV+0] #   Subtract (with carry) MS byte of 
           STA     [_DV_DIV+0] #   divisor and store the result

########## Invert multiplier if necessary (XOR sign in flag)
_DV_IDND:  LDA     [_DV_FLAG]   # Load the flag
           XOR     [_DV_RES+2]  #   XOR it with MS byte of dividend
           AND      %10000000   #   Clear bits (except sign) to 0
           STA     [_DV_FLAG]   #   Store the flag away again
           LDA     [_DV_RES+2]  # Load ACC with MS dividend
           JNN     [_DV_LOOP]   # If positive value, jump to next part
                                #   ... otherwise ...
           LDA      $00         # Load ACC with 0
           SUB     [_DV_RES+3]  #   Subtract (no carry) LS byte of 
           STA     [_DV_RES+3]  #   dividend and store the result
           LDA      $00         # Load ACC with 0
           SUBC    [_DV_RES+2]  #   Subtract (with carry) MS byte of 
           STA     [_DV_RES+2]  #   dividend and store the result

########## Hold tight - this is the start of the main division loop
_DV_LOOP:  BLDX      16         # Load index reg with the number of
                                # times we want to go around loop
_DV_DOIT:  LDA     [_DV_RES+3]  # Shift the 4-byte (32-bit) result
           SHL                  #   one bit to the left. Start with
           STA     [_DV_RES+3]  #   the LS byte: _DV_RES+3
           LDA     [_DV_RES+2]  # Now do _DV_RES+2
           ROLC                 #   Use a rotate here
           STA     [_DV_RES+2]  #    :
           LDA     [_DV_RES+1]  # Now do _DV_RES+1
           ROLC                 #   Use a rotate here
           STA     [_DV_RES+1]  #    :
           LDA     [_DV_RES+0]  # Now do _DV_RES+0
           ROLC                 #   Use a rotate here
           STA     [_DV_RES+0]  #    :

########## Subtract the divisor from the two MS bytes of the result
_DV_SUB:   LDA     [_DV_RES+1]  # Load ACC with _DV_RES+1
           SUB     [_DV_DIV+1]  #   Subtract (no carry) LS byte of
           STA     [_DV_RES+1]  #   divisor and store result
           LDA     [_DV_RES+0]  # Load ACC with DV_RES+0
           SUBC    [_DV_DIV+0]  #   Subtract (with carry) MS byte of
           STA     [_DV_RES+0]  #   divisor and store result

########## Check to see if we need to add the divisor back in again
_DV_ADD:   JC      [_DV_SET1]   # Jump if carry (borrow) = 1
           LDA     [_DV_RES+1]  # Load ACC with _DV_RES+1
           ADD     [_DV_DIV+1]  #   Add (no carry) LS byte of
           STA     [_DV_RES+1]  #   divisor and store result
           LDA     [_DV_RES+0]  # Load ACC with DV_RES+0
           ADDC    [_DV_DIV+0]  #   Add (with carry) MS byte of
           STA     [_DV_RES+0]  #   divisor and store result
           JMP     [_DV_ELUP]   # Jump to the end of the loop

########## Force the LS bit of the LS result byte to 1
_DV_SET1:  LDA     [_DV_RES+3]  # Load LS byte of result
           OR       %00000001   #   Force LS bit to 1
           STA     [_DV_RES+3]  #   and store it back again

########## Check to see if we're done
_DV_ELUP:  DECX                 # Decrement the index register
           JNZ     [_DV_DOIT]   # If not zero, then do another loop

########## Perform a round-half-even algorithm
_DV_RND:   LDA     [_DV_RES+1]  # Load LS byte of remainder
           SHL                  #   Multiply by two (shift left one
           STA     [_DV_RES+1]  #   bit and store result
           LDA     [_DV_RES+0]  # Repeat for MS byte of remainder
           ROLC                 #   but use a rotate this time
           STA     [_DV_RES+0]  # 

                                # Start by comparing MS bytes
_DV_CPMS:  LDA     [_DV_DIV+0]  # Load ACC with MS divisor
           CMPA    [_DV_RES+0]  # Compare to MS remainder x2 
           JC      [_DV_SIGN]   # Do nothing if divisor is bigger
           JNZ     [_DV_FRND]   # Force round up if divisor is smaller

                                # If MS bytes are equal compare LS
_DV_CPLS:  LDA     [_DV_DIV+1]  # Load ACC with LS divisor
           CMPA    [_DV_RES+1]  # Compare to LS remainder x 2
           JC      [_DV_SIGN]   # Do nothing if divisor is bigger
           JNZ     [_DV_FRND]   # Force round up if divisor is smaller

                                # Do round-half-even if MS&LS are equal 
_DV_RHE:   LDA     [_DV_RES+3]  # Load LS byte of quotient
           AND      %00000001   # Mask out all but LS bit
           JZ      [_DV_SIGN]   # Do nothing if quotient already even

                                # Otherwise do a round-up
_DV_FRND:  LDA     [_DV_RES+3]  # Load ACC with LS quotient
           ADD      $01         #   Add 1 (no carry) to the ACC
           STA     [_DV_RES+3]  #   and store the result
           LDA     [_DV_RES+2]  # Load ACC with MS quotient
           ADDC     $00         #   Add 0 (but with carry flag)
           STA     [_DV_RES+2]  #   and store the result

########## Check the flag to see if we have to negate the result
_DV_SIGN:  LDA     [_DV_FLAG]   # Load the flag byte
           JNN     [_DV_SAVE]   # Jump if MS bit = 0
           LDA      $00         #   Otherwise invert LS two bytes
           SUB     [_DV_RES+3]  #   of the result by subtracting
           STA     [_DV_RES+3]  #   them from zero
           LDA      $00         #    :
           SUBC    [_DV_RES+2]  #    :
           STA     [_DV_RES+2]  #    :

########## Save the LS two bytes of the 4-byte result on the stack
_DV_SAVE:  LDA     [_DV_RES+3]  # Load ACC with LS byte of 2-byte
           PUSHA                #   quotient and push it onto the stack
           LDA     [_DV_RES+2]  # Load ACC with MS byte of 2-byte
           PUSHA                #   quotient and push it onto the stack

########## Return to main program
_DV_RET:   LDA     [_DV_RADD+1] # Load ACC with LS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           LDA     [_DV_RADD]   # Load ACC with MS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           RTS                  # That's it, exit the subroutine

########## Reserve temp locations for this subroutine
_DV_RADD: .2BYTE                # Reserve 2-byte temp location for
                                #   the return address
_DV_DIV:  .2BYTE                # Reserve 2-byte temp location for
                                #   the divisor
_DV_RES:  .4BYTE                # Reserve 4-byte temp location for
                                #   the result (remainder + quotient)
_DV_FLAG: .BYTE                 # Reserve 1-byte to use as a flag
########## This is the end of the _DIV subroutine

#---------------------------------------------------------------------#
