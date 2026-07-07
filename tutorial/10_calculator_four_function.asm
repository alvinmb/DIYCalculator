# ================================================================
# 10_calculator_four_function.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# A working 4-function (+ - * /) calculator, built entirely from
# the primitives shown in exercises 05-09: keypad polling, the
# Calculator's own display, and simple assembly-language loops.
#
# What this program does
# -----------------------
#   Lets you type a single-digit sum on the Calculator, e.g.
#       5  +  3  =        ->  shows  5+3=8
#       7  *  8  =        ->  shows  7*8=56
#       2  -  9  =        ->  shows  2-9=-7
#       9  /  0  =        ->  shows  9/0=Err
#   Every keypress is echoed to the display as you type it, so the
#   full expression builds up on screen exactly like a real
#   calculator, then the '=' key replaces nothing - it just appends
#   the computed answer.
#
# Limitations (kept simple on purpose - see "Try this next")
# ------------------------------------------------------------
#   - Operands are single digits only (0-9), no multi-digit numbers
#     and no decimal point.
#   - Division shows the integer quotient only (no remainder).
#   - Dividing by zero shows "Err" instead of a number.
#
# How it works
# -------------
#   The program is a small state machine driven by KEY ($F011):
#
#     STAGE 0   waiting for the first digit  (operand 1)
#     STAGE 1   waiting for an operator      (+ - * /)
#     STAGE 2   waiting for the second digit (operand 2)
#     STAGE 3   waiting for '='  (or Enter)
#     STAGE 4   answer is showing - the next digit starts a new sum
#
#   $F011 is a read-clear latch (see exercise 05): each keypress is
#   read exactly once into KEYVAL and every later comparison in that
#   pass re-uses KEYVAL, since a second LDA [KEY] would just see the
#   $FF idle code.
#
#   Multiply is repeated addition (add OP1 to itself OP2 times) and
#   divide is repeated subtraction (subtract OP2 from OP1 while it
#   still fits, counting how many times) - the CPU has no hardware
#   MUL or DIV instruction, so every calculator and multiply/divide
#   routine on this machine builds the operation out of ADD/SUB in
#   a loop. Because operands here are single digits (0-9 at most),
#   the loops are at most 9 iterations - simple enough to read in
#   one sitting, unlike the 16-bit shift-add/shift-subtract versions
#   in Data/int-mult-2-byte.asm and Data/int-div-2-byte.asm, which
#   solve the same problem for much bigger numbers.
#
#   A note on this CPU's flags (read this before you adapt the
#   pattern below for your own code): SUB/CMPA set the Carry flag
#   to mean "the accumulator is STRICTLY GREATER THAN the operand"
#   - not the more usual "no borrow was needed" (which on most CPUs
#   also covers the equal case). That means a single "jump if
#   carry" or "jump if no-carry" branch only ever catches strictly-
#   greater or strictly-less; it silently gets the equal case wrong.
#   Every "is the left-hand side >= the right-hand side?" test in
#   this program - can OP1 still absorb another subtraction of OP2,
#   is the result >= 10, is OP1 >= OP2 for a same-sign subtraction -
#   therefore uses a three-way test instead of one branch: CMPA,
#   then JC for strictly-greater, JZ for exactly-equal, and only
#   falls through to "strictly less" if neither fired. This was
#   discovered (and is explained at length) in exercise 11's
#   circumference-button program; every exact-division and exact-
#   multiple-of-10 case here needed the same fix.
#
#   A second gotcha, this time about the DIY buttons themselves:
#   pressing a digit button does NOT send its ASCII code ($30-$39)
#   to $F011 - the button framework (tools/diy_button.py) silently
#   converts digit/hex-letter buttons down to a raw nibble (0-15)
#   before transmitting, so CPU programs can read keypad digits as
#   plain binary values. That means digit "1" actually arrives as
#   byte $01. The Calculator's CE button used to be assigned that
#   same byte ($01), making CE and digit "1" bit-for-bit identical
#   on the wire - pressing "1" was silently swallowed and treated as
#   a clear instead of a digit, since this program had no way to
#   tell the two keypresses apart. The real fix was to move CE to a
#   free byte outside the 0-15 nibble range ($7F) in _BUTTON_DEFAULTS
#   (tools/calculator.py), so it can never again collide with any
#   digit or hex-letter button; this program watches for that new
#   value below, alongside Clear ($1B, ESC) as the two ways to reset.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, then on the Calculator press:
#   a digit, an operator, a digit, then '=' (the calculator's '='
#   key, or Enter). Try all four operators, try a subtraction where
#   the second number is bigger (negative result), try dividing by
#   0, and try a case where the operator divides evenly or the
#   result is an exact multiple of 10 (e.g. 4/2, 2*5) - these are
#   exactly the "equal" edge cases the flag note above covers.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise to see
#   each keypress arrive on $F011 and each character land on $F031
#   in real time.
#
# Try this next
# ---------------
#   - Show the division remainder as well as the quotient.
#   - Accept two-digit operands (you'll need a second state per
#     operand and a decimal-to-binary combine step: tens*10 + ones).
#   - Replace repeated addition/subtraction with the shift-and-add /
#     shift-and-subtract algorithms from Data/fmult.asm and
#     Data/int-div-2-byte.asm - same idea, fewer loop iterations.
# ================================================================

