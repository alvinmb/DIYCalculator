#######################################################################
# Name:     _NEG                                                      #
#                                                                     #
# Function: Negates a 16-bit signed binary value (changes a positive  #
#           value into its negative equivalent and vice versa) and    #
#           returns a 16-bit result in the range -32,767 through      #
#           +32,767. Note that this routine assumes that it will      #
#           not be presented with a value of -32,768, and therefore   #
#           does not perform an error check for this input value)     #
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Most-significant byte of number to be negated             #
#           Least-significant byte of number to be negated            #
#                                                                     #
# Exit:     Top of stack                                              #
#           Most-significant byte of result                           #
#           Least-significant byte of result                          #
#                                                                     #
# Modifies: Accumulator                                               #
#                                                                     #
# Size:     Program = 37 bytes                                        #
#           Data    =  4 bytes                                        #
#######################################################################

########## Get return address from stack and store it
_NEG:      POPA                 # Retrieve MS byte of return
           STA     [_NG_RADD]   #   address from stack and store it
           POPA                 # Retrieve LS byte of return
           STA     [_NG_RADD+1] #   address from stack and store it

########## Get subtrahend and minuend from stack
_NG_GNUM:  POPA                 # Retrieve MS byte of number to be
           STA     [_NG_NUM]    #   negated from stack and store it
           POPA                 # Retrieve LS byte of number to be
           STA     [_NG_NUM+1]  #   negated from stack and store it

########## Perform the subtraction
_NG_DOIT:  LDA     $00          # Load ACC with zero
           SUB     [_NG_NUM+1]  # Sub LS byte of number from ACC
           PUSHA                #   and push LS result onto stack
           LDA     $00          # Load ACC zero
           SUBC    [_NG_NUM]    # Sub MS byte of number from ACC w
           PUSHA                # (borrow) and push MS result to stack

########## Return to main program
_NG_RET:   LDA     [_NG_RADD+1] # Load ACC with LS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           LDA     [_NG_RADD]   # Load ACC with MS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           RTS                  # That's it, exit the subroutine

########## Reserve temp locations for this subroutine
_NG_RADD: .2BYTE                # Reserve 2-byte temp location for
                                #   the return address
_NG_NUM:  .2BYTE                # Reserve 2-byte temp location for
                                #   the number to be negated
########## This is the end of the _NEG subroutine

#---------------------------------------------------------------------#
