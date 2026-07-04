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

GETSTUFF:  RTS                  # This will be the raw input routine
GETNUM:    RTS                  # This will get a decimal number
DISPNUM:   RTS                  # This will display a decimal number
DISPERR:   RTS                  # This will display an error message
CHK2NEG:   RTS                  # This will check for -32,768

_NOTYET:   RTS                  # Catch-all for unimplemented functions
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