KEY:     .EQU    $F011
DISP:    .EQU    $F031

        .ORG    $4000

START:  LDA     $00
        STA     [STAGE]        # begin waiting for the first digit

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
        JZ      [ST_OP1]
        CMPA    $01
        JZ      [ST_OPCODE]
        CMPA    $02
        JZ      [ST_OP2]
        CMPA    $04
        JZ      [ST_NEWCALC]
        JMP     [ST_EQUALS]     # only remaining value is STAGE 3

# ---------------------------------------------------------------
# STAGE 4 -> 0 : answer was showing, this digit starts a new sum
# ---------------------------------------------------------------
ST_NEWCALC:
        LDA     $1B             # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_OP1]

# ---------------------------------------------------------------
# STAGE 0 : first operand
# ---------------------------------------------------------------
ST_OP1: LDA     [KEYVAL]
        STA     [DISP]          # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F             # ASCII '0'-'9' -> binary 0-9
        STA     [OP1]
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : operator  (+ - * /)
# ---------------------------------------------------------------
ST_OPCODE:
        LDA     [KEYVAL]
        STA     [OPCODE]        # remember which operator was pressed
        STA     [DISP]          # echo it
        LDA     $02
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 2 : second operand
# ---------------------------------------------------------------
ST_OP2: LDA     [KEYVAL]
        STA     [DISP]
        LDA     [KEYVAL]
        AND     $0F
        STA     [OP2]
        LDA     $03
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 3 : waiting for '=' (or Enter) - ignore anything else
# ---------------------------------------------------------------
ST_EQUALS:
        LDA     [KEYVAL]
        CMPA    $3D             # '='
        JZ      [DO_EQUALS]
        CMPA    $0D             # Enter
        JZ      [DO_EQUALS]
        JMP     [WAIT]

DO_EQUALS:
        LDA     $3D
        STA     [DISP]          # echo the '=' sign

        LDA     [OPCODE]
        CMPA    $2B             # '+'
        JZ      [DO_ADD]
        CMPA    $2D             # '-'
        JZ      [DO_SUB]
        CMPA    $2A             # '*'
        JZ      [DO_MUL]
        CMPA    $2F             # '/'
        JZ      [DO_DIV]
        JMP     [WAIT]          # (shouldn't happen)

# ---------------------------------------------------------------
# Addition:  RESULT = OP1 + OP2   (max 9+9=18, always positive)
# ---------------------------------------------------------------
DO_ADD: LDA     [OP1]
        ADD     [OP2]
        STA     [RESULT]
        LDA     $00
        STA     [NEG]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Subtraction:  RESULT = OP1 - OP2  (negate + flag if OP1 < OP2)
#
# CMPA sets Carry only when OP1 is STRICTLY greater than OP2 (see
# the flag note up top), so both the greater-than case (C=1) and
# the equal case (Z=1, result is 0) need to reach SUB_POS - only
# OP1 strictly less than OP2 falls through to the negative branch.
# ---------------------------------------------------------------
DO_SUB: LDA     [OP1]
        CMPA    [OP2]
        JC      [SUB_POS]       # C=1: OP1 > OP2, no borrow needed
        JZ      [SUB_POS]       # Z=1: OP1 == OP2, result is 0, no borrow
        LDA     [OP2]           # OP1 < OP2: compute OP2-OP1 instead
        SUB     [OP1]
        STA     [RESULT]
        LDA     $01
        STA     [NEG]
        JMP     [SHOW_RESULT]
