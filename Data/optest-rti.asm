# optest-rti.asm  --  coverage test for RTI (return from interrupt)
# Builds an RTI stack frame manually using PUSHSR + PSHA:
#   push flags (deepest),  push hi(AFTER)=$40,  push lo(AFTER)=$0A
# Then JMP to RTI routine. RTI pops lo/hi->PC, pops flags.
# If PC is correctly restored to AFTER ($400A), displays 'R'.
#
# Byte layout (ORG $4000):
#   $4000 PUSHSR       1 byte
#   $4001 LDA $40      2 bytes
#   $4003 PSHA         1 byte
#   $4004 LDA $0A      2 bytes
#   $4006 PSHA         1 byte
#   $4007 JMP [RTI_]   3 bytes
#   $400A AFTER        <-- return lands here
#   $4010 RTI_

          .ORG     $4000
MAINDISP: .EQU     $F031

          PUSHSR               # push flags (= 0 at reset) -- deepest frame slot
          LDA      $40         # hi byte of AFTER ($400A)
          PSHA
          LDA      $0A         # lo byte of AFTER ($400A)
          PSHA                 # SP now points at top of RTI frame
          JMP      [RTI_]      # jump to the RTI instruction
AFTER:    LDA      $52         # 'R' -- we returned here correctly
          STA      [MAINDISP]
          HALT
          NOP                  # padding so RTI_ lands at $4010
          NOP
          NOP
          NOP
          NOP
          NOP
RTI_:     RTI
          .END
