# Building a Virtual 8-Bit Computer on a Raspberry Pi
## *How PY-DIYCALCULATOR brings a classic computing education project to life on the world's favourite single-board computer*

---

*By Alvin Brown & Clive "Max" Maxfield*

---

There is something deeply satisfying about understanding how a computer works from the ground up — not in the abstract sense of software layers and operating system calls, but right down to the transistors, logic gates, registers, and raw binary arithmetic that make every digital device tick. For decades, the book *How Computers Do Math* by Clive "Max" Maxfield and Alvin Brown has guided curious minds through the architecture of an imaginary 8-bit computer called the Beboputer, teaching assembly language, memory-mapped input and output, binary arithmetic, and the fundamentals of CPU design. Now, with PY-DIYCALCULATOR — a faithful Python and PyQt5 reimagining of the original companion software — the Beboputer has arrived on the Raspberry Pi, and the combination is nothing short of wonderful.

This article walks you through everything you need to know: what PY-DIYCALCULATOR is, what it can do, how to get it running on your Pi, and how to start writing your first assembly language programs.

---

## What Is PY-DIYCALCULATOR?

PY-DIYCALCULATOR is a fully functional emulator of the fictional 8-bit Beboputer CPU, implemented in Python 3 and PyQt5. It faithfully recreates the instruction set, memory architecture, and peripheral devices described in *How Computers Do Math*, giving readers — and anyone curious about computing history and CPU design — a hands-on environment in which to experiment without needing any physical hardware beyond the computer in front of them.

**Don't Panic** if any of the terms on this page are unfamiliar to you, because everything is explained in our book *How Computers Do Math*, and by the time you've read this little scamp you'll be an expert.

The DIY Calculator is based on a very simple microcomputer system comprising a central processing unit (CPU), some memory, and some input and output (I/O) ports (these ports allow the system to "talk" with the outside world). The CPU itself is very straightforward and easy to understand: it has an 8-bit data bus and a 16-bit address bus; it contains a small number of simple registers like an accumulator, index register, and stack pointer; and it supports a very simple instruction set along the lines of ADD, SUBTRACT, SHIFT, ROTATE, AND, and OR.

This virtual system comes equipped with an assembler and a variety of diagnostic tools, such as a CPU Register Display, a Memory Display, and more — the list goes on.

The DIY Calculator also features a virtual calculator front panel with buttons, lights, and a pseudo-liquid crystal display (LCD). This front panel is "connected" to the virtual computer via its input and output ports.

The application presents a rich graphical user interface with multiple floating panels, a built-in assembler and text editor, a virtual workbench with switches and display devices, a calculator widget, a terminal, a memory walker, a disassembler, and a simulated clock. Every instruction the virtual CPU executes is visible in real time. Every memory location can be inspected. Every port can be watched. It is, in effect, a complete learning laboratory for 8-bit computing.

During the course of *How Computers Do Math*, we learn how to create software routines that detect when the various buttons are pressed, input decimal numbers and convert them into the binary representations used by the computer, perform math operations on these numbers, and then convert them back into decimal values to be presented on the main display.

First we learn about the binary and hexadecimal number systems, and then we learn a little about computers and calculators and perform some simple experiments with the DIY Calculator. Next we are introduced to some fundamental computing concepts such as the use of the index register, the stack, and subroutines. Along the way we gain familiarity with the assembly language used to create programs for the DIY Calculator.

As we proceed through the book, we create a simple four-function (add, subtract, multiply, and divide) calculator program that treats all values as 16-bit integers. Although it is fun to see this calculator perform its magic, we also discover the limitations associated with our 16-bit number representations. Thus, in the More Cool Stuff area on the website, we introduce more sophisticated representations such as fixed-point and floating-point.

And in addition to all of the above, we'll discover lots of interesting snippets of information, such as the origin of the math symbols we use like +, −, ×, ÷, and =.

What makes the Raspberry Pi such an ideal host for this software is a combination of factors: the Pi runs a Debian-based Linux distribution, Python 3 is a first-class citizen of the platform, PyQt5 is available through the standard package manager without any compilation required, and the Pi is inexpensive enough that a student or hobbyist can dedicate one entirely to this kind of project. Running PY-DIYCALCULATOR on a Raspberry Pi 4 or Pi 5 with a connected display feels completely natural — the GUI is responsive, the assembler is fast, and the whole experience has the right flavour of sitting in front of a dedicated learning machine.

