# ================================================================
# 19_tiny_basic.asm
# Beboputer Hands-On Tutorial - A Tiny BASIC Interpreter
#
# A small interactive BASIC-style interpreter that runs entirely on
# the emulated Beboputer CPU, using the on-screen Keyboard for input
# and the Terminal for output.
#
# Try it
# -------
#   Open Tools -> Keyboard... and Display -> Terminal, assemble this
#   file, Load -> CPU, click Run, then click on the Terminal/Keyboard
#   to type. Press CAPS on the Keyboard tool first -- this
#   interpreter only understands upper-case letters.
#
# Language
# ---------
#   Type one statement per line, press ENTER after each. Statements
#   are numbered 0, 1, 2... in the order you type them (that number
#   is what GOTO/THEN jump to -- there is no line renumbering or
#   editing, and no backspace, because the Terminal hardware has no
#   way to erase a character once it is on screen). Type RUN on its
#   own line when you are done entering statements.
#
#     LETv=e            set variable v (A-Z) to expression e
#     PRINTe            print a number/expression, then a newline
#     PRINT"text"        print a literal string, then a newline
#     INPUTv             prompt "?" and read a number into v
#     IFe1<e2THENn        e1 relop e2 (relop is <, =, or >) ->
#     IFe1=e2THENn         jump to statement n if true
#     IFe1>e2THENn
#     GOTOn               jump to statement n
#     POKEa=e             write e (0-255) to RAM address a
#     END                 stop the program
#
#   An expression e is a single term, or two terms joined by + or -:
#   TERM, TERM+TERM, or TERM-TERM. A term is either a 1-3 digit
#   decimal number (0-255; values wrap past 255, there is no
#   overflow check), a single variable letter A-Z, or PEEKa (the
#   byte currently stored at RAM address a). There is no operator
#   precedence to worry about because there is never more than one
#   operator -- PEEKa always binds to its own address argument
#   first, so PEEKA+10 means "(the byte at address A) + 10", not
#   "the byte at address A+10". No spaces are allowed anywhere in a
#   statement -- this is a fixed-format mini-language, not a
#   forgiving one. Up to 10 statements (0-9), each up to 24
#   characters, fit in one program.
#
#   An address a (used by PEEK and POKE) is a 1-3 digit decimal
#   number (0-255, reaches RAM page zero only), a $ followed by 1-4
#   uppercase hex digits (0-65535, reaches anywhere -- including the
#   memory-mapped I/O ports, e.g. PEEK$F011 reads the Keyboard latch
#   and POKE$F031=72 writes to the Calculator's display port), or a
#   single variable letter A-Z (its 0-255 value is used as a page-
#   zero address).
#
# Example program
# -----------------
#   Countdown from 5, printing each number, then announce done:
#
#     0: LETA=5
#     1: PRINTA
#     2: LETA=A-1
#     3: IFA>0THEN1
#     4: PRINT"DONE"
#     5: END
#     RUN
#
# ================================================================

KEY:     .EQU    $F011
TERM:    .EQU    $F028
ZP:      .EQU    $0000    # base for PEEK/POKE's "[ZP,X]" trick --
                            # IX is set to the FULL 16-bit target
                            # address, so addr(ZP)+IX = the address
                            # itself, giving PEEK/POKE arbitrary
                            # 16-bit reach instead of the LINES/VARS
                            # buffers' own base addresses.

MAX_LINES: .EQU  10
LINE_LEN:  .EQU  25

        .ORG    $4000

# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------
START:
        LDA     $00
        STA     [LINECNT]
        STA     [IXHI]          # IXHI is always 0 -- see SETIX below

        JSR     PRINT_BANNER

