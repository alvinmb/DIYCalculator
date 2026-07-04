## Lab 2c
## Clear the main display, then loop around displaying 
## characters '9' downto '1', then exit the program

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
           LDA     $09        # Load the accumulator with $09
LOOP:      STA     [MAINDISP] # Store accumulator to the main display
           DECA               # Decrement the accumulator
           JNZ     [LOOP]     # Jump to LOOP if ACC isn't zero
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program


