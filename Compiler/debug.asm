#######################################################################
## Start of constant declarations                                    ##
#######################################################################

.EQU MAINDISP      $F031        # Address of out port for main display
.EQU SIXLEDS       $F032        # Address of out port for six LEDs
.EQU KEYPAD        $F011        # Address of input port for keypad

.EQU CLRCODE       $10          # Special code to clear main display
.EQU BELLCODE      $11          # Special code to “beep” the display
.EQU BACKCODE      $12          # Code to delete last character 

.EQU BINMODE       %00000100    # LED code to indicate binary mode
.EQU DECMODE       %00000010    # LED code to indicate decimal mode
.EQU HEXMODE       %00000001    # LED code to indicate hexadecimal mode

.EQU CLRKEY        $10          # Code associated with the “Clear” key
.EQU CEKEY         $11          # Code associated with the “CE” key
.EQU BACKKEY       $12          # Code associated with the “Back” key
.EQU ENTERKEY      $13          # Code associated with the “Enter” key

#######################################################################
## End of constant declarations                                      ##
#######################################################################

          .ORG     $4000        # Set program origin

#######################################################################
## Start of initialization                                           ##
#######################################################################

INIT:      LDA     CLRCODE      # Load accumulator with clear code
           STA     [MAINDISP]   #   and write it to the main display
           LDA     DECMODE      # Load accumulator with dec mode code
           STA     [SIXLEDS]    #   and write it to port driving LEDs
           BLDSP   $EFFF        # load stack pointer with initial value

#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

MAINLOOP:  JSR     [GETSTUFF]   # Call routine to get some input
           LDA     [INSTRING]   # Load ACC with first code in INSTRING
           CMPA     $09         # Compare value in ACC with $09
           JC      [DOFUNC]     # If value in ACC > $09 then jump
           JSR     [GETNUM]     #   else it's a number so get it
           JMP     [MAINLOOP]   #   then jump back for more input

########## Call the appropriate math/other function/subroutine
DOFUNC:    SUB      $14         # Subtract offset from ACC
           SHL                  # Shift left (multiply by 2)
           STA     [TEMPX+1]    # Store in LS byte of temp X reg
           BLDX    [TEMPX]      # Load index register
           JSR     [[KEY_H14,X]]# Call appropriate subroutine
           JSR     [DISPNUM]    # Call routine to display result
           JMP     [MAINLOOP]   # Jump back for more input

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################


########## Start of GETSTUFF subroutine
########## Read a series of codes from the keypad until 
########## the “Enter” key is pressed

########## Initialize the input string with dummy values 
GETSTUFF:  BLDX    10           # Load the index register with 10
           LDA     $FF          # Load ACC with $FF
_GS_ISTR:  DECX                 # Decrement the index reg
           STA     [INSTRING,X] # Store ACC in string
           JNZ     [_GS_ISTR]   # Jump back if index reg not zero

########## Initialize the “first” flag with 1
_GS_IFST:  LDA      $01         # Load ACC with 1 (meaning “first”)
           STA     [_GS_FST]    # Store this value into the flag

########## This is the main loop where we load a series of key codes
########## into 'INSTRING' until the enter key is pressed
           BLDX     0           # Load the index register with 0

########## Wait for a key to be pressed
_GS_LOOP:  LDA     [KEYPAD]     # Load accumulator from keypad
           JN      [_GS_LOOP]   # Jump back if no key pressed
           STA     [_GS_TEMP]   # Store this code in temp location

########## If this is the first key, then clear the display
_GS_TFST:  LDA     [_GS_FST]    # Retrueve the “first” flag
           JZ      [_GS_DOIT]   # Jump if 0 (not the first key)
           LDA      CLRCODE     # Otherwise load ACC with clear code
           STA     [MAINDISP]   #   store to main display
           LDA      $00         #   then load ACC with 0
           STA     [_GS_FST]    #   and set “first” flag to “not first”

########## Process the key
_GS_DOIT:  LDA     [_GS_TEMP]   # Retrieve the key code from temp
           CMPA     ENTERKEY    # Compare to code for 'Enter" key
           JNZ     [_GS_STOR]   #   if not the same store it
           RTS                  #   else return from this routine
           
