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
           BLDSP   $EFFF      # Load stack pointer with initial value
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

########## Get two 16-bit numbers and push them onto the top of the
########## stack; perform some action on them and display the result
MAINLOOP:  JSR     [GETNUM]     # Get 1st 16-bit number (NUMA)
           JSR     [GETNUM]     # Get 2nd 16-but number (NUMB)
           JSR     [_DIV]       # Divide NUMA by NUMB
           JSR     [DISPNUM]    # Display 16-bit number from stack
      
########## Wait for any key to be pressed, then clear the main
########## display and do it all again
WAITKEY:   LDA     [KEYPAD]     # Load accumulator from keypad
           JN      [WAITKEY]    # Jump back if no key pressed
           LDA      CLRCODE     # Load accumulator with clear code
           STA     [MAINDISP]   #   and store it to the main display
           JMP     [MAINLOOP]   # Jump back and do it all again

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

########## Start of GETNUM subroutine
########## Get four hex digits, use them to form a 16-bit binary 
########## value, and store that value on the stack

########## Pop the return address off the stack and save it 
GETNUM:    POPA                 # Pop the MS byte of return address
           STA     [_GN_RADD]   #   off the stack and store it
           POPA                 # Pop the LS byte of return address
           STA     [_GN_RADD+1] #   off the stack and store it

########## Load a series of key codes into 'INSTRING' until we see
########## the 'Enter' key (we assume other keys are 0-9 and/or A-F
########## and we don't perform any error checking)
           BLDX    $0000        # Load the index register with 0
_GN_LOOP:  LDA     [KEYPAD]     # Load accumulator from keypad
           JN      [_GN_LOOP]   # Jump back if no key pressed
           CMPA    $13          # Compare to code for 'Enter" key
           JZ      [_GN_STR]    # If the same, jump to process string
           STA     [MAINDISP]   # Copy this key code to main display
           STA     [INSTRING,X] # Also store this code in string
           INCX                 # Increment the index register
           JMP     [_GN_LOOP]   # Jump back and wait for another key

########## Build a 16-bit binary number and push it in the stack
_GN_STR:   LDA     [INSTRING+2] # Load accumulator with 3rd character
           SHL                  #   in 'INSTRING' and shift it left
           SHL                  #   four bits ...
           SHL                  #     :
           SHL                  #     :
           OR      [INSTRING+3] # OR result with 4th character and 
           PUSHA                #   push this LS byte onto the stack

           LDA     [INSTRING]   # Load accumulator with 1st character
           SHL                  #   in 'INSTRING' and shift it left
           SHL                  #   four bits ...
           SHL                  #     :
           SHL                  #     :
           OR      [INSTRING+1] # OR result with 2nd character and 
           PUSHA                #   push this MS byte onto the stack

########## Write a space to the main display
_GN_SPC:   LDA     $20          # Load acc with ASCII code for space 
           STA     [MAINDISP]   # Write it to the main display

########## Return gracefully from this subroutine
_GN_RET:   LDA     [_GN_RADD+1] # Get LS byte of return address from
           PUSHA                #   temp location and push onto stack
           LDA     [_GN_RADD]   # Get MS byte of return address from
           PUSHA                #   temp location and push onto stack
           RTS                  # Return from this subroutine

_GN_RADD: .2BYTE                # 2-byte temp location used to store
                                #   the return address for this routine
########## End of GETNUM subroutine

#---------------------------------------------------------------------#

########## Start of DISPNUM subroutine
########## Retrieve a 16-bit binary value from the stack, convert
########## it into 4 hex digits, and display these digits

########## Pop the return address off the stack and save it 
DISPNUM:   POPA                 # Pop the MS byte of return address
           STA     [_DN_RADD]   # off the stack and store it
           POPA                 # Pop the LS byte of return address
           STA     [_DN_RADD+1] # off the stack and store it

########## Write an equals sign ('=') and space to the main display 
_DN_EQ:    LDA     $3D          # Load acc with ASCII code for '='
           STA     [MAINDISP]   #   and store it to the main display
           LDA     $20          # Load acc with ASCII code for ' '
           STA     [MAINDISP]   #   and store it to the main display
         
