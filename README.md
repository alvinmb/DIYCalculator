# Beboputer_python port

**Current version: 10.0.0** — see [RELEASE_NOTES.md](RELEASE_NOTES.md) for what's changed, and [VERSIONING.md](VERSIONING.md) for how version numbers are managed and released.

Festooned with nuggets of information and tidbits of trivia, our book How Computers Do Math (ISBN: 0471732788) provides an incredibly fun and interesting introduction to the way in which computers perform their magic in general and how they do math in particular (check out the contents).

The CD-ROM accompanying the book contains a virtual "Do-it-Yourself (DIY)" computer/calculator called the DIY Calculator. The book’s step-by-step interactive laboratories guide you in the creation of a simple calculator program to run on your DIY Calculator (check out the laboratories). This CD-ROM also contains a wealth of additional information, such as the 200-page Official DIY Calculator Data Book and a rather interesting History of Calculators, Computers, and Other Stuff document.
the origional software was only made available on the windows platform. The software has been converted to Python, making it available on Windows, macOS and Linux, specifically on the Raspberry Pi OS. As of v10.0.0 the primary build (`beboputer_tk`) uses tkinter, part of the Python standard library, instead of PyQt5 — see the "Which build?" note below.

## Installing

- **Windows**: run `BeboputerTkSetup.exe` from the latest release (build it yourself with `bin\beboputer_tk\build_installer.bat`).
- **Raspberry Pi / Debian**: `sudo dpkg -i beboputer_10.0.0_all.deb && sudo apt-get install -f` (see `bin/beboputer_tk/RPI_INSTALL/README.txt` for details, or build the .deb yourself with `bash bin/beboputer_tk/RPI_INSTALL/build_deb.sh`).
- **macOS**: no packaged tkinter installer yet — run from source (below) in the meantime.
- **From source**: `python -m beboputer_tk` (requires Python 3.8+; tkinter ships with the standard Python installer, no extra packages to install) from the `bin/` folder.

### Which build?

`beboputer_tk` (tkinter) is the actively developed, primary build going forward — see the v10.0.0 entry in [RELEASE_NOTES.md](RELEASE_NOTES.md) for why. The original PyQt5 build, `beboputer_v7`, is **discontinued** — it still lives in the repo for reference and can be run from source with `python -m beboputer_v7` (requires PyQt5) or built via `bin/beboputer_v7/build_installer.bat` / `bin/beboputer_v7/MAC_INSTALL/build_mac.sh`, but it receives no further updates of any kind (installer releases, packaging, or code changes) — all development happens on `beboputer_tk` only.