_GS_STOR:  STA     [INSTRING,X] # Else store this code in string
           INCX                 # Increment the index register

           CMPA     $09         # Compare code to that for number '9'
           JC      [_GS_LOOP]   # If code is bigger, don't display
           STA     [MAINDISP]   #    else copy code to main display
           JMP     [_GS_LOOP]   #    then wait for next key

_GS_FST:  .BYTE                 # Flag to indicate first character
_GS_TEMP: .BYTE                 # Just a temp location
########## End of GETSTUFF subroutine

#---------------------------------------------------------------------#


########## Start of decimal GETNUM subroutine
########## Assumes INSTRING contains one or more decimal digits 

########## Pop the return address off the stack and save it 
GETNUM:    POPA                 # Pop the MS byte of return address
           STA     [_GN_RADD]   #   off the stack and store it
           POPA                 # Pop the LS byte of return address
           STA     [_GN_RADD+1] #   off the stack and store it

########## Initialize temp 2-byte value and index register
_GN_INIT:  BLDX     0           # Load the index register with 0
           LDA      0           # Load ACC with 0
           STA     [_GN_TMPA]   # Clear MS byte of temp location
           STA     [_GN_TMPA+1] # Clear LS byte of temp location

########## Start of main loop
_GN_DOIT:  LDA     [INSTRING,X] # Load the next key code
           JN      [_GN_STA]    # If code = $FF we're done

########## Multiply by 2 and store in two locations 
_GN_ML2:   LDA     [_GN_TMPA+1] # Load LS byte of temp value
           SHL                  #   shift left by 1 bit
           STA     [_GN_TMPA+1] #   store it in LS 1st temp value
           STA     [_GN_TMPB+1] #   also store in LS 2nd temp value

           LDA     [_GN_TMPA]   # Load MS byte of temp value
           ROLC                 #   rotate left by 1 bit
           STA     [_GN_TMPA]   #   store it in MS 1st temp value
           STA     [_GN_TMPB]   #   also store in MS 2nd temp value 

########## Multiply main location by 4 and store it
_GN_ML4:   LDA     [_GN_TMPA+1] # Load LS byte of temp value
           SHL                  #   shift left 1 bit
           STA     [_GN_TMPA+1] #   store it
           LDA     [_GN_TMPA]   # Load MS byte of temp value
           ROLC                 #   rotate left by 1 bit
           STA     [_GN_TMPA]   #   store it

           LDA     [_GN_TMPA+1] # Load LS byte of temp value
           SHL                  #   shift left 1 bit
           STA     [_GN_TMPA+1] #   store it
           LDA     [_GN_TMPA]   # Load MS byte of temp value
           ROLC                 #   rotate left by 1 bit
           STA     [_GN_TMPA]   #   store it

########## Add the value multiplied by 2 to the value multiplied by 8
_GN_AMUL:  LDA     [_GN_TMPA+1] # Load LS byte of x8
           ADD     [_GN_TMPB+1] #   add (no carry) LS byte x2
           STA     [_GN_TMPA+1] #   and store the result
           LDA     [_GN_TMPA]   # Load MS byte of x8
           ADDC    [_GN_TMPB]   #   add (with carry) MS byte x2
           STA     [_GN_TMPA]   #   and store the result

########## Add the value of the key code in
_GN_AKEY:  LDA     [INSTRING,X] # Load ACC with key code
           ADD     [_GN_TMPA+1] #   add (no carry) the LS temp value
           STA     [_GN_TMPA+1] #   and store the result
           LDA      $00         # Load ACC with 0
           ADDC    [_GN_TMPA]   #   add (with carry) the MS temp value
           STA     [_GN_TMPA]   #   and store the result

########## Increment the index register and do it all again
_GN_INCX:  INCX                 # Increment the index register
           JMP     [_GN_DOIT]   # Jump back to look at the next code

########## Store the 2-byte binary number on the stack
_GN_STA:   LDA     [_GN_TMPA+1] # Load ACC with LS byte of number 
           PUSHA                # Push it into the stack
           LDA     [_GN_TMPA]   # Load ACC with MS byte of number 
           PUSHA                # Push it into the stack

########## Return gracefully from this subroutine
_GN_RET:   LDA     [_GN_RADD+1] # Get LS byte of return address from
           PUSHA                #   temp location and push onto stack
           LDA     [_GN_RADD]   # Get MS byte of return address from
           PUSHA                #   temp location and push onto stack
           RTS                  # Return from this subroutine