---

## Before You Begin: What You Will Need

To follow this guide you will need:

- A Raspberry Pi 3B+, Pi 4 (any RAM variant), or Pi 5
- Raspberry Pi OS (Bookworm or Bullseye, 32-bit or 64-bit)
- A keyboard, mouse, and monitor (or VNC access)
- An internet connection for the initial package installation
- The PY-DIYCALCULATOR project archive (a zip file of the `Bebop_python` folder)

Older Pi models such as the Pi 2 or Pi Zero are not recommended — they lack the processing power to keep the GUI responsive, and PyQt5 can be slow to initialise on lower-specification hardware. On a Pi 4 or Pi 5, however, the application launches in under five seconds and runs perfectly throughout a long session.

---

## Installing PY-DIYCALCULATOR on Raspberry Pi OS

The easiest installation route uses the provided shell script, which handles everything automatically — dependency checking, file copying, desktop menu registration, and launcher creation. The whole process takes about two minutes on a Pi 4 with a decent internet connection.

### Step 1: Transfer the Project Archive

Copy the `Bebop_python` zip archive to your Pi. The simplest methods are a USB drive, `scp` from another machine on the same network, or downloading directly from a GitHub repository if the project is hosted there. Once transferred, open a terminal and unzip it:

```bash
cd ~
unzip Bebop_python.zip
```

This creates a `Bebop_python` folder in your home directory containing the full project.

### Step 2: Run the Installer

The installer script lives inside the project:

```bash
chmod +x ~/Bebop_python/bin/beboputer_v7/install_linux.sh
~/Bebop_python/bin/beboputer_v7/install_linux.sh
```

The script performs the following actions automatically:

**Checks for Python 3.** Python 3 ships with Raspberry Pi OS, so this step will almost always pass immediately.

**Installs PyQt5 via apt.** This is the critical step. Installing PyQt5 via `sudo apt install python3-pyqt5` downloads pre-compiled binaries from the Raspberry Pi OS package repositories. This takes a matter of seconds. The alternative — installing via pip — would compile PyQt5 from source, which on a Pi 3 can take several hours. The installer prioritises apt precisely to avoid this.

**Copies the application files** to `~/.local/share/beboputer`, which keeps everything neatly in your home directory and avoids any need for administrator permissions during normal operation.

**Creates a launcher script** at `~/.local/bin/beboputer` so you can start the application from any terminal simply by typing `beboputer`.

**Registers a `.desktop` entry** so PY-DIYCALCULATOR appears in the Raspberry Pi OS application menu under the Education or Emulators category, complete with an icon. After installation you can launch it just as you would any other desktop application.

### Step 3: Launch the Application

Either click the newly created menu entry, or from a terminal:

```bash
beboputer
```

The application opens maximised, filling your screen with the main window. By design, the window has no close, minimise, or maximise buttons — the application is intended to be a dedicated environment, and you exit cleanly using the **File → Exit** menu option.

---

## A Tour of the Interface

When PY-DIYCALCULATOR first opens, you are greeted by the main window with a menu bar across the top. All of the application's tools and panels are accessed through this menu bar. Let us walk through each section.

### The CPU Registers Panel

Accessible from the **Display** menu, the CPU Registers panel is the heartbeat of the emulator. It shows the current state of every register in the Beboputer CPU:

- **Accumulator (ACC)** — the primary 8-bit working register through which arithmetic and logic operations flow
- **Program Counter (PC)** — the 16-bit address of the next instruction to be fetched
- **Stack Pointer (SP)** — points to the current top of the hardware stack in RAM
- **Index Register (IX)** — an 8-bit register used for indexed addressing modes
- **Flags register** — individual bits showing the current state of the Carry (C), Zero (Z), Negative (N), and Overflow (V) flags after each instruction

Watching these registers during program execution is one of the most educational aspects of the tool. You can see exactly how a `CMPA` instruction sets the Carry flag, how an `ADD` operation causes the Overflow flag to trigger, or how a branch instruction reads the Zero flag to decide whether to jump.

### The Message Display

