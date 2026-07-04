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
test_paths.py — Tests for the resource_path() helper (paths.py).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

import pytest
from beboputer_v7.paths import resource_path


class TestResourcePath:
    def test_returns_string(self):
        assert isinstance(resource_path('BITMAPS'), str)

    def test_bitmaps_dir_exists_in_source(self):
        p = resource_path('BITMAPS')
        assert os.path.isdir(p), f"Expected BITMAPS dir at: {p}"

    def test_config_dir_exists_in_source(self):
        p = resource_path('Config')
        assert os.path.isdir(p), f"Expected Config dir at: {p}"

    def test_ini_file_exists(self):
        p = resource_path('Config', 'DIYCALC.INI')
        assert os.path.isfile(p), f"Expected DIYCALC.INI at: {p}"

    def test_path_is_absolute(self):
        p = resource_path('BITMAPS')
        assert os.path.isabs(p)

    def test_no_double_separators(self):
        p = resource_path('Config', 'DIYCALC.INI')
        # normpath should eliminate any redundant separators
        assert '//' not in p and '\\\\' not in p

    def test_useg0_bitmap_exists(self):
        p = resource_path('BITMAPS', 'USEG0.BMP')
        assert os.path.isfile(p), f"Expected USEG0.BMP at: {p}"

    def test_dseg0_bitmap_exists(self):
        p = resource_path('BITMAPS', 'DSEG0.BMP')
        assert os.path.isfile(p), f"Expected DSEG0.BMP at: {p}"

    def test_not_frozen_uses_project_root(self):
        """In source mode, sys.frozen should not be set."""
        assert not getattr(sys, 'frozen', False)