# ---------------------------------------------------------------
# Entry loop: read one statement per iteration into LINES[LINECNT]
# ---------------------------------------------------------------
ENTRY_LOOP:
        LDA     [LINECNT]
        JSR     PRINTNUM
        LDA     $3A              # ':'
        STA     [TERM]

        LDA     [LINECNT]
        JSR     LINE_OFFSET      # ACC = LINECNT*LINE_LEN
        STA     [IXLO]
        BLDX    [IXHI]

ENTRY_CHAR:
        JSR     READ_KEY
        CMPA    $05               # ENTER
        JZ      [ENTRY_ENTERED]
        CMPA    $20
        JZ      [ENTRY_STORE]
        JC      [ENTRY_STORE]
        JMP     [ENTRY_CHAR]      # discard control byte, keep waiting
ENTRY_STORE:
        STA     [LINES,X]
        INCX
        JMP     [ENTRY_CHAR]

ENTRY_ENTERED:
        LDA     $0A               # move the Terminal to a new line -- ENTER
        STA     [TERM]             # itself is $05, which the Terminal ignores
                                     # (only 0x0A/printable ASCII render), so
                                     # without this the next prompt would print
                                     # right after the just-typed line with no
                                     # visible break.
        LDA     $00
        STA     [LINES,X]         # terminate the stored line

        LDA     [LINECNT]
        JSR     LINE_OFFSET
        STA     [IXLO]
        BLDX    [IXHI]
        LDA     [LINES,X]
        CMPA    $52                # 'R'
        JNZ     [ENTRY_NOTRUN]
        INCX
        LDA     [LINES,X]
        CMPA    $55                # 'U'
        JNZ     [ENTRY_NOTRUN]
        INCX
        LDA     [LINES,X]
        CMPA    $4E                # 'N'
        JNZ     [ENTRY_NOTRUN]
        INCX
        LDA     [LINES,X]
        JNZ     [ENTRY_NOTRUN]     # 4th byte must be the $00 terminator
        JMP     [DO_RUN]

ENTRY_NOTRUN:
        LDA     [LINECNT]
        ADD     $01
        STA     [LINECNT]
        CMPA    MAX_LINES
        JZ      [ENTRY_FULL]
        JMP     [ENTRY_LOOP]

ENTRY_FULL:
        JSR     PRINT_FULL_MSG
        JMP     [DO_RUN]

# ---------------------------------------------------------------
# RUN: execute stored statements from index 0
# ---------------------------------------------------------------
DO_RUN:
        LDA     $00
        STA     [CURLINE]
RUN_LOOP:
        LDA     [CURLINE]
        CMPA    [LINECNT]
        JZ      [RUN_DONE]
        JC      [RUN_DONE]
        JSR     EXEC_LINE
        LDA     [FLOWFLAG]
        JZ      [RUN_INCR]
        CMPA    $01
        JZ      [RUN_LOOP]         # a jump already updated CURLINE
        HALT                        # FLOWFLAG==2 -> END statement
RUN_INCR:
        LDA     [CURLINE]
        ADD     $01
        STA     [CURLINE]
        JMP     [RUN_LOOP]
RUN_DONE:
        HALT

# ---------------------------------------------------------------
# EXEC_LINE: interpret LINES[CURLINE]. Sets FLOWFLAG:
#   0 = fall through to next statement
#   1 = CURLINE was set explicitly (GOTO / IF-THEN taken)
#   2 = END was executed
# ---------------------------------------------------------------
EXEC_LINE:
        LDA     $00
        STA     [FLOWFLAG]

        LDA     [CURLINE]
        JSR     LINE_OFFSET
        STA     [IXLO]
        BLDX    [IXHI]

        LDA     [LINES,X]
        CMPA    $4C                # 'L' LET
        JZ      [EL_LET]
        CMPA    $50                # 'P' PRINT / POKE
        JZ      [EL_P]
        CMPA    $49                # 'I' IF / INPUT
        JZ      [EL_I]
        CMPA    $47                # 'G' GOTO
        JZ      [EL_GOTO]
        CMPA    $45                # 'E' END
        JZ      [EL_END]
        RTS                         # unrecognised -- treat as NOP