The Message Display is the application's diagnostic log — a scrolling text panel that records system events. When you load a program, reset the CPU, step through instructions, halt execution, or purge RAM, the message display reports what happened and when. It is always visible and serves as a running commentary on the state of the emulator.

### The Terminal

The Terminal panel is a CRT-style output device driven by the Beboputer itself via the memory-mapped port at address `$F028`. When a program writes a byte to this address, the corresponding ASCII character appears in the terminal window. This allows Beboputer programs to produce scrolling text output, creating a genuine interaction between the virtual CPU and a simulated output device.

### The Memory Walker

The Memory Walker is a powerful inspection tool that shows the contents of RAM in real time. You can navigate to any address in the 64KB memory space and see the raw byte values. As programs are loaded and executed, the Memory Walker reflects changes immediately. It is particularly useful for understanding how the stack grows and shrinks during subroutine calls, or for verifying that a program has written the expected values to output ports.

### The Disassembler

The Disassembler panel reads from the Program Counter and shows the human-readable assembly mnemonics corresponding to the machine code currently in memory. This is invaluable when debugging: rather than reading raw hex values, you can see the actual instructions the CPU is about to execute.

### The Port Map Status

The Port Map panel shows the current values of all memory-mapped input and output ports. This is where you can see in real time what data has been written to the workbench displays or what value a switch bank is currently presenting.

---

## The Tools Menu

Beyond the display panels, PY-DIYCALCULATOR provides a set of interactive tool windows.

### System Clock

The System Clock tool controls the speed at which the emulated CPU runs. The default is 100 Hz — 100 instruction cycles per second — which is slow enough to watch the registers change in real time. You can increase this for programs that need to run quickly, or slow it down further for careful step-by-step study.

### EPROM Burner

The EPROM Burner simulates the process of programming read-only memory. In a real 8-bit system from the 1970s or 1980s, programs were often stored on EPROM chips that had to be erased with ultraviolet light and reprogrammed with a special device. The Beboputer's EPROM Burner lets you load assembled programs into specific areas of the memory map, mimicking this workflow without the UV lamp.

### The Calculator

The Calculator is a full-featured RPN (Reverse Polish Notation) calculator built into the application, reflecting the educational context of the original *How Computers Do Math* book. It supports hexadecimal, decimal, octal, and binary arithmetic — exactly the kind of number-base conversions you need constantly when writing assembly language.

### The Keyboard

The Keyboard tool provides a virtual hexadecimal keypad that simulates the physical keyboard described in *How Computers Do Math*. It presents sixteen hex digit keys (0–9 and A–F) plus additional function keys, and is connected to the Beboputer via two memory-mapped ports:

| Port | Address | Direction | Description |
|---|---|---|---|
| Keyboard data | `$F020` | Input | ASCII value of the last key pressed |
| Keyboard status | `$F010` | Input | Bit 0 = 1 when a new keypress is waiting |

This two-port design mirrors the way real hardware keyboards work: a program first polls the status port to check whether a key has been pressed, and only reads the data port once it knows a value is waiting. This prevents the program from accidentally reading a stale value from a previous keypress.

A typical keyboard-polling loop in Beboputer assembly looks like this:

```
KBSTAT:  .EQU    $F010       # keyboard status port
KBDATA:  .EQU    $F020       # keyboard data port

         .ORG    $4000

WAIT:    LDA     [KBSTAT]    # read keyboard status
         AND     $01         # isolate bit 0 (key-ready flag)
         JZ      [WAIT]      # loop until a key is available
         LDA     [KBDATA]    # read the key value
         ...                 # process it
```

The `AND $01` masks off everything except the key-ready bit. When no key has been pressed, bit 0 is 0 and the `JZ` (Jump if Zero) instruction sends the program back to the top of the loop. The moment a key is pressed in the Keyboard window, bit 0 goes high, the loop exits, and the program reads the waiting ASCII value from the data port.

This pattern — polling a status port before reading a data port — is fundamental to real-world hardware interfacing and is one of the most important concepts the Beboputer teaches. Once you have understood it in this visual, interactive environment, you will recognise it immediately when you encounter it in device driver code, embedded firmware, or any system that communicates with external peripherals.

### Workbench 1

The Workbench is perhaps the most visually engaging part of the entire application. It simulates a physical electronics workbench populated with switches and display devices, all wired to the Beboputer's memory-mapped I/O ports. The devices and their addresses are:

