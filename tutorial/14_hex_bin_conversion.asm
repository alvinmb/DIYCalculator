# ================================================================
# 14_hex_bin_conversion.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# Convert a hex digit to binary, or four typed bits back to a hex
# digit, using the Bin/Hex buttons and the LEDs in the Calculator's
# top row.
#
# The top row: three blank buttons, then Bin, Dec, Hex
# --------------------------------------------------------
#   Above the main keypad sits a strip of six LED+button pairs (see
#   tools/calculator.py's _top_led_row): three blank/unassigned
#   buttons, then Bin, then Dec, then Hex, each with its own LED
#   directly beside it. All six LEDs are driven by one port, $F032 -
#   bit 5 is the leftmost LED, bit 0 the rightmost - exactly the
#   port exercise 07 introduced. This exercise only uses Bin and
#   Hex; Dec is left for you in "Try this next".
#
# A button-code collision this exercise ran into (and fixed)
# ---------------------------------------------------------------
#   Bin and Dec used to default to codes $02 and $0A. Digit and hex-
#   letter buttons don't send their ASCII code - tools/diy_button.py
#   converts them down to a raw nibble first (0-9 for digits, 10-15
#   for A-F, see exercise 10's note on this) - which meant digit "2"
#   arrives as plain byte $02, identical to Bin's old code, and hex
#   letter "A" arrives as byte $0A, identical to Dec's old code. A
#   program watching for "did the user press Bin?" by comparing
#   against $02 could not tell that apart from someone simply typing
#   the digit 2. This is the same class of bug exercise 10 found
#   between CE and digit "1" - and the fix is the same: Bin, Dec,
#   and Hex were moved to $43/$44/$45 in _BUTTON_DEFAULTS
#   (tools/calculator.py), all outside the 0-15 nibble range, so
#   they can never again collide with a digit or hex-letter
#   keypress. This exercise watches for those new codes below.
#
# What this program does
# -----------------------
#   Press Hex, then type one hex digit (0-9 or A-F): the display
#   shows the digit, then its 4-bit binary pattern, and the same
#   pattern lights up on the LEDs.
#       Hex   A     ->  shows  A=1010          (LEDs: . X . X)
#       Hex   7     ->  shows  7=0111          (LEDs: . X X X)
#
#   Press Bin, then type exactly four bits using the 0 and 1 keys,
#   most-significant bit first: the LEDs light up live as each bit
#   lands, and once the fourth bit arrives the display shows the
#   equivalent hex digit.
#       Bin   1010  ->  shows  1010=A          (LEDs light as you type)
#       Bin   0111  ->  shows  0111=7
#
#   Clear or CE resets to the beginning at any point, and turns the
#   LEDs off. Pressing Hex or Bin again after an answer starts a new
#   conversion (any other key while an answer is showing is
#   ignored - press Hex or Bin to begin the next one).
#
# How it works
# -------------
#   A keypad-polling state machine, same shape as every earlier
#   exercise, with two independent entry modes instead of one:
#
#     STAGE 0   idle - waiting for Hex or Bin to choose a direction
#     STAGE 1   Hex mode - waiting for one hex digit
#     STAGE 2   Bin mode - collecting four bits
#     STAGE 3   answer is showing - Hex or Bin starts the next one
#
# Hex -> Bin: the digit already IS the nibble
# -----------------------------------------------
#   Because digit and hex-letter buttons already arrive as their raw
#   nibble value (0-15, per the note above), there is nothing to
#   decode - KEYVAL already holds the exact 4-bit value the digit
#   represents. Writing it straight to LEDS lights the matching bits
#   immediately:
#
#     ST_HEXENTRY:
#             LDA     [KEYVAL]
#             STA     [DISP]           # echo the digit as typed
#             LDA     [KEYVAL]
#             AND     $0F              # already 0-15; kept for safety
#             STA     [NIBBLE]
#             JMP     [SHOW_HEX_TO_BIN]
#
#   SHOW_HEX_TO_BIN then prints the four binary characters one at a
#   time, most-significant bit first, by shifting a saved copy right
#   by 3, then 2, then 1, then 0 places and masking off everything
#   but the bottom bit with AND $01:
#
#     LDA     [TEMP]
#     SHR
#     SHR
#     SHR                      # bit 3 is now in bit 0's position
#     AND     $01
#     OR      $30              # 0 or 1 -> ASCII '0' or '1'
#     STA     [DISP]
#
# Bin -> Hex: building a nibble one bit at a time
# ----------------------------------------------------
#   Typing bits most-significant-first is exactly how you'd read
#   them off a page, and it turns into a shift-and-OR each keypress:
#   shift the nibble-so-far left one place (making room, and
#   guaranteeing the new bottom bit is 0), then OR in whichever of 0
#   or 1 was just typed:
#
#     BIN_BIT:
#             LDA     [KEYVAL]
#             STA     [DISP]           # echo the '0' or '1' as typed
#             LDA     [NIBBLE]
#             SHL
#             OR      [KEYVAL]
#             STA     [NIBBLE]
#             STA     [LEDS]           # live feedback - light it now
#             LDA     [BITCNT]
#             INCA
#             STA     [BITCNT]
#             CMPA    $04
#             JZ      [SHOW_BIN_TO_HEX]
#             JMP     [WAIT]
#
#   After four bits, NIBBLE holds exactly the value that many binary
#   digits represent - 1,0,1,0 becomes 0001 -> 0010 -> 0101 -> 1010
#   as each SHL-then-OR runs, ending at decimal 10.
#
# A familiar three-way test, in a new job
# -------------------------------------------
#   Turning that nibble (0-15) into a displayable character needs a
#   digit '0'-'9' for 0-9, but a letter 'A'-'F' for 10-15 - and the
#   boundary between them needs the same three-way CMPA/JC/JZ test
#   exercises 10-13 use for "greater than or equal to" comparisons,
#   just repurposed here to classify a value instead of compare two
#   variables. A lone JC (checking only "strictly greater than 10")
#   would miss NIBBLE landing exactly on 10 - which is precisely the
#   input "1010" that this exercise most wants to get right, since
#   that's the whole point of typing four 1-or-0 digits to spell out
#   the letter A:
#
#     SHOW_BIN_TO_HEX:
#             LDA     $3D              # '='
#             STA     [DISP]
#             LDA     [NIBBLE]
#             CMPA    $0A
#             JC      [BTH_LETTER]     # C=1: NIBBLE > 10
#             JZ      [BTH_LETTER]     # Z=1: NIBBLE == 10 - this is 'A'
#             LDA     [NIBBLE]         # falls through: NIBBLE < 10
#             OR      $30
#             STA     [DISP]
#             JMP     [RESET_STATE]
#     BTH_LETTER:
#             LDA     [NIBBLE]
#             SUB     $0A              # 0-5
#             ADD     $41              # 'A'-'F'
#             STA     [DISP]
#             JMP     [RESET_STATE]
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run. Press Hex, then a hex digit -
#   watch the LEDs and the binary digits appear together. Press
#   Clear, then Bin, then type four bits (e.g. 1, 0, 1, 0) - watch
#   each LED light up as you go, then see "=A" appear once the
#   fourth bit lands. Try 1010 specifically to confirm the boundary
#   case above renders "A", not ":" (which is what OR $30 applied to
#   10 directly would wrongly produce).
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise to see
#   $F011 receive $45 (Hex) or $43 (Bin) the instant you press them,
#   and each bit land on $F011 as a plain $00/$01 while typing in Bin
#   mode. Watch $F032 change live as each LED updates.
#
# Try this next
# ---------------
#   - Wire up Dec too: after a Hex or Bin conversion, pressing Dec
#     could show the same nibble's decimal value (0-15) instead.
#   - Extend this to a full byte (two hex digits / eight bits)
#     instead of one nibble - you'll need a second LED port or to
#     show the byte across two conversions, since this Calculator
#     only has six LEDs to work with.
#   - Add input validation: right now, typing anything other than 0
#     or 1 in Bin mode is silently ignored rather than flagged.
# ================================================================

