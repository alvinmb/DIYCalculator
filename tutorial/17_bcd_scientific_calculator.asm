# ================================================================
# 17_bcd_scientific_calculator.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# A small scientific calculator: type a two-digit value, press Sin,
# Cos, Tan, x^2, or n!, and read the answer off the display. Unlike
# exercise 12 (which stored everything in plain binary), the typed
# value here is packed BCD throughout, the same representation
# exercise 13's four-function calculator uses - x^2 and n! are
# genuine BCD arithmetic (DADD, the same way exercise 13 multiplies),
# not table lookups.
#
# What this program does
# -----------------------
#   Type a two-digit value (always two digits - a leading zero for
#   single-digit values, e.g. 05), then press one of the five
#   scientific keys:
#       4  5   Sin    ->  shows  45Sin=0.71
#       4  5   Cos    ->  shows  45Cos=0.71
#       4  5   Tan    ->  shows  45Tan=1.00
#       9  0   Sin    ->  shows  90Sin=1.00
#       9  0   Tan    ->  shows  90Tan=Err   (out of range - see below)
#       0  4   x^2    ->  shows  04x^2=16
#       1  2   x^2    ->  shows  12x^2=Err   (144 needs 3 digits)
#       0  4   n!     ->  shows  04n!=24
#       0  5   n!     ->  shows  05n!=Err    (120 needs 3 digits)
#   Sin and Cos accept 00-90. Tan accepts 00-68 (see exercise 12 for
#   why tan's table has to stop there - the same limit applies here).
#   x^2 and n! both top out well before 99 in packed BCD (two digits,
#   00-99 only) - anything whose true answer needs a third digit
#   shows Err instead, the same convention exercise 13 uses for its
#   four operators.
#
# Why x^2 and n! are "real" BCD arithmetic, but Sin/Cos/Tan aren't
# -------------------------------------------------------------------
#   x^2 and n! are computed with this CPU's DADD instruction, exactly
#   the way exercise 13 builds multiply out of repeated BCD addition -
#   x^2 is just "add X to a running total, X times" (X*X), and n! is
#   "multiply the running total by X, X-1, X-2, ... down to 1", where
#   each of those multiplies is itself a repeated-BCD-addition loop.
#   Every intermediate value stays packed BCD from typed input to
#   displayed output - see DO_SQR and DO_FAC below.
#
#   Sine, cosine, and tangent can't be built out of adds and
#   subtracts at all (see exercise 12's header for the full
#   explanation) - the only way this CPU produces them is the same
#   precomputed lookup table exercise 12 uses, addressed by a plain
#   binary index. Since the typed value is stored as packed BCD here
#   (not plain binary, like exercise 12), BCD_TO_BIN below converts
#   it to a binary 0-99 index before every trig lookup - the table
#   itself, and the FORMAT_VAL display routine that turns a table
#   entry into "W.FF" on screen, are carried over from exercise 12
#   unchanged, since a lookup table has no "BCD version" to switch to.
#
# How it works
# -------------
#   Same keypad-polling state machine as exercises 10-13:
#
#     STAGE 0   waiting for the tens digit of X
#     STAGE 1   waiting for the ones digit of X
#     STAGE 2   waiting for Sin, Cos, Tan, x^2, or n!
#     STAGE 3   answer is showing - next digit clears and restarts
#
#   Entry packs the two typed digits into one BCD byte (XVAL) exactly
#   the way exercise 13 packs each operand - SHL x4 moves the tens
#   digit into the top nibble, then OR merges the ones digit into the
#   bottom nibble.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run. START clears the display first
#   (the display isn't blank by default - it still shows whatever the
#   last program left there), so the exercise always begins on a clean
#   screen no matter what ran before it. Type two digits, then press
#   Sin, Cos, Tan, x^2, or n!. Try the overflow cases above to see the
#   Err path, and try Clear/CE mid-entry to confirm a fresh sum starts
#   cleanly.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status to see $F011 receive each digit
#   and function code, and Registers to watch the Carry flag after
#   each DADD in DO_SQR/DO_FAC - that's the overflow test firing.
#
# Try this next
# ---------------
#   - Add Log and 1/x. Log has no cheap BCD trick either (another
#     lookup table, same BCD_TO_BIN conversion this program already
#     does for Sin/Cos/Tan); 1/x needs a genuine fractional result
#     representation this program doesn't have yet.
#   - Extend x^2's range past two digits using DADDC to chain a
#     second BCD byte, the same way exercise 13's "Try this next"
#     suggests for its four operators.
# ================================================================

