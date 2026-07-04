# optest-psha.asm  --  coverage test for PSHA
# Pushes 'P' onto stack, clobbers ACC, pops it back, displays it.
# Verifies: PSHA preserves ACC across a stack round-trip.

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $50          # 'P'
          PSHA                  # push 'P'
          LDA      $00          # clobber ACC
          POPA                  # pop -> ACC = 'P' ($50)
          STA      [MAINDISP]   # display 'P'
          HALT
          .END
