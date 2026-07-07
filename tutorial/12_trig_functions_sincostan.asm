# ================================================================
# 12_trig_functions_sincostan.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# Type an angle in degrees, press Sin, Cos, or Tan, and read the
# answer straight off the display.
#
# Before you assemble this: no button setup needed
# -------------------------------------------------
#   Exercise 11 had to claim a blank button because Circumference
#   isn't a button the Calculator already has. Sin, Cos, and Tan are
#   different - they're real buttons in the scientific column on the
#   left of the keypad already, wired up in _BUTTON_DEFAULTS same as
#   every other key:
#       Sin -> Code $73   Cos -> Code $63   Tan -> Code $74
#   Nothing currently listens for those three bytes on port $F011,
#   so today they light up and do nothing. This exercise is what
#   makes them do something - just assemble, load, and run; there is
#   no Configure Button Attributes step to do first.
#
# What this program does
# -----------------------
#   Type a two-digit angle in degrees (always two digits - type a
#   leading zero for single-digit angles, e.g. 05 for 5 degrees),
#   then press Sin, Cos, or Tan. The display fills in "=" followed
#   by the answer to two decimal places:
#       4  5   Sin    ->  shows  =0.71
#       4  5   Cos    ->  shows  =0.71
#       4  5   Tan    ->  shows  =1.00
#       9  0   Sin    ->  shows  =1.00
#       0  0   Cos    ->  shows  =1.00
#       9  0   Tan    ->  shows  =Err   (tangent has no finite value
#                                        at 90 degrees)
#   Sin and Cos accept any angle from 00 to 90. Tan only goes up to
#   68 - see "How it works" for why - anything past that (including
#   90) shows Err, the same way exercise 10 shows Err for divide by
#   zero rather than a wrong number.
#
# How it works
# -------------
#   Same keypad-polling state machine as exercises 10 and 11, just
#   with one more stage for the second digit:
#
#     STAGE 0   waiting for the tens digit of the angle
#     STAGE 1   waiting for the ones digit of the angle
#     STAGE 2   waiting for Sin, Cos, or Tan
#     STAGE 3   answer is showing - next digit clears and restarts
#
#   The interesting part is how the actual sine/cosine/tangent gets
#   computed, because this CPU has no MUL or DIV instruction and no
#   idea what a fraction is - every value in it is a plain 0-255
#   whole number. Exercises 10 and 11 got by with ADD and repeated
#   subtraction because + and - (and even x and / by a fixed amount
#   like 2xpi) can be built out of those. Sine and cosine can't -
#   there's no short loop of adds and subtracts that produces
#   "the sine of 37 degrees" from scratch.
#
#   The trick is to not compute it at all. A table of every answer,
#   worked out ahead of time and assembled straight into the
#   program as data, is just as valid a "function" as a formula -
#   looking a value up is exactly what a function does, and a table
#   lookup is something this CPU is very good at. So SIN_TABLE below
#   holds 91 bytes: entry 0 is sin(0 degrees) x100 rounded to the
#   nearest whole number, entry 1 is sin(1 degree) x100, and so on
#   up to entry 90 = sin(90 degrees) x100 = 100. (The x100 scaling
#   is the same fixed-point idea exercise 11 used for pi - it turns
#   "0.71" into the whole number 71, which this CPU can actually
#   store.) COS_TABLE is the same idea for cosine. Reading the
#   angle straight out of memory and using it as an index into
#   these tables - byte SIN_TABLE+37 IS sin(37 degrees)x100, no
#   arithmetic required - is the entire "calculation".
#
#   Doing this needs the Index register (IX), which exercise 09
#   introduced for walking a message character by character. The
#   same [TABLE,X] addressing mode - "read the byte at TABLE's
#   address, plus whatever is currently in IX" - is exactly a table
#   lookup once IX holds the angle instead of a walking counter.
#   BLDX loads IX from a 2-byte memory location (the same
#   big-endian, high-byte-first layout as RESULT in exercise 11),
#   so DEGIDX below exists purely to hold the angle as a 2-byte
#   value (high byte always $00, low byte the angle 0-99) so BLDX
#   has somewhere 16-bit to load it from.
#
#   Tangent is built from the exact same kind of table (TAN_TABLE),
#   but it can't cover the same 0-90 range. Mathematically tan(x)
#   grows without bound as x approaches 90 - tan(89) is already
#   about 57.3 - and this table can only hold whole numbers 0-255
#   per byte (max representable is 2.55 once scaled x100). tan(68)
#   x100 rounds to 248, right up against that ceiling; tan(69)x100
#   would be 261, which no longer fits in a byte. So TAN_TABLE stops
#   at 68 entries, and DO_TAN checks the angle against that limit
#   the same way exercise 10's DO_DIV checks for a zero divisor
#   before it would produce a nonsense answer - out of range means
#   Err, not a wrong number silently truncated to fit.
#
#   One new instruction shows up here: JSR / RTS. Sin, Cos, and Tan
#   all finish the exact same way - take whatever byte the table
#   lookup produced (0-255, meaning 0.00-2.55) and turn it into
#   "=W.FF" on the display - so that display-formatting code is
#   written once, as a subroutine (FORMAT_VAL), and JSR [FORMAT_VAL]
#   calls it from all three places. JSR pushes the return address on
#   the stack and jumps there; RTS at the end of FORMAT_VAL pops
#   that address back off and returns to right after the JSR that
#   called it - which is why DO_SIN, DO_COS, and DO_TAN can each
#   JSR the same routine and each correctly come back to their own
#   JMP [RESET_STATE] afterwards, instead of all three ending up in
#   the same place.
#
#   FORMAT_VAL itself is just exercise 11's repeated-subtraction
#   decimal conversion again, run twice: subtract 100 from VAL while
#   it still fits (the count becomes the one whole-number digit,
#   0-2), then subtract 10 from what's left while it still fits (the
#   count becomes the tenths digit, 0-9, and whatever remains after
#   that, also 0-9, is the hundredths digit) - both loops use the
#   same CMPA/JC/JZ "greater-than-or-equal" pair exercises 10 and 11
#   rely on throughout, since this CPU's Carry flag alone only means
#   strictly-greater-than (see either of those exercises for the
#   full explanation if you haven't read it yet).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run. On the Calculator, type two
#   digits (e.g. 3 0 for 30 degrees), then press Sin, Cos, or Tan.
#   Check the answer against any calculator's sin/cos/tan in degree
#   mode - it should match to two decimal places (tan will be
#   slightly rounder near its table limit, since a single byte only
#   has so much room).
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise to see
#   $F011 receive $73/$63/$74 the instant you press Sin/Cos/Tan, and
#   Registers to watch IX load with the angle right before each
#   table lookup.
#
# Try this next
# ---------------
#   - Extend TAN_TABLE's usable range by scaling it x10 instead of
#     x100 (less precision, but tan(x) up to about 25 would then fit
#     in a byte) or by storing it as a 2-byte table the way RESULT
#     was 16-bit in exercise 11.
#   - Add an ASin/ACos/ATan button that runs SIN_TABLE "backwards" -
#     scan it for the closest match to a typed value and report the
#     index (angle) that produced it.
#   - Accept a flexible one-or-two-digit angle instead of always
#     requiring two digits, the same extension suggested for the
#     radius in exercise 11.
# ================================================================

