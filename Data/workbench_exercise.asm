# ================================================================
# workbench_exercise.asm
# Exercises all Workbench 1 switches and every display
#
# Assembler : das.py  (Assembler / Editor window)
# Load addr : $4000
#
# What it does
# ------------
#   Reads both 8-bit switch banks continuously and fans the
#   values out to every display on the workbench and calculator:
#
#   Switch Bank 1 ($F000)
#     -> 8-bit LED bar          $F020  (direct mirror)
#     -> 7-seg undecoded        $F021  (lower 7 bits light segments a-g)
#     -> 7-seg decoded lo-nib   $F022  (low  nibble displayed as hex digit)
#     -> dual 7-seg decoded     $F023  (hi nibble = left digit,
#                                       lo nibble = right digit)
#     -> calculator display     $F031  (2-char ASCII hex: e.g. "A3")
#
#   Switch Bank 2 ($F001)
#     -> calculator LEDs        $F032  (bits 5..0 = LEDs left to right)
#
# Port map
# --------
#   $F000  Input  -- 8-bit Switch Bank 1
#   $F001  Input  -- 8-bit Switch Bank 2
#   $F021  Output -- 7-segment undecoded  (bits 6..0 -> segs a-g)
#   $F022  Output -- 8-bit LED bar
#   $F023  Output -- single 7-seg decoded (low nibble -> digit 0-F)
#   $F024  Output -- dual 7-seg decoded   (hi nib=left, lo=right)
#   $F031  Output -- calculator scrolling display
#   $F032  Output -- calculator LED strip (bits 5..0)
#
# Carry flag after CMPA $09:
#   C=1  ACC > $09  -> digit is A-F -> add $37
#   C=0  ACC <= $09 -> digit is 0-9 -> add $30
# ================================================================

SW1:      .EQU    $F000
SW2:      .EQU    $F001
SEG7U:    .EQU    $F021    # 7-seg undecoded
LED8:     .EQU    $F022    # 8-bit LED bar
SEG7D:    .EQU    $F023    # single 7-seg decoded
SEG7DD:   .EQU    $F024    # dual 7-seg decoded
CALCDSP:  .EQU    $F031
CALCLED:  .EQU    $F032

          .ORG    $4000

# -- Init: clear calculator display once at startup ---------------

INIT:     LDA     $1B
          STA     [CALCDSP]

# ================================================================
# MAIN LOOP
# ================================================================

LOOP:

# -- 1. Read SW1 and mirror to workbench displays -----------------

          LDA     [SW1]
          STA     [LED8]
          STA     [SEG7U]
          STA     [SEG7DD]
          AND     $0F
          STA     [SEG7D]

# -- 2. Read SW2 and mirror to calculator LEDs --------------------

          LDA     [SW2]
          AND     $3F
          STA     [CALCLED]

# -- 3. Show SW1 as two hex digits on the calculator display ------

          LDA     $1B
          STA     [CALCDSP]

          LDA     [SW1]

# High nibble

          SHR
          SHR
          SHR
          SHR
          AND     $0F
          CMPA    $09
          JC      [HIAF]
          ADD     $30
          JMP     [STOHI]
HIAF:     ADD     $37
STOHI:    STA     [CALCDSP]

# Low nibble

          LDA     [SW1]
          AND     $0F
          CMPA    $09
          JC      [LOAF]
          ADD     $30
          JMP     [STOLO]
LOAF:     ADD     $37
STOLO:    STA     [CALCDSP]

# -- 4. Repeat ----------------------------------------------------

          JMP     [LOOP]

          .END
