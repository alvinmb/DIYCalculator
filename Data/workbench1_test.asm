# ================================================================
# workbench1_test.asm
# Workbench 1 — Switch Bank 1 → LED Display test
#
# Assembler : das.py (via the built-in Assembler / Editor window)
# Load addr : $4000 (assembled with .ORG $4000)
#
# What this test does
# -------------------
#   Continuously reads the upper 8-bit switch bank (port $F000)
#   and mirrors the switch states to the 8-bit LED display
#   (port $F022) in a tight loop.
#
#   Toggle any switch on Workbench 1 and the matching LED
#   should light up immediately.
#
# HOW TO RUN
# ----------
#   1. Open Workbench 1 from the Tools menu
#   2. Power ON the calculator (On/Off button)
#   3. Open Assembler/Editor from the Tools menu
#   4. File > Open this file, then click Assemble
#   5. Click "Load -> CPU"
#   6. Press RUN on the calculator panel
#   7. Toggle switches on Workbench 1 — LEDs mirror them
#
# Workbench 1 Port Map
# --------------------
#   Input   $F000   8-Bit Switch Bank 1
#   Input   $F001   8-Bit Switch Bank 2
#   Output  $F021   7-Segment Un-decoded  (bits 0-6 → segments a-g)
#   Output  $F022   8-Bit LED Display         <-- correct address
#   Output  $F023   7-Segment Decoded     (low nibble → hex digit 0-F)
#   Output  $F024   Dual 7-Segment Decoded (hi nibble=left, lo=right)
# ================================================================

SW8BIT1:  .EQU    $F000          # Upper bank of 8-bit switches
LED8BIT:  .EQU    $F022          # 8-bit LED Display  (NOT $F020 — that is the keyboard data port)

          .ORG    $4000          # Set program origin

LOOP:
          LDA     [SW8BIT1]      # Read from upper 8-bit switches
          STA     [LED8BIT]      # Write to 8-bit LED Display
          JMP     [LOOP]         # Do it all again

          .END
