# optest-bldiv.asm  --  coverage test for BLDIV (load interrupt vector)
# BLDIV [IVPTR] reads 2 bytes from IVPTR into the interrupt vector register.
# Verifies the instruction executes without crash, then displays 'V'.

          .ORG     $4000
MAINDISP: .EQU     $F031

          BLDIV    [IVPTR]      # load interrupt vector from memory at IVPTR
          LDA      $56          # 'V'
          STA      [MAINDISP]   # display 'V'
          HALT
IVPTR:    .BYTE    $40, $00     # vector value = $4000
          .END
