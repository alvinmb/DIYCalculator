# ================================================================
# 11_circle_circumference_button.asm
# Beboputer Hands-On Tutorial — Bonus Exercise (Calculator)
#
# Give the Calculator a new button: type a radius, press it, and
# read off the circle's circumference.
#
# Before you assemble this: create the button
# ----------------------------------------------
#   Every key on the Calculator - digits, operators, Sin, Cos, all
#   of them - is a "DIY Button" that just writes one fixed byte to
#   port $F011 when clicked (see tools/diy_button.py). The left-hand
#   bank has a 5x4 grid of blank buttons kept in reserve for exactly
#   this - each one defaults to Code $00, Description "Unassigned",
#   meaning it isn't wired to anything yet and is free to use. This
#   exercise claims one of those instead of repurposing a button
#   (like Sin) that already has a role of its own.
#
#     1. With the Calculator switched OFF, right-click any blank
#        button in that left-hand grid to open Configure Button
#        Attributes (top-left slot is a good default choice).
#     2. Change Annotation to  Circ
#     3. Change Description to  Circumference from radius
#     4. Change Code to  $80  - this program watches for that same
#        value, so the button and the program agree on what byte
#        means "compute the circumference". ($80 is free: nothing
#        in _BUTTON_DEFAULTS uses it, and it falls outside the
#        ASCII digit/hex-letter ranges diy_button.py special-cases,
#        so it passes straight through unchanged.)
#     5. Click OK, then switch the Calculator back ON.
#
#   That's the whole trick: a "custom button" is just a label and a
#   byte value. All the actual behaviour - reading the radius,
#   doing the math, showing the answer - lives entirely in this
#   .asm program, exactly like every other exercise so far.
#
#   Keep this layout: clicking OK auto-saves the button to
#   Config/defbuttons.ini, but that file is shared by every exercise
#   - reconfiguring a different button later, or clicking File ->
#   Restore Defaults, overwrites it and this button reverts to
#   "Unassigned". To keep a copy you can always get back, use File ->
#   Save Button File... once you're happy with the setup. The dialog
#   defaults to %APPDATA%\PY-DIYCALCULATOR\buttons, but save it into
#   %APPDATA%\PY-DIYCALCULATOR\Config instead - the same folder
#   defbuttons.ini lives in - so the backup (e.g. circ_button.ini)
#   sits right next to it and you can restore by copying it back over
#   defbuttons.ini directly, as well as via File -> Load Button File....
#
# What this program does
# -----------------------
#   Type a single digit (0-9) for the radius, then press Circ. The
#   display fills in "=" followed by the circumference, e.g.
#       9  Circ        ->  shows  9=56.5
#       1  Circ        ->  shows  1=6.2
#       0  Circ        ->  shows  0=0.0
#   Circumference = 2 x pi x radius. Since this only ever works
#   with a single-digit radius (0-9), the answer never needs more
#   than two whole-number digits plus one decimal place.
#
# How it works
# -------------
#   Same keypad-polling state machine as exercise 10:
#
#     STAGE 0   waiting for the radius digit
#     STAGE 1   waiting for the Circ button
#     STAGE 2   answer is showing - next digit clears and restarts
#
#   The new part is the arithmetic. 2 x pi is approximately 6.28,
#   which isn't a whole number - and this CPU only does integer
#   arithmetic. The fix is the same trick real fixed-point code
#   uses everywhere: scale pi up by 100 first (pi -> 314), so
#   2 x pi x 100 becomes the whole number 628. Multiplying that by
#   the radius gives the circumference already multiplied by 100
#   (so 56.52 arrives as the whole number 5652) - then dividing
#   back down by 100 at display time peels the decimal point back
#   off. 314/100 is only accurate to about 2 decimal places, which
#   is why the exercise only ever shows one decimal digit.
#
#   628 x 9 = 5652 no longer fits in one byte (max 255), so unlike
#   exercise 10 the running total here is a 16-bit value, RESULT /
#   RESULT+1 (high byte / low byte, the same big-endian layout used
#   for .2BYTE elsewhere in this codebase - see Data/int-mult-2-
#   byte.asm). Adding 628 to it 9 times uses ADD on the low bytes
#   and ADDC (add-with-carry) on the high bytes, so a carry out of
#   the low byte correctly ripples into the high byte - the 16-bit
#   equivalent of carrying a 1 when you add by hand. (ADD/ADDC's
#   carry chains the ordinary way on this CPU - it's only the
#   subtract side that needs the workaround explained below.)
#
#   Turning that 16-bit total back into digits happens in two
#   passes, both built from the same repeated-subtraction idea as
#   exercise 10's decimal conversion:
#     1. Subtract 100 from RESULT until it won't fit any more. The
#        count is the whole-number part of the circumference
#        (always <= 56, so it fits back in one byte from here on);
#        whatever is left (0-99) is the fractional part times 100.
#     2. Subtract 10 from that leftover until it won't fit any
#        more. That count (0-9) is the one decimal digit shown.
#
#   A note on this CPU's flags (read this if you're adapting the
#   pattern below for your own code):
#     SUB/CMPA set the Carry flag to mean "accumulator is STRICTLY
#     GREATER THAN the operand" - not the more usual "no borrow was
#     needed" (which on most CPUs also covers the equal case). One
#     consequence: after CMPA K, the pair "JC greater / JZ equal /
#     falls through to less-than" is what you need to test
#     "is ACC >= K" - a lone JNC does NOT cover the equal case, it
#     only catches strictly-less-than.
#       The second consequence is bigger: chaining SUBC after SUB to
#     do a 16-bit subtract does NOT work on this CPU, because SUBC
#     consumes the Carry flag as if it directly were "borrow needed"
#     - but Carry from the preceding SUB means the opposite thing
#     (greater-than) in the common case, so SUBC ends up subtracting
#     one too many from the high byte whenever the low-byte
#     subtraction did NOT need to borrow, and one too few when it
#     did. Both DIV100_LOOP and TENTHS_LOOP/WTENS_LOOP below use a
#     manual borrow test instead: subtract the low byte, then look
#     at the flags from THAT subtraction to decide by hand whether
#     to knock 1 off the high byte, rather than trusting SUBC to do
#     it. This was verified empirically against the real CPU - see
#     the project notes for the test cases that pin this down
#     (e.g. 628-100 with SUBC alone silently loses 256 from the
#     high byte; the manual-borrow version gets 528 exactly right).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run. On the Calculator, type a
#   digit 0-9, then press Circ (the blank button you just
#   configured). Compare the answer against 2 x pi x radius on any
#   calculator - it should match to one decimal place.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status alongside this exercise to see
#   $F011 receive $80 (Circ) the moment you click it, and each
#   character land on $F031 as the answer is written out.
#
# Try this next
# ---------------
#   - Add an "Area" button too (area = pi x r x r - you'll need to
#     multiply the radius by itself first, then by 314, then divide
#     by 100 twice since both the squaring and the pi-scaling add a
#     factor of 100).
#   - Use a closer approximation of pi (e.g. 3142, scaled by 1000
#     instead of 100) for one more decimal digit of accuracy.
#   - Accept a two-digit radius, the same extension suggested at
#     the end of exercise 10.
# ================================================================