KEY:      .EQU    $F011
DISP:     .EQU    $F031
SIN_KEY:  .EQU    $3A
COS_KEY:  .EQU    $39
TAN_KEY:  .EQU    $38
SQR_KEY:  .EQU    $3D        # x^2
FAC_KEY:  .EQU    $36        # n!

        .ORG    $4000

START:  LDA     $1B             # clear code - the display isn't blank on
        STA     [DISP]          # its own; it still holds whatever the
                                 # previously run program left showing
        LDA     $00
        STA     [STAGE]        # begin waiting for the tens digit

# ---------------------------------------------------------------
# Main loop - poll the keypad, dispatch on STAGE
# ---------------------------------------------------------------
WAIT:   LDA     [KEY]
        CMPA    $FF             # $FF = idle, no key waiting
        JZ      [WAIT]
        STA     [KEYVAL]        # stash it - this is the ONLY read of KEY

        CMPA    $10             # Clear key
        JZ      [DO_CLEAR]
        CMPA    $11             # CE key
        JZ      [DO_CLEAR]

        LDA     [STAGE]
        CMPA    $00
        JZ      [ST_TENS]
        CMPA    $01
        JZ      [ST_ONES]
        CMPA    $03
        JZ      [ST_NEWCALC]
        JMP     [ST_FUNC]        # only remaining value is STAGE 2

# ---------------------------------------------------------------
# STAGE 3 -> 0 : answer was showing, this digit starts a new value
# ---------------------------------------------------------------
ST_NEWCALC:
        LDA     $1B              # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_TENS]

# ---------------------------------------------------------------
# STAGE 0 : tens digit -> top nibble of XVAL (packed BCD)
# ---------------------------------------------------------------
ST_TENS:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F              # ASCII '0'-'9' -> binary 0-9
        SHL
        SHL
        SHL
        SHL                      # move it into the top nibble
        STA     [XVAL]
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : ones digit -> bottom nibble of XVAL
# ---------------------------------------------------------------
ST_ONES:
        LDA     [KEYVAL]
        STA     [DISP]
        LDA     [KEYVAL]
        AND     $0F
        OR      [XVAL]           # merge with the tens nibble already there
        STA     [XVAL]           # XVAL is now one packed-BCD byte, 00-99
        LDA     $02
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 2 : waiting for Sin, Cos, Tan, x^2, or n! - ignore anything else
# ---------------------------------------------------------------
ST_FUNC:
        LDA     [KEYVAL]
        STA     [FUNCKEY]         # remembered for the display echo below
        CMPA    SIN_KEY
        JZ      [DO_SIN]
        CMPA    COS_KEY
        JZ      [DO_COS]
        CMPA    TAN_KEY
        JZ      [DO_TAN]
        CMPA    SQR_KEY
        JZ      [DO_SQR]
        CMPA    FAC_KEY
        JZ      [DO_FAC]
        JMP     [WAIT]

# ---------------------------------------------------------------
# BCD_TO_BIN - convert packed-BCD XVAL into a plain-binary 0-99
# value in BINVAL, for use as a table index (BLDX/[TABLE,X] need an
# ordinary binary offset, not a packed-BCD byte). Same tens*10+ones
# combine exercise 12 uses, just starting from BCD nibbles instead
# of two separately-typed digits.
# ---------------------------------------------------------------
BCD_TO_BIN:
        LDA     [XVAL]
        STA     [TEMP]
        SHR
        SHR
        SHR
        SHR                      # tens digit (0-9), now in the low nibble
        STA     [TCNT]
        LDA     $00
        STA     [BINVAL]
        JMP     [B2B_TEST]
B2B_LOOP:
        LDA     [BINVAL]
        ADD     $0A              # +10 per tens digit (plain binary add -
        STA     [BINVAL]         # BINVAL itself is never BCD)
        LDA     [TCNT]
        DECA
        STA     [TCNT]
B2B_TEST:
        LDA     [TCNT]
        CMPA    $00
        JNZ     [B2B_LOOP]

        LDA     [TEMP]
        AND     $0F              # ones digit (0-9)
        ADD     [BINVAL]
        STA     [BINVAL]         # BINVAL = tens*10+ones, plain binary 0-99
        RTS

