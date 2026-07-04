# optest-daddc-dsubc.asm  --  coverage test for DADDC / DSUBC (BCD with carry/borrow)
#
# DADDC test:
#   DADD $99+$01 -> ACC=$00, C=1 (BCD overflow sets carry)
#   LDA $30; DADDC $20 -> BCD 30+20+1=51, ACC=$51='Q'
#
# DSUBC test:
#   DSUB $01-$02 -> ACC=$99, borrow=1 (C=1)
#   LDA $50; DSUBC $10 -> BCD 50-10-1=39, ACC=$39='9'

          .ORG     $4000
MAINDISP: .EQU     $F031

          LDA      $99
          DADD     $01          # BCD 99+01=100 -> ACC=$00, C=1
          LDA      $30
          DADDC    $20          # BCD 30+20+C(1)=51, ACC=$51='Q'
          STA      [MAINDISP]   # display 'Q'

          LDA      $01
          DSUB     $02          # BCD 01-02 -> borrow, ACC=$99, C=1
          LDA      $50
          DSUBC    $10          # BCD 50-10-C(1)=39, ACC=$39='9'
          STA      [MAINDISP]   # display '9'
          HALT
          .END
