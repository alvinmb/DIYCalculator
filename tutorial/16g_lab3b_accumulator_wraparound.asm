# ================================================================
# 16g_lab3b_accumulator_wraparound.asm
# Beboputer Hands-On Tutorial — Lab 3b
#
# Watch an 8-bit accumulator count all the way up and wrap back
# around to zero.
#
# What this program does
# -----------------------
#   Starts the accumulator at 0, counts it up by 1 over and over,
#   and stops the instant it wraps back around to 0 again - which
#   takes exactly 255 increments, since an 8-bit register can only
#   hold values 0 through 255.
#
# How it works
# -------------
#   The entire program is four lines:
#
#     LDA         0       # Load accumulator with zero
#     LOOP:      INCA                # Increment the accumulator
#                JNZ     [LOOP]      # Jump to LOOP if ACC !=0
#                JMP     [$0000]     # Jump to address $0000
#
#   INCA adds 1 to the accumulator and sets the Zero flag exactly
#   when the result is 0. The first time through, ACC goes 0 -> 1,
#   Z is clear, JNZ ("jump if Z flag not set") loops back. This
#   keeps happening - 1, 2, 3, ... - climbing all the way up through
#   255 ($FF). The 256th increment is where it gets interesting:
#   an 8-bit register has no 257th value to hold, so 255 + 1 wraps
#   around to 0 instead of becoming 256. That's the one and only
#   time INCA's result is 0, so that's the one and only time JNZ
#   stops firing, and the loop falls through to the terminating jump.
#
#   This is the same "jump to zeroed memory" stopping trick exercise
#   09 and Lab 2a both explain (RAM below $4000 is zeroed at power-on,
#   and a zeroed byte decodes as NOP, so the CPU just spins on NOPs
#   forever once it lands there) - there's nothing displayed, no
#   keypad read, nothing but the accumulator counting and wrapping.
#   It's a stripped down, minimal way to see 8-bit overflow happen
#   with your own eyes in the debugger, without any display logic
#   getting in the way of the one concept being demonstrated.
#
# Try it
# -------
#   Assemble, Load -> CPU, and switch to Step mode (Run will finish
#   this in a flash since there's nothing slowing it down - Step is
#   how you actually watch it happen). Step through and count how
#   many times INCA runs before Z finally sets.
#
# Watch it happen
# -----------------
#   Open Registers and watch the accumulator and the Z flag as you
#   Step: ACC counts 1, 2, 3, ... up to 255 ($FF), then the next
#   INCA takes it to $00 and only then does Z flip to 1 - the loop
#   runs 255 times, not 256, because 0 was the starting value the
#   loop counted up *from*, not one it counted through again until
#   the wrap.
# ================================================================

## Lab 3b - Simple program to demonstrate the way in which
##          the program counter works

          .ORG     $4000	 # Set program's origin to address $4000
           LDA         0       # Load accumulator with zero
LOOP:      INCA                # Increment the accumulator
           JNZ     [LOOP]      # Jump to LOOP if ACC !=0
           JMP     [$0000]     # Jump to address $0000
          .END                 # Terminate the program
