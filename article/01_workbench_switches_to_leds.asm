# ================================================================
# 01_workbench_switches_to_leds.asm
# Beboputer Hands-On Tutorial — Section 3.1 (Workbench 1)
#
# Mirror the switches on the LED bar.
#
# What this program does
# -----------------------
#   Continuously reads Switch Bank 1 (port $F000) and copies the
#   value straight to the 8-bit LED bar (port $F022).
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run on the Calculator, then flip
#   switches in Workbench 1's Switch Bank 1 and watch the LED bar
#   respond immediately.
# ================================================================

SW1:    .EQU    $F000
LED8:   .EQU    $F022

        .ORG    $4000

LOOP:   LDA     [SW1]
        STA     [LED8]
        JMP     [LOOP]

        .END    $4000
