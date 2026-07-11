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
Shared Qt stylesheet + colour palette.

Imported by every visual module so the look-and-feel stays in one place.
The values are unchanged from ``beboputer_v4.py``.
"""

# ============================================================
#  COLOUR PALETTE  (Classic Mac / Win95 — matches calc.py)
# ============================================================
C = {
    "bg":          "#c0c0c0",   # classic system grey
    "panel":       "#c0c0c0",
    "border":      "#808080",   # dark bevel
    "border_lt":   "#ffffff",   # light bevel highlight
    "green":       "#006400",   # dark green for titles (LCD-style)
    "green_dim":   "#c8f0c8",   # mint LCD background
    "green_mid":   "#004d00",
    "amber":       "#8b6914",   # dark amber
    "red":         "#cc0000",   # calc red
    "red_dark":    "#8b0000",   # deep red (dots)
    "blue":        "#000080",   # classic Win navy
    "magenta":     "#cc00cc",   # calc magenta
    "white":       "#ffffff",
    "grey":        "#606060",
    "lcd_bg":      "#c8f0c8",   # mint LCD
    "lcd_fg":      "#000000",
    "btn_bg":      "#d4d0c8",   # beige button face
    "btn_bdr":     "#888888",
    "btn_hot":     "#e0dcd0",
    "btn_press":   "#c0bdb5",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background: {C['bg']};
    color: #000;
}}
QMdiArea {{
    background: #808080;
    border: none;
}}
QWidget {{
    background: {C['panel']};
    color: #000;
    font-family: 'MS Sans Serif','Tahoma','Arial';
    font-size: 11px;
}}
QMenuBar {{
    background: {C['panel']};
    color: #000;
    border-bottom: 1px solid {C['border']};
    font-size: 18px;
}}
QMenuBar::item:selected {{
    background: {C['blue']};
    color: {C['panel']};
    font-size: 18px;
}}
QMenu {{
    background: {C['panel']};
    color: #000;
    border: 1px solid {C['border']};
}}
QMenu::item:selected {{
    background: {C['blue']};
    color: {C['white']};
}}
QToolBar {{
    background: {C['panel']};
    border-bottom: 1px solid {C['border']};
    spacing: 4px;
}}
QStatusBar {{
    background: {C['panel']};
    color: #000;
    border-top: 1px solid {C['border']};
    font-size: 18px;
}}
QToolTip {{
    background-color: #ffffcc;
    color: #000;
    border: 1px solid {C['border']};
    padding: 2px 4px;
    font-family: 'MS Sans Serif','Tahoma','Arial';
    font-size: 11px;
}}
QPushButton {{
    background-color: {C['btn_bg']};
    color: #000;
    border: 1px solid {C['btn_bdr']};
    border-top-color: {C['border_lt']};
    border-left-color: {C['border_lt']};
    border-radius: 2px;
    padding: 3px 8px;
    font-family: 'MS Sans Serif','Tahoma','Arial';
    font-size: 15px;
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: {C['btn_hot']};
}}
QPushButton:pressed {{
    border-top-color: {C['btn_bdr']};
    border-left-color: {C['btn_bdr']};
    border-bottom-color: {C['border_lt']};
    border-right-color: {C['border_lt']};
    background-color: {C['btn_press']};
}}
QPushButton:disabled {{
    color: {C['grey']};
    background: {C['bg']};
}}
QLineEdit {{
    background: {C['lcd_bg']};
    color: #000;
    border: 2px inset {C['btn_bdr']};
    padding: 2px 4px;
    font-family: 'Courier New';
    selection-background-color: {C['blue']};
    selection-color: {C['white']};
}}
QLineEdit:focus {{
    border: 2px inset {C['green']};
}}
QTextEdit, QPlainTextEdit {{
    background: {C['lcd_bg']};
    color: #000;
    border: 2px inset {C['btn_bdr']};
    font-family: 'Courier New';
    font-size: 18px;
    selection-background-color: {C['blue']};
    selection-color: {C['white']};
}}
QLabel {{
    color: #000;
    background: transparent;
}}
QGroupBox {{
    color: #000;
    border: 2px groove {C['btn_bdr']};
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    color: #000;
    background: {C['panel']};
    padding: 0 4px;
}}
QCheckBox {{
    color: #000;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 2px inset {C['btn_bdr']};
    background: {C['white']};
}}
QCheckBox::indicator:checked {{
    background: {C['lcd_bg']};
}}
QTableWidget {{
    background: {C['lcd_bg']};
    color: #000;
    border: 2px inset {C['btn_bdr']};
    gridline-color: {C['btn_bdr']};
    selection-background-color: {C['blue']};
    selection-color: {C['white']};
    font-family: 'Courier New';
    font-size: 18px;
}}
QTableWidget::item:selected {{
    background: {C['blue']};
    color: {C['white']};
}}
QHeaderView::section {{
    background: {C['btn_bg']};
    color: #000;
    border: 1px outset {C['btn_bg']};
    padding: 3px 5px;
    font-weight: bold;
}}
QScrollBar:vertical {{
    background: {C['bg']};
    width: 16px;
    border: 1px solid {C['btn_bdr']};
}}
QScrollBar::handle:vertical {{
    background: {C['btn_bg']};
    border: 1px outset {C['btn_bg']};
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C['btn_hot']};
}}
QScrollBar:horizontal {{
    background: {C['bg']};
    height: 16px;
    border: 1px solid {C['btn_bdr']};
}}
QScrollBar::handle:horizontal {{
    background: {C['btn_bg']};
    border: 1px outset {C['btn_bg']};
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {C['btn_hot']};
}}
QComboBox {{
    background: {C['white']};
    color: #000;
    border: 2px inset {C['btn_bdr']};
    padding: 2px 4px;
}}
QComboBox::drop-down {{
    border: 1px outset {C['btn_bg']};
    background: {C['btn_bg']};
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background: {C['white']};
    color: #000;
    border: 1px solid {C['btn_bdr']};
    selection-background-color: {C['blue']};
    selection-color: {C['white']};
}}
QSplitter::handle {{
    background: {C['bg']};
    border: 1px outset {C['bg']};
}}
"""
