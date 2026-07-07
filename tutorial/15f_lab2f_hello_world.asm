# ================================================================
# 15f_lab2f_hello_world.asm
# Beboputer Hands-On Tutorial — Lab 2f
#
# Print "HELLO WORLD!" on the Calculator's main display.
#
# What this program does
# -----------------------
#   Clears the display, then writes out the message "HELLO WORLD!"
#   one character at a time and stops.
#
# How it works
# -------------
#   This is the same table-walking idea exercise 09 uses for its own
#   message - in fact, if this looks familiar, it's because exercise
#   09 is built on exactly this pattern. The message is stored as
#   plain ASCII bytes right after the code, and the Index register
#   (X) walks through them one at a time:
#
#     BLDX        0       # Load the index register with 0
#     LOOP:      LDA     [MESSAGE,X] # Load accumulator with character
#                JZ      [$0000]     # If character = $00 jump to $0000
#     STORE:     STA     [MAINDISP]  # ... else write character to display
#                INCX                # Increment the index register
#                JMP     [LOOP]      # Jump back to LOOP
#
#     MESSAGE:  .BYTE $48, $45, $4C, $4C, $4F, $20
#                #      H    E    L    L    O  SPACE
#                .BYTE $57, $4F, $52, $4C, $44, $21, $00
#                #      W    0    R    L    D    !  NUL
#
#   [MESSAGE,X] is indexed addressing: "read the byte at MESSAGE's
#   address, plus whatever X currently holds." With X starting at 0,
#   the first pass reads MESSAGE+0 ($48, 'H'); INCX makes it 1 for
#   the next pass (MESSAGE+1, $45 'E'); and so on down the table.
#   JZ checks the character that was just loaded before doing
#   anything else with it - the moment a $00 byte turns up (the
#   very last entry in the table, deliberately placed there as a
#   terminator), JZ jumps to $0000 and the program stops (see Lab
#   2a's note on why "jump to zeroed memory" works as a stopping
#   point). Every character before that $00 gets written to the
#   display and the loop continues.
#
#   Notice the message is written as two separate .BYTE lines under
#   one MESSAGE label - the assembler doesn't care how many .BYTE
#   directives you split a table across, only that they all come one
#   after another with no other code between them; the label just
#   marks where the very first byte lands, and INCX walks past the
#   line break exactly the same as it would if it were all one line
#   (see exercise 09 for the same technique used with a shorter
#   message).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - "HELLO WORLD!" appears on the
#   display, one character at a time (fast enough that it looks
#   instantaneous at full run speed - switch to Step to watch each
#   character land individually).
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and Step through the program to
#   watch $F031 receive each character in turn, and watch the Index
#   register count up 0, 1, 2, ... in the Registers panel as X walks
#   the table.
#
# Try this next
# ---------------
#   - Change MESSAGE to your own text - remember the final $00
#     terminator, or the loop will walk straight past the end of the
#     table into whatever bytes happen to follow it.
#   - Replace JZ [$0000] with a proper HALT ($3C), the way exercise
#     09 does, and compare the two approaches directly.
# ================================================================

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
