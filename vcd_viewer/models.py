"""
VCD Waveform Viewer - Data Models
Defines the data structures for signals, markers, and waveform data
"""


class Signal:
    """Represents a signal in the VCD file"""

    def __init__(self, identifier, name, width=1, scope=""):
        self.identifier = identifier  # Short VCD identifier (e.g., "!")
        self.name = name  # Full signal name
        self.width = width  # Bit width
        self.scope = scope  # Hierarchical scope
        self.changes = []  # List of (timestamp, value) tuples
        self.visible = True  # Display flag

    def add_change(self, timestamp, value):
        """Add a value change at given timestamp"""
        self.changes.append((timestamp, value))

    def get_value_at(self, timestamp):
        """Get signal value at specific timestamp"""
        if not self.changes:
            return None

        # Find the most recent change before or at timestamp
        value = None
        for ts, val in self.changes:
            if ts > timestamp:
                break
            value = val
        return value

    def get_full_name(self):
        """Get fully qualified signal name"""
        if self.scope:
            return f"{self.scope}.{self.name}"
        return self.name


class Marker:
    """Represents a time marker in the waveform viewer"""

    def __init__(self, timestamp, label="", color="red"):
        self.timestamp = timestamp
        self.label = label
        self.color = color


class WaveformData:
    """Container for all waveform data from VCD file"""

    def __init__(self):
        self.timescale = "1ns"  # Time unit
        self.signals = {}  # Dict: identifier -> Signal
        self.markers = []  # List of Markers
        self.max_timestamp = 0  # Maximum time value
        self.scope_hierarchy = {}  # Hierarchical organization

    def add_signal(self, signal):
        """Add a signal to the data model"""
        self.signals[signal.identifier] = signal

        # Update scope hierarchy
        if signal.scope:
            if signal.scope not in self.scope_hierarchy:
                self.scope_hierarchy[signal.scope] = []
            self.scope_hierarchy[signal.scope].append(signal)

    def get_signal_by_identifier(self, identifier):
        """Retrieve signal by its VCD identifier"""
        return self.signals.get(identifier)

    def get_all_signals(self):
        """Get list of all signals sorted by scope and name"""
        return sorted(self.signals.values(), key=lambda s: (s.scope, s.name))

    def add_marker(self, marker):
        """Add a time marker"""
        self.markers.append(marker)
        self.markers.sort(key=lambda m: m.timestamp)

    def update_max_timestamp(self, timestamp):
        """Update the maximum timestamp seen"""
        if timestamp > self.max_timestamp:
            self.max_timestamp = timestamp
