## Lab 2b
## Program to clear the calculator's main display (using labels)

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program


