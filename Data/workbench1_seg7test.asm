# ================================================================
# workbench1_seg7test.asm
# Workbench 1 — Lower Switch Bank → 7-Segment Displays test
#
# Assembler : das.py (via the built-in Assembler / Editor window)
# Load addr : $4000 (assembled with .ORG $4000)
#
# What this test does
# -------------------
#   Continuously reads the lower 8-bit switch bank (port $F001)
#   and mirrors the switch value to both 7-segment displays:
#
#   $F023  7-Seg Decoded     — shows the LOW NIBBLE (bits 3-0)
#                              as a single hex digit (0 to F)
#
#   $F024  Dual 7-Seg Decoded — shows the FULL BYTE as two digits:
#                              left  digit = HIGH nibble (bits 7-4)
#                              right digit = LOW  nibble (bits 3-0)
#
#   Example: if switches = 1010 0110 (binary) = $A6
#     $F023 shows "6"  (low nibble only)
#     $F024 shows "A6" (both nibbles)
#
# HOW TO RUN
# ----------
#   1. Open Workbench 1 from the Tools menu
#   2. Power ON the calculator (On/Off button)
#   3. Open Assembler/Editor from the Tools menu
#   4. File > Open this file, then click Assemble
#   5. Click "Load -> CPU"
#   6. Press RUN on the calculator panel
#   7. Toggle switches on Switch Bank 2 (lower row) and watch
#      the 7-segment displays update instantly
#
# Workbench 1 Port Map
# --------------------
#   Input   $F000   8-Bit Switch Bank 1  (upper row)
#   Input   $F001   8-Bit Switch Bank 2  (lower row)  <-- used here
#   Output  $F021   7-Seg Un-decoded     (bits 0-6 map to segments a-g)
#   Output  $F022   8-Bit LED Display
#   Output  $F023   7-Seg Decoded        (low nibble → hex digit 0-F)
#   Output  $F024   Dual 7-Seg Decoded   (hi nibble=left, lo nibble=right)
# ================================================================

SW8BIT2:  .EQU    $F001          # Lower bank of 8-bit switches
SEG7D:    .EQU    $F023          # 7-Seg Decoded  (low nibble → hex digit)
DUAL_SEG: .EQU    $F024          # Dual 7-Seg Decoded (hi=left, lo=right)

          .ORG    $4000          # Set program origin

LOOP:
          LDA     [SW8BIT2]      # Read lower switch bank into accumulator
          STA     [SEG7D]        # Low nibble (bits 3-0) → single 7-seg display
          STA     [DUAL_SEG]     # Full byte  → dual 7-seg (hi nibble left, lo right)
          JMP     [LOOP]         # Loop forever

          .END
