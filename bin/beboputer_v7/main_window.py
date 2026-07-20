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
BebopMain — top-level MDI window.

Wires together the CPU, panels, dialogs and tool windows.  The menu
bar and toolbar are constructed here directly (the v4 source applied
extra Tools-menu entries via a module-level monkey-patch; that has
been folded back into :meth:`_build_menu` / :meth:`_build_toolbar`).

Panel responsibilities
──────────────────────
Message Display  — always-on diagnostic log; receives emulator system
                   messages (step results, resets, halts, file loads …).
Terminal         — CRT-style device driven by the Beboputer itself via
                   memory-mapped port $F028.  Power is controlled by the
                   calculator's On/Off button.
"""

import os
import random
import webbrowser
from pathlib import Path

from .paths import resource_path, default_open_dir as _default_open_dir, default_save_dir as _default_save_dir

# ── Cross-platform file-dialog default directories ──────────────────────────
# See paths.py: default_open_dir()/default_save_dir() point at Data/
# WorkInProgress when running from source, and at a single writable
# ~/Documents/PY-DIYCALCULATOR workspace (seeded with the sample files)
# in packaged builds, since the app's install folder is not reliably
# writable by a non-admin user there.

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QStatusBar, QDialog, QVBoxLayout,
    QFileDialog, QMessageBox, QInputDialog,
    QToolBar, QPushButton,
)

from .constants import FLAG_I


class _PanelDialog(QDialog):
    """Thin QDialog wrapper that gives a panel widget a native OS title bar.

    Works identically to EpromBurner — the OS draws the title bar, so
    there are no Qt stylesheet / ControllerWidget conflicts.
    Closing the dialog hides it rather than destroying it so the panel
    can be re-raised from the menu/toolbar.
    """

    def __init__(self, widget, title, x, y, w, h, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(w, h)
        self.move(x, y)
        # Remove the "?" help button Qt adds to QDialogs by default.
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)

    def closeEvent(self, event):
        """Hide on user close; accept when the app is shutting down."""
        if getattr(self, '_app_closing', False):
            event.accept()
        else:
            event.ignore()
            self.hide()

from .cpu import CPU
from .panels.cpu_panel import CPUPanel
from .panels.disassembler import DisassemblerPanel
from .panels.memory_walker import MemoryWalker
from .panels.port_monitor import PortMonitor
from .panels.message_display import MessageDisplay
from .panels.terminal import Terminal
from .dialogs.about import AboutDialog
from .menus import build_menus
from .dialogs.eprom_burner import EpromBurner
from .dialogs.system_clock import SystemClockDialog
from .tools.calculator import Calculator
from .tools.compiler import CompilerWindow
from .tools.keyboard import KeyboardPanel
from .tools.workbench import WorkbenchPanel
from .instruction_messages import InstructionMessages
from . import __version__


class BebopMain(QMainWindow):

    def __init__(self):
        super().__init__()
        self.cpu = CPU()
        self._instr_msgs = InstructionMessages()
        self._run_timer = QTimer(self)
        self._run_timer.timeout.connect(self._run_tick)
        self._clock_hz = 100   # simulated Hz (ticks/sec)
        self.setWindowTitle(f"PY-DIYCALCULATOR  v{__version__}")
        # Remove the OS close, minimise and maximise buttons.
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowCloseButtonHint
            & ~Qt.WindowMinimizeButtonHint
            & ~Qt.WindowMaximizeButtonHint
        )
        self.showMaximized()
        self._build_ui()
        self._refresh_all()

        # Boot messages go straight to the always-on diagnostic log.
        self.msg_display.message("PY-DIYCALCULATOR")
        self.msg_display.message(
            f"RAM: {self.cpu.RAM_SIZE // 1024}KB  |  Clock: {self._clock_hz}Hz (simulated)"
        )
        self.msg_display.message("Switch calculator on (click on/off) button")
        self.msg_display.message("Load a .RAM file")

        # Show the Calculator on app start and wire its On/Off → terminal.
        self._show_calculator()

        # Keypad port $F011: read-clear strobe — resets to $FF (no-key) the
        # moment the CPU reads a key value, so polling loops see each key once.
        def _keypad_read_hook(val):
            if val != 0xFF:
                self.cpu.ram[0xF011] = 0xFF
        self.cpu._read_hooks[0xF011] = _keypad_read_hook

        # Write hook: capture each keypress for the port monitor BEFORE the
        # read-clear strobe wipes ram[0xF011] back to $FF.
        # CE ($10) and Clear ($11) also immediately clear the display port so
        # the calculator clears even when no CPU program is running.
        def _keypad_write_hook(val):
            self.port_mon.on_key_press(val)
            if val in (0x10, 0x11):          # CE or Clear
                self.cpu._write(0xF031, 0x10)  # send CLRCODE to display
        self.cpu._write_hooks[0xF011] = _keypad_write_hook

    # ---------------------------------------------------------------- build --

    def _build_ui(self):
        self._build_menu()
        self._build_toolbar()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        # Grey background fills the main window behind the floating panels.
        bg = QWidget()
        bg.setStyleSheet("background: #808080;")
        self.setCentralWidget(bg)

        # ── floating panel dialogs ────────────────────────────────────────────
        #
        #  On startup only three panels are shown:
        #    Calculator      — top-left (positioned in _show_calculator)
        #    Memory Walker   — left column
        #    Message Display — fills the remainder
        #
        #  All other panels are created hidden; use the Display/Tools menus
        #  to open them.
        #
        # ── startup layout ───────────────────────────────────────────────────────
        # y=65 clears the main window title bar (~30 px) + menu bar (~25 px).
        # x positions: calculator(10) + calc_width(720) + gap(10) = 740 for walker;
        #              walker(740) + walker_width(260) + gap(10)  = 1010 for message.
        _Y   = 65
        _MWX = 740    # Memory Walker left edge
        _MDX = 1010   # Message Display left edge
        self.mem_walker    = self._sub(MemoryWalker(self.cpu),       "Memory Walker",         _MWX,  _Y, 260, 680, visible=True)
        self.port_mon      = self._sub(PortMonitor(self.cpu),      "I/O Ports Display",        0, 450, 405, 270, visible=False)
        self.msg_display   = self._sub(MessageDisplay(),           "Message Display",        _MDX,  _Y, 516, 340, visible=True)
        self.cpu_panel     = self._sub(CPUPanel(self.cpu),         "CPU Register Display",   650,   10, 300, 270, visible=False)
        self.terminal      = self._sub(Terminal(),                 "Terminal",               650,  410, 595, 420, visible=False)
        self.disassembler  = self._sub(DisassemblerPanel(self.cpu),"Disassembler",          1010,  400, 420, 420, visible=False)

        # Hook memory-mapped port $F028 → terminal.write_char.
        # Any  STORE ($F028), A  instruction sends ACC as one ASCII byte
        # to the terminal screen (only rendered when the terminal is on).
        self.cpu._write_hooks[0xF028] = self.terminal.write_char

        self._connect_ctrl()

    def _sub(self, widget, title, x, y, w, h, visible=True):
        """Wrap widget in a floating _PanelDialog; show it only if visible=True."""
        dlg = _PanelDialog(widget, title, x, y, w, h, parent=self)
        if visible:
            dlg.show()
        return widget

    def _connect_ctrl(self):
        # The Memory Walker can also drive the CPU (STEP column / RUN-to-BP).
        # Wire its signals to a full refresh so the CPU register display,
        # port monitor, etc. update on every instruction it executes.
        self.mem_walker.step_executed.connect(self._on_mem_walker_step)
        self.mem_walker.bp_hit.connect(self._on_mem_walker_bp_hit)

    def _build_menu(self):
        build_menus(self)

    def _build_toolbar(self):
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        self.interrupt_btn = QPushButton("⚡ Interrupt")
        self.interrupt_btn.setStyleSheet("font-weight: bold;")
        self.interrupt_btn.setToolTip(
            "Assert the interrupt mask bit (flag I) — the same effect as "
            "the CPU executing SETIM."
        )
        self.interrupt_btn.clicked.connect(self._do_interrupt)
        tb.addWidget(self.interrupt_btn)

    # --------------------------------------------------------------- CPU ops --

    def _do_run(self):
        if self.cpu.halted:
            self.msg_display.message("CPU is HALTed. Reset first.")
            return
        self.cpu.running = True
        self._run_timer.start(1000 // max(1, self._clock_hz))
        self.statusBar().showMessage("Running…")

    def _do_halt(self):
        self.cpu.running = False
        self._run_timer.stop()
        self.statusBar().showMessage(f"Halted at PC=${self.cpu.pc:04X}")
        self._refresh_all()

    def _do_step(self):
        self._run_timer.stop()
        self.cpu.running = False
        self.cpu.step()
        self.msg_display.message(self._instr_msgs.describe(self.cpu))
        self._check_port_output()
        self._refresh_all()
        if self.cpu.halted:
            self.statusBar().showMessage("HALT instruction executed.")
            self.msg_display.message("--- HALT ---")

    def _do_interrupt(self):
        """Manually assert the interrupt mask bit (flag I).

        Same effect as the CPU executing a SETIM instruction, but
        triggered from the UI rather than from a running program —
        lets you test interrupt-mask-dependent code paths without
        having to assemble a SETIM into the program itself.

        Only takes effect while the calculator is switched on — with
        the calculator off there's no powered board to interrupt, same
        reasoning as _open_project()'s "must be ON to load a file" gate.
        """
        calc = getattr(self, "_calc_win", None)
        if calc is None or not calc.powered:
            self.msg_display.message("Interrupt ignored — calculator is off.")
            self.statusBar().showMessage("Interrupt ignored — calculator is off.")
            return
        self.cpu.flags |= FLAG_I
        self.cpu.flags_touched |= FLAG_I
        self._refresh_all()
        self.msg_display.message("⚡ Interrupt: mask bit (I) set.")
        self.statusBar().showMessage("Interrupt mask bit (I) set.")

    def _workbench_open_and_calc_on(self) -> bool:
        """True when the Workbench window is visible and the calculator is
        powered on.

        Gates whether loading a program should leave the calculator's
        display alone. With the Workbench open and the calc on, the user
        is watching a live board -- a program load shouldn't visibly
        disturb the calc screen (blanking it or swapping in the boot-dash
        placeholder) the way a full Reset intentionally does.
        """
        wb   = getattr(self, "_workbench_win", None)
        calc = getattr(self, "_calc_win", None)
        return (wb is not None and wb.isVisible()
                and calc is not None and calc.powered)

    def _do_reset(self, clear_calc_display=True):
        """Reset the CPU (and Workbench/Terminal/port monitor) to idle.

        clear_calc_display=False is used on power-on (see
        _on_power_changed): _apply_power_state() has just written the
        boot dash sequence to the calculator, and clearing the display
        here would immediately wipe it back to blank before the user ever
        sees the dashes. The explicit Reset button always wants the
        clear, so it keeps the default of True.
        """
        self._run_timer.stop()
        self.cpu.reset()
        if clear_calc_display and getattr(self, "_calc_win", None) is not None:
            # blank_display(), not write_display(0x10): a Reset means no
            # program is driving the display yet, so it should go truly
            # blank -- showing "0" would misleadingly imply a program had
            # already initialized it.
            self._calc_win.blank_display()
        self.port_mon.reset()   # clear I/O port display
        if getattr(self, "_workbench_win", None) is not None:
            self._workbench_win.reset()   # switches back to OFF, outputs blanked
        self.terminal.clear()   # blank the terminal screen, if anything was printed
        self.msg_display.message("↺ CPU Reset.")
        self.statusBar().showMessage("Reset")
        self._refresh_all()

    def _run_tick(self):
        if self.cpu.halted:
            self._run_timer.stop()
            self.cpu.running = False
            self.statusBar().showMessage(f"HALT at PC=${self.cpu.pc:04X}")
            self._refresh_all()
            return
        bp_hit = None
        for _ in range(10):    # execute 10 instructions per tick
            self.cpu.step()
            self._check_port_output()
            self.cpu_panel.refresh()
            self.port_mon.refresh()
            if self.cpu.halted:
                break
            # Stop on a Memory Walker breakpoint, same as its own
            # "RUN to BP" button -- previously the main toolbar's Run
            # ignored breakpoints entirely, so e.g. a BP set at $0000
            # to catch lab2a's `JMP [$0000]` had no effect here and
            # Run would just free-run through the NOP sled forever.
            if self.cpu.pc in self.mem_walker._breakpoints:
                bp_hit = self.cpu.pc
                break
        # Keep the Message Display and Memory Walker's ▶ pointer live
        # while Run is ticking -- previously only the CPU panel/port
        # monitor refreshed here, so the Message Display showed nothing
        # and the pointer stayed frozen at wherever it was when Run was
        # clicked, even though the CPU kept executing underneath (bug
        # #0003: looked like Run wasn't doing anything).
        self.mem_walker.highlight_pc(self.cpu.pc)
        self.msg_display.message(self._instr_msgs.describe(self.cpu))
        if self.cpu.halted:
            self._run_timer.stop()
            self.cpu.running = False
            self.statusBar().showMessage("HALT instruction executed.")
            self.msg_display.message("--- HALT ---")
        elif bp_hit is not None:
            self._run_timer.stop()
            self.cpu.running = False
            reason = f"BP hit at ${bp_hit:04X}"
            self.statusBar().showMessage(reason)
            self.msg_display.message(reason)

    def _on_mem_walker_step(self, mnemonic):
        """Called after the MemoryWalker single-steps the CPU."""
        self.msg_display.message(self._instr_msgs.describe(self.cpu))
        self._check_port_output()
        self._refresh_all()   # keeps Disassembler (and mem walker) on the live PC
        if self.cpu.halted:
            self.statusBar().showMessage("HALT instruction executed.")
            self.msg_display.message("--- HALT ---")

    def _on_mem_walker_bp_hit(self, reason):
        """Called when MemoryWalker.run_to_breakpoint stops (BP / HALT / limit)."""
        self.msg_display.message(reason)
        self.statusBar().showMessage(reason)
        self._check_port_output()
        self._refresh_all()   # keeps Disassembler (and mem walker) on the live PC

    def _check_port_output(self):
        """If CPU wrote to port 1, forward to the terminal as ASCII."""
        ch = self.cpu.ports_out[1]
        if ch != 0:
            self.terminal.write_char(ch)
            self.cpu.ports_out[1] = 0

    def _refresh_all(self):
        self.cpu_panel.refresh()
        self.port_mon.refresh()
        self.mem_walker.highlight_pc(self.cpu.pc)
        # Keep disassembler in sync with PC when the panel is visible.
        dlg = self.disassembler.parent()
        if dlg is not None and dlg.isVisible():
            self.disassembler.refresh_at_pc(self.cpu.pc)

    # ----------------------------------------------------------- menu slots --

    def _show_cpu(self):
        self._raise_sub(self.cpu_panel)

    def _show_mem_walker(self):
        self._raise_sub(self.mem_walker)

    def _show_ports(self):
        self._raise_sub(self.port_mon)

    def _show_msg_display(self):
        self._raise_sub(self.msg_display)

    def _show_terminal(self):
        self._raise_sub(self.terminal)

    def _show_disassembler(self):
        self._raise_sub(self.disassembler)

    def _raise_sub(self, widget):
        """Bring a panel's dialog window to front."""
        dlg = widget.parent()
        if isinstance(dlg, _PanelDialog):
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()

    def _new_project(self):
        if QMessageBox.question(self, "New Project", "Clear all RAM and reset CPU?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.cpu.ram = bytearray(self.cpu.RAM_SIZE)
            self._do_reset()

    def _open_project(self):
        calc = getattr(self, "_calc_win", None)
        if calc is None or not calc.powered:
            QMessageBox.warning(
                self, "Calculator Off",
                "The calculator must be switched ON before you can load a file.\n\n"
                "Press the On\\Off button on the calculator, then try again."
            )
            return
        dlg = QFileDialog(self, "Open ROM/RAM")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setNameFilters(["ROM Files (*.rom *.ram)", "All Files (*)"])
        dlg.setDirectory(_default_open_dir())
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = dlg.selectedFiles()[0]
        if path:
            self._load_file(path)

    def _load_file(self, path):
        # Load address is chosen by file extension:
        #   .rom  -> $0000  (boot / system code at the reset vector)
        #   .ram  -> $4000  (compiler output / user program)
        #   other -> $4000  (treated as a raw bytecode blob, legacy default)
        ext = os.path.splitext(path)[1].lower()
        LOAD_ADDR = 0x0000 if ext == ".rom" else 0x4000
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.cpu.ram = bytearray(self.cpu.RAM_SIZE)
            # Fresh ram_touched too: a newly loaded file replaces RAM
            # wholesale, so only the bytes the file actually supplies
            # are "known" — everything else should read back as
            # undefined ($XX) in Memory Walker, not stale touched state
            # left over from whatever ran before.
            self.cpu.ram_touched = bytearray(self.cpu.RAM_SIZE)
            if len(data) == self.cpu.RAM_SIZE:
                self.cpu.ram[:] = data
                self.cpu.ram_touched[:] = b"\x01" * self.cpu.RAM_SIZE
                msg    = f"Loaded: {os.path.basename(path)}  (full 64KB image)"
                status = f"Loaded {path} (full 64KB image)"
            else:
                max_bytes = self.cpu.RAM_SIZE - LOAD_ADDR
                chunk = data[:max_bytes]
                self.cpu.ram[LOAD_ADDR:LOAD_ADDR + len(chunk)] = chunk
                self.cpu.ram_touched[LOAD_ADDR:LOAD_ADDR + len(chunk)] = b"\x01" * len(chunk)
                msg    = (f"Loaded: {os.path.basename(path)}  "
                          f"({len(chunk)} bytes @ ${LOAD_ADDR:04X})")
                status = f"Loaded {path} @ ${LOAD_ADDR:04X}"
            # Don't blank the calculator display on load: real hardware
            # shows the boot-style dash placeholder until the freshly
            # loaded program actually drives the display, so reset
            # without clearing (clear_calc_display=False) and then show
            # the dashes explicitly -- same placeholder used at power-on.
            #
            # Exception: with the Workbench open and the calc on, leave
            # the display exactly as it is -- don't even swap in the
            # dash placeholder. The user is watching a live board and a
            # load shouldn't visibly disturb the calc screen.
            self._do_reset(clear_calc_display=False)
            if (getattr(self, "_calc_win", None) is not None
                    and not self._workbench_open_and_calc_on()):
                self._calc_win.show_dash_display()
            self.msg_display.message(msg)
            self.statusBar().showMessage(status)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _save_project(self):
        dlg = QFileDialog(self, "Save ROM")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setNameFilters(["ROM Files (*.rom)", "All Files (*)"])
        dlg.setDefaultSuffix("rom")
        dlg.setDirectory(_default_save_dir())
        if dlg.exec_() != QFileDialog.Accepted:
            return
        path = dlg.selectedFiles()[0]
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(bytes(self.cpu.ram))
                self.msg_display.message(f"Saved: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _save_project_as(self):
        self._save_project()

    def _load_ram(self):
        self._open_project()

    def _save_ram(self):
        self._save_project()

    # -- Calculator button-file commands (moved here from the Calculator's
    # own File menu, which has been removed -- these just delegate to the
    # Calculator instance's existing handlers) ------------------------------

    def _load_button_file(self):
        if getattr(self, "_calc_win", None) is not None:
            self._calc_win._load_button_file()

    def _save_button_file(self):
        if getattr(self, "_calc_win", None) is not None:
            self._calc_win._save_button_file()

    def _restore_defaults(self):
        if getattr(self, "_calc_win", None) is not None:
            self._calc_win._restore_defaults()

    def _purge_ram(self):
        if QMessageBox.question(self, "Purge RAM", "Zero all 64KB of RAM?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._do_purge_ram()

    def _do_purge_ram(self):
        """Zero all RAM in-place and restore I/O sentinels.

        Every byte is now a known, deterministic value ($00), so mark
        all of RAM as "touched" — Memory Walker should display $00,
        not the undefined-garbage placeholder ($XX).
        """
        for i in range(self.cpu.RAM_SIZE):
            self.cpu.ram[i] = 0
            self.cpu.ram_touched[i] = 1
        self.cpu.ram[0xF011] = 0xFF  # restore keypad idle sentinel
        self.cpu.ram[0xF031] = 0x00  # clear display port
        self.cpu.ram[0xF032] = 0x00  # clear LED port
        self._refresh_all()
        self.msg_display.message("RAM purged.")

    def _do_random_fill_ram(self):
        """Fill all RAM with random bytes in-place and restore I/O sentinels.

        Real SRAM powers up in whatever state it happens to settle into —
        every location holds unpredictable garbage ($XX), not a suspiciously
        tidy $00. Used on power-on instead of _do_purge_ram() so the
        emulator matches that behaviour; Purge RAM (explicit menu action)
        and power-off keep the deterministic all-zero clear.

        Every byte's "touched" flag is cleared along with the refill —
        without this, addresses touched in a *previous* power cycle
        (e.g. the default program at $4000-$400C, or I/O sentinels)
        would keep showing their stale "known" status in Memory Walker,
        displaying the new random garbage as if it were a real value
        instead of the undefined-garbage placeholder ($XX).

        $0000-$3FFF is ROM, not RAM: real ROM contents are burned in
        and never "power up as garbage", so that range is left alone
        here (zeroed, not randomized) and stays marked "known" --
        only $4000-$FFFF gets the random-garbage treatment.
        """
        rom_end = self.cpu.ROM_END
        for i in range(rom_end):
            self.cpu.ram[i] = 0
            self.cpu.ram_touched[i] = 1
        for i in range(rom_end, self.cpu.RAM_SIZE):
            self.cpu.ram[i] = random.randint(0, 255)
            self.cpu.ram_touched[i] = 0
        self.cpu.ram[0xF011] = 0xFF  # restore keypad idle sentinel
        self.cpu.ram[0xF031] = 0x00  # clear display port
        self.cpu.ram[0xF032] = 0x3F  # LEDs on by default (see cpu.reset())
        for addr in (0xF011, 0xF031, 0xF032):
            self.cpu.ram_touched[addr] = 1  # sentinels are known, not garbage
        self._refresh_all()
        self.msg_display.message("Power on: RAM randomized (real hardware powers up with garbage, not zeros).")

    def _do_power_off_ram(self):
        """Mark RAM undefined on power-off, instead of zeroing it.

        $0000-$3FFF is ROM and stays defined (untouched here). The RAM
        region ($4000-$FFFF) is marked "known=0" -- undefined ($XX) in
        Memory Walker -- because there's no real hardware state to show
        once the board is off, same reasoning as the random-garbage
        power-on fill. This intentionally does NOT touch the underlying
        byte values (unlike Purge RAM, which really does zero them):
        power-off isn't "erase," it's just "we don't know/care what's
        there right now."
        """
        rom_end = self.cpu.ROM_END
        for i in range(rom_end, self.cpu.RAM_SIZE):
            self.cpu.ram_touched[i] = 0
        self._refresh_all()
        self.msg_display.message("Power off.")

    def _on_power_changed(self, on: bool):
        """Slot for Calculator power_changed — the On/Off button resets RAM
        on every transition and resets the CPU to an idle state.

        Power-on fills RAM with random garbage (matching real SRAM
        power-up behaviour) rather than zeroing it, so it does NOT
        auto-run: running at that point would free-run through random
        opcodes with nothing meaningful executing. Load or assemble a
        program first, then press Run/Step.

        Power-off marks RAM undefined again (see _do_power_off_ram) --
        it used to call _do_purge_ram() (deterministic all-zero, all
        "known"), but that's the explicit Purge RAM menu action's job,
        not power-off's. Showing $00 everywhere after power-off was
        misleading: once the board is off there's no defined state to
        show, same reasoning as the random-garbage power-on behaviour.
        """
        self.terminal.set_power(on)
        if on:
            self._do_random_fill_ram()
            self._do_reset(clear_calc_display=False)
        else:
            # Powering off must halt execution immediately -- otherwise the
            # run timer keeps ticking underneath the (now visibly "off")
            # calculator and the CPU keeps executing until the next thing
            # that happens to call _run_timer.stop() (e.g. power-on's
            # _do_reset()), making it look like a second click was needed
            # just to stop the program.
            self._run_timer.stop()
            self.cpu.running = False
            self._do_power_off_ram()

    def _power_on_clear(self):
        """On calculator power-on: zero data/stack area ($0000–$3FFF) and
        reset I/O sentinels.  Program space ($4000+) is preserved so an
        assembled program survives a power cycle."""
        for i in range(0x4000):
            self.cpu.ram[i] = 0
        self.cpu.ram[0xF011] = 0xFF  # keypad idle sentinel
        self.cpu.ram[0xF031] = 0x00  # clear display port
        self.cpu.ram[0xF032] = 0x00  # clear LED port
        self._refresh_all()
        self.msg_display.message("Power on: data RAM cleared ($0000–$3FFF).")

    def _find_address(self):
        # Build the dialog explicitly (rather than the QInputDialog.getText()
        # convenience call) so the label/input font can be bumped +2pt over
        # the app-wide default -- set via an inline stylesheet, since once a
        # stylesheet has touched font-size anywhere (styles.py's global
        # QWidget rule does), a plain setFont() on the dialog gets silently
        # overridden rather than merged (same issue noted in compiler.py's
        # button styling).
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Find Address")
        dlg.setLabelText("Enter hex address:")
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setStyleSheet("font-size: 10pt;")   # app default is ~8pt; +2pt
        ok = dlg.exec_() == QInputDialog.Accepted
        txt = dlg.textValue()
        if ok:
            try:
                addr = int(txt, 16)
                self.mem_walker._base = addr & 0xFFF0
                self.mem_walker.addr_edit.setText(f"{self.mem_walker._base:04X}")
                self.mem_walker._refresh()
                self._raise_sub(self.mem_walker)
            except ValueError:
                pass

    def _set_clock(self):
        dlg = SystemClockDialog(self._clock_hz, self)
        if dlg.exec_() == SystemClockDialog.Accepted:
            val = dlg.value()
            self._clock_hz = val
            if self._run_timer.isActive():
                self._run_timer.setInterval(1000 // max(1, val))
            self.msg_display.message(f"Clock set to {val}Hz")

    def _show_eprom(self):
        dlg = EpromBurner(self.cpu, self)
        dlg.ram_changed.connect(self._refresh_all)
        dlg.show()

    def _show_calculator(self):
        """Open (or focus) the standalone Calculator window."""
        if getattr(self, "_calc_win", None) is None:
            self._calc_win = Calculator(self)
            self._calc_win.move(10, 65)   # top-left, below main window menu bar
            # Wire the On/Off button → terminal power + RAM purge (both directions).
            self._calc_win.power_changed.connect(self._on_power_changed)
            # Hook memory-mapped port $F031 → calculator display.
            # Any  STORE ($F031), A  instruction sends ACC as one ASCII byte
            # to the calculator's display (only when the calculator is on).
            self.cpu._write_hooks[0xF031] = self._calc_win.write_display
            self.cpu._write_hooks[0xF032] = self._calc_win.write_leds
        self._calc_win.show()
        self._calc_win.raise_()
        self._calc_win.activateWindow()

    def _show_keyboard(self):
        """Open (or focus) the on-screen Keyboard."""
        if getattr(self, "_keyboard_win", None) is None:
            self._keyboard_win = KeyboardPanel(self.cpu, terminal_cb=self.terminal.write_char, parent=self)
        self._keyboard_win.show()
        self._keyboard_win.raise_()
        self._keyboard_win.activateWindow()

    def _show_workbench(self):
        """Open (or focus) Workbench 1."""
        if getattr(self, "_workbench_win", None) is None:
            self._workbench_win = WorkbenchPanel(self.cpu, parent=self)
            # Mirror the calculator's On/Off state into the workbench.
            self._calc_win.power_changed.connect(self._workbench_win.set_power)
            # Sync immediately in case the calculator is already on.
            self._workbench_win.set_power(self._calc_win.powered)
        self._workbench_win.show()
        self._workbench_win.raise_()
        self._workbench_win.activateWindow()

    def _show_compiler(self):
        """Open (or focus) the merged DIY Calculator Assembler window."""
        if getattr(self, "_compiler_win", None) is None:
            self._compiler_win = CompilerWindow(self, host_main=self)
        self._compiler_win.show()
        self._compiler_win.raise_()
        self._compiler_win.activateWindow()

    def changeEvent(self, event):
        """Keep the window maximized — prevent title-bar double-click restore."""
        from PyQt5.QtCore import QEvent
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if not (self.windowState() & Qt.WindowMaximized):
                self.showMaximized()

    def closeEvent(self, event):
        """Close all associated windows and quit the application."""
        # Mark every _PanelDialog so its closeEvent accepts instead of hiding.
        for dlg in self.findChildren(_PanelDialog):
            dlg._app_closing = True
        # Close standalone tool windows (Calculator, Keyboard, Compiler).
        for attr in ('_calc_win', '_keyboard_win', '_workbench_win', '_compiler_win'):
            win = getattr(self, attr, None)
            if win is not None:
                win.close()
        event.accept()
        QApplication.instance().quit()

    def _show_help(self):
        """Open the HTML help file in the system default browser.

        Source layout : bin/beboputer_v7_help.html  (one level above this pkg)
        Bundle layout : sys._MEIPASS/beboputer_v7_help.html  (bundle root)
        """
        import sys as _sys
        if getattr(_sys, 'frozen', False):
            # PyInstaller bundle — spec copies the file to the bundle root.
            help_path = resource_path('beboputer_v7_help.html')
        else:
            # Running from source — file lives in bin/, one level above package.
            help_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), '..', 'beboputer_v7_help.html')
            )
        webbrowser.open(f"file:///{help_path.replace(os.sep, '/')}")

    def _show_web(self):
        """Open the DIY Calculator homepage in the system default browser."""
        webbrowser.open("https://www.clivemaxfield.com/diycalculator/index.shtml")

    def _show_about(self):
        AboutDialog(self).exec_()

    def _show_credits(self):
        QMessageBox.information(self, "The Crew....",
            "PY-DIYCALCULATOR\n\n"
            "by Clive 'Max' Maxfield & Alvin Brown\n"
            "Python/PyQt5 port\n\n"
            "Assembler based on DAS by David Venhoek\n\n")
