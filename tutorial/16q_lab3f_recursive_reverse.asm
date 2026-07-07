# ================================================================
# 16q_lab3f_recursive_reverse.asm
# Beboputer Hands-On Tutorial - Lab 3f (recursive string reversal)
#
# Print a fixed message backward - using a subroutine that calls
# itself once per character, with no array or manual index math.
#
# What this program does
# -----------------------
#   On its own, with no keypad interaction, prints the 9-character
#   message stored in its table, in reverse order, and stops. The
#   table holds "SWAP PAWS" - and because that particular phrase
#   reads the same forwards and backwards (character 0 matches
#   character 8, character 1 matches character 7, and so on, with
#   the space sitting in the exact middle), the reversed output
#   looks identical to the original on the display. That's
#   deliberate: see the note at the end of "How it works" on why
#   watching the registers, not just the display, is how you confirm
#   the reversal is really happening.
#
# How it works
# -------------
#   This is 16m's stack-based reversal trick and 16n/16o's nested
#   subroutines combined into one elegant idea: a subroutine that
#   reverses a message by calling itself, once per character, and
#   letting the call stack itself remember the order to print them
#   back in:
#
#     REVERSE:   LDA     [PHRASE,X] # Load ACC with a character
#                JNZ     [GOIN]     # If it's not NUL jump to GO_IN
#     RETURN1:   RTS                # Otherwise return from subroutine
#
#     GOIN:      PUSHA              # Push the character onto the stack
#                INCX               # Increment the index register
#     INSIDE:    JSR     [REVERSE]  # The subroutine calls itself recursively
#
#     COMEOUT:   POPA               # Pop a character off the stack
#                STA     [MAINDISP] # Copy to main display
#     RETURN2:   RTS                # Return from subroutine
#
#   [PHRASE,X] is the same indexed-addressing message-walking idea
#   Lab 2f's "HELLO WORLD!" uses (exercise 15f) - X starts at 0 and
#   counts up through the table one character at a time. But instead
#   of displaying each character as it's read and moving on, REVERSE
#   pushes the character onto the stack, advances X, and calls
#   itself to go read the next character - before doing anything
#   at all with the one it just read.
#
#   That single JSR [REVERSE] at INSIDE is the whole trick: it means
#   nothing gets displayed until the recursion bottoms out. REVERSE
#   keeps calling itself, pushing one more character each time,
#   until LDA [PHRASE,X] finally loads the table's terminating $00 -
#   at that point JNZ doesn't fire, and this innermost call just
#   returns immediately via RETURN1, without pushing anything.
#
#   From there, every one of the outer calls resumes exactly where it
#   left off - at COMEOUT, right after its own JSR [REVERSE] - and
#   pops back the character it pushed before recursing. Since the
#   stack is Last-In-First-Out (the same property 16m's simpler
#   stack-based reversal relies on), the very last character pushed
#   (the one right before the terminator) is the very first one
#   popped - so it's the first one displayed. Each returning call
#   displays its own character and then returns to whichever call
#   invoked it, one level up, which displays its character next -
#   and so on, all the way back out to the very first call, which
#   displays the very first character in the table last. The message
#   comes out back-to-front with no array, no manually-managed
#   count, and no [STORE-1,X]-style address arithmetic anywhere -
#   the recursive call stack is the reversal mechanism.
#
#   This is the same shape as 16p's recursive FACTOR: descend first
#   (pushing something at each level), hit a base case, then do one
#   small piece of work as each level unwinds on the way back out.
#   FACTOR multiplies on the way out; REVERSE displays on the way out
#   - same underlying pattern, applied to two different problems.
#
#   One more thing worth knowing before running this: PHRASE is
#   declared as two separate .BYTE lines - $53,$57,$41,$50,$20 (that's
#   "SWAP ") followed by $50,$41,$57,$53,$00 (that's "PAWS" plus the
#   NUL terminator) - nine displayable characters in total, forming
#   the single string "SWAP PAWS". Reverse those nine characters
#   (S-W-A-P-space-P-A-W-S) end for end and you get back S-W-A-P-
#   space-P-A-W-S - the exact same sequence. The phrase was chosen
#   as a palindrome on purpose, which is why the display alone can't
#   prove the recursion reversed anything - the "Watch it happen"
#   section below is where the real evidence is.
#
# Try it
# -------
#   Assemble, Load -> CPU, click Run - the display shows "SWAP PAWS",
#   which is what the reversed message looks like for this
#   particular (palindromic) phrase - see the note above.
#
# Watch it happen
# -----------------
#   Open Registers and watch the stack pointer drop once per
#   character as REVERSE recurses in (X counting 0, 1, 2, 3, 4 along
#   the way), then watch it rise again as each level's COMEOUT pops
#   and displays its character on the way back out - Step slowly to
#   see the "all the way in, then one at a time coming back out"
#   shape play out in the Registers panel.
#
# Try this next
# ---------------
#   - Change PHRASE to a longer message (remembering the trailing
#     $00 terminator, per Lab 2f's note) and confirm it still reverses
#     correctly, however long it is.
#   - Compare this file directly against 16m: both reverse a
#     sequence using the stack's natural LIFO order, but 16m reads
#     keypad input into the stack in a loop, while this one builds
#     the same stack contents through recursive calls instead.
# ================================================================

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
           LDA     HEXMODE    # Load accumulator with hex mode code
           STA     [SIXLEDS]  # Write to port driving six LEDs
#######################################################################
## End of initialization                                             ##
#######################################################################


#######################################################################
## Start of main program body                                        ##
#######################################################################

           BLDX    0          # Load index register with 0
           BLDSP   $EFFF      # Load stack pointer with $EFFF
OUTSIDE:   JSR     [REVERSE]  # Call the subroutine
FINISH:    JMP     [$0000]    # Terminate the program

#######################################################################
## End of main program body                                          ##
#######################################################################


#######################################################################
## Start of subroutines                                              ##
#######################################################################

########## Recursive subroutine to display string in reverse order
REVERSE:   LDA     [PHRASE,X] # Load ACC with a character
           JNZ     [GOIN]     # If it's not NUL jump to GO_IN
RETURN1:   RTS                # Otherwise return from subroutine

########## Store the character on the stack and go further in
GOIN:      PUSHA              # Push the character onto the stack
           INCX               # Increment the index register
INSIDE:    JSR     [REVERSE]  # The subroutine calls itself recursively

########## Retrieve and display a character and come out
COMEOUT:   POPA               # Pop a character off the stack
           STA     [MAINDISP] # Copy to main display
RETURN2:   RTS                # Return from subroutine

#######################################################################
## End of subroutines                                                ##
#######################################################################


#######################################################################
## Start of global data                                              ##
#######################################################################

PHRASE:   .BYTE $53, $57, $41, $50, $20
           #      S    W    A    P  SPACE

          .BYTE $50, $41, $57, $53, $00
           #      P    A    W    S  NUL

#######################################################################
## End of global data                                                ##
#######################################################################

          .END
                # That's all folks