EL_I:
        INCX
        LDA     [LINES,X]
        CMPA    $46                 # 'F' -> IF ; else assume INPUT
        JZ      [EL_IF]
        JMP     [EL_INPUT]

EL_P:
        INCX
        LDA     [LINES,X]
        CMPA    $4F                 # 'O' -> POKE ; else assume PRINT
        JZ      [EL_POKE]
        JMP     [EL_PRINT]

# ---- POKE a=expr --------------------------------------------------
EL_POKE:
        INCX
        INCX
        INCX                        # skip "OKE" (dispatcher above
                                      # already consumed the leading 'P')
        JSR     EVAL_ADDR
        INCX                         # skip '='
        JSR     EVAL_EXPR
        STA     [POKEVAL]
        BLDX    [PADDRHI]
        LDA     [POKEVAL]
        STA     [ZP,X]
        RTS

# ---- LET v=expr -------------------------------------------------
EL_LET:
        INCX
        INCX
        INCX                        # skip "LET"
        LDA     [LINES,X]
        SUB     $41                  # 'A' -> 0
        STA     [LVARIDX]
        INCX                          # skip var letter
        INCX                          # skip '='
        JSR     EVAL_EXPR
        STA     [LSAVEACC]
        LDA     [LVARIDX]
        STA     [IXLO]
        BLDX    [IXHI]
        LDA     [LSAVEACC]
        STA     [VARS,X]
        RTS

# ---- PRINT expr | PRINT"text" -----------------------------------
EL_PRINT:
        INCX
        INCX
        INCX
        INCX                          # skip "RINT" (EL_P above already
                                        # consumed the leading 'P')
        LDA     [LINES,X]
        CMPA    $22                    # '"'
        JZ      [EL_PRINT_STR]
        JSR     EVAL_EXPR
        JSR     PRINTNUM
        LDA     $0A
        STA     [TERM]
        RTS
EL_PRINT_STR:
        INCX                            # skip opening quote
EL_PRINT_STR_LOOP:
        LDA     [LINES,X]
        JZ      [EL_PRINT_STR_DONE]      # ran off the end -- safety
        CMPA    $22                       # closing quote
        JZ      [EL_PRINT_STR_DONE]
        STA     [TERM]
        INCX
        JMP     [EL_PRINT_STR_LOOP]
EL_PRINT_STR_DONE:
        LDA     $0A
        STA     [TERM]
        RTS

# ---- INPUT v ------------------------------------------------------
EL_INPUT:
        INCX
        INCX
        INCX
        INCX                             # skip "NPUT" (dispatcher already
                                           # consumed the leading 'I' in EL_I)
        LDA     [LINES,X]
        SUB     $41
        STA     [LVARIDX]
        LDA     $3F                       # '?'
        STA     [TERM]
        JSR     INPUT_NUM
        STA     [LSAVEACC]
        LDA     [LVARIDX]
        STA     [IXLO]
        BLDX    [IXHI]
        LDA     [LSAVEACC]
        STA     [VARS,X]
        LDA     $0A
        STA     [TERM]
        RTS

# ---- IF e1 relop e2 THEN n -----------------------------------------
EL_IF:
        INCX                              # skip 'F' (the 'I' + 'F' pair: dispatcher already
                                            # consumed 'I' via INCX in EL_I, this skips 'F')
        JSR     EVAL_EXPR
        STA     [TERM1]
        LDA     [LINES,X]
        STA     [RELOP]
        INCX                                # skip relop char
        JSR     EVAL_EXPR
        STA     [TERM2]
        INCX
        INCX
        INCX
        INCX                                 # skip "THEN"
        JSR     PARSE_NUM                     # target line number
        STA     [IFTARGET]

        LDA     [RELOP]
        CMPA    $3D                            # '='
        JZ      [IF_EQ]
        CMPA    $3C                             # '<'
        JZ      [IF_LT]
        JMP     [IF_GT]                          # otherwise '>'

