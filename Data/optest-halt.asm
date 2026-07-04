# optest-halt.asm  --  coverage test for HALT
# Loads 'H' into ACC, displays it, then HALTs.
# Verifies: HALT stops execution cleanly.

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $48          # 'H'
          STA      [MAINDISP]   # display 'H'
          HALT                  # stop -- cpu.halted should be True
          .END
