# ================================================================
# 09_terminal_print_message.asm
# Beboputer Hands-On Tutorial — Section 6 (Terminal)
#
# Print a stored message on the Terminal.
#
# What this program does
# -----------------------
#   Needs no input device - it prints a fixed message stored in
#   the program itself, using the Index register (IX) to walk a
#   table of bytes and the Zero flag (set automatically by LDA)
#   to detect the $00 terminator. MSG spells out
#   "HELLO, BEBOPUTER!" followed by a newline ($0A) and the $00
#   terminator that ends the loop.
#
# Try it
# -------
#   Assemble, Load -> CPU, and click Run (or Step through it to
#   watch IX count up and PC walk the loop on the CPU Registers
#   panel).
#
# Check your work
# -----------------
#   After assembling, find MSG's address in the assembly listing,
#   then type it into the Memory Walker's address field and click
#   GO. The DATA column should show exactly the 19 bytes below,
#   in order.
#
# Try this next
# ---------------
#   Change the .BYTE table to your own message. Every line must
#   end with a $00 terminator for the JZ to find, and each .BYTE
#   line can hold as many comma-separated values as you like.
# ================================================================

TERM:   .EQU    $F028

        .ORG    $4000

        BLDX    $0000      # IX = 0 (index into MSG)

LOOP:   LDA     [MSG,X]    # load the next character
        JZ      [DONE]     # the $00 terminator ends the message
        STA     [TERM]     # send it to the Terminal
        INCX               # move to the next character
        JMP     [LOOP]

DONE:   HALT

MSG:    .BYTE   $48, $45, $4C, $4C, $4F, $2C, $20, $42
        .BYTE   $45, $42, $4F, $50, $55, $54, $45, $52
        .BYTE   $21, $0A, $00

        .END    $4000