IF_EQ:
        LDA     [TERM1]
        CMPA    [TERM2]
        JZ      [IF_TAKE]
        RTS
IF_LT:
        LDA     [TERM1]
        CMPA    [TERM2]
        JZ      [IF_NOTAKE]                       # equal -> not less-than
        JC      [IF_NOTAKE]                        # TERM1>TERM2 -> not less-than
        JMP     [IF_TAKE]
IF_GT:
        LDA     [TERM1]
        CMPA    [TERM2]
        JC      [IF_TAKE]                           # TERM1>TERM2
        RTS
IF_NOTAKE:
        RTS
IF_TAKE:
        LDA     [IFTARGET]
        STA     [CURLINE]
        LDA     $01
        STA     [FLOWFLAG]
        RTS

# ---- GOTO n ---------------------------------------------------------
EL_GOTO:
        INCX
        INCX
        INCX
        INCX                                       # skip "GOTO"
        JSR     PARSE_NUM
        STA     [CURLINE]
        LDA     $01
        STA     [FLOWFLAG]
        RTS

# ---- END --------------------------------------------------------------
EL_END:
        LDA     $02
        STA     [FLOWFLAG]
        RTS

# =================================================================
# Expression evaluation
# =================================================================

# EVAL_EXPR: parses TERM [(+|-) TERM] at [LINES,X]; returns value in
# ACC; leaves IX just past what it consumed.
EVAL_EXPR:
        JSR     EVALTERM
        STA     [EETERM1]
        LDA     [LINES,X]
        CMPA    $2B                 # '+'
        JZ      [EE_ADD]
        CMPA    $2D                  # '-'
        JZ      [EE_SUB]
        LDA     [EETERM1]
        RTS
EE_ADD:
        INCX
        JSR     EVALTERM
        STA     [EETERM2]
        LDA     [EETERM1]
        ADD     [EETERM2]
        RTS
EE_SUB:
        INCX
        JSR     EVALTERM
        STA     [EETERM2]
        LDA     [EETERM1]
        SUB     [EETERM2]
        RTS

# TERM: parses a single term (digit literal or variable letter) at
# [LINES,X]; returns value in ACC; leaves IX just past what it
# consumed.
EVALTERM:
        LDA     [LINES,X]
        CMPA    $30                  # '0'
        JZ      [T_DIGIT]
        JC      [T_CHECKHI]
        JMP     [T_LETTER]
T_CHECKHI:
        CMPA    $39                  # '9'
        JZ      [T_DIGIT]
        JC      [T_CHECKP]
        JMP     [T_DIGIT]
T_CHECKP:
        CMPA    $50                   # 'P' -> PEEK ; else a plain variable
        JZ      [T_PEEK]
        JMP     [T_LETTER]
T_DIGIT:
        JSR     PARSE_NUM
        RTS
T_LETTER:
        LDA     [LINES,X]
        SUB     $41
        STA     [TVARIDX]
        BSTX    [PCURHI]
        LDA     [TVARIDX]
        STA     [IXLO]
        BLDX    [IXHI]
        LDA     [VARS,X]
        STA     [TVAL]
        BLDX    [PCURHI]
        INCX
        LDA     [TVAL]
        RTS

# T_PEEK: parses "PEEKa" (a = an EVAL_ADDR address-spec) at [LINES,X];
# returns RAM[a] in ACC; leaves IX just past what it consumed. Mirrors
# T_LETTER's BSTX/BLDX-around-a-repurposed-IX trick: EVAL_ADDR itself
# consumes/restores the parse cursor while resolving the address, then
# this detours IX a second time -- to the resolved RAM address itself
# -- for the actual read.
T_PEEK:
        INCX
        INCX
        INCX
        INCX                        # skip "PEEK"
        JSR     EVAL_ADDR
        BSTX    [PCURHI]
        BLDX    [PADDRHI]
        LDA     [ZP,X]
        STA     [TVAL]
        BLDX    [PCURHI]
        LDA     [TVAL]
        RTS

