## Lab 2d
## Clear the main display then loop around reading key codes
## and displaying any keys in the range '0' to '9'

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
KEYPAD:   .EQU     $F011      # Address of input port for keypad
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
LOOP:      LDA     [KEYPAD]   # Load the accumulator from the keypad
           JN      [LOOP]     # Jump to LOOP if N flag is set
           CMPA    $09        # Compare accumulator to code $09
           JC      [LOOP]     # Jump to LOOP if C flag is set
           STA     [MAINDISP] # ... else store accumulator to display
           JMP     [LOOP]     # Jump to LOOP
          .END                # This is the end of the program