_GN_RADD: .2BYTE                # 2-byte temp location used to store
                                #   the return address for this routine
_GN_TMPA: .2BYTE                # One 2-byte temp location
_GN_TMPB: .2BYTE                # Another 2-byte temp location
########## End of GETNUM subroutine

#---------------------------------------------------------------------#

########## Start of decimal DISPNUM subroutine
########## Assumes a 2-byte integer is on top of the stack 

########## Pop the return address off the stack and save it 
DISPNUM:   POPA                 # Pop the MS byte of return address
           STA     [_DN_RADD]   #   off the stack and store it
           POPA                 # Pop the LS byte of return address
           STA     [_DN_RADD+1] #   off the stack and store it

########## Clear the main display
_DN_CDIS:  LDA      CLRCODE     # Load ACC with clear code
           STA     [MAINDISP]   #    and copy to main display

########## Initialize the “first” flag with 1
_DN_IFST:  LDA      $01         # Load ACC with 1 (meaning “first”)
           STA     [_DN_FST]    # Store this value into the flag

########## Pop the number off the top of the stack
_DN_GNUM:  POPA                 # Pop the MS byte of number
           STA     [_DN_TMP]    #   off the stack and store it
           POPA                 # Pop the LS byte of number
           STA     [_DN_TMP+1]  #   off the stack and store it

########## Push a copy of the number back onto the stack
_DN_PNUM:  PUSHA                # Push LS byte of number onto stack
           LDA     [_DN_TMP]    # Retrieve MS byte of number
           PUSHA                #   and push it onto the stack

########## Display '-' and invert number if necessary
_DN_INV:   JNN     [_DN_DOIT]   # Jump if the value isn't negative
           LDA      $2D         #   else load ASCII code for minus sign
           STA     [MAINDISP]   #   and store to main display
           LDA      $00         # Load ACC with 0
           SUB     [_DN_TMP+1]  #   subtract (no carry) LS byte of
           STA     [_DN_TMP+1]  #   number and store it
           LDA      $00         # Load ACC with 0
           SUBC    [_DN_TMP]    #   subtract (with carry) MS byte of
           STA     [_DN_TMP]    #   number and store it

########## Subtract the different powers of ten
_DN_DOIT:  BLDX     $2710       # Load X reg with $2710 (10,000)
           JSR     [_DN_NEST]   #    and call nested subroutine
           BLDX     $03E8       # Load X reg with $03E8 (1,000)
           JSR     [_DN_NEST]   #    and call nested subroutine
           BLDX     $0064       # Load X reg with $0064 (100)
           JSR     [_DN_NEST]   #    and call nested subroutine
           BLDX     $000A       # Load X reg with $000A (10)
           JSR     [_DN_NEST]   #    and call nested subroutine

########## Display the number of 1s irrespective of its value
_DN_01:    LDA     [_DN_TMP+1]  # Load ACC with LS number (1s)
           STA     [MAINDISP]   #    and display it

########## Return gracefully from the main DISPNUM subroutine
_DN_RET:   LDA     [_DN_RADD+1] # Get LS byte of return address from
           PUSHA                #   temp location and push onto stack
           LDA     [_DN_RADD]   # Get MS byte of return address from
           PUSHA                #   temp location and push onto stack
           RTS                  # Return from this subroutine

########## This is the start of the nested subroutine that repeatedly
########## subtracts the power of 10 (passed in via the X reg)
_DN_NEST:  BSTX    [_DN_TMPX]   # Store contents of index reg
           BLDX     0           # Load index register with 0

########## Subtract the power of 10 from the number
_DN_SUB:   LDA     [_DN_TMP+1]  # Load ACC with LS number
           SUB     [_DN_TMPX+1] #   subtract (no carry) LS power of 10 
           STA     [_DN_TMP+1]  #   and store result
           LDA     [_DN_TMP]    # Load ACC with MS number
           SUBC    [_DN_TMPX]   #   subtract (w carry) MS power of 10
           STA     [_DN_TMP]    #   and store it
           JNC     [_DN_ADD]    # If carry = 0 then recover
           INCX                 #    else increment index reg
           JMP     [_DN_SUB]    #    and go for it again