KEY:      .EQU    $F011
DISP:     .EQU    $F031
LEDS:     .EQU    $F032
BIN_KEY:  .EQU    $43        # code the Bin button sends (post-fix)
HEX_KEY:  .EQU    $45        # code the Hex button sends (post-fix)

        .ORG    $4000

START:  LDA     $00
        STA     [STAGE]        # begin idle, waiting for Hex or Bin

# ---------------------------------------------------------------
# Main loop - poll the keypad, dispatch on STAGE
# ---------------------------------------------------------------
WAIT:   LDA     [KEY]
        CMPA    $FF             # $FF = idle, no key waiting
        JZ      [WAIT]
        STA     [KEYVAL]        # stash it - this is the ONLY read of KEY

        CMPA    $1B             # Clear key
        JZ      [DO_CLEAR]
        CMPA    $7F             # CE key
        JZ      [DO_CLEAR]

        LDA     [STAGE]
        CMPA    $00
        JZ      [ST_IDLE]
        CMPA    $01
        JZ      [ST_HEXENTRY]
        CMPA    $02
        JZ      [ST_BINENTRY]
        JMP     [ST_ANSWER]      # only remaining value is STAGE 3

# ---------------------------------------------------------------
# STAGE 3 -> 0 : answer was showing - Hex/Bin starts a new one
# ---------------------------------------------------------------
ST_ANSWER:
        LDA     $1B              # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_IDLE]