# ---------------------------------------------------------------
# Sin and Cos: valid for XVAL 00-90. Look up SIN_TABLE[BINVAL]
# (scaled x100, plain binary - same table format as exercise 12) and
# format it with FORMAT_VAL.
# ---------------------------------------------------------------
DO_SIN: JSR     [BCD_TO_BIN]
        LDA     [BINVAL]
        CMPA    $5A              # 90 decimal
        JC      [ERR_OUT]        # BINVAL > 90: outside this table
        LDA     $00
        STA     [DEGIDX]
        LDA     [BINVAL]
        STA     [DEGIDX+1]
        BLDX    [DEGIDX]
        LDA     [SIN_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

DO_COS: JSR     [BCD_TO_BIN]
        LDA     [BINVAL]
        CMPA    $5A              # 90 decimal
        JC      [ERR_OUT]
        LDA     $00
        STA     [DEGIDX]
        LDA     [BINVAL]
        STA     [DEGIDX+1]
        BLDX    [DEGIDX]
        LDA     [COS_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Tan: valid for XVAL 00-68 only - same table-size limit as
# exercise 12 (tan(69)x100 = 261, too big for one byte).
# ---------------------------------------------------------------
DO_TAN: JSR     [BCD_TO_BIN]
        LDA     [BINVAL]
        CMPA    $44              # 68 decimal
        JC      [ERR_OUT]
        LDA     $00
        STA     [DEGIDX]
        LDA     [BINVAL]
        STA     [DEGIDX+1]
        BLDX    [DEGIDX]
        LDA     [TAN_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# x^2:  RESULT = XVAL * XVAL, in packed BCD, via XVAL repeated BCD
# additions of XVAL - exactly exercise 13's DO_MUL pattern with both
# operands equal to XVAL. MCNT is itself packed BCD (it started as
# XVAL), so it counts down with DSUB $01, not DECA - see exercise
# 13's header note for why.
# ---------------------------------------------------------------
DO_SQR: LDA     $00
        STA     [RESULT]
        LDA     [XVAL]
        STA     [MCNT]
        JMP     [SQR_TEST]
SQR_LOOP:
        LDA     [RESULT]
        DADD    [XVAL]
        STA     [RESULT]
        JC      [ERR_OUT]        # running total spilled past 2 digits
        LDA     [MCNT]
        DSUB    $01
        STA     [MCNT]
SQR_TEST:
        LDA     [MCNT]
        CMPA    $00
        JNZ     [SQR_LOOP]
        JMP     [SHOW_BCD_RESULT]

# ---------------------------------------------------------------
# n!:  RESULT = XVAL * (XVAL-1) * (XVAL-2) * ... * 1, in packed BCD.
#
# FCNT counts down from XVAL to 1 (BCD, DSUB $01). Each pass
# multiplies RESULT by FCNT the same way DO_SQR multiplies - by
# repeated BCD addition - using FICNT as that inner loop's own
# countdown and FMUL_ACC to hold the value being repeatedly added
# (RESULT itself is rebuilt from $00 as the inner loop runs, so it
# can't also be the thing being added).
# 0! and 1! both correctly come out as 1 (RESULT starts at 1 and the
# loop never subtracts below it for XVAL 0 or 1).
# ---------------------------------------------------------------
DO_FAC: LDA     $01
        STA     [RESULT]         # 0! = 1! = 1
        LDA     [XVAL]
        CMPA    $00
        JZ      [SHOW_BCD_RESULT]
        LDA     $01
        CMPA    [XVAL]
        JZ      [SHOW_BCD_RESULT] # XVAL == 1: RESULT already 1, done
        LDA     [XVAL]
        STA     [FCNT]
FAC_TEST:
        LDA     [FCNT]
        CMPA    $00
        JZ      [SHOW_BCD_RESULT]

        LDA     [RESULT]
        STA     [FMUL_ACC]        # value to add, repeatedly, below
        LDA     $00
        STA     [RESULT]          # rebuilt as FCNT copies of FMUL_ACC
        LDA     [FCNT]
        STA     [FICNT]
FAC_INNER:
        LDA     [FICNT]
        CMPA    $00
        JZ      [FAC_INNER_DONE]
        LDA     [RESULT]
        DADD    [FMUL_ACC]
        STA     [RESULT]
        JC      [ERR_OUT]         # running total spilled past 2 digits
        LDA     [FICNT]
        DSUB    $01
        STA     [FICNT]
        JMP     [FAC_INNER]
FAC_INNER_DONE:
        LDA     [FCNT]
        DSUB    $01
        STA     [FCNT]
        JMP     [FAC_TEST]

# ---------------------------------------------------------------
# Out-of-range or overflowed result for whichever function was pressed
# ---------------------------------------------------------------
ERR_OUT:
        JSR     [ECHO_FUNC]
        LDA     $3D              # '='
        STA     [DISP]
        LDA     $45              # 'E'
        STA     [DISP]
        LDA     $72              # 'r'
        STA     [DISP]
        LDA     $72              # 'r'
        STA     [DISP]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# ECHO_FUNC - print the two/three-letter name of whichever
# scientific key was pressed (FUNCKEY), so the expression on screen
# reads e.g. "45Sin=0.71" instead of just "45=0.71". Called once,
# from FORMAT_VAL/SHOW_BCD_RESULT's shared entry points below.
# ---------------------------------------------------------------
ECHO_FUNC:
        LDA     [FUNCKEY]
        CMPA    SIN_KEY
        JZ      [EF_SIN]
        CMPA    COS_KEY
        JZ      [EF_COS]
        CMPA    TAN_KEY
        JZ      [EF_TAN]
        CMPA    SQR_KEY
        JZ      [EF_SQR]
        JMP     [EF_FAC]         # only remaining key is n!

EF_SIN: LDA     $53              # 'S'
        STA     [DISP]
        LDA     $69              # 'i'
        STA     [DISP]
        LDA     $6E              # 'n'
        STA     [DISP]
        RTS
EF_COS: LDA     $43              # 'C'
        STA     [DISP]
        LDA     $6F              # 'o'
        STA     [DISP]
        LDA     $73              # 's'
        STA     [DISP]
        RTS
EF_TAN: LDA     $54              # 'T'
        STA     [DISP]
        LDA     $61              # 'a'
        STA     [DISP]
        LDA     $6E              # 'n'
        STA     [DISP]
        RTS
EF_SQR: LDA     $78              # 'x'
        STA     [DISP]
        LDA     $5E              # '^'
        STA     [DISP]
        LDA     $32              # '2'
        STA     [DISP]
        RTS
EF_FAC: LDA     $6E              # 'n'
        STA     [DISP]
        LDA     $21              # '!'
        STA     [DISP]
        RTS

# ---------------------------------------------------------------
# FORMAT_VAL - shared by DO_SIN/DO_COS/DO_TAN via JSR/RTS. Carried
# over from exercise 12 unchanged (see the header note on why the
# trig table/display path has no BCD version).
#
# Turns VAL (0-255, meaning 0.00-2.55) into "Fn=W.FF" on the display
# (Fn from ECHO_FUNC, then '=', then the value):
#   1. Subtract 100 from VAL while it still fits - the count (0-2)
#      is the single whole-number digit.
#   2. Subtract 10 from what's left while it still fits - the count
#      (0-9) is the tenths digit; whatever remains (0-9) is the
#      hundredths digit.
# ---------------------------------------------------------------
FORMAT_VAL:
        JSR     [ECHO_FUNC]
        LDA     $3D              # '='
        STA     [DISP]

        LDA     $00
        STA     [WHOLE]
FV_100_LOOP:
        LDA     [VAL]
        CMPA    $64              # 100
        JC      [FV_100_SUB]     # C=1: VAL > 100
        JZ      [FV_100_SUB]     # Z=1: VAL == 100
        JMP     [FV_100_DONE]    # VAL < 100, done
FV_100_SUB:
        LDA     [VAL]
        SUB     $64
        STA     [VAL]
        LDA     [WHOLE]
        INCA
        STA     [WHOLE]
        JMP     [FV_100_LOOP]
FV_100_DONE:
        LDA     [WHOLE]          # single digit, 0-2
        OR      $30
        STA     [DISP]
        LDA     $2E              # '.'
        STA     [DISP]

        LDA     $00
        STA     [FTENS]
FV_10_LOOP:
        LDA     [VAL]
        CMPA    $0A
        JC      [FV_10_SUB]      # C=1: VAL > 10
        JZ      [FV_10_SUB]      # Z=1: VAL == 10
        JMP     [FV_10_DONE]     # VAL < 10, done
FV_10_SUB:
        LDA     [VAL]
        SUB     $0A
        STA     [VAL]
        LDA     [FTENS]
        INCA
        STA     [FTENS]
        JMP     [FV_10_LOOP]
FV_10_DONE:
        LDA     [FTENS]          # tenths digit - always shown, no
        OR      $30              # leading-zero suppression, so the
        STA     [DISP]           # fraction always prints as 2 digits
        LDA     [VAL]            # hundredths digit, whatever is left
        OR      $30
        STA     [DISP]

        RTS

# ---------------------------------------------------------------
# SHOW_BCD_RESULT - shared by DO_SQR/DO_FAC. RESULT is already
# packed BCD (00-99), so unlike FORMAT_VAL this needs no conversion
# loop at all - just split the nibbles (see exercise 13's header
# note for the full explanation of why packed BCD skips the loop).
# ---------------------------------------------------------------
SHOW_BCD_RESULT:
        JSR     [ECHO_FUNC]
        LDA     $3D              # '='
        STA     [DISP]

        LDA     [RESULT]
        STA     [TEMP]           # keep a copy - SHR below destroys ACC
        SHR
        SHR
        SHR
        SHR                      # tens digit, 0-9, now in the low nibble
        CMPA    $00
        JZ      [SBR_ONES]       # suppress a leading zero on the tens digit
        OR      $30
        STA     [DISP]
SBR_ONES:
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
        LDA     $03              # STAGE 3: next digit clears & restarts
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# Variables (reserved bytes - see exercise 09 for this pattern)
# ---------------------------------------------------------------
STAGE:    .BYTE
XVAL:     .BYTE       # packed BCD, 00-99, the typed value
KEYVAL:   .BYTE
FUNCKEY:  .BYTE
TEMP:     .BYTE
TCNT:     .BYTE
BINVAL:   .BYTE       # XVAL converted to plain binary, for table indexing
DEGIDX:   .2BYTE
VAL:      .BYTE       # trig table result, binary fixed-point x100
WHOLE:    .BYTE
FTENS:    .BYTE
RESULT:   .BYTE       # packed BCD, x^2/n! result
MCNT:     .BYTE
FCNT:     .BYTE
FICNT:    .BYTE
FMUL_ACC: .BYTE

# ---------------------------------------------------------------
# SIN_TABLE[d] = round(sin(d degrees) x 100), d = 0..90
# (identical to exercise 12's table - see that exercise for how it
# was generated)
# ---------------------------------------------------------------
SIN_TABLE:
        .BYTE   $00, $02, $03, $05, $07, $09, $0A, $0C, $0E, $10
        .BYTE   $11, $13, $15, $16, $18, $1A, $1C, $1D, $1F, $21
        .BYTE   $22, $24, $25, $27, $29, $2A, $2C, $2D, $2F, $30
        .BYTE   $32, $34, $35, $36, $38, $39, $3B, $3C, $3E, $3F
        .BYTE   $40, $42, $43, $44, $45, $47, $48, $49, $4A, $4B
        .BYTE   $4D, $4E, $4F, $50, $51, $52, $53, $54, $55, $56
        .BYTE   $57, $57, $58, $59, $5A, $5B, $5B, $5C, $5D, $5D
        .BYTE   $5E, $5F, $5F, $60, $60, $61, $61, $61, $62, $62
        .BYTE   $62, $63, $63, $63, $63, $64, $64, $64, $64, $64
        .BYTE   $64

# ---------------------------------------------------------------
# COS_TABLE[d] = round(cos(d degrees) x 100), d = 0..90
# ---------------------------------------------------------------
COS_TABLE:
        .BYTE   $64, $64, $64, $64, $64, $64, $63, $63, $63, $63
        .BYTE   $62, $62, $62, $61, $61, $61, $60, $60, $5F, $5F
        .BYTE   $5E, $5D, $5D, $5C, $5B, $5B, $5A, $59, $58, $57
        .BYTE   $57, $56, $55, $54, $53, $52, $51, $50, $4F, $4E
        .BYTE   $4D, $4B, $4A, $49, $48, $47, $45, $44, $43, $42
        .BYTE   $40, $3F, $3E, $3C, $3B, $39, $38, $36, $35, $34
        .BYTE   $32, $30, $2F, $2D, $2C, $2A, $29, $27, $25, $24
        .BYTE   $22, $21, $1F, $1D, $1C, $1A, $18, $16, $15, $13
        .BYTE   $11, $10, $0E, $0C, $0A, $09, $07, $05, $03, $02
        .BYTE   $00

# ---------------------------------------------------------------
# TAN_TABLE[d] = round(tan(d degrees) x 100), d = 0..68 only - see
# exercise 12's header note: tan(69)x100 = 261, too big for one byte.
# ---------------------------------------------------------------
TAN_TABLE:
        .BYTE   $00, $02, $03, $05, $07, $09, $0B, $0C, $0E, $10
        .BYTE   $12, $13, $15, $17, $19, $1B, $1D, $1F, $20, $22
        .BYTE   $24, $26, $28, $2A, $2D, $2F, $31, $33, $35, $37
        .BYTE   $3A, $3C, $3E, $41, $43, $46, $49, $4B, $4E, $51
        .BYTE   $54, $57, $5A, $5D, $61, $64, $68, $6B, $6F, $73
        .BYTE   $77, $7B, $80, $85, $8A, $8F, $94, $9A, $A0, $A6
        .BYTE   $AD, $B4, $BC, $C4, $CD, $D6, $E1, $EC, $F8

        .END    $4000