########## We've gone too far, so add power of 10 back in again
_DN_ADD:   LDA     [_DN_TMP+1]  # Load ACC with LS number
           ADD     [_DN_TMPX+1] #   add (no carry) LS power of 10
           STA     [_DN_TMP+1]  #   and store result
           LDA     [_DN_TMP]    # Load ACC with MS number
           ADDC    [_DN_TMPX]   #   add (w carry) MS power of 10
           STA     [_DN_TMP]    #   and store it

########## Test to see if this is the first digit to be displayed
_DN_TSTF:  BSTX    [_DN_TMPX]   # Store the index register
           LDA     [_DN_FST]    # Load the first flag
           JNZ     [_DN_TSTZ]   # If 1 (first) then jump to test for 0
           LDA     [_DN_TMPX+1] #    else load ACC with LS X
           STA     [MAINDISP]   #    store to main display
           RTS                  #    and return to main routine

########## If this is the first digit, test for a non-zero value
_DN_TSTZ:  LDA     [_DN_TMPX+1] # Load ACC with LS byte of X reg
           JNZ     [_DN_DFST]   #    if non-0 jump to display
           RTS                  #    else return to main routine
_DN_DFST:  STA     [MAINDISP]   # Store code to main display
           LDA      $00         #    then load ACC with 0
           STA     [_DN_FST]    #    and store it to “first” flag
           RTS                  #    and return to main routine
########## This is the end of the nested subroutine

_DN_RADD: .2BYTE                # 2-byte temp location used to store
                                #   the return address for this routine
_DN_TMP:  .2BYTE                # A 2-byte temp location
_DN_TMPX: .2BYTE                # A 2-byte temp location for the X reg
_DN_FST:  .BYTE                 # A 1-byte temp location
########## End of DISPNUM subroutine

#---------------------------------------------------------------------#


########## Start of DISPERR subroutine
########## Display an error message and then quit the program

########## First clear the display
DISPERR:   LDA      CLRCODE     # Load ACC with clear code
           STA     [MAINDISP]   #   and copy it to the main display

########## Display the word "Error: " (note the space)
_DE_ERR:   BSTX    [TEMPX]      # Store X reg in temp location
           BLDX    MSG_000      # Load X reg with start of msg 000
_DE_LUPA:  LDA     [0,X]        # Load a character from the msg
           JZ      [_DE_MSG]    # If it's a NUL jump to next bit
           STA     [MAINDISP]   #   otherwise copy it to main display
           INCX                 # Increment the index register
           JMP     [_DE_LUPA]   # Jump back for next character

########## Now display the main error message then terminate
_DE_MSG:   BLDX    [TEMPX]      # Reload X reg from temp location
_DE_LUPB:  LDA     [0,X]        # Load a character from the msg
           JZ      [$0000]      # If it's a NUL terminate the program
           STA     [MAINDISP]   #   otherwise copy it to main display
           INCX                 # Increment the index register
           JMP     [_DE_LUPB]   # Jump back for next character
########## End of DISPERR subroutine

#---------------------------------------------------------------------#


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


########## Start of _NOTYET subroutine
########## Display an error message and then quit the program

########## First clear the display
_NOTYET:   BLDX     MSG_010     # Load X reg with addr of message
           JSR     [DISPERR]    # Jump to display error subroutine

########## End of _NOTYET subroutine

#---------------------------------------------------------------------#

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

########## Invert dividend if necessary (XOR sign in flag)
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

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

INSTRING: .BYTE *10             # Reserve 10 bytes to store a string
TEMPX:    .2BYTE                # Reserve 2-byte location for X reg

########## Start of message strings
MSG_000:  .BYTE $45, $52, $52, $4F, $52, $3A, $20, $00
MSG_001:  .BYTE $43, $61, $72, $72, $79, $20, $3D, $20, $31, $00
MSG_002:  .BYTE $42, $6F, $72, $72, $6F, $77, $20, $3D, $20, $30, $00
MSG_003:  .BYTE $4F, $76, $65, $72, $66, $6C, $6F, $77, $00
MSG_004:  .BYTE $55, $6E, $64, $65, $72, $66, $6C, $6F, $77, $00
MSG_005:  .BYTE $54, $6F, $6F, $20, $62, $69, $67, $00
MSG_006:  .BYTE $54, $6F, $6F, $20, $73, $6D, $61, $6C, $6C, $00
MSG_007:  .BYTE $44, $69, $76, $69, $64, $65, $20, $62, $79, $20, $30, $00
MSG_008:  .BYTE $4F, $75, $74, $20, $6F, $66, $20, $72, $61, $6E, $67, $65, $00
MSG_009:  .BYTE $2D, $33, $32, $2C, $37, $36, $38, $00
MSG_010:  .BYTE $4E, $6F, $74, $20, $69, $6D, $70, $6C, $65, $6D, $65, $6E, $74, $65, $64, $00

