## Lab 2a
## Simple program to clear the calculator's main display

          .ORG     $4000	# Set program's origin to address $4000
           LDA     $10        # Load accumulator with clear code
           STA     [$F031]    # Store accumulator to address $F031
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program