# PARSE_NUM: reads 1-3 decimal digit characters at [LINES,X],
# accumulates their value (wrapping past 255), stops at the first
# non-digit character. Returns value in ACC; leaves IX at the first
# non-digit.
PARSE_NUM:
        LDA     $00
        STA     [PNRES]
PN_LOOP:
        LDA     [LINES,X]
        CMPA    $30                   # '0'
        JZ      [PN_ISDIGIT]
        JC      [PN_CHECKHI]
        JMP     [PN_DONE]
PN_CHECKHI:
        CMPA    $39                    # '9'
        JZ      [PN_ISDIGIT]
        JC      [PN_DONE]
PN_ISDIGIT:
        LDA     [LINES,X]
        SUB     $30
        STA     [PNDIGIT]
        LDA     [PNRES]
        STA     [T10TMP]
        SHL
        STA     [T10TMP2]
        SHL
        SHL
        ADD     [T10TMP2]
        ADD     [PNDIGIT]
        STA     [PNRES]
        INCX
        JMP     [PN_LOOP]
PN_DONE:
        LDA     [PNRES]
        RTS

# EVAL_ADDR: parses an address-spec at [LINES,X] -- decimal (1-3
# digits, 0-255), $ + 1-4 uppercase hex digits (0-65535), or a single
# variable letter A-Z (its value used as a 0-255 address) -- into the
# 16-bit PADDRHI:PADDRLO. Leaves IX just past what it consumed.
EVAL_ADDR:
        LDA     [LINES,X]
        CMPA    $24                  # '$'
        JZ      [EA_HEX]
        CMPA    $30                  # '0'
        JZ      [EA_DEC]
        JC      [EA_DEC_HI]
        JMP     [EA_VAR]
EA_DEC_HI:
        CMPA    $39                   # '9'
        JZ      [EA_DEC]
        JC      [EA_VAR]
        JMP     [EA_DEC]
EA_DEC:
        JSR     PARSE_NUM              # 8-bit, 0-255 -- page zero only
        STA     [PADDRLO]
        LDA     $00
        STA     [PADDRHI]
        RTS
EA_VAR:
        LDA     [LINES,X]
        SUB     $41
        STA     [TVARIDX]
        BSTX    [PCURHI]
        LDA     [TVARIDX]
        STA     [IXLO]
        BLDX    [IXHI]
        LDA     [VARS,X]
        STA     [PADDRLO]
        LDA     $00
        STA     [PADDRHI]
        BLDX    [PCURHI]
        INCX
        RTS
EA_HEX:
        INCX                           # skip '$'
        LDA     $00
        STA     [PHHI]
        STA     [PHLO]
EA_HEX_LOOP:
        LDA     [LINES,X]
        JSR     HEXVAL
        CMPA    $FF                     # HEXVAL's "not a hex digit" sentinel
        JZ      [EA_HEX_DONE]
        STA     [PHDIGIT]
        JSR     PH_SHL4
        LDA     [PHLO]
        OR      [PHDIGIT]
        STA     [PHLO]
        INCX
        JMP     [EA_HEX_LOOP]
EA_HEX_DONE:
        LDA     [PHHI]
        STA     [PADDRHI]
        LDA     [PHLO]
        STA     [PADDRLO]
        RTS

# HEXVAL: ACC (a char) in; returns its hex nibble value (0-15) in ACC
# if ACC is '0'-'9' or uppercase 'A'-'F', else returns $FF. Same
# three-way JZ-equal/JC-greater-than/fallthrough-less-than idiom used
# throughout this file for CMPA (Carry is set iff ACC > operand, so
# "ACC < operand" has to be the un-branched fallthrough case, not a
# JC target -- an earlier draft of this routine got that backwards).
HEXVAL:
        CMPA    $30                    # '0'
        JZ      [HV_ISDIGIT]
        JC      [HV_CHECKHI9]
        JMP     [HV_NOTHEX]              # ACC < '0'
