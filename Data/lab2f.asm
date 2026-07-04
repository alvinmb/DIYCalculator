## Lab 2f
## Program to write "Hello World" to the main display

CLRCODE:  .EQU     $10         # Special code to clear the main display
MAINDISP: .EQU     $F031       # Address of main display output port
          .ORG     $4000	 # Set program's origin to address $4000
           LDA     CLRCODE     # Load accumulator with clear code
           STA     [MAINDISP]  # Store accumulator to main display
           BLDX        0       # Load the index register with 0 
LOOP:      LDA     [MESSAGE,X] # Load accumulator with character
           JZ      [$0000]     # If character = $00 jump to $0000
STORE:     STA     [MAINDISP]  # ... else write character to display
           INCX                # Increment the index register
           JMP     [LOOP]      # Jump back to LOOP

MESSAGE:  .BYTE $48, $45, $4C, $4C, $4F, $20
           #      H    E    L    L    O  SPACE

          .BYTE $57, $4F, $52, $4C, $44, $21, $00
           #      W    0    R    L    D    !  NUL
          .END



