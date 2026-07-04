# ================================================================
# keyboard_to_display.asm
# Keyboard → Calculator Display test
#
# Assembler : das.py  (via the built-in Assembler / Editor window)
# Load addr : $4000   (assembled with .ORG $4000)
#
# What this test does
# -------------------
#   Polls the on-screen keyboard port ($F011) in a tight loop.
#   When a key is pressed the ASCII code is forwarded straight to
#   the calculator display ($F031).  The port is then cleared so
#   the next keypress can be detected.
#
#   Special keys
#   ------------
#   ESC  ($1B)  — the calculator display treats $1B as a clear-
#                 screen code, so pressing ESC wipes the display.
#   All other printable keys appear as characters on the display.
#
# Port map
# --------
#   Input  $F011   On-screen keyboard  (0 = idle, else ASCII code)
#   Output $F031   Calculator display  ($1B = clear, else char)
# ================================================================

KEYBOARD: .EQU    $F011          # On-screen keyboard input port
CALCDSP:  .EQU    $F031          # Calculator display output port
CLRDISP:  .EQU    $1B            # ESC — clears the calculator display

          .ORG    $4000          # Set program origin

# ── Initialise ────────────────────────────────────────────────────

INIT:     LDA     CLRDISP        # Send ESC to clear the display on start-up
          STA     [CALCDSP]
          LDA     $00
          STA     [KEYBOARD]     # Make sure keyboard port starts cleared

# ── Main loop — poll keyboard, echo to display ────────────────────

WAIT:     LDA     [KEYBOARD]     # Read keyboard port
          JZ      [WAIT]         # Zero = no key yet, keep waiting

          STA     [CALCDSP]      # Non-zero = key pressed; send to display

          LDA     $00
          STA     [KEYBOARD]     # Clear the port so next key can be detected

          JMP     [WAIT]         # Go back and wait for next key

          .END
