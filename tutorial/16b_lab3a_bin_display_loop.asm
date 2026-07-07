# ================================================================
# 16b_lab3a_bin_display_loop.asm
# Beboputer Hands-On Tutorial — Lab 3a (version 2)
#
# The same binary display as 16a - as one loop instead of eight
# copy-pasted blocks.
#
# What this program does
# -----------------------
#   Behaves identically to 16a: wait for a key, clear the display,
#   show '%', then show that key's raw code as eight binary digits.
#   The visible result on the display is exactly the same. What's
#   different is entirely inside the code.
#
# How it works
# -------------
#   16a's eight nearly-identical TEST blocks collapse into one block
#   that runs eight times, counted down by the Index register:
#
#     BLDX    8          # Load X reg with number of bits
#     LOOP:      LDA     [TEMP8]    # Reload ACC with copy of key code
#                SHL                # Shift left 1 bit
#                STA     [TEMP8]    # Store new value in temp location
#                JC      [DISP_1]   # If carry = 1, jump to display a 1
#     DISP_0:    LDA     0          # ... otherwise load acc with 0
#                STA     [MAINDISP] # ... and store it to main display
#                JMP     [DISPDECX] # ... then go and decrement the X reg
#     DISP_1:    LDA     1          # Load acc with 1
#                STA     [MAINDISP] # ... and store it to main display
#     DISPDECX:  DECX               # Decrement the X reg
#                JNZ     [LOOP]     # If not zero jump back for next bit
#
#   BLDX 8 loads the Index register with the loop count (8 bits to
#   show). Each pass through LOOP does the exact same SHL/JC dance
#   16a did per bit, then DECX counts the register down by one and
#   JNZ ("jump if Z flag not set") repeats LOOP as long as X hasn't
#   reached zero yet. The eighth pass leaves X at 0, JNZ stops
#   firing, and the code falls through to DONE.
#
#   This is the same "loop instead of unrolling" idea exercise 15c's
#   countdown loop and 15e's LED chase both use, just applied to a
#   fixed bit-count instead of a changing value or a shifting LED
#   pattern - one small block of code, plus a counter, replaces eight
#   copies of nearly the same thing.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run, press keys - the display should
#   look identical to 16a's for every key you try.
#
# Watch it happen
# -----------------
#   Open Registers and watch the Index register count down 8, 7, 6,
#   ... 1, 0 as LOOP repeats - compare this to 16a, which has no
#   Index register activity at all (it used the source code itself
#   as its "loop counter," unrolled eight times).
#
# Try this next
# ---------------
#   - Compare the total byte count of 16a vs 16b (Load -> CPU reports
#     size, or check the assembler's listing) - the loop version is
#     dramatically smaller for identical behavior, at the cost of a
#     few extra instructions executed per pass (DECX and JNZ, which
#     16a's unrolled version didn't need).
#   - See exercise 16h and 16i for a further-refined version of this
#     same loop idea, applied with a nybble separator added in.
# ================================================================

## Lab 3a binary display using the index (X) register

#######################################################################
## Start of constant declarations                                    ##
#######################################################################
MAINDISP: .EQU     $F031      # Address of output port for main display
SIXLEDS:  .EQU     $F032      # Address of output port for six LEDs
KEYPAD:   .EQU     $F011      # Address of input port for keypad
CLRCODE:  .EQU     $10        # Special code to clear the main display
BINMODE:  .EQU     %00000100  # LED code to indicate binary mode
DECMODE:  .EQU     %00000010  # LED code to indicate decimal mode
HEXMODE:  .EQU     %00000001  # LED code to indicate hexadecimal mode
#######################################################################
## End of constant declarations                                      ##
#######################################################################

          .ORG     $4000      # Set program origin

#######################################################################
## Start of initialization                                           ##
#######################################################################
INIT:      LDA     CLRCODE    # Load accumulator with clear code
           STA     [MAINDISP] # Write clear code to main display
           LDA     BINMODE    # Load accumulator with bin mode code
           STA     [SIXLEDS]  # Write to port driving six LEDs
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

########## Wait for key to be pressed
GETKEY:    LDA     [KEYPAD]   # Load ACC with code from keypad
           JN      [GETKEY]   # Jump back if no key pressed
           STA     [TEMP8]    # Store key code in temp location

########## Prepare the main display
CLRDISP:   LDA     CLRCODE    # Load ACC with clear code
           STA     [MAINDISP] # Clear main display
DISPPERC:  LDA     $25        # Load ACC with ASCII code for '%'
           STA     [MAINDISP] # Write '%' to main display

########## Display the binary value
           BLDX    8          # Load X reg with number of bits
LOOP:      LDA     [TEMP8]    # Reload ACC with copy of key code
           SHL                # Shift left 1 bit
           STA     [TEMP8]    # Store new value in temp location
           JC      [DISP_1]   # If carry = 1, jump to display a 1
DISP_0:    LDA     0          # ... otherwise load acc with 0
           STA     [MAINDISP] # ... and store it to main display
           JMP     [DISPDECX] # ... then go and decrement the X reg
DISP_1:    LDA     1          # Load acc with 1
           STA     [MAINDISP] # ... and store it to main display
DISPDECX:  DECX               # Decrement the X reg
           JNZ     [LOOP]     # If not zero jump back for next bit

########## Do it all again
DONE:      JMP     [GETKEY]   # Jump back and wait for new key

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################
TEMP8:    .BYTE               # 8-bit temp location to store data
#######################################################################
## End of global data                                                ##
#######################################################################

          .END
                # That's all folks
