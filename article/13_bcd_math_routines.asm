# ================================================================
# 13_bcd_math_routines.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# A 4-function (+ - * /) calculator built on packed BCD instead of
# plain binary - same idea as exercise 10, but every number in this
# program is stored the way this CPU's DADD/DSUB instructions expect:
# two decimal digits packed into one byte, one digit per nibble.
#
# What this program does
# -----------------------
#   Same look and feel as exercise 10, just with two-digit operands
#   (always type both digits - a leading zero for single-digit
#   values, e.g. 05):
#       2  3  +  1  4  =        ->  shows  23+14=37
#       0  9  /  0  3  =        ->  shows  09/03=03
#       0  5  -  1  2  =        ->  shows  05-12=Err       (negative - see "Limitations")
#       6  0  *  6  0  =        ->  shows  60*60=Err       (3600 needs 3 digits - see "Limitations")
#       9  9  /  0  0  =        ->  shows  99/00=Err
#
# Limitations (kept simple on purpose - see "Try this next")
# ------------------------------------------------------------
#   - Operands are two BCD digits only: 00-99.
#   - A result that would need a third digit (100 or more) shows
#     Err instead of wrapping or truncating - see "Packed BCD"
#     below for why this program has no easy way to show it.
#   - Subtraction shows Err instead of a negative number - there is
#     no packed-BCD "minus sign" convention used here (see "Try this
#     next" for how a real calculator would extend this).
#   - Division shows the integer quotient only (no remainder).
#
# Packed BCD: two decimal digits, one byte, no conversion needed
# -----------------------------------------------------------------
#   Every previous exercise stored numbers in plain binary and paid
#   for it at display time: exercises 10-12 all needed a repeated-
#   subtraction loop (subtract 10, or 100, again and again, counting
#   how many times) just to turn a binary total back into decimal
#   digits, because a binary byte has no idea where one decimal
#   digit ends and the next begins.
#
#   Packed BCD fixes that by never converting in the first place.
#   Each byte holds exactly two decimal digits, one per nibble - the
#   high nibble is the tens digit, the low nibble is the ones digit,
#   both always 0-9. The number 47 is stored as the single byte
#   $47 - not because 47 happens to equal 0x47 in binary (that is a
#   coincidence of how hex digits are written), but because the
#   nibble 4 and the nibble 7 are exactly the digits "47" is made of.
#   Reading a BCD byte back out is just splitting it into its two
#   nibbles and turning each into an ASCII character - no loop, no
#   subtraction, no math at all. SHOW_RESULT below is a third the
#   size of exercise 10's SHOW_RESULT for exactly this reason.
#
#   The catch is that ordinary ADD/SUB do not understand this
#   packing - ADD $47,$08 in plain binary gives $4F (a nibble of 15,
#   not a valid digit), because binary addition has no concept of
#   "carry at 10" the way decimal addition does. This CPU has four
#   extra instructions - DADD, DADDC, DSUB, DSUBC - that add and
#   subtract packed BCD bytes correctly: whenever a nibble would
#   overflow past 9, they carry (or borrow) 1 into the other nibble
#   automatically, the same way you carry a 1 when adding 47+8 by
#   hand. $47 DADD $08 correctly gives $55 (55), not $4F.
#
# How it works
# -------------
#   Same keypad-polling state machine as exercise 10, just with a
#   second digit per operand:
#
#     STAGE 0   waiting for the tens digit of operand 1
#     STAGE 1   waiting for the ones digit of operand 1
#     STAGE 2   waiting for an operator      (+ - * /)
#     STAGE 3   waiting for the tens digit of operand 2
#     STAGE 4   waiting for the ones digit of operand 2
#     STAGE 5   waiting for '='  (or Enter)
#     STAGE 6   answer is showing - the next digit starts a new sum
#
#   Packing two typed digits into one BCD byte needs no multiply or
#   decimal-composition trick (contrast exercise 12's TENS*10+ONES) -
#   a nibble is a fixed 4-bit-wide slot, so the tens digit just needs
#   shifting into the top half with SHL, and the ones digit ORs
#   straight into the bottom half:
#
#     LDA   [KEYVAL]
#     AND   $0F            # ASCII digit -> binary 0-9
#     SHL
#     SHL
#     SHL
#     SHL                  # 0-9 moved into the top nibble, bottom = 0
#     STA   [OP1]          # tens digit stored
#     ...
#     LDA   [KEYVAL]
#     AND   $0F
#     OR    [OP1]          # ones digit merges into the bottom nibble
#     STA   [OP1]          # OP1 is now a single packed-BCD byte
#
# Addition and the overflow check
# ---------------------------------
#   DADD does the packed add and reports, via Carry, whether the
#   true two-digit result needed a third digit (i.e. the sum was
#   100 or more - two BCD digits can only hold 00-99):
#
#     DO_ADD: LDA     [OP1]
#             DADD    [OP2]
#             STA     [RESULT]
#             JC      [ERR_OUT]   # sum >= 100 - doesn't fit in 2 digits
#             JMP     [SHOW_RESULT]
#
# Subtraction: DSUB's Carry means the OPPOSITE of SUB/CMPA's
# ------------------------------------------------------------------
#   This is the one flag detail worth slowing down for, because it
#   is the exact reverse of the rule exercises 10-12 hammer home.
#   Plain SUB/CMPA set Carry when the accumulator is STRICTLY
#   GREATER THAN the operand - not the usual "a borrow was needed."
#   DSUB does NOT share that quirk: its Carry means an honest,
#   conventional "yes, a borrow was needed" - which for a single
#   subtraction is exactly "the left-hand side was smaller than the
#   right-hand side." Subtracting 12 from 5 in BCD (05 DSUB 12)
#   correctly sets Carry, because 5 is less than 12; subtracting 5
#   from 5 (an equal case) correctly leaves Carry clear, because no
#   borrow was needed to reach zero. That means - unlike every
#   three-way CMPA/JC/JZ dance in exercises 10-12 - a single JC after
#   DSUB is already the complete, correct test:
#
#     DO_SUB: LDA     [OP1]
#             DSUB    [OP2]
#             STA     [RESULT]
#             JC      [ERR_OUT]   # a genuine borrow: OP1 was < OP2
#             JMP     [SHOW_RESULT]
#
#   (This program treats that as "can't show it" rather than
#   negating it - see "Try this next" for what a full negative-
#   number version would need.)
#
#   A note for anyone cross-checking this against the manufacturer's
#   own documentation: the official "DIY Calculator: BCD Instructions"
#   appendix (Rev 1.0, 2005) describes DSUB/DSUBC's Carry the other way
#   round - as a "borrow-not" bit (1 = no borrow needed, 0 = a borrow
#   happened), matching how the real hardware forms the subtraction
#   internally via a nines-complement add. This emulator deliberately
#   keeps the "honest borrow" polarity described above instead (1 = a
#   borrow was needed), since that's what this tutorial, its worked
#   examples, and the test suite are all built around. If you're
#   porting code from the printed appendix, just remember DSUB/DSUBC's
#   JC/JNC read backwards compared to the official doc.
#
# Multiply, and why the loop counter needs DSUB too
# ----------------------------------------------------
#   Multiply is still repeated addition, exactly like exercise 10 -
#   add OP1 to a running RESULT, OP2 times, using DADD instead of
#   ADD so the running total stays valid packed BCD, with the same
#   overflow check DO_ADD uses:
#
#     MUL_LOOP:
#             LDA     [RESULT]
#             DADD    [OP1]
#             STA     [RESULT]
#             JC      [ERR_OUT]    # running total spilled past 2 digits
#             LDA     [MCNT]
#             DSUB    $01          # NOT DECA - see below
#             STA     [MCNT]
#     MUL_TEST:
#             LDA     [MCNT]
#             CMPA    $00
#             JNZ     [MUL_LOOP]
#
#   MCNT counts down from OP2 to 0, one loop per multiplication. It
#   is tempting to count down with plain DECA, the way every counter
#   in exercises 09-12 did - but MCNT holds a packed BCD value here
#   (it started as OP2), and DECA is a plain binary decrement with no
#   idea that a nibble stops at 9. $30 (BCD 30) decremented with DECA
#   gives $2F - not $29 - because binary decrement borrows across the
#   whole byte instead of stopping at the nibble boundary, leaving an
#   invalid digit (F) sitting in the ones place. DSUB $01 decrements
#   the correct, BCD-aware way, so 30 counts down 30, 29, 28, ...,
#   1, 0 exactly as expected. Any loop counter built out of a BCD
#   value needs DSUB (or DADD, counting up) for this same reason -
#   plain INCA/DECA are only safe on counters that were never BCD to
#   begin with (like exercise 10's MCNT, which counted a plain binary
#   digit 0-9 and never crossed a nibble boundary).
#
# Divide: DSUB doubles as both the test and the subtraction
# ---------------------------------------------------------------
#   Divide is repeated subtraction again, but DSUB's honest borrow
#   flag lets the loop skip the separate CMPA "does it still fit?"
#   check exercise 10 needed. DSUB itself IS the test: try the
#   subtraction, and only keep the result if no borrow was needed:
#
#     DIV_LOOP:
#             LDA     [DREM]
#             DSUB    [OP2]
#             JC      [DIV_DONE]   # borrowed - DREM was < OP2, stop
#             STA     [DREM]       # no borrow - the subtraction stands
#             LDA     [RESULT]
#             DADD    $01          # quotient += 1 (BCD)
#             STA     [RESULT]
#             JMP     [DIV_LOOP]
#     DIV_DONE:
#
#   When DSUB does borrow, its result is a meaningless wrapped value
#   (exactly like subtracting 5-8 by hand and refusing to borrow -
#   the digits come out wrong) - so it is simply never stored; DREM
#   is left exactly as it was before that attempt, which is correct,
#   since that attempt should not have happened.
#
# Displaying a packed BCD byte: no loop needed at all
# -------------------------------------------------------
#   This is the payoff mentioned up top. RESULT already holds two
#   correct decimal digits, one per nibble, so showing it is just
#   isolating each nibble and turning it into ASCII with OR $30 -
#   the tens digit needs shifting down into position first (SHR four
#   times moves the top nibble into the bottom, filling the vacated
#   top bits with 0, exactly undoing the SHL packing done at entry):
#
#     LDA     [RESULT]
#     STA     [TEMP]         # keep a copy - the shifts below destroy it
#     SHR
#     SHR
#     SHR
#     SHR                    # tens digit, 0-9, now in the low nibble
#     CMPA    $00
#     JZ      [SR_ONES]      # suppress a leading zero, same as exercise 10
#     OR      $30
#     STA     [DISP]
#     SR_ONES:
#     LDA     [TEMP]
#     AND     $0F            # ones digit
#     OR      $30
#     STA     [DISP]
#
#   Compare this to exercise 10's SHOW_RESULT, which needed a whole
#   repeated-subtraction TENS_LOOP to get the same two digits out of
#   a plain binary RESULT. That loop is gone here - not simplified,
#   just genuinely unnecessary, because the digits were never lost
#   in the first place.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, then on the Calculator press:
#   two digits, an operator, two digits, then '=' (or Enter). Try
#   09/03=03 to see exact division, 05-12 to see the borrow/Err path,
#   99/00 for divide-by-zero, and something like 60*60 to see the
#   overflow Err path (60*60=3600, needs four digits - nowhere close
#   to fitting in one packed-BCD byte).
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise to watch
#   each keypress arrive on $F011, and Registers to watch the Carry
#   flag flip after each DADD/DSUB - notice it behaves like an
#   ordinary "did this operation overflow/borrow?" flag here, the
#   opposite of plain SUB/CMPA's quirky "strictly greater than".
#
# Try this next
# ---------------
#   - Add a NEG flag and a '-' sign, the way exercise 10 handles a
#     negative result, so 05-12 shows -07 instead of Err. You will
#     need to compute OP2 DSUB OP1 instead when the first attempt
#     borrows, exactly mirroring exercise 10's DO_SUB.
#   - Extend RESULT to two packed-BCD bytes (four digits, 0000-9999)
#     using DADDC/DSUBC to chain the carry/borrow between them, the
#     BCD equivalent of exercise 11's 16-bit RESULT/RESULT+1.
#   - Show the division remainder (DREM already holds it when
#     DIV_DONE is reached) alongside the quotient.
# ================================================================

