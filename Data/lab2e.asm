## Lab 2e
## Program to write patterns to the calculator's LEDs

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
SIXLEDS:  .EQU     $F032      # Address of output port for six LEDs
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
LOOPA:     LDA     $20        # Load accumulator with $20
LOOPB:     STA     [SIXLEDS]  # Store accumulator to six LEDs
           SHR                # Shift accumulator 1 bit to the right
           JNZ     [LOOPB]    # Jump to LOOPB if Z flag not set
           JMP     [LOOPA]    # ..else jump to LOOPA
          .END                # This is the end of the program


