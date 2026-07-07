# ================================================================
# 15b_lab2b_labeled_constants.asm
# Beboputer Hands-On Tutorial — Lab 2b
#
# The exact same program as Lab 2a - clear the display and stop -
# rewritten using named constants instead of raw numbers.
#
# What this program does
# -----------------------
#   Identical behavior to 15a_lab2a_clear_display.asm: writes the
#   display's clear code to the display port, then stops. Assemble
#   both and compare the bytes - they produce the same program.
#
# How it works
# -------------
#   .EQU gives a name to a constant value at assembly time. Every
#   place that name appears later gets replaced with the value
#   during assembly - the CPU never sees "CLRCODE" or "MAINDISP",
#   only the numbers $10 and $F031 they stand for:
#
#     CLRCODE:  .EQU  $10       # Special code to clear the main display
#     MAINDISP: .EQU  $F031     # Address of output port for main display
#
#   With those two names defined, the body of the program reads
#   like a sentence instead of a string of addresses:
#
#     LDA     CLRCODE     # Load accumulator with clear code
#     STA     [MAINDISP]  # Store accumulator to main display
#     JMP     [$0000]     # Jump to address $0000
#
#   Compare that to Lab 2a's LDA $10 / STA [$F031] - same two
#   instructions, same two numbers, but "CLRCODE" and "MAINDISP"
#   tell you what those numbers mean without needing a comment to
#   explain it. This is exactly the same trick exercises 01 onward
#   use everywhere (SW1, LED8, KEY, DISP, and so on) - .EQU costs
#   nothing at runtime and makes every later exercise far easier to
#   read than Lab 2a's style would be once a program gets longer
#   than a handful of lines.
#
#   Note that MAINDISP is used with the indirect-address brackets,
#   [MAINDISP], exactly the way [$F031] was written directly in Lab
#   2a - a label stands in for a number, so it follows the same
#   addressing-mode rules as the number it replaces.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - you should see exactly the
#   same result as Lab 2a. Then open both files side by side and
#   compare: everywhere Lab 2a has a raw number, Lab 2b has a name
#   that explains it.
#
# Watch it happen
# -----------------
#   Open the Memory Walker after assembling and look at the bytes
#   at $4000 onward - they are identical to Lab 2a's, byte for byte.
#   Labels are a convenience for you while writing the program; the
#   assembled program itself doesn't know they ever existed.
#
# Try this next
# ---------------
#   - Add a third .EQU, e.g. EXITADDR: .EQU $0000, and use JMP
#     [EXITADDR] instead of JMP [$0000] - now every address in the
#     program has a name.
# ================================================================

CLRCODE:  .EQU     $10        # Special code to clear the main display
MAINDISP: .EQU     $F031      # Address of output port for main display
          .ORG     $4000	# Set program's origin to address $4000
           LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Store accumulator to main display
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program