SUB_POS:
        LDA     [OP1]
        SUB     [OP2]
        STA     [RESULT]
        LDA     $00
        STA     [NEG]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Multiply:  RESULT = OP1 * OP2, via OP2 repeated additions of OP1
# (max 9*9=81 - fits comfortably in one byte)
# ---------------------------------------------------------------
DO_MUL: LDA     $00
        STA     [RESULT]
        LDA     [OP2]
        STA     [MCNT]
        JMP     [MUL_TEST]
MUL_LOOP:
        LDA     [RESULT]
        ADD     [OP1]
        STA     [RESULT]
        LDA     [MCNT]
        DECA
        STA     [MCNT]
MUL_TEST:
        LDA     [MCNT]
        CMPA    $00
        JNZ     [MUL_LOOP]
        LDA     $00
        STA     [NEG]
        JMP     [SHOW_RESULT]

# ---------------------------------------------------------------
# Divide:  RESULT = OP1 / OP2 (integer quotient), via repeated
# subtraction of OP2 from a running remainder. OP2=0 -> "Err".
#
# Loop while DREM >= OP2 (checked as: DREM strictly greater than
# OP2, OR DREM exactly equal to OP2 - the three-way CMPA/JC/JZ
# combination from the flag note up top; a lone JNC would stop one
# subtraction too early whenever OP2 divides OP1 evenly, e.g. 4/2).
# ---------------------------------------------------------------
DO_DIV: LDA     [OP2]
        CMPA    $00
        JZ      [DIV_ERR]

        LDA     $00
        STA     [RESULT]        # quotient, counts up
        LDA     [OP1]
        STA     [DREM]          # remainder, counts down
DIV_LOOP:
        LDA     [DREM]
        CMPA    [OP2]
        JC      [DIV_SUB]       # C=1: DREM > OP2, still fits
        JZ      [DIV_SUB]       # Z=1: DREM == OP2, still fits exactly
        JMP     [DIV_DONE]      # DREM < OP2, can't subtract again
DIV_SUB:
        LDA     [DREM]
        SUB     [OP2]
        STA     [DREM]
        LDA     [RESULT]
        INCA
        STA     [RESULT]
        JMP     [DIV_LOOP]
DIV_DONE:
        LDA     $00
        STA     [NEG]
        JMP     [SHOW_RESULT]

DIV_ERR:
        LDA     $45             # 'E'
        STA     [DISP]
        LDA     $72             # 'r'
        STA     [DISP]
        LDA     $72             # 'r'
        STA     [DISP]
        JMP     [RESET_STATE]

# ---------------------------------------------------------------
# Show RESULT (0-81, binary) as decimal digits, '-' first if NEG.
#
# Same three-way CMPA/JC/JZ test peels off the tens digit correctly
# even when RESULT is an exact multiple of 10 (e.g. 2*5=10) - a
# lone JNC would stop one subtraction too early and leave RESULT=10
# to be OR $30'd directly, producing ':' (0x3A) instead of "10".
# ---------------------------------------------------------------
SHOW_RESULT:
        LDA     [NEG]
        CMPA    $00
        JZ      [SR_TENS]
        LDA     $2D             # '-'
        STA     [DISP]

SR_TENS:
        LDA     $00
        STA     [TENS]
TENS_LOOP:
        LDA     [RESULT]
        CMPA    $0A
        JC      [TENS_SUB]      # C=1: RESULT > 10, still fits
        JZ      [TENS_SUB]      # Z=1: RESULT == 10, still fits exactly
        JMP     [TENS_DONE]     # RESULT < 10, tens digit is done
TENS_SUB:
        LDA     [RESULT]
        SUB     $0A
        STA     [RESULT]
        LDA     [TENS]
        INCA
        STA     [TENS]
        JMP     [TENS_LOOP]
TENS_DONE:
        LDA     [TENS]
        CMPA    $00
        JZ      [SR_ONES]       # no leading zero when tens digit is 0
        LDA     [TENS]
        OR      $30
        STA     [DISP]
SR_ONES:
        LDA     [RESULT]        # what's left (0-9) is the ones digit
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
        LDA     $04             # STAGE 4: next digit clears & restarts
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
NEG:     .BYTE
KEYVAL:  .BYTE
MCNT:    .BYTE
DREM:    .BYTE
TENS:    .BYTE

        .END    $4000
