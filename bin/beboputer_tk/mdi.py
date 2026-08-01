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
mdi.py -- a QMdiArea/QMdiSubWindow-alike for plain tkinter, which has no
built-in MDI container.

    MdiArea   -- a Frame that acts as the "desktop" -- clips its
                 children to its own bounds, like QMdiArea's viewport.
    MdiChild  -- a floating sub-window inside that Frame: title bar
                 (drag to move, double-click to toggle maximize),
                 close button, resize grip in the bottom-right corner,
                 raises to the front on click -- the same feature set
                 as QMdiSubWindow (minus minimize, which the Qt app
                 doesn't use either).

Both are built entirely from tk.Frame/Label + place() geometry
management and mouse-event bindings -- no third-party packages.

tile_children() arranges an MdiArea's children without overlap, using
the same 3-tier fallback idea as beboputer_v7/main_window.py's
_layout_startup_panels(): side-by-side if everything fits, else a
2-row wrap, else a stacked column -- computed against the MdiArea's
current size instead of the screen's.

Verified via headless testing during this migration's Phase 0 spike --
drag, resize, maximize/restore, raise-to-front, close, and non-overlap
tiling all confirmed correct. See prototypes/tkinter_migration/
pseudo_mdi.py for the runnable interactive demo this was promoted
from, and TKINTER_MIGRATION.md sec. 3.1 for the full spike writeup.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field


# ── look & feel constants ────────────────────────────────────────────────
TITLE_BG        = "#2E74B5"
TITLE_BG_INACT  = "#8FA8BE"
TITLE_FG        = "#FFFFFF"
TITLE_H         = 32
GRIP_SIZE       = 14
MIN_W, MIN_H    = 160, 100
DESKTOP_BG      = "#B9C7D6"
BORDER          = "#1F4E78"


class MdiChild(tk.Frame):
    """One floating sub-window living inside an MdiArea.

    Parameters
    ----------
    area : MdiArea
        The parent desktop this child is placed on.
    title : str
    x, y, width, height : int
        Initial geometry, in the MdiArea's own coordinate space.
    resizable : bool
        Whether the bottom-right resize grip is shown.
    on_close : callable() -> None, optional
        Called after the child removes itself. If it returns falsy
        (or is None), the child is destroyed; the callback can also
        just hide it instead by not destroying anything itself --
        MdiChild always does its own destroy() regardless, so use
        on_close for bookkeeping (e.g. clearing a "panel open" flag),
        not to veto the close.
    """

    def __init__(self, area: "MdiArea", title: str,
                 x: int = 20, y: int = 20, width: int = 320, height: int = 220,
                 resizable: bool = True, closable: bool = True,
                 maximizable: bool = True, on_close=None):
        super().__init__(area, bg=BORDER, bd=0, highlightthickness=1,
                          highlightbackground=BORDER, highlightcolor=BORDER)
        self.area = area
        self.resizable_ = resizable
        self.maximizable_ = maximizable
        self.on_close = on_close
        self._maximized = False
        self._restore_geom = None  # (x, y, w, h) saved across maximize toggle

        self.x, self.y, self.width, self.height = x, y, width, height

        # -- title bar --------------------------------------------------
        self.titlebar = tk.Frame(self, bg=TITLE_BG, height=TITLE_H)
        self.titlebar.pack(side="top", fill="x")
        self.titlebar.pack_propagate(False)

        self.title_lbl = tk.Label(
            self.titlebar, text=title, bg=TITLE_BG, fg=TITLE_FG,
            font=("Segoe UI", 15, "bold"), anchor="w",
        )
        self.title_lbl.pack(side="left", fill="both", expand=True, padx=(8, 0))

        if closable:
            close_btn = tk.Label(
                self.titlebar, text="✕", bg=TITLE_BG, fg=TITLE_FG,
                font=("Segoe UI", 16, "bold"), width=3, cursor="hand2",
            )
            close_btn.pack(side="right", fill="y")
            close_btn.bind("<Button-1>", lambda e: self.close())
            close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#C0392B"))
            close_btn.bind("<Leave>", lambda e: close_btn.config(bg=TITLE_BG))

        self._max_btn = None
        if maximizable:
            max_btn = tk.Label(
                self.titlebar, text="□", bg=TITLE_BG, fg=TITLE_FG,
                font=("Segoe UI", 16, "bold"), width=3, cursor="hand2",
            )
            max_btn.pack(side="right", fill="y")
            max_btn.bind("<Button-1>", lambda e: self.toggle_maximize())
            self._max_btn = max_btn

        # -- content area -------------------------------------------------
        self.content = tk.Frame(self, bg="#D4D0C8")
        self.content.pack(side="top", fill="both", expand=True)

        # -- resize grip --------------------------------------------------
        self.grip = None
        if resizable:
            self.grip = tk.Frame(self, bg=BORDER, cursor="bottom_right_corner",
                                  width=GRIP_SIZE, height=GRIP_SIZE)
            self.grip.place(relx=1.0, rely=1.0, anchor="se")
            self.grip.bind("<ButtonPress-1>", self._resize_start)
            self.grip.bind("<B1-Motion>", self._resize_drag)

        # -- drag-to-move ---------------------------------------------------
        for w in (self.titlebar, self.title_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
        if maximizable:
            self.title_lbl.bind("<Double-Button-1>", lambda e: self.toggle_maximize())

        # raise-to-front on any click anywhere in the child
        self.bind("<ButtonPress-1>", self._raise_only, add="+")
        self.titlebar.bind("<ButtonPress-1>", self._raise_only, add="+")

        self._place()
        self.raise_child()

    # -- title -----------------------------------------------------------------

    def set_title(self, text: str):
        """Update the title-bar text -- used by panels whose displayed
        name changes at runtime (e.g. the Assembler/Editor showing the
        current file name, matching Qt's setWindowTitle() calls)."""
        self.title_lbl.configure(text=text)

    # -- geometry ------------------------------------------------------------

    def _place(self):
        self.place(x=self.x, y=self.y, width=self.width, height=self.height)

    def raise_child(self):
        self.lift()
        self.area._set_active(self)

    def _set_active_look(self, active: bool):
        bg = TITLE_BG if active else TITLE_BG_INACT
        self.titlebar.config(bg=bg)
        self.title_lbl.config(bg=bg)

    # -- drag -----------------------------------------------------------------

    def _drag_start(self, event):
        self._drag_dx = event.x_root - self.winfo_x() - self.area.winfo_rootx()
        self._drag_dy = event.y_root - self.winfo_y() - self.area.winfo_rooty()
        self.raise_child()

    def _drag_move(self, event):
        if self._maximized:
            return
        area_w = self.area.winfo_width()
        area_h = self.area.winfo_height()
        new_x = event.x_root - self.area.winfo_rootx() - self._drag_dx
        new_y = event.y_root - self.area.winfo_rooty() - self._drag_dy
        # keep at least a sliver of the title bar reachable inside the desktop
        new_x = max(-(self.width - 40), min(new_x, area_w - 40))
        new_y = max(0, min(new_y, area_h - TITLE_H))
        self.x, self.y = new_x, new_y
        self._place()

    # -- resize ---------------------------------------------------------------

    def _resize_start(self, event):
        self._resize_ox = event.x_root
        self._resize_oy = event.y_root
        self._resize_ow = self.width
        self._resize_oh = self.height
        self.raise_child()

    def _resize_drag(self, event):
        if self._maximized:
            return
        area_w = self.area.winfo_width()
        area_h = self.area.winfo_height()
        dw = event.x_root - self._resize_ox
        dh = event.y_root - self._resize_oy
        new_w = max(MIN_W, min(self._resize_ow + dw, area_w - self.x))
        new_h = max(MIN_H, min(self._resize_oh + dh, area_h - self.y))
        self.width, self.height = new_w, new_h
        self._place()

    # -- maximize toggle --------------------------------------------------------

    def toggle_maximize(self):
        if not self.maximizable_:
            return
        if not self._maximized:
            self._restore_geom = (self.x, self.y, self.width, self.height)
            self.x, self.y = 0, 0
            self.width = self.area.winfo_width()
            self.height = self.area.winfo_height()
            self._maximized = True
            self._max_btn.config(text="❒")
        else:
            self.x, self.y, self.width, self.height = self._restore_geom
            self._maximized = False
            self._max_btn.config(text="□")
        self._place()
        self.raise_child()

    # -- close ------------------------------------------------------------------

    def close(self):
        self.area._forget(self)
        if self.on_close is not None:
            self.on_close()
        self.destroy()

    def _raise_only(self, event):
        self.raise_child()


class MdiArea(tk.Frame):
    """The 'desktop' surface that MdiChild windows live on.

    Just a plain Frame with a distinct background so child windows read
    clearly against it -- MdiChild.place()s itself directly onto this
    frame's coordinate space and MdiArea clips naturally because place()
    coordinates outside a Frame's bounds are simply not drawn.
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", DESKTOP_BG)
        super().__init__(parent, **kwargs)
        self._children: list[MdiChild] = []
        self._active: MdiChild | None = None

    def add_child(self, title, x=20, y=20, width=320, height=220,
                  resizable=True, closable=True, maximizable=True,
                  on_close=None) -> MdiChild:
        child = MdiChild(self, title, x, y, width, height,
                          resizable=resizable, closable=closable,
                          maximizable=maximizable, on_close=on_close)
        self._children.append(child)
        return child

    def _forget(self, child: MdiChild):
        if child in self._children:
            self._children.remove(child)
        if self._active is child:
            self._active = self._children[-1] if self._children else None

    def _set_active(self, child: MdiChild):
        prev, self._active = self._active, child
        if prev is not None and prev is not child and prev.winfo_exists():
            prev._set_active_look(False)
        child._set_active_look(True)

    @property
    def children_windows(self):
        return list(self._children)


# ── non-overlap initial layout ──────────────────────────────────────────────

@dataclass
class PanelSpec:
    title: str
    width: int
    height: int
    min_width: int = MIN_W
    min_height: int = MIN_H
    resizable: bool = True
    closable: bool = True
    maximizable: bool = True


def tile_children(area: MdiArea, specs: list[PanelSpec], margin: int = 8):
    """Place *specs* on *area* without overlap, mirroring
    main_window.py's _layout_startup_panels() 3-tier fallback:

      1. Side-by-side in one row, if the sum of widths fits.
      2. Two-row wrap, if a 2-row grid fits.
      3. Stacked single column (scrolled by resizing, same as the last
         resort in the Qt version), each panel shrunk to fit if needed.

    Returns the list of created MdiChild windows, in *specs* order.
    """
    area.update_idletasks()
    avail_w = max(area.winfo_width(), 1)
    avail_h = max(area.winfo_height(), 1)

    total_w = sum(s.width for s in specs) + margin * (len(specs) + 1)
    tallest = max(s.height for s in specs) + margin * 2

    children: list[MdiChild] = []

    if total_w <= avail_w and tallest <= avail_h:
        # Tier 1: side-by-side
        x = margin
        for s in specs:
            c = area.add_child(s.title, x=x, y=margin, width=s.width,
                                height=s.height, resizable=s.resizable,
                                closable=s.closable, maximizable=s.maximizable)
            children.append(c)
            x += s.width + margin
        return children

    half = (len(specs) + 1) // 2
    row1, row2 = specs[:half], specs[half:]
    row1_w = sum(s.width for s in row1) + margin * (len(row1) + 1)
    row2_w = sum(s.width for s in row2) + margin * (len(row2) + 1)
    row_h = max((s.height for s in row1), default=0) + margin
    total_h = row_h + max((s.height for s in row2), default=0) + margin * 2

    if max(row1_w, row2_w) <= avail_w and total_h <= avail_h:
        # Tier 2: two-row wrap
        x = margin
        for s in row1:
            c = area.add_child(s.title, x=x, y=margin, width=s.width,
                                height=s.height, resizable=s.resizable,
                                closable=s.closable, maximizable=s.maximizable)
            children.append(c)
            x += s.width + margin
        x = margin
        y2 = row_h + margin
        for s in row2:
            c = area.add_child(s.title, x=x, y=y2, width=s.width,
                                height=s.height, resizable=s.resizable,
                                closable=s.closable, maximizable=s.maximizable)
            children.append(c)
            x += s.width + margin
        return children

    # Tier 3: stacked column, shrink each to fit the available width and
    # an equal share of the available height.
    each_h = max(MIN_H, (avail_h - margin * (len(specs) + 1)) // len(specs))
    y = margin
    for s in specs:
        w = min(s.width, avail_w - margin * 2)
        c = area.add_child(s.title, x=margin, y=y, width=w, height=each_h,
                            resizable=s.resizable, closable=s.closable,
                            maximizable=s.maximizable)
        children.append(c)
        y += each_h + margin
    return children


