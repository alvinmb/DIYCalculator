## Lab 3b - Simple program to demonstrate the way in which 
##          the program counter works

          .ORG     $4000	 # Set program's origin to address $4000
           LDA         0       # Load accumulator with zero
LOOP:      INCA                # Increment the accumulator
           JNZ     [LOOP]      # Jump to LOOP if ACC !=0
           JMP     [$0000]     # Jump to address $0000
          .END                 # Terminate the program
