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
           ### THIS IS WHERE WE WILL CALL THE MATH ROUTINE
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

########## This is where the math subroutine will go


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
