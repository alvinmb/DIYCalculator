# ================================================================
# 08_keyboard_echo_to_terminal.asm
# Beboputer Hands-On Tutorial — Section 5.1 (Keyboard + Terminal)
#
# Echo typed characters to the Terminal.
#
# What this program does
# -----------------------
#   The on-screen Keyboard writes raw ASCII codes to the same port
#   the Calculator uses, $F011 (unlike the Calculator's hex keys,
#   the Keyboard tool does not translate digits to raw nibbles).
#   This program polls that port and echoes each keystroke to the
#   Terminal at $F028, translating the Keyboard tool's ENTER code
#   ($05) into the Terminal's newline code ($0A) along the way.
#
# Worth knowing
# --------------
#   The on-screen Keyboard tool already echoes every keystroke
#   straight to the Terminal itself, independent of this program -
#   it is a direct convenience wire built into the tool. Once this
#   program is also polling $F011 and writing to $F028, each
#   keystroke will appear TWICE. That is expected, not a bug -
#   watching the doubling happen is a good way to confirm this
#   program really is reading and reacting to each keypress.
#
# Try it
# -------
#   Open Tools -> Keyboard... and Display -> Terminal, assemble,
#   Load -> CPU, click Run, then type on the on-screen Keyboard.
# ================================================================

KEY:    .EQU    $F011
TERM:   .EQU    $F028

        .ORG    $4000

WAIT:   LDA     [KEY]      # read the keyboard port
        CMPA    $FF
        JZ      [WAIT]     # idle - keep waiting

        CMPA    $05        # is it the Keyboard tool's ENTER code?
        JNZ     [SEND]     # no - send the byte as typed
        LDA     $0A        # yes - translate to the Terminal's newline code
SEND:   STA     [TERM]
        JMP     [WAIT]

        .END    $4000