KEY:     .EQU    $F011
DISP:    .EQU    $F031

        .ORG    $4000

START:  LDA     $00
        STA     [STAGE]        # begin waiting for operand 1's tens digit

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
        JZ      [ST_OP1_TENS]
        CMPA    $01
        JZ      [ST_OP1_ONES]
        CMPA    $02
        JZ      [ST_OPCODE]
        CMPA    $03
        JZ      [ST_OP2_TENS]
        CMPA    $04
        JZ      [ST_OP2_ONES]
        CMPA    $06
        JZ      [ST_NEWCALC]
        JMP     [ST_EQUALS]      # only remaining value is STAGE 5

# ---------------------------------------------------------------
# STAGE 6 -> 0 : answer was showing, this digit starts a new sum
# ---------------------------------------------------------------
ST_NEWCALC:
        LDA     $1B              # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_OP1_TENS]

# ---------------------------------------------------------------
# STAGE 0 : operand 1, tens digit -> top nibble of OP1
# ---------------------------------------------------------------
ST_OP1_TENS:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F              # ASCII '0'-'9' -> binary 0-9
        SHL
        SHL
        SHL
        SHL                      # move it into the top nibble
        STA     [OP1]
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : operand 1, ones digit -> bottom nibble of OP1
# ---------------------------------------------------------------
ST_OP1_ONES:
        LDA     [KEYVAL]
        STA     [DISP]
        LDA     [KEYVAL]
        AND     $0F
        OR      [OP1]            # merge with the tens nibble already there
        STA     [OP1]            # OP1 is now one packed-BCD byte, 00-99
        LDA     $02
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 2 : operator  (+ - * /)
# ---------------------------------------------------------------
ST_OPCODE:
        LDA     [KEYVAL]
        STA     [OPCODE]         # remember which operator was pressed
        STA     [DISP]           # echo it
        LDA     $03
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 3 : operand 2, tens digit -> top nibble of OP2
# ---------------------------------------------------------------
ST_OP2_TENS:
        LDA     [KEYVAL]
        STA     [DISP]
        LDA     [KEYVAL]
        AND     $0F
        SHL
        SHL
        SHL
        SHL
        STA     [OP2]
        LDA     $04
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 4 : operand 2, ones digit -> bottom nibble of OP2
# ---------------------------------------------------------------
ST_OP2_ONES:
        LDA     [KEYVAL]
        STA     [DISP]
        LDA     [KEYVAL]
        AND     $0F
        OR      [OP2]
        STA     [OP2]
        LDA     $05
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 5 : waiting for '=' (or Enter) - ignore anything else
# ---------------------------------------------------------------
ST_EQUALS:
        LDA     [KEYVAL]
        CMPA    $3D              # '='
        JZ      [DO_EQUALS]
        CMPA    $0D              # Enter
        JZ      [DO_EQUALS]
        JMP     [WAIT]

