A Python plus tickle rewrite of the vb based software that was included with the book "How computers do Math" by Clive Max Maxfield & Alvin Brown. 

The application will run on a raspberry pi and Windows. I have been testing on a Raspberry pi 5 with 1GB of memory an on Windows 11. 

Source code is also available for anyone to download.  We have added several New tools that were not in the  version delivered with the book.

- **Code Coverage** (Tools → Code Coverage…) — load a program, run it, and see which source lines actually executed vs. never ran, highlighted green/red, with a percentage summary and a saveable report. A "Track Live" mode records coverage from real interactive use (Calculator Step/Run, Memory Walker), not just headless runs.

- **Code Profiler** (Tools → Code Profiler…) — same workflow as Coverage, but ranks every line by share of total execution time, with a Hot Spots summary and a 4-tier heat-map highlight.

- **A Tiny BASIC interpreter** (`tutorial/19_tiny_basic.asm`, Exercise 19) — a small interactive BASIC-style language, written entirely in DIY Calculator assembly, driven by the on-screen Keyboard and Terminal. Supports `LET`, `PRINT`, `INPUT`, `IF...THEN`, `GOTO`, `END`, PEEK`/`POKE`** — `PEEKa` reads a byte from any RAM address, `POKEa=e` writes one, with decimal, `$hex`, or variable-letter addressing. Hex addresses reach the full 64KB space, including the memory-mapped I/O ports — so a typed-in BASIC program can now read the Keyboard latch or write the Calculator's display directly (`PEEK$F011`, `POKE$F031=72`).

In Addition we have converted the Beboputer data book into an HTML document that is now available in the application under the Help menu tree

To install the app move the .DEB file onto the pi host
ssh <user>@<host>
sudo dpkg -i beboputer_10.1.8_all.deb
sudo apt-get install -f
```
When installed the app can be launched via the pull down menu under the education branch, or from the command line by typing beboputer