KEY:      .EQU    $F011
DISP:     .EQU    $F031
CIRC_KEY: .EQU    $80        # code assigned to the blank "Circ" button

        .ORG    $4000

START:  LDA     $00
        STA     [STAGE]        # begin waiting for the radius digit

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
        JZ      [ST_RADIUS]
        CMPA    $02
        JZ      [ST_NEWCALC]
        JMP     [ST_CIRC]        # only remaining value is STAGE 1

# ---------------------------------------------------------------
# STAGE 2 -> 0 : answer was showing, this digit starts a new one
# ---------------------------------------------------------------
ST_NEWCALC:
        LDA     $1B              # clear code - wipes the old expression
        STA     [DISP]
        JMP     [ST_RADIUS]

# ---------------------------------------------------------------
# STAGE 0 : radius digit
# ---------------------------------------------------------------
ST_RADIUS:
        LDA     [KEYVAL]
        STA     [DISP]           # echo the digit as typed
        LDA     [KEYVAL]
        AND     $0F              # ASCII '0'-'9' -> binary 0-9
        STA     [RADIUS]
        LDA     $01
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# STAGE 1 : waiting for Circ - ignore anything else
# ---------------------------------------------------------------
ST_CIRC:
        LDA     [KEYVAL]
        CMPA    CIRC_KEY
        JZ      [DO_CIRC]
        JMP     [WAIT]

# ---------------------------------------------------------------
# RESULT (16-bit, big-endian: RESULT=hi, RESULT+1=lo)
#       = K * RADIUS = 628 * RADIUS
#       = circumference, x100  (2 x pi x radius x 100, pi = 3.14)
# ---------------------------------------------------------------
DO_CIRC:
        LDA     $3D              # '=' sign
        STA     [DISP]

        LDA     $00
        STA     [RESULT]
        STA     [RESULT+1]
        LDA     [RADIUS]
        STA     [CNT]
        JMP     [MUL_TEST]
MUL_LOOP:
        LDA     [RESULT+1]       # low byte
        ADD     [K+1]            # + K's low byte
        STA     [RESULT+1]
        LDA     [RESULT]         # high byte
        ADDC    [K]              # + K's high byte + carry
        STA     [RESULT]
        LDA     [CNT]
        DECA
        STA     [CNT]
MUL_TEST:
        LDA     [CNT]
        CMPA    $00
        JNZ     [MUL_LOOP]