########## Start of cunning re-direction
KEY_H14:  .2BYTE _NEG           # +/-  Negate
KEY_H15:  .2BYTE _NOTYET        # .    Decimal point
KEY_H16:  .2BYTE _ADD           # +    Add
KEY_H17:  .2BYTE _SUB           # -    Subtract
KEY_H18:  .2BYTE _MULT          # *    Multiply
KEY_H19:  .2BYTE _DIV           # /    Divide
KEY_H1A:  .2BYTE _NOTYET        # =    Equals
KEY_H1B:  .2BYTE _NOTYET        # (    Left parenthesis
KEY_H1C:  .2BYTE _NOTYET        # Pi   Constant Pi
KEY_H1D:  .2BYTE _NOTYET        # Mod  Modulus
KEY_H1E:  .2BYTE _NOTYET        #      Unassigned
KEY_H1F:  .2BYTE _NOTYET        # )    Right parenthesis
KEY_H20:  .2BYTE _NOTYET        # F-S  Scientific on/off
KEY_H21:  .2BYTE _NOTYET        # Exp  Exponential
KEY_H22:  .2BYTE _NOTYET        #      Unassigned
KEY_H23:  .2BYTE _NOTYET        #      Unassigned
KEY_H24:  .2BYTE _NOTYET        #      Unassigned
KEY_H25:  .2BYTE _NOTYET        #      Unassigned
KEY_H26:  .2BYTE _NOTYET        #      Unassigned
KEY_H27:  .2BYTE _NOTYET        #      Unassigned
KEY_H28:  .2BYTE _NOTYET        #      Unassigned
KEY_H29:  .2BYTE _NOTYET        #      Unassigned
KEY_H2A:  .2BYTE _NOTYET        #      Unassigned
KEY_H2B:  .2BYTE _NOTYET        #      Unassigned
KEY_H2C:  .2BYTE _NOTYET        #      Unassigned
KEY_H2D:  .2BYTE _NOTYET        #      Unassigned
KEY_H2E:  .2BYTE _NOTYET        #      Unassigned
KEY_H2F:  .2BYTE _NOTYET        #      Unassigned
KEY_H30:  .2BYTE _NOTYET        #      Unassigned
KEY_H31:  .2BYTE _NOTYET        #      Unassigned
KEY_H32:  .2BYTE _NOTYET        #      Unassigned
KEY_H33:  .2BYTE _NOTYET        #      Unassigned
KEY_H34:  .2BYTE _NOTYET        #      Unassigned
KEY_H35:  .2BYTE _NOTYET        #      Unassigned
KEY_H36:  .2BYTE _NOTYET        # n!   Factorial
KEY_H37:  .2BYTE _NOTYET        # Log  logarithm
KEY_H38:  .2BYTE _NOTYET        # Tan  Tangent
KEY_H39:  .2BYTE _NOTYET        # Cos  Cosine
KEY_H3A:  .2BYTE _NOTYET        # Sin  Sine
KEY_H3B:  .2BYTE _NOTYET        # 1/x  Reciprocal
KEY_H3C:  .2BYTE _NOTYET        # Rx   Square root
KEY_H3D:  .2BYTE _NOTYET        # x^2  X squared
KEY_H3E:  .2BYTE _NOTYET        # x^3  X cubed
KEY_H3F:  .2BYTE _NOTYET        # y^x  Y to the power of X
KEY_H40:  .2BYTE _NOTYET        # Hex  Switch to hex
KEY_H41:  .2BYTE _NOTYET        # Dec  Switch to decimal
KEY_H42:  .2BYTE _NOTYET        # Bin  Switch to binary
KEY_H43:  .2BYTE _NOTYET        #      Unassigned
KEY_H44:  .2BYTE _NOTYET        #      Unassigned
KEY_H45:  .2BYTE _NOTYET        #      Unassigned

#######################################################################
## End of global data                                                ##
#######################################################################
        
          .END                  # That's all folks