########## Break-out and display the MS byte (1st and 2nd digits)
_DN_MSB:   POPA                 # Pop the MS byte off the stack
           PUSHA                #   and push a copy back for later
           SHR                  # Then shift it right by 4 bits
           SHR                  #   :
           SHR                  #   :
           SHR                  #   :
           AND     $0F          # Clear MS 4 bits to 0
           STA     [MAINDISP]   #   and store 1st digit to main display
           POPA                 # Pop the MS byte off the stack again
           AND     $0F          # Clear MS 4 bits to 0
           STA     [MAINDISP]   #   and store 2nd digit to main display

########## Break-out and display the LS byte (3rd and 4th digits)
_DN_LSB:   POPA                 # Pop the LS byte off the stack
           PUSHA                #   and push a copy back for later
           SHR                  # Then shift it right by 4 bits
           SHR                  #   :
           SHR                  #   :
           SHR                  #   :
           AND     $0F          # Clear MS 4 bits to 0
           STA     [MAINDISP]   #   and store 3rd digit to main display
           POPA                 # Pop the LS byte off the stack again
           AND     $0F          # Clear MS 4 bits to 0
           STA     [MAINDISP]   #   and store 4th digit to main display

########## Return gracefully from this subroutine
_DN_RET:   LDA     [_DN_RADD+1] # Get LS byte of return address from
           PUSHA                #   temp location and push onto stack
           LDA     [_DN_RADD]   # Get MS byte of return address from
           PUSHA                #   temp location and push onto stack
           RTS                  # Return from this subroutine

_DN_RADD: .2BYTE                # 2-byte temp location used to store
                                #   the return address for this routine
########## End of DISPNUM subroutine

#---------------------------------------------------------------------#

########## Start of DISPERR subroutine
########## Display an error message and then quit the program

########## First clear the display
DISPERR:   LDA      CLRCODE     # Load ACC with clear code
           STA     [MAINDISP]   #   and copy it to the main display

########## Display the word "Error: " (note the space)
_DE_ERR:   BSTX    [TMP2BYTE]   # Store the value in the X register
           BLDX    MSG_000      # Load X reg with start of msg 000
_DE_LUPA:  LDA     [0,X]        # Load a character from the msg
           JZ      [_DE_MSG]    # If it's a NUL jump to next bit
           STA     [MAINDISP]   #   otherwise copy it to main display
           INCX                 # Increment the index register
           JMP     [_DE_LUPA]   # Jump back for next character

########## Now display the main error message then terminate
_DE_MSG:   BLDX    [TMP2BYTE]   # Reload the X reg's original value
_DE_LUPB:  LDA     [0,X]        # Load a character from the msg
           JZ      [$0000]      # If it's a NUL terminate the program
           STA     [MAINDISP]   #   otherwise copy it to main display
           INCX                 # Increment the index register
           JMP     [_DE_LUPB]   # Jump back for next character
########## End of DISPERR subroutine

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

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################
INSTRING: .BYTE *10             # Reserve 10 bytes to store a string
TMPBYTE:  .BYTE                 # Reserve a 1-byte temp location
TMP2BYTE: .2BYTE                # Reserve a 2-byte temp location
TMP4BYTE: .4BYTE                # Reserve a 4-byte temp location

########## Start of message strings
MSG_000: .byte $45, $52, $52, $4F, $52, $3A, $20, $00
MSG_001: .byte $43, $61, $72, $72, $79, $20, $3D, $20, $31, $00
MSG_002: .byte $42, $6F, $72, $72, $6F, $77, $20, $3D, $20, $30, $00
MSG_003: .byte $4F, $76, $65, $72, $66, $6C, $6F, $77, $00
MSG_004: .byte $55, $6E, $64, $65, $72, $66, $6C, $6F, $77, $00
MSG_005: .byte $54, $6F, $6F, $20, $62, $69, $67, $00
MSG_006: .byte $54, $6F, $6F, $20, $73, $6D, $61, $6C, $6C, $00
MSG_007: .byte $44, $69, $76, $69, $64, $65, $20, $62, $79, $20, $30, $00
MSG_008: .byte $4F, $75, $74, $20, $6F, $66, $20, $72, $61, $6E, $67, $65, $00
MSG_009: .byte $2D, $33, $32, $2C, $37, $36, $38, $00
MSG_010: .byte $4E, $6F, $74, $20, $69, $6D, $70, $6C, $65, $6D, $65, $6E, $74, $65, $64, $00
#######################################################################
## End of global data                                                ##
#######################################################################

          .END                # That's all folks
