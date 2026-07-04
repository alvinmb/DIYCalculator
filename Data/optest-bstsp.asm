# optest-bstsp.asm  --  coverage test for BSTSP (store stack pointer)
# Sets SP to $4021 via BLDSP, stores it with BSTSP, reads lo byte ($21='!').
#
# Byte layout (ORG $4000):
#   $4000: BLDSP $4021     (3)
#   $4003: BSTSP [STORETO] (3)
#   $4006: LDA  [STORETO+1](3)  lo byte of SP = $21 = '!'
#   $4009: STA  [MAINDISP] (3)
#   $400C: HALT             (1)
#   $400D: STORETO          (2 bytes storage)

          .ORG     $4000
MAINDISP: .EQU     $F031

          BLDSP    $4021        # SP = $4021
          BSTSP    [STORETO]    # store SP: hi=$40 -> STORETO, lo=$21 -> STORETO+1
          LDA      [STORETO+1]  # ACC = $21 = '!'
          STA      [MAINDISP]   # display '!'
          HALT
STORETO:  .BYTE    $00, $00     # 2-byte storage for SP value
          .END
