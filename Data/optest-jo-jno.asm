# optest-jo-jno.asm  --  coverage test for JO / JNO
# ADD $80+$80: both operands negative, result positive -> V=1 (overflow).
# JO  should branch (V=1).
# JNO should fall through (V=1, so NOT-overflow is false).
# Correct path displays 'O'.

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $80
          ADD      $80          # $80+$80=$00, C=1, V=1 (neg+neg=pos)
          JO       [OVFL]       # must take this branch
          LDA      $4E          # 'N' -- JO failed (should not reach here)
          STA      [MAINDISP]
          JMP      [DONE]
OVFL:     JNO      [FAIL]       # must NOT take this branch (V=1)
          LDA      $4F          # 'O' -- both JO and JNO correct
          STA      [MAINDISP]
          JMP      [DONE]
FAIL:     LDA      $46          # 'F'
          STA      [MAINDISP]
DONE:     HALT
          .END