DO_EQUALS:
        LDA     $3D
        STA     [DISP]           # echo the '=' sign

        LDA     [OPCODE]
        CMPA    $2B              # '+'
        JZ      [DO_ADD]
        CMPA    $2D              # '-'
        JZ      [DO_SUB]
        CMPA    $2A              # '*'
        JZ      [DO_MUL]
        CMPA    $2F              # '/'
        JZ      [DO_DIV]
        JMP     [WAIT]           # (shouldn't happen)

# ---------------------------------------------------------------
# Addition:  RESULT = OP1 + OP2 (packed BCD). Carry after DADD means
# the true sum needed a third digit (>= 100) - too big to show here.
# ---------------------------------------------------------------
DO_ADD: LDA     [OP1]
        DADD    [OP2]
        STA     [RESULT]
        JC      [ERR_OUT]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Subtraction:  RESULT = OP1 - OP2 (packed BCD). Unlike plain
# SUB/CMPA, DSUB's Carry means an ordinary "a borrow was needed" -
# OP1 was strictly less than OP2 - so one JC is the whole test (see
# the header note for the full explanation of why this is the
# opposite convention from exercises 10-12).
# ---------------------------------------------------------------
DO_SUB: LDA     [OP1]
        DSUB    [OP2]
        STA     [RESULT]
        JC      [ERR_OUT]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Multiply:  RESULT = OP1 * OP2, via OP2 repeated BCD additions of
