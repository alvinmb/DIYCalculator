# Copyright (c) 2026 Alvin Brown & Clive Maxfield
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
menus.py — Menu bar construction for BebopMain.

Keeping menu-building separate from BebopMain reduces the size of
main_window.py and makes it easy to add or reorganise menu items
without touching the rest of the application logic.

Usage::

    from .menus import build_menus
    build_menus(self)   # called from BebopMain._build_menu()
"""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAction


def build_menus(win) -> None:
    """Populate *win*'s menu bar.

    Parameters
    ----------
    win:
        A :class:`BebopMain` instance.  Every action slot referenced here
        (``win._do_run``, ``win._show_cpu``, etc.) must be a method on *win*.
    """
    mb = win.menuBar()

    menu_font = QFont()
    menu_font.setPointSize(15)
    mb.setFont(menu_font)
    mb.setStyleSheet("QMenu { font-size: 15pt; } QMenuBar { font-size: 15pt; }")

    def act(text, slot) -> QAction:
        a = QAction(text, win)
        a.triggered.connect(slot)
        a.setFont(menu_font)
        return a

    # ── File ─────────────────────────────────────────────────────────────────
    fm = mb.addMenu("&File")
    fm.setFont(menu_font)
    fm.addAction(act("&New Project...",     win._new_project))
    fm.addAction(act("&Open Project...",    win._open_project))
    fm.addAction(act("&Save Project...",    win._save_project))
    fm.addAction(act("Save Project &As...", win._save_project_as))
    fm.addSeparator()
    fm.addAction(act("&Load RAM...",        win._load_ram))
    fm.addAction(act("&Save RAM...",        win._save_ram))
    fm.addAction(act("&Purge RAM...",       win._purge_ram))
    fm.addSeparator()
    fm.addAction(act("&Exit",               win.close))

    # ── Memory ───────────────────────────────────────────────────────────────
    mm = mb.addMenu("&Memory")
    mm.setFont(menu_font)
    mm.addAction(act("Memory &Walker",      win._show_mem_walker))
    mm.addAction(act("&Find Address...",    win._find_address))

    # ── Display ──────────────────────────────────────────────────────────────
    dm = mb.addMenu("&Display")
    dm.setFont(menu_font)
    dm.addAction(act("&CPU Registers",      win._show_cpu))
    dm.addAction(act("&Message Display",    win._show_msg_display))
    dm.addAction(act("&Terminal",           win._show_terminal))
    dm.addAction(act("&Port Map Status",    win._show_ports))
    dm.addAction(act("&Disassembler",       win._show_disassembler))

    # ── Tools ────────────────────────────────────────────────────────────────
    tm = mb.addMenu("&Tools")
    tm.setFont(menu_font)
    tm.addAction(act("System &Clock...",        win._set_clock))
    tm.addSeparator()
    tm.addAction(act("EPROM &Burner",           win._show_eprom))
    tm.addAction(act("Calculator...",           win._show_calculator))
    tm.addAction(act("Keyboard...",             win._show_keyboard))
    tm.addAction(act("Workbench 1...",          win._show_workbench))
    tm.addAction(act("Assembler / Editor...",   win._show_compiler))

    # ── Help ─────────────────────────────────────────────────────────────────
    hm = mb.addMenu("&Help")
    hm.setFont(menu_font)
    hm.addAction(act("&Help…",      win._show_help))
    hm.addAction(act("DIY Calculator on the web", win._show_web))
    hm.addSeparator()
    hm.addAction(act("&About...",   win._show_about))
    hm.addAction(act("&Credits...", win._show_credits))
