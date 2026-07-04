# optest-clrim-setim.asm  --  coverage test for CLRIM / SETIM
# SETIM sets FLAG_I ($10), CLRIM clears it.
# Verifies both by reading flags register via PUSHSR/POPA.

          .ORG     $4000
MAINDISP: .EQU     $F031
FLAG_I:   .EQU     $10

          SETIM                 # set interrupt-mask flag
          PUSHSR                # push flags
          POPA                  # flags -> ACC
          AND      FLAG_I       # isolate FLAG_I bit
          JZ       [FAIL]       # if zero, SETIM did not work
          CLRIM                 # clear interrupt-mask flag
          PUSHSR                # push flags again
          POPA                  # flags -> ACC
          AND      FLAG_I       # should be 0 now
          JNZ      [FAIL]       # if not zero, CLRIM did not work
          LDA      $49          # 'I' -- both ops correct
          STA      [MAINDISP]
          JMP      [DONE]
FAIL:     LDA      $46          # 'F' -- something wrong
          STA      [MAINDISP]
DONE:     HALT
          .END