# OP1. MCNT (the loop countdown) is itself a packed-BCD value, so it
# must count down with DSUB $01, not DECA - see the header note.
# ---------------------------------------------------------------
DO_MUL: LDA     $00
        STA     [RESULT]
        LDA     [OP2]
        STA     [MCNT]
        JMP     [MUL_TEST]
MUL_LOOP:
        LDA     [RESULT]
        DADD    [OP1]
        STA     [RESULT]
        JC      [ERR_OUT]        # running total spilled past 2 digits
        LDA     [MCNT]
        DSUB    $01              # BCD decrement - NOT DECA
        STA     [MCNT]
MUL_TEST:
        LDA     [MCNT]
        CMPA    $00
        JNZ     [MUL_LOOP]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Divide:  RESULT = OP1 / OP2 (integer quotient), via repeated BCD
# subtraction of OP2 from a running remainder. OP2=0 -> Err. DSUB's
# own Carry flag doubles as the "does it still fit?" test - see the
# header note for why no separate CMPA is needed here.
# ---------------------------------------------------------------
DO_DIV: LDA     [OP2]
        CMPA    $00
        JZ      [ERR_OUT]

        LDA     $00
        STA     [RESULT]         # quotient, BCD, counts up
        LDA     [OP1]
        STA     [DREM]           # remainder, BCD, counts down