KEY:      .EQU    $F011
DISP:     .EQU    $F031
SIN_KEY:  .EQU    $73        # code the Sin button already sends
COS_KEY:  .EQU    $63        # code the Cos button already sends
TAN_KEY:  .EQU    $74        # code the Tan button already sends

        .ORG    $4000

START:  LDA     $00
        STA     [STAGE]        # begin waiting for the tens digit

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
        JZ      [ST_TENS]
        CMPA    $01
        JZ      [ST_ONES]
        CMPA    $03
        JZ      [ST_NEWCALC]
        JMP     [ST_FUNC]        # only remaining value is STAGE 2

# ---------------------------------------------------------------
# STAGE 3 -> 0 : answer was showing, this digit starts a new one
# ---------------------------------------------------------------
ST_NEWCALC:
        LDA     $1B              # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_TENS]

# ---------------------------------------------------------------
# STAGE 0 : tens digit of the angle
# ---------------------------------------------------------------
ST_TENS:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F              # ASCII '0'-'9' -> binary 0-9
        STA     [TENS]
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : ones digit of the angle -> combine into DEG = TENS*10+ONES
# ---------------------------------------------------------------
ST_ONES:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F
        STA     [ONES]

        LDA     $00
        STA     [DEG]
        LDA     [TENS]
        STA     [CNT]
        JMP     [MUL10_TEST]
