#######################################################################
# Name:     _ADD                                                      #
#                                                                     #
# Function: Add two 16-bit SIGNED binary numbers together and         #
#           return a 16-bit result in the range -32,767 to +32,767    # 
#                                                                     #
# Entry:    Top of stack                                              #
#           Most-significant byte of return address                   #
#           Least-significant byte of return address                  #
#           Most-significant byte of second number  (addend)          #
#           Least-significant byte of second number (addend)          #
#           Most-significant byte of first number   (augend)          #
#           Least-significant byte of first number  (augend)          #
#                                                                     #
# Exit:     Top of stack                                              #
#           Most-significant byte of result         (sum)             #
#           Least-significant byte of result        (sum)             #
#                                                                     #
# Modifies: Accumulator (also index register if error)                #
#                                                                     #
# Size:     Program = 53 bytes                                        #
#           Data    =  5 bytes                                        #
#######################################################################

########## Get return address from stack and store it
_ADD:      POPA                 # Retrieve MS byte of return
           STA     [_AD_RADD]   #   address from stack and store it
           POPA                 # Retrieve LS byte of return
           STA     [_AD_RADD+1] #   address from stack and store it

########## Get addend and augend from stack
_AD_GNUM:  POPA                 # Retrieve MS byte of addend from
           STA     [_AD_NUMB]   #   stack and store it
           POPA                 # Retrieve LS byte of addend from
           STA     [_AD_NUMB+1] #   stack and store it
           POPA                 # Retrieve MS byte of augend from
           STA     [_AD_NUMA]   #   stack and store it
           POPA                 # Retrieve LS byte of augend from
                                #   stack & leave it in the ACC

########## Perform the addition
_AD_DOIT:  ADD     [_AD_NUMB+1] # Add LS byte of addend to ACC
           PUSHA                #   and push LS sum onto stack
           LDA     [_AD_NUMA]   # Load ACC with MS byte of augend
                                # from temp location
           ADDC    [_AD_NUMB]   # Add MS byte of addend to ACC w
           PUSHA                # carry and push MS sum onto stack

########## Make sure there isn't an overflow from the MS addition
_AD_CHKO:  JNO     [_AD_CHKN]   # If no overflow jump to next test 
           BLDX     MSG_003     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine
                                # (which terminates the program)

########## Call the CHK2NEG subroutine to test for -32,768
_AD_CHKN:  JSR     [CHK2NEG]    # Call the CHK2NEG subroutine

########## Return to main program
_AD_RET:   LDA     [_AD_RADD+1] # Load ACC with LS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           LDA     [_AD_RADD]   # Load ACC with MS byte of return
                                #   address from temp location and
           PUSHA                #   push it back onto the stack
           RTS                  # That's it, exit the subroutine

########## Reserve temp locations for this subroutine
_AD_RADD: .2BYTE                # Reserve 2-byte temp location for
                                #   the return address
_AD_NUMA: .BYTE                 # Reserve 1-byte temp location for
                                #   the MS byte of the augend
_AD_NUMB: .2BYTE                # Reserve 2-byte temp location for
                                #   the addend
########## This is the end of the _ADD subroutine

#---------------------------------------------------------------------#