DIV_LOOP:
        LDA     [DREM]
        DSUB    [OP2]
        JC      [DIV_DONE]       # borrowed - DREM < OP2, stop here
        STA     [DREM]           # no borrow - the subtraction stands
        LDA     [RESULT]
        DADD    $01              # quotient += 1 (BCD)
        STA     [RESULT]
        JMP     [DIV_LOOP]
DIV_DONE:
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Out-of-range result for whichever operator was pressed
# ---------------------------------------------------------------
ERR_OUT:
        LDA     $45              # 'E'
        STA     [DISP]
        LDA     $72              # 'r'
        STA     [DISP]
        LDA     $72              # 'r'
        STA     [DISP]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Show RESULT: a packed-BCD byte needs no conversion loop, just a
# nibble split - see the header note for the full explanation.
# ---------------------------------------------------------------
SHOW_RESULT:
        LDA     [RESULT]
        STA     [TEMP]           # keep a copy - SHR below destroys ACC
        SHR
        SHR
        SHR
        SHR                      # tens digit, 0-9, now in the low nibble
        CMPA    $00
        JZ      [SR_ONES]        # suppress a leading zero on the tens digit
        OR      $30
        STA     [DISP]
SR_ONES:
        LDA     [TEMP]
        AND     $0F              # ones digit
        OR      $30
        STA     [DISP]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Explicit Clear / CE handling
# ---------------------------------------------------------------
DO_CLEAR:
        LDA     $1B
        STA     [DISP]
        LDA     $00
        STA     [STAGE]
        JMP     [WAIT]

RESET_STATE:
        LDA     $06              # STAGE 6: next digit clears & restarts
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# Variables (reserved bytes - see exercise 09 for this pattern)
# ---------------------------------------------------------------
STAGE:   .BYTE
OP1:     .BYTE
OP2:     .BYTE
OPCODE:  .BYTE
RESULT:  .BYTE
TEMP:    .BYTE
KEYVAL:  .BYTE
MCNT:    .BYTE
DREM:    .BYTE

        .END    $4000
