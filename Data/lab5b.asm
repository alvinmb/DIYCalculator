#######################################################################
## Start of constant declarations                                    ##
#######################################################################

MAINDISP: .EQU     $F031        # Address of out port for main display
SIXLEDS:  .EQU     $F032        # Address of out port for six LEDs
KEYPAD:   .EQU     $F011        # Address of input port for keypad

CLRCODE:  .EQU     $10          # Special code to clear main display
BELLCODE: .EQU     $11          # Special code to “beep” the display
BACKCODE: .EQU     $12          # Code to delete last character 

BINMODE:  .EQU     %00000100    # LED code to indicate binary mode
DECMODE:  .EQU     %00000010    # LED code to indicate decimal mode
HEXMODE:  .EQU     %00000001    # LED code to indicate hexadecimal mode

CLRKEY:   .EQU     $10          # Code associated with the “Clear” key
CEKEY:    .EQU     $11          # Code associated with the “CE” key
BACKKEY:  .EQU     $12          # Code associated with the “Back” key
ENTERKEY: .EQU     $13          # Code associated with the “Enter” key


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

## Main body will go here

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


GETNUM:    RTS                  # This will get a decimal number
DISPNUM:   RTS                  # This will display a decimal number

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

_ADD:      RTS                  # This will be our 16-bit addition
_SUB:      RTS                  # This will be our 16-bit subtraction
_MULT:     RTS                  # This will be our 16-bit multiply
_DIV:      RTS                  # This will be our 16-bit divide
_NEG:      RTS                  # This will be our 16-bit negation

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

INSTRING: .BYTE *10             # Reserve 10 bytes to store a string
TEMPX:    .2BYTE                # Reserve 2-byte location for X reg

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