# ---------------------------------------------------------------
# STAGE 0 : idle - waiting for Hex or Bin to pick a direction
# ---------------------------------------------------------------
ST_IDLE:
        LDA     [KEYVAL]
        CMPA    HEX_KEY
        JZ      [START_HEX]
        CMPA    BIN_KEY
        JZ      [START_BIN]
        JMP     [WAIT]           # anything else is ignored

START_HEX:
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

START_BIN:
        LDA     $00
        STA     [NIBBLE]
        LDA     $00
        STA     [BITCNT]
        LDA     $02
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : Hex mode - waiting for exactly one hex digit
# ---------------------------------------------------------------
ST_HEXENTRY:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F              # already 0-15; kept for safety
        STA     [NIBBLE]
        JMP     [SHOW_HEX_TO_BIN]

SHOW_HEX_TO_BIN:
        LDA     $3D              # '='
        STA     [DISP]

        LDA     [NIBBLE]
        STA     [LEDS]           # light the matching bits immediately
        STA     [TEMP]           # keep a copy - the shifts below destroy ACC

        LDA     [TEMP]
        SHR
        SHR
        SHR                      # bit 3 into bit 0's position
        AND     $01
        OR      $30
        STA     [DISP]

        LDA     [TEMP]
        SHR
        SHR                      # bit 2 into bit 0's position
        AND     $01
        OR      $30
        STA     [DISP]

        LDA     [TEMP]
        SHR                      # bit 1 into bit 0's position
        AND     $01
        OR      $30
        STA     [DISP]

        LDA     [TEMP]           # bit 0 is already in position
        AND     $01
        OR      $30
        STA     [DISP]

        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# STAGE 2 : Bin mode - collecting four bits, MSB first
# ---------------------------------------------------------------
ST_BINENTRY:
        LDA     [KEYVAL]
        CMPA    $00
        JZ      [BIN_BIT]
        CMPA    $01
        JZ      [BIN_BIT]
        JMP     [WAIT]           # anything but 0 or 1 is ignored

BIN_BIT:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the '0' or '1' as typed
        LDA     [NIBBLE]
        SHL                      # make room; new bottom bit is 0
        OR      [KEYVAL]         # merge in the bit just typed
        STA     [NIBBLE]
        STA     [LEDS]           # live feedback - light it now
        LDA     [BITCNT]
        INCA
        STA     [BITCNT]
        CMPA    $04
        JZ      [SHOW_BIN_TO_HEX]
        JMP     [WAIT]

SHOW_BIN_TO_HEX:
        LDA     $3D              # '='
        STA     [DISP]
        LDA     [NIBBLE]
        CMPA    $0A
        JC      [BTH_LETTER]     # C=1: NIBBLE > 10
        JZ      [BTH_LETTER]     # Z=1: NIBBLE == 10 - this is 'A'
        LDA     [NIBBLE]         # falls through: NIBBLE < 10
        OR      $30
        STA     [DISP]
        JMP     [RESET_STATE]
BTH_LETTER:
        LDA     [NIBBLE]
        SUB     $0A              # 0-5
        ADD     $41              # 'A'-'F'
        STA     [DISP]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Explicit Clear / CE handling - also blanks the LEDs
# ---------------------------------------------------------------
DO_CLEAR:
        LDA     $1B
        STA     [DISP]
        LDA     $00
        STA     [STAGE]
        LDA     $00
        STA     [LEDS]
        JMP     [WAIT]

RESET_STATE:
        LDA     $03              # STAGE 3: Hex/Bin starts a new conversion
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# Variables (reserved bytes - see exercise 09 for this pattern)
# ---------------------------------------------------------------
STAGE:   .BYTE
NIBBLE:  .BYTE
BITCNT:  .BYTE
KEYVAL:  .BYTE
TEMP:    .BYTE

        .END    $4000