| Device | Port Address | Description |
|---|---|---|
| Switch Bank 1 | `$F000` | 8 toggle switches — input |
| Switch Bank 2 | `$F001` | 8 toggle switches — input |
| Keyboard status | `$F010` | Bit 0 = 1 when a keypress is waiting — input |
| Keyboard data | `$F020` | ASCII value of last key pressed — input |
| 7-seg undecoded | `$F021` | Bits 6–0 drive segments a–g directly |
| 8-bit LED bar | `$F022` | 8 individual LEDs |
| Single 7-seg decoded | `$F023` | Low nibble shown as hex digit 0–F |
| Dual 7-seg decoded | `$F024` | High nibble = left digit, low nibble = right |
| Calculator display | `$F031` | Scrolling ASCII character display |
| Calculator LEDs | `$F032` | 6 individual LEDs |

Writing to these addresses from an assembly language program causes the corresponding display to update instantly. Flipping the switches changes the values readable from the input addresses. The combination creates a genuinely tactile simulation of hardware I/O.

### The Assembler / Editor

The Assembler and Editor is the integrated development environment where you write, assemble, and load Beboputer programs. It is divided into several functional areas:

**The source editor** occupies the main portion of the window — a plain-text editing area where you type your assembly language source code. It supports full keyboard editing including cut, copy, paste, undo, and redo. Programs are written one instruction per line, with labels in the left column, mnemonics in the centre, and operands to the right. Comments are introduced with the `#` character and run to the end of the line.

**The toolbar** across the top of the window provides the key workflow controls:

- **New** — clears the editor and starts a fresh program
- **Open** — loads a previously saved `.asm` source file from disk
- **Save / Save As** — writes the current source to a `.asm` file so your work is preserved between sessions
- **Assemble** — translates the source code into machine code. If the assembly succeeds, the resulting bytes are loaded directly into the Beboputer's RAM at the address specified by the `.ORG` directive, ready to run immediately. If errors are found, they are reported in the output panel below the editor.
- **Clear** — clears the output panel

**The output panel** at the bottom of the window shows the results of each assembly attempt. A successful assembly prints a listing of each source line alongside its assembled address and hex machine-code bytes — for example:

```
4000  A9        LDA     [SW1]
4003  8D        STA     [LED8]
4006  4C        JMP     [LOOP]
```

This listing is invaluable for understanding the relationship between assembly language and machine code. You can see exactly how many bytes each instruction occupies and what its opcode looks like in hexadecimal. If an error occurs — a typo in a mnemonic, an undefined label, or a missing `.ORG` directive — the output panel highlights the offending line and describes the problem clearly.

**Assembler syntax at a glance:**

| Element | Syntax | Example |
|---|---|---|
| Comment | `#` to end of line | `# read switch bank` |
| Label definition | `NAME:` in column 1 | `LOOP:` |
| Constant definition | `.EQU value` | `SW1: .EQU $F000` |
| Load address | `.ORG address` | `.ORG $4000` |
| Immediate operand | bare value | `LDA $FF` or `ADD 10` |
| Memory reference | `[address or label]` | `LDA [SW1]` |
| End of source | `.END` | `.END` |

Once assembled, the program is live in RAM and can be run, stepped through, or inspected in the Memory Walker immediately — no separate load step is required.

---

## Writing Your First Assembly Language Program

The Beboputer assembly language is clean and readable. Instructions use familiar mnemonics: `LDA` to load the accumulator, `STA` to store it, `ADD` and `SUB` for arithmetic, `JMP` to jump unconditionally, `JZ` to jump if the Zero flag is set, `JSR` to call a subroutine, `RTS` to return. The assembler supports labels, constants defined with `.EQU`, and the `.ORG` directive to set the load address.

Comments begin with `#`. Immediate values are written as plain numbers (e.g. `$3F` for hex, `63` for decimal). Memory references are written in square brackets (e.g. `[SW1]` or `[$F000]`).

Here is a simple program that reads Switch Bank 1 and mirrors its value continuously to the LED bar:

```
SW1:     .EQU    $F000
LED8:    .EQU    $F022

         .ORG    $4000

LOOP:    LDA     [SW1]
         STA     [LED8]
         JMP     [LOOP]

         .END
```

