# ================================================================
# 15a_lab2a_clear_display.asm
# Beboputer Hands-On Tutorial — Lab 2a
#
# The shortest possible Beboputer program: clear the Calculator's
# main display and stop.
#
# What this program does
# -----------------------
#   Writes the display's "clear" code ($10) to the display port
#   ($F031), then jumps to address $0000 and stays there.
#
# How it works
# -------------
#   Four instructions, no labels, nothing but raw numbers - as bare
#   as a Beboputer program gets:
#
#     LDA  $10        load the accumulator with the literal value
#                      $10 - the byte this Calculator treats as
#                      "clear the display" (see tools/calculator.py's
#                      write_display: $0D, $10, and $1B all clear it)
#     STA  [$F031]    store the accumulator to address $F031 - the
#                      Calculator's main display port
#     JMP  [$0000]    jump to address $0000
#
#   That last jump is worth pausing on. This CPU has no HALT-and-
#   stay-halted state you fall into automatically - once the last
#   instruction runs, the Program Counter simply keeps advancing
#   into whatever comes next unless you tell it otherwise. Address
#   $0000 is always zeroed out on power-on and stays that way unless
#   a program is deliberately loaded there, and a zeroed byte
#   decodes as opcode $00 - NOP, "do nothing, move to the next
#   instruction." So JMP [$0000] sends the CPU into an address full
#   of NOPs, where it will keep fetching NOP after NOP forever - not
#   a true halt, but a program that has, for all practical purposes,
#   stopped doing anything. (This CPU does have a real HALT
#   instruction, opcode $3C - exercise 09 uses it. Lab 2a's "jump
#   into zeroed memory" trick is the more old-fashioned way of
#   getting the same practical result, and is worth recognizing
#   since you'll see it again in Lab 2c/2d/2f below.)
#
#   Notice this program has no .EQU declarations and no labels at
#   all - $4000, $10, and $F031 are typed as plain numbers every
#   time. That is deliberate: Lab 2b takes this exact program and
#   rewrites it with named constants, so you can compare the two
#   side by side and see directly what labels buy you.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run. The Calculator's display goes
#   blank (or stays blank, if it already was) and the program then
#   sits idle.
#
# Watch it happen
# -----------------
#   Open Display -> Port Map Status and watch $F031 receive $10 the
#   moment you click Run, then step through with Step to see the
#   Program Counter land on $0000 and stay in the 0000-0000
#   neighborhood, incrementing through NOPs.
#
# Try this next
# ---------------
#   - Replace JMP [$0000] with HALT ($3C) and compare - Display ->
#     Port Map Status and the Registers panel should look identical
#     either way, since both leave the display showing the same
#     thing; the difference only shows up in the Registers panel
#     (HALT stops the Program Counter dead; JMP [$0000] leaves it
#     ticking through NOPs).
#   - Change $10 to a different value and see what else the display
#     does with it (see tools/calculator.py's write_display for the
#     full list of what each byte range means).
# ================================================================

          .ORG     $4000	# Set program's origin to address $4000
           LDA     $10        # Load accumulator with clear code
           STA     [$F031]    # Store accumulator to address $F031
           JMP     [$0000]    # Jump to address $0000
          .END                # This is the end of the program
