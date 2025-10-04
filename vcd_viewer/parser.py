"""
VCD Waveform Viewer - VCD File Parser
Parses standard VCD format files and populates WaveformData
"""

import re
from models import Signal, WaveformData


class VCDParser:
    """Parser for Value Change Dump (VCD) files"""

    def __init__(self):
        self.data = WaveformData()
        self.current_scope = []
        self.current_timestamp = 0

    def parse_file(self, filename):
        """Parse a VCD file and return WaveformData object"""
        self.data = WaveformData()
        self.current_scope = []
        self.current_timestamp = 0

        with open(filename, "r") as f:
            lines = f.readlines()

        self._parse_lines(lines)
        return self.data

    def _parse_lines(self, lines):
        """Parse all lines from VCD file"""
        in_header = True
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Header sections
            if line.startswith("$"):
                if line.startswith("$timescale"):
                    i = self._parse_timescale(lines, i)
                elif line.startswith("$scope"):
                    i = self._parse_scope(lines, i)
                elif line.startswith("$upscope"):
                    self._pop_scope()
                    i += 1
                elif line.startswith("$var"):
                    i = self._parse_var(lines, i)
                elif line.startswith("$enddefinitions"):
                    in_header = False
                    i += 1
                else:
                    # Skip other header commands
                    i = self._skip_to_end(lines, i)

            # Value change sections
            elif line.startswith("#"):
                i = self._parse_timestamp(lines, i)

            # Value changes
            elif not in_header:
                self._parse_value_change(line)
                i += 1
            else:
                i += 1

    def _parse_timescale(self, lines, index):
        """Parse $timescale directive"""
        line = lines[index].strip()

        # Extract timescale from current or next line
        match = re.search(r"(\d+\s*\w+)", line)
        if match:
            self.data.timescale = match.group(1).strip()
        elif index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            match = re.search(r"(\d+\s*\w+)", next_line)
            if match:
                self.data.timescale = match.group(1).strip()

        return self._skip_to_end(lines, index)

    def _parse_scope(self, lines, index):
        """Parse $scope directive"""
        line = lines[index].strip()
        parts = line.split()

        if len(parts) >= 3:
            scope_name = parts[2]
            self.current_scope.append(scope_name)

        return index + 1

    def _pop_scope(self):
        """Exit current scope"""
        if self.current_scope:
            self.current_scope.pop()

    def _parse_var(self, lines, index):
        """Parse $var directive"""
        line = lines[index].strip()
        # Format: $var <type> <width> <identifier> <name> $end
        parts = line.split()

        if len(parts) >= 5:
            var_type = parts[1]
            width = int(parts[2])
            identifier = parts[3]
            name = parts[4]

            scope = ".".join(self.current_scope)
            signal = Signal(identifier, name, width, scope)
            self.data.add_signal(signal)

        return self._skip_to_end(lines, index)

    def _skip_to_end(self, lines, index):
        """Skip to $end marker"""
        while index < len(lines):
            if "$end" in lines[index]:
                return index + 1
            index += 1
        return index

    def _parse_timestamp(self, lines, index):
        """Parse timestamp marker"""
        line = lines[index].strip()
        # Format: #<timestamp>
        timestamp_str = line[1:]  # Remove '#'

        try:
            self.current_timestamp = int(timestamp_str)
            self.data.update_max_timestamp(self.current_timestamp)
        except ValueError:
            pass

        return index + 1

    def _parse_value_change(self, line):
        """Parse a value change line"""
        line = line.strip()

        if not line:
            return

        # Binary value: <value><identifier>
        # Example: "0!" means signal ! changes to 0
        if line[0] in "01xzXZ":
            if len(line) > 1:
                value = line[0]
                identifier = line[1:]
                signal = self.data.get_signal_by_identifier(identifier)
                if signal:
                    signal.add_change(self.current_timestamp, value)

        # Bus value: b<binary_value> <identifier>
        # Example: "b1010 !" means signal ! changes to binary 1010
        elif line.startswith("b") or line.startswith("B"):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # Remove 'b' prefix
                identifier = parts[1]
                signal = self.data.get_signal_by_identifier(identifier)
                if signal:
                    signal.add_change(self.current_timestamp, value)

        # Real value: r<real_value> <identifier>
        elif line.startswith("r") or line.startswith("R"):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # Remove 'r' prefix
                identifier = parts[1]
                signal = self.data.get_signal_by_identifier(identifier)
                if signal:
                    signal.add_change(self.current_timestamp, value)
