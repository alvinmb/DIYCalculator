#######################################################################
# Name:     _SUB                                                      #
#                                                                     #
# Function: Subtracts one 16-bit SIGNED binary numbers from another;  #
#           returns a 16-bit result in the range -32,767 to +32,767   #
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Most-significant byte of second number  (subtrahend)      #
#           Least-significant byte of second number (subtrahend)      #
#           Most-significant byte of first number   (minuend)         #
#           Least-significant byte of first number  (minuend)         #
#                                                                     #
# Exit:     Top of stack                                              #
#           Most-significant byte of result         (difference)      #
#           Least-significant byte of result        (difference)      #
#                                                                     #
# Modifies: Accumulator (also index register if error)                #
#                                                                     #
# Size:     Program = 53 bytes                                        #
#           Data    =  5 bytes                                        #
#######################################################################

########## Get return address from stack and store it
_SUB:      POPA                 # Retrieve MS byte of return
           STA     [_SB_RADD]   #   address from stack and store it
           POPA                 # Retrieve LS byte of return
           STA     [_SB_RADD+1] #   address from stack and store it

########## Get subtrahend and minuend from stack
_SB_GNUM:  POPA                 # Retrieve MS byte of subtrahend
           STA     [_SB_NUMB]   #   from stack and store it
           POPA                 # Retrieve LS byte of subtrahend
           STA     [_SB_NUMB+1] #   from stack and store it
           POPA                 # Retrieve MS byte of minuend from
           STA     [_SB_NUMA]   #   stack and store it
           POPA                 # Retrieve LS byte of minuend from
                                #   stack & leave it in the ACC

########## Perform the subtraction
_SB_DOIT:  SUB     [_SB_NUMB+1] # Sub LS byte of subtrahend from ACC
           PUSHA                #   and push LS diference onto stack
           LDA     [_SB_NUMA]   # Load ACC with MS byte of minuend
                                #   from temp location
           SUBC    [_SB_NUMB]   # Sub MS byte of subtrahend from ACC
           PUSHA                # w (borrow) and push MS diff to stack

########## Make sure there isn't an overflow from the MS subtraction
_SB_CHKO:  JNO     [_SB_CHKN]   # If no overflow jump to next test 
           BLDX     MSG_003     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine
                                # (which terminates the program)

########## Call the CHK2NEG subroutine to test for -32,768
_SB_CHKN:  JSR     [CHK2NEG]    # Call the CHK2NEG subroutine

########## Return to main program
_SB_RET:   LDA     [_SB_RADD+1] # Load ACC with LS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           LDA     [_SB_RADD]   # Load ACC with MS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           RTS                  # That's it, exit the subroutine

########## Reserve temp locations for this subroutine
_SB_RADD: .2BYTE                # Reserve 2-byte temp location for
                                #   the return address
_SB_NUMA: .BYTE                 # Reserve 1-byte temp location for
                                #   the MS byte of the minuend
_SB_NUMB: .2BYTE                # Reserve 2-byte temp location for
                                #   the subtrahend
########## This is the end of the _SUB subroutine

#---------------------------------------------------------------------#
