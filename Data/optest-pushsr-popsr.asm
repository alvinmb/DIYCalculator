# optest-pushsr-popsr.asm  --  coverage test for PUSHSR / POPSR
# Sets Z flag via SUB $00-$00, pushes flags, clears Z, pops flags back.
# JNZ after POPSR: if Z was NOT restored -> FAIL ('F').
# Otherwise display 'S' (success).

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $00
          SUB      $00          # Z=1 (result is zero)
          PUSHSR                # save flags (Z=1)
          LDA      $FF
          SUB      $00          # Z=0 (result $FF != 0)
          POPSR                 # restore flags -> Z should be 1 again
          JNZ      [FAIL]       # if Z not restored, branch to FAIL
          LDA      $53          # 'S' -- success
          STA      [MAINDISP]
          JMP      [DONE]
FAIL:     LDA      $46          # 'F' -- fail
          STA      [MAINDISP]
DONE:     HALT
          .END