HV_CHECKHI9:
        CMPA    $39                     # '9'
        JZ      [HV_ISDIGIT]
        JC      [HV_CHECKALPHA]
        JMP     [HV_ISDIGIT]              # '0' < ACC < '9'
HV_CHECKALPHA:
        CMPA    $41                     # 'A'
        JZ      [HV_ISALPHA]
        JC      [HV_CHECKHIF]
        JMP     [HV_NOTHEX]               # '9' < ACC < 'A'
HV_CHECKHIF:
        CMPA    $46                      # 'F'
        JZ      [HV_ISALPHA]
        JC      [HV_NOTHEX]                # ACC > 'F'
        JMP     [HV_ISALPHA]                # 'A' < ACC < 'F'
HV_ISDIGIT:
        SUB     $30
        RTS
HV_ISALPHA:
        SUB     $37                       # 'A'(0x41)-10 -> 'A' maps to 10
        RTS
HV_NOTHEX:
        LDA     $FF
        RTS

# PH_SHL4: shifts the 16-bit pair PHHI:PHLO left by 4 bits (one hex
# nibble) -- four single-bit shifts, carry chained from PHLO's SHL
# into PHHI's ROLC each time.
PH_SHL4:
        LDA     [PHLO]
        SHL
        STA     [PHLO]
        LDA     [PHHI]
        ROLC
        STA     [PHHI]
        LDA     [PHLO]
        SHL
        STA     [PHLO]
        LDA     [PHHI]
        ROLC
        STA     [PHHI]
        LDA     [PHLO]
        SHL
        STA     [PHLO]
        LDA     [PHHI]
        ROLC
        STA     [PHHI]
        LDA     [PHLO]
        SHL
        STA     [PHLO]
        LDA     [PHHI]
        ROLC
        STA     [PHHI]
        RTS

# INPUT_NUM: blocks on the Keyboard, reading 1-3 decimal digits
# terminated by ENTER; returns value in ACC.
INPUT_NUM:
        LDA     $00
        STA     [PNRES]
IN_LOOP:
        JSR     READ_KEY
        CMPA    $05                     # ENTER
        JZ      [IN_DONE]
        CMPA    $30
        JZ      [IN_ISDIGIT]
        JC      [IN_CHECKHI]
        JMP     [IN_LOOP]                 # ignore non-digit
IN_CHECKHI:
        CMPA    $39
        JZ      [IN_ISDIGIT]
        JC      [IN_LOOP]
IN_ISDIGIT:
        SUB     $30
        STA     [PNDIGIT]
        LDA     [PNRES]
        STA     [T10TMP]
        SHL
        STA     [T10TMP2]
        SHL
        SHL
        ADD     [T10TMP2]
        ADD     [PNDIGIT]
        STA     [PNRES]
        JMP     [IN_LOOP]
IN_DONE:
        LDA     [PNRES]
        RTS

# LINE_OFFSET: ACC (0..MAX_LINES-1) in; returns ACC = ACC*LINE_LEN.
LINE_OFFSET:
        STA     [LOCNT]
        LDA     $00
        STA     [LORES]
LO_LOOP:
        LDA     [LOCNT]
        JZ      [LO_DONE]
        LDA     [LORES]
        ADD     LINE_LEN
        STA     [LORES]
        LDA     [LOCNT]
        SUB     $01
        STA     [LOCNT]
        JMP     [LO_LOOP]
LO_DONE:
        LDA     [LORES]
        RTS

# PRINTNUM: ACC (0-255) in; prints its decimal digits (no leading
# zeros) to the Terminal. Destroys ACC.
PRINTNUM:
        STA     [PNVAL]
        LDA     $00
        STA     [HCNT]
