########## Start of CHK2NEG subroutine
########## Retrieve a 16-bit binary value from the stack and test it.
########## If -32,768, call DISPERR, else return number intact.

########## Pop the return address off the stack and save it 
CHK2NEG:   POPA                 # Pop the MS byte of return address
           STA     [_CN_RADD]   #   off the stack and store it
           POPA                 # Pop the LS byte of return address
           STA     [_CN_RADD+1] #   off the stack and store it
         
########## Pop the number to be testes off the stack
_CN_GNUM:  POPA                 # Pop MS byte of number off the
           STA     [_CN_NUM]    #   stack and store it
           POPA                 # Pop LS byte of number off the
           STA     [_CN_NUM+1]  #   stack and store it
 
########## Push a copy of the number back onto the stack
_CN_PNUM:  PUSHA                # Push LS byte of number onto stack
           LDA     [_CN_NUM]    # Retrieve MS byte of number
           PUSHA                #   and push it onto the stack 

########## Check the MS byte to see if it's equal to $80 
_CN_CKMS:  CMPA    $80          # Compare contents of ACC to $80
           JNZ     [_CN_RET]    # If not equal we're OK so return

########## Check the LS byte to see if it's equal to $00 
_CN_CKLS:  LDA     [_CN_NUM+1]  # Load ACC with LS byte of number
           CMPA    $00          # Compare contents of ACC to $00
           JNZ     [_CN_RET]    # If not equal we're OK so return

########## Call the error message display subroutine 
_CN_DERR:  BLDX     MSG_009     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine
                                # (which terminates the program)

########## Return gracefully from this subroutine
_CN_RET:   LDA     [_CN_RADD+1] # Get LS byte of return address from
           PUSHA                #   temp location and push onto stack
           LDA     [_CN_RADD]   # Get MS byte of return address from
           PUSHA                #   temp location and push onto stack
           RTS                  # Return from this subroutine

########## Reserve temp locations for this subroutine
_CN_RADD: .2BYTE                # 2-byte temp location used to store
                                #   the return address for this routine
_CN_NUM:  .2BYTE                # 2-byte temp location to store
                                #   the number we're checking
########## End of CHK2NEG subroutine

#---------------------------------------------------------------------#


