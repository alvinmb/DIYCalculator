# ================================================================
# test_calc.asm
# DIY Calculator Interface — display + LED + register test
#
# Assembler : das.py  (via the built-in Assembler / Editor window)
# Load addr : $4000   (assembled with .ORG $4000)
#
# What this test does
# -------------------
#   1. Clears the calculator display  (ESC = $1B  -> port $F031)
#   2. Writes "HELLO" one char at a time        -> port $F031
#   3. Turns on all 6 LEDs  ($3F = %00111111)  -> port $F032
#   4. Arithmetic sequence to drive CPU regs:
#        A = 10  (LOAD)
#        A = 15  (ADD  5)
#        A = 12  (SUB  3)
#        A = 13  (INCA)
#   5. HALT  — inspect ACC / flags in the CPU Register Display
#
# Ports
# -----
#   $F031  Calculator display  — printable ASCII appended;
#                                $1B / $0D / $00 clears screen
#   $F032  Calculator LEDs     — bits 5..0 = LEDs left to right
#                                (1 = bright red, 0 = dark red)
# ================================================================

        .ORG    $4000

# -- Symbolic port addresses -----------------------------------

CALCDSP: .EQU   $F031          # calculator display port
CALCLED: .EQU   $F032          # calculator LED port

# ==============================================================
# Step 1 — clear the display
# ==============================================================

        LDA     $1B            # ESC clears the display
        STA     [CALCDSP]      # -> $F031

# ==============================================================
# Step 2 — write "HELLO" to the calculator display
# ==============================================================

        LDA     $48            # 'H'
        STA     [CALCDSP]
        LDA     $45            # 'E'
        STA     [CALCDSP]
        LDA     $4C            # 'L'
        STA     [CALCDSP]
        LDA     $4C            # 'L'
        STA     [CALCDSP]
        LDA     $4F            # 'O'
        STA     [CALCDSP]

# ==============================================================
# Step 3 — LED strip: light all 6 LEDs
#   bit 5 = leftmost LED, bit 0 = rightmost LED
#   $3F = %00111111 -> all 6 LEDs ON
# ==============================================================

        LDA     $3F            # all 6 LEDs on
        STA     [CALCLED]      # -> $F032

# ==============================================================
# Step 4 — arithmetic to exercise CPU registers
# Expected final state: ACC=$0D (13), Z=0, N=0, C=0
# ==============================================================

        LDA     $0A            # ACC = 10  (0x0A)
        ADD     $05            # ACC = 15  (0x0F)  C=0 Z=0 N=0
        SUB     $03            # ACC = 12  (0x0C)
        INCA                   # ACC = 13  (0x0D)

# ==============================================================
# Done — HALT and inspect the CPU Register Display
# ==============================================================

        HALT

        .END    $4000
