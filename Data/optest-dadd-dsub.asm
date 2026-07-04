# optest-dadd-dsub.asm  --  coverage test for DADD / DSUB (BCD arithmetic)
# DADD $50 + $25 = BCD 75  -> ACC=$75 = 'u'
# DSUB $75 - $25 = BCD 50  -> ACC=$50 = 'P'

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $50
          DADD     $25          # BCD 50+25=75, ACC=$75='u'
          STA      [MAINDISP]   # display 'u'
          LDA      $75
          DSUB     $25          # BCD 75-25=50, ACC=$50='P'
          STA      [MAINDISP]   # display 'P'
          HALT
          .END