Type this into the Assembler / Editor, click Assemble, then click **Run** in the Control toolbar. Flip the switches in the Workbench 1 window and watch the LED bar respond immediately.

The `CMPA` instruction deserves special mention because it behaves differently from many other 8-bit CPUs: in the Beboputer, the Carry flag is set when the Accumulator is *greater than* the operand, rather than the more common convention where Carry indicates a borrow. Keep this in mind when writing comparison and branching logic — the branch instruction `JC` (Jump if Carry) will fire when `ACC > operand`.

---

## Stepping Through a Program

One of the most powerful learning features is single-step execution. Instead of clicking **Run**, click **Step**. The CPU executes exactly one instruction and then halts, updating all register displays, the Memory Walker, and the Port Map. You can see precisely what each instruction did: which flags changed, what value arrived in the accumulator, what address the Program Counter moved to. Stepping through a subroutine call and watching the Stack Pointer decrement as the return address is pushed onto the stack is the kind of insight that no textbook diagram can fully convey.

---

## Managing Memory

The Beboputer has a full 64KB address space (`$0000` to `$FFFF`). User programs are typically loaded at `$4000`, leaving the lower addresses free for data and the stack, and the upper range (`$F000`–`$F0FF`) reserved for memory-mapped I/O. RAM can be cleared at any time using **File → Purge RAM**, which zeroes all 64KB and restores the I/O sentinel values, then refreshes the Memory Walker and all display panels automatically.

The EPROM Burner can load pre-assembled binary images into any region of the address space, simulating the presence of ROM chips in a physical system.

---

## Exiting the Application

Because the main window deliberately has no OS-level close button — reinforcing the idea of a dedicated embedded environment — you exit using **File → Exit**. This cleanly shuts down the CPU timer, closes all floating panels and tool windows, and terminates the application.

---

## Why the Raspberry Pi Is the Perfect Host

The Raspberry Pi's combination of affordable hardware, a mature Debian-based operating system, and strong Python support makes it an ideal dedicated machine for PY-DIYCALCULATOR. A Pi 4 or Pi 5 with a seven-inch or ten-inch touchscreen display, housed in a small case on a desk, becomes a permanent learning station — always ready to assemble and run Beboputer programs, always presenting the virtual workbench, always available for experimentation.

There is also something philosophically appropriate about running an 8-bit computer emulator on a modern ARM processor. The Beboputer's fictional CPU processes instructions one at a time at 100 cycles per second. The Pi 4's ARM Cortex-A72 is executing hundreds of millions of instructions per second underneath it — all in service of simulating something so gloriously, instructively simple.

For educators, the combination is compelling. A classroom of Raspberry Pis, each running PY-DIYCALCULATOR, gives every student their own complete assembly language development environment for the cost of a single textbook. The visual immediacy of the workbench displays, the register panel, and the step-by-step execution mode makes abstract concepts — flags, stacks, memory-mapped I/O, subroutine calls — concrete and observable.

---

## Conclusion

PY-DIYCALCULATOR on the Raspberry Pi is more than just a piece of software. It is a bridge between the golden age of 8-bit computing and modern hardware, between theory and practice, between a book and a blinking LED. Whether you are a student encountering assembly language for the first time, an educator looking for an engaging hands-on tool, or a seasoned engineer who learned to program on a Z80 or 6502 and wants to revisit those fundamentals, the Beboputer has something to offer.

Install it. Flip the switches. Watch the LEDs. Write a few dozen lines of assembly. Step through them instruction by instruction and watch the Program Counter tick forward, the flags flip, the accumulator fill with values. Then write something more ambitious — a hex display routine, a sorting algorithm, a looping pattern on the LED bar — and feel the satisfaction of understanding exactly what the machine is doing at every moment.

That understanding is rarer than it should be. PY-DIYCALCULATOR, on a Raspberry Pi, puts it within reach of everyone.

---

*Festooned with nuggets of information and tidbits of trivia, our book* How Computers Do Math *(ISBN: 0471732788) provides an incredibly fun and interesting introduction to the way in which computers perform their magic in general and how they do math in particular. PY-DIYCALCULATOR is the companion software to the book, published by Wiley. The Python software can be downloaded from the DIY Calculator website: [DIY Calculator :: Home of How Computers Do Math](https://www.clivemaxfield.com/diycalculator/)*
