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
        self.color = "#00ff00"  # Default signal color (green)

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

    def get_edges(self):
        """Get list of all edge timestamps"""
        return [ts for ts, _ in self.changes]


class Marker:
    """Represents a time marker in the waveform viewer"""

    def __init__(self, timestamp, label="", color="red"):
        self.timestamp = timestamp
        self.label = label
        self.color = color
        self.selected = False
        self.dragging = False


class Cursor:
    """Represents the draggable time cursor"""

    def __init__(self, timestamp=0):
        self.timestamp = timestamp
        self.visible = True
        self.dragging = False


class WaveformData:
    """Container for all waveform data from VCD file"""

    def __init__(self):
        self.timescale = "1ns"  # Time unit
        self.signals = {}  # Dict: identifier -> Signal
        self.markers = []  # List of Markers
        self.max_timestamp = 0  # Maximum time value
        self.scope_hierarchy = {}  # Hierarchical organization
        self.cursor = Cursor(0)  # Initialize cursor
        self.time_base = (
            "auto"  # Display time base: "auto", "fs", "ps", "ns", "us", "ms", "s"
        )
        self.display_order = []  # List of signal names in display order

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

    def get_signal_by_name(self, full_name):
        """Retrieve signal by its full name"""
        for signal in self.signals.values():
            if signal.get_full_name() == full_name:
                return signal
        return None

    def get_all_signals(self):
        """Get list of all signals sorted by scope and name"""
        return sorted(self.signals.values(), key=lambda s: (s.scope, s.name))

    def get_signals_in_display_order(self):
        """Get signals in the user-specified display order"""
        if not self.display_order:
            return self.get_all_signals()

        # Build a dict for quick lookup
        signal_dict = {s.get_full_name(): s for s in self.signals.values()}

        # Return signals in display order
        ordered_signals = []
        for name in self.display_order:
            if name in signal_dict:
                ordered_signals.append(signal_dict[name])

        # Add any signals not in display_order at the end
        ordered_names = set(self.display_order)
        for signal in self.get_all_signals():
            if signal.get_full_name() not in ordered_names:
                ordered_signals.append(signal)

        return ordered_signals

    def add_marker(self, marker):
        """Add a time marker"""
        self.markers.append(marker)
        self.markers.sort(key=lambda m: m.timestamp)

    def remove_marker(self, marker):
        """Remove a time marker"""
        if marker in self.markers:
            self.markers.remove(marker)

    def get_selected_markers(self):
        """Get list of selected markers"""
        return [m for m in self.markers if m.selected]

    def update_max_timestamp(self, timestamp):
        """Update the maximum timestamp seen"""
        if timestamp > self.max_timestamp:
            self.max_timestamp = timestamp

    def get_all_edges(self):
        """Get all edge timestamps from visible signals"""
        edges = set()
        for signal in self.get_all_signals():
            if signal.visible:
                edges.update(signal.get_edges())
        return sorted(edges)
