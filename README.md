# Beboputer_python port

**Current version: 8.0.0** — see [RELEASE_NOTES.md](RELEASE_NOTES.md) for what's changed, and [VERSIONING.md](VERSIONING.md) for how version numbers are managed and released.

Festooned with nuggets of information and tidbits of trivia, our book How Computers Do Math (ISBN: 0471732788) provides an incredibly fun and interesting introduction to the way in which computers perform their magic in general and how they do math in particular (check out the contents).

The CD-ROM accompanying the book contains a virtual "Do-it-Yourself (DIY)" computer/calculator called the DIY Calculator. The book’s step-by-step interactive laboratories guide you in the creation of a simple calculator program to run on your DIY Calculator (check out the laboratories). This CD-ROM also contains a wealth of additional information, such as the 200-page Official DIY Calculator Data Book and a rather interesting History of Calculators, Computers, and Other Stuff document.
the origional software was only made available on the windows platform. The software has been converted to Python and QT5, makeing it available on Window,MacOS and Linux, specifically on the Raspbery PI os.

## Installing

- **Windows**: run `BeboputerSetup.exe` from the latest release.
- **Raspberry Pi / Debian**: `sudo dpkg -i beboputer_8.0.0_all.deb && sudo apt-get install -f` (see `bin/beboputer_v7/RPI_INSTALL/README.txt` for details and an alternate one-shot install script).
- **macOS**: build via `bin/beboputer_v7/MAC_INSTALL/build_mac.sh`.
- **From source**: `python -m beboputer_v7` (requires Python 3.8+ and PyQt5) from the `bin/` folder.