PN2_H_LOOP:
        LDA     [PNVAL]
        CMPA    $64
        JC      [PN2_H_SUB]
        JZ      [PN2_H_SUB]
        JMP     [PN2_H_DONE]
PN2_H_SUB:
        SUB     $64
        STA     [PNVAL]
        LDA     [HCNT]
        ADD     $01
        STA     [HCNT]
        JMP     [PN2_H_LOOP]
PN2_H_DONE:
        LDA     $00
        STA     [TCNT]
PN2_T_LOOP:
        LDA     [PNVAL]
        CMPA    $0A
        JC      [PN2_T_SUB]
        JZ      [PN2_T_SUB]
        JMP     [PN2_T_DONE]
PN2_T_SUB:
        SUB     $0A
        STA     [PNVAL]
        LDA     [TCNT]
        ADD     $01
        STA     [TCNT]
        JMP     [PN2_T_LOOP]
PN2_T_DONE:
        LDA     [HCNT]
        JZ      [PN2_SKIP_H]
        ADD     $30
        STA     [TERM]
PN2_SKIP_H:
        LDA     [HCNT]
        JNZ     [PN2_FORCE_T]
        LDA     [TCNT]
        JZ      [PN2_SKIP_T]
PN2_FORCE_T:
        LDA     [TCNT]
        ADD     $30
        STA     [TERM]
PN2_SKIP_T:
        LDA     [PNVAL]
        ADD     $30
        STA     [TERM]
        RTS

# READ_KEY: blocks until a key is pressed; returns its raw byte in
# ACC. $F011 is a read-clear latch, so this consumes the keypress.
READ_KEY:
RK_WAIT:
        LDA     [KEY]
        CMPA    $FF
        JZ      [RK_WAIT]
        RTS

# ---- banner / messages ---------------------------------------------
PRINT_BANNER:
        BSTX    [PCURHI]
        BLDX    $0000
PB_LOOP:
        LDA     [BANNER,X]
        JZ      [PB_DONE]
        STA     [TERM]
        INCX
        JMP     [PB_LOOP]
PB_DONE:
        BLDX    [PCURHI]
        RTS

PRINT_FULL_MSG:
        BSTX    [PCURHI]
        BLDX    $0000
PF_LOOP:
        LDA     [FULLMSG,X]
        JZ      [PF_DONE]
        STA     [TERM]
        INCX
        JMP     [PF_LOOP]
PF_DONE:
        BLDX    [PCURHI]
        RTS

BANNER:  .BYTE   "TINY BASIC"
         .BYTE   $0A, $00

FULLMSG: .BYTE   "PROGRAM FULL"
         .BYTE   $0A, $00

# =================================================================
# Scratch storage
# =================================================================
VARS:     .BYTE   *26
LINES:    .BYTE   *250
LINECNT:  .BYTE
CURLINE:  .BYTE
FLOWFLAG: .BYTE
IXHI:     .BYTE
IXLO:     .BYTE
PCURHI:   .BYTE
PCURLO:   .BYTE
LOCNT:    .BYTE
LORES:    .BYTE
PNVAL:    .BYTE
HCNT:     .BYTE
TCNT:     .BYTE
T10TMP:   .BYTE
T10TMP2:  .BYTE
PNDIGIT:  .BYTE
PNRES:    .BYTE
EETERM1:  .BYTE
EETERM2:  .BYTE
TERM1:    .BYTE
TERM2:    .BYTE
RELOP:    .BYTE
IFTARGET: .BYTE
LVARIDX:  .BYTE
LSAVEACC: .BYTE
TVARIDX:  .BYTE
TVAL:     .BYTE
PADDRHI:  .BYTE
PADDRLO:  .BYTE
PHHI:     .BYTE
PHLO:     .BYTE
PHDIGIT:  .BYTE
POKEVAL:  .BYTE

        .END    $4000