# ---------------------------------------------------------------
# Divide RESULT by 100 -> WHOLE (integer circumference, fits in a
# byte: max 56) and a 0-99 remainder left behind in RESULT+1.
#
# Loop while RESULT >= 100 (checked as: high byte nonzero, OR low
# byte strictly greater than 100, OR low byte equal to 100 - that
# three-way CMPA/JNZ + JC + JZ combination is what "greater-than-
# or-equal" actually takes on this CPU, per the flag note above).
#
# Each subtraction is a manual-borrow 16-bit subtract: SUB the low
# byte by 100 first, then look at ITS flags (not SUBC) to decide
# whether the high byte needs to lose 1 - JC or JZ after that SUB
# means the low byte did NOT need to borrow (it was >= 100), so the
# high byte is left alone; otherwise it borrowed, so the high byte
# is decremented by 1 with a plain SUB $01.
# ---------------------------------------------------------------
        LDA     $00
        STA     [WHOLE]
DIV100_LOOP:
        LDA     [RESULT]         # high byte
        CMPA    $00
        JNZ     [DIV100_SUB]     # nonzero -> RESULT >= 256 > 100, subtract
        LDA     [RESULT+1]       # high byte is 0 - compare low byte to 100
        CMPA    $64
        JC      [DIV100_SUB]     # C=1: low byte > 100, subtract
        JZ      [DIV100_SUB]     # Z=1: low byte == 100, subtract
        JMP     [DIV100_DONE]    # otherwise low byte < 100, stop
DIV100_SUB:
        LDA     [RESULT+1]
        SUB     $64              # 100 decimal
        STA     [RESULT+1]
        JC      [DIV100_NOBORROW]  # C=1: old low byte > 100, no borrow
        JZ      [DIV100_NOBORROW]  # Z=1: old low byte == 100, no borrow
        LDA     [RESULT]           # borrow: high byte loses 1
        SUB     $01
        STA     [RESULT]
        JMP     [DIV100_CNT]
DIV100_NOBORROW:
        LDA     [RESULT]           # no borrow: high byte unchanged
        STA     [RESULT]
DIV100_CNT:
        LDA     [WHOLE]
        INCA
        STA     [WHOLE]
        JMP     [DIV100_LOOP]
DIV100_DONE:

# ---------------------------------------------------------------
# Divide the 0-99 remainder by 10 -> TENTHS (the one decimal digit
# shown). What's left after that (hundredths) is simply dropped.
#
# This is only ever an 8-bit value, so no borrow chaining is
# needed - just the same CMPA/JC/JZ "greater-than-or-equal" test
# used above, in place of the single JNC this loop used to use
# (JNC alone missed the case where REM was exactly 10).
# ---------------------------------------------------------------
        LDA     [RESULT+1]
        STA     [REM]
        LDA     $00
        STA     [TENTHS]
TENTHS_LOOP:
        LDA     [REM]
        CMPA    $0A
        JC      [TENTHS_SUB]     # C=1: REM > 10
        JZ      [TENTHS_SUB]     # Z=1: REM == 10
        JMP     [TENTHS_DONE]    # REM < 10, done
TENTHS_SUB:
        LDA     [REM]
        SUB     $0A
        STA     [REM]
        LDA     [TENTHS]
        INCA
        STA     [TENTHS]
        JMP     [TENTHS_LOOP]
TENTHS_DONE:

# ---------------------------------------------------------------
# Display WHOLE (tens + ones, no leading zero) . TENTHS
#
# Same fix here as TENTHS_LOOP above: CMPA/JC/JZ instead of a lone
# JNC, so a WHOLE of exactly 10, 20, ... 50 peels off a tens digit
# correctly instead of stopping one iteration short.
# ---------------------------------------------------------------
        LDA     $00
        STA     [WTENS]
WTENS_LOOP:
        LDA     [WHOLE]
        CMPA    $0A
        JC      [WTENS_SUB]      # C=1: WHOLE > 10
        JZ      [WTENS_SUB]      # Z=1: WHOLE == 10
        JMP     [WTENS_DONE]     # WHOLE < 10, done
WTENS_SUB:
        LDA     [WHOLE]
        SUB     $0A
        STA     [WHOLE]
        LDA     [WTENS]
        INCA
        STA     [WTENS]
        JMP     [WTENS_LOOP]
WTENS_DONE:
        LDA     [WTENS]
        CMPA    $00
        JZ      [W_ONES]         # skip leading zero on the tens digit
        LDA     [WTENS]
        OR      $30
        STA     [DISP]
W_ONES: LDA     [WHOLE]          # what's left (0-9) is the ones digit
        OR      $30
        STA     [DISP]

        LDA     $2E              # '.'
        STA     [DISP]

        LDA     [TENTHS]
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
        LDA     $02              # STAGE 2: next digit clears & restarts
        STA     [STAGE]
        JMP     [WAIT]

# ---------------------------------------------------------------
# Variables (reserved bytes - see exercise 09 for this pattern)
# ---------------------------------------------------------------
STAGE:    .BYTE
RADIUS:   .BYTE
KEYVAL:   .BYTE
CNT:      .BYTE
RESULT:   .2BYTE
WHOLE:    .BYTE
WTENS:    .BYTE
REM:      .BYTE
TENTHS:   .BYTE

K:        .2BYTE  $0274         # 628 decimal = 2 x pi(3.14) x 100

        .END    $4000
