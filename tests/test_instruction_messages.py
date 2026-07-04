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
test_instruction_messages.py — Tests for InstructionMessages (instruction_messages.py).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

import pytest
from beboputer_v7.instruction_messages import InstructionMessages, _OPCODE_MSG
from beboputer_v7.cpu import CPU
from beboputer_v7.constants import FLAG_C, FLAG_Z, FLAG_N, FLAG_V, FLAG_I


def make_cpu_after(*program_bytes, base=0x4000):
    """Return CPU after executing the first instruction of program_bytes."""
    cpu = CPU()
    cpu.reset()
    for i, b in enumerate(program_bytes):
        cpu.ram[base + i] = b
    cpu.pc = base
    cpu.step()
    return cpu


class TestINILoading:
    def test_loads_messages(self):
        msgs = InstructionMessages()
        assert len(msgs._messages) > 0, "No messages loaded from DIYCALC.INI"

    def test_loads_over_200_messages(self):
        msgs = InstructionMessages()
        assert len(msgs._messages) >= 200

    def test_halt_message_present(self):
        msgs = InstructionMessages()
        # Message 33 = HALT description
        assert 33 in msgs._messages
        assert msgs._messages[33]  # non-empty

    def test_missing_ini_returns_empty(self):
        msgs = InstructionMessages(ini_path='nonexistent/path/file.ini')
        assert msgs._messages == {}


class TestDescribe:
    def setup_method(self):
        self.msgs = InstructionMessages()

    def test_describe_returns_string(self):
        cpu = make_cpu_after(0x01, 0x05)   # LDA $05
        result = self.msgs.describe(cpu)
        assert isinstance(result, str)

    def test_describe_contains_register_values(self):
        cpu = make_cpu_after(0x01, 0x42)   # LDA $42
        result = self.msgs.describe(cpu)
        assert 'ACC' in result or '$42' in result or '66' in result

    def test_describe_halt(self):
        cpu = make_cpu_after(0x3C)         # HALT
        result = self.msgs.describe(cpu)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_describe_unknown_opcode(self):
        cpu = CPU()
        cpu.reset()
        cpu.instr = 0xFF                   # not in opcode map
        result = self.msgs.describe(cpu)
        assert isinstance(result, str)


class TestFormatTokens:
    def setup_method(self):
        self.msgs = InstructionMessages()

    def _make_cpu(self):
        cpu = CPU()
        cpu.reset()
        return cpu

    def test_percent_d_substituted(self):
        cpu = self._make_cpu()
        cpu.acc = 42
        result = self.msgs._fmt("%d", cpu, 0x01)
        assert result == "42"

    def test_percent_a_substituted(self):
        cpu = self._make_cpu()
        cpu.pc = 0x1234
        result = self.msgs._fmt("%a", cpu, 0x01)
        assert result == "$1234"

    def test_percent_t_substituted(self):
        cpu = self._make_cpu()
        result = self.msgs._fmt("%t", cpu, 0x3C)
        assert result == "$3C"

    def test_percent_x_substituted(self):
        cpu = self._make_cpu()
        cpu.ix = 0xABCD
        result = self.msgs._fmt("%x", cpu, 0x00)
        assert result == "$ABCD"

    def test_flag_tokens(self):
        cpu = self._make_cpu()
        cpu.flags = FLAG_C | FLAG_Z
        cpu.flags_touched = 0xFF
        result = self.msgs._fmt("C=%c Z=%z N=%n", cpu, 0x00)
        assert "C=1" in result
        assert "Z=1" in result
        assert "N=0" in result


class TestOpcodeCoverage:
    def test_all_opcodes_have_mapping(self):
        """Every opcode in _OPCODE_MSG should map to a valid message ID."""
        msgs = InstructionMessages()
        missing = []
        for opcode, msg_id in _OPCODE_MSG.items():
            if msg_id not in msgs._messages:
                missing.append((opcode, msg_id))
        assert missing == [], f"Missing messages for opcodes: {missing}"

    def test_opcode_map_covers_halt(self):
        assert 0x3C in _OPCODE_MSG

    def test_opcode_map_covers_all_lda_modes(self):
        for op in [0x01, 0x02, 0x03, 0x04, 0x05]:
            assert op in _OPCODE_MSG, f"LDA opcode ${op:02X} not in map"

    def test_opcode_map_covers_jumps(self):
        for op in [0x45, 0x48, 0x49, 0x4C, 0x4D, 0x4A, 0x4B]:
            assert op in _OPCODE_MSG, f"Jump opcode ${op:02X} not in map"