MUL10_LOOP:
        LDA     [DEG]
        ADD     $0A              # +10 per tens digit, no carry needed:
        STA     [DEG]            # DEG never exceeds 99 here
        LDA     [CNT]
        DECA
        STA     [CNT]
MUL10_TEST:
        LDA     [CNT]
        CMPA    $00
        JNZ     [MUL10_LOOP]

        LDA     [DEG]
        ADD     [ONES]
        STA     [DEG]

        LDA     $02
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 2 : waiting for Sin, Cos, or Tan - ignore anything else
# ---------------------------------------------------------------
ST_FUNC:
        LDA     [KEYVAL]
        CMPA    SIN_KEY
        JZ      [DO_SIN]
        CMPA    COS_KEY
        JZ      [DO_COS]
        CMPA    TAN_KEY
        JZ      [DO_TAN]
        JMP     [WAIT]

# ---------------------------------------------------------------
# Sin and Cos: valid for DEG 0-90. Look up SIN_TABLE[DEG] (already
# scaled x100) and format it.
# ---------------------------------------------------------------
DO_SIN:
        LDA     [DEG]
        CMPA    $5A              # 90 decimal
        JC      [ERR_OUT]        # DEG > 90: outside this table
        LDA     $00
        STA     [DEGIDX]         # high byte of the 16-bit index = 0
        LDA     [DEG]
        STA     [DEGIDX+1]       # low byte = the angle itself
        BLDX    [DEGIDX]
        LDA     [SIN_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

DO_COS:
        LDA     [DEG]
        CMPA    $5A              # 90 decimal
        JC      [ERR_OUT]        # DEG > 90: outside this table
        LDA     $00
        STA     [DEGIDX]
        LDA     [DEG]
        STA     [DEGIDX+1]
        BLDX    [DEGIDX]
        LDA     [COS_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Tan: only valid for DEG 0-68 here - see the header note on why
# TAN_TABLE has to stop there. 69 and up (including 90) show Err.
# ---------------------------------------------------------------
DO_TAN:
        LDA     [DEG]
        CMPA    $44              # 68 decimal
        JC      [ERR_OUT]        # DEG > 68: table stops here
        LDA     $00
        STA     [DEGIDX]
        LDA     [DEG]
        STA     [DEGIDX+1]
        BLDX    [DEGIDX]
        LDA     [TAN_TABLE,X]
        STA     [VAL]
        JSR     [FORMAT_VAL]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Out-of-range angle for whichever function was pressed
# ---------------------------------------------------------------
ERR_OUT:
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
# FORMAT_VAL - shared by DO_SIN/DO_COS/DO_TAN via JSR/RTS.
#
# Turns VAL (0-255, meaning 0.00-2.55) into "=W.FF" on the display:
#   1. Subtract 100 from VAL while it still fits - the count (0-2)
#      is the single whole-number digit.
#   2. Subtract 10 from what's left while it still fits - the count
#      (0-9) is the tenths digit; whatever remains (0-9) is the
#      hundredths digit.
# Both loops use the CMPA/JC/JZ "greater-than-or-equal" pair, same
# reason as exercises 10 and 11: a lone JNC would miss the case
# where VAL lands exactly on 100 or exactly on 10.
# ---------------------------------------------------------------
FORMAT_VAL:
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
TENS:     .BYTE
ONES:     .BYTE
DEG:      .BYTE
CNT:      .BYTE
KEYVAL:   .BYTE
DEGIDX:   .2BYTE
VAL:      .BYTE
WHOLE:    .BYTE
FTENS:    .BYTE

# ---------------------------------------------------------------
# SIN_TABLE[d] = round(sin(d degrees) x 100), d = 0..90
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
# the header note: tan(69)x100 = 261, too big for one byte.
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
