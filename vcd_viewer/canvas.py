"""
VCD Waveform Viewer - Waveform Canvas
Handles rendering of waveforms on a Tkinter canvas
"""

import tkinter as tk


class WaveformCanvas:
    """Canvas widget for displaying waveforms"""

    def __init__(self, parent, waveform_data):
        self.waveform_data = waveform_data

        # Create scrollable canvas
        self.frame = tk.Frame(parent)

        # Horizontal scrollbar
        self.h_scrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Vertical scrollbar
        self.v_scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        self.canvas = tk.Canvas(
            self.frame,
            bg="black",
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        # Display parameters
        self.time_scale = 1.0  # Pixels per time unit
        self.signal_height = 40
        self.signal_spacing = 10
        self.left_margin = 200  # Space for signal names

        # Colors
        self.colors = {
            "background": "#1e1e1e",
            "grid": "#3e3e3e",
            "signal_high": "#00ff00",
            "signal_low": "#008800",
            "signal_x": "#ff0000",
            "signal_z": "#0000ff",
            "text": "#ffffff",
            "label_bg": "#2e2e2e",
        }

        self.canvas.config(bg=self.colors["background"])

    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)

    def draw_waveforms(self):
        """Draw all visible waveforms"""
        self.canvas.delete("all")

        if not self.waveform_data or not self.waveform_data.signals:
            return

        signals = self.waveform_data.get_all_signals()
        visible_signals = [s for s in signals if s.visible]

        if not visible_signals:
            return

        # Calculate canvas size
        max_time = self.waveform_data.max_timestamp
        canvas_width = int(max_time * self.time_scale) + self.left_margin + 100
        canvas_height = (
            len(visible_signals) * (self.signal_height + self.signal_spacing) + 100
        )

        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        # Draw time grid
        self._draw_time_grid(max_time, canvas_width, canvas_height)

        # Draw each signal
        y_offset = 50
        for signal in visible_signals:
            self._draw_signal(signal, y_offset)
            y_offset += self.signal_height + self.signal_spacing

        # Draw markers
        self._draw_markers(canvas_height)

    def _draw_time_grid(self, max_time, width, height):
        """Draw time grid and axis"""
        # Determine appropriate time step for grid
        time_step = self._calculate_time_step(max_time)

        # Draw vertical grid lines
        t = 0
        while t <= max_time:
            x = self.left_margin + int(t * self.time_scale)

            # Grid line
            self.canvas.create_line(
                x, 0, x, height, fill=self.colors["grid"], dash=(2, 4)
            )

            # Time label
            self.canvas.create_text(
                x, 20, text=str(t), fill=self.colors["text"], font=("Courier", 8)
            )

            t += time_step

    def _calculate_time_step(self, max_time):
        """Calculate appropriate time step for grid"""
        if max_time <= 0:
            return 100

        # Aim for ~10 grid lines
        raw_step = max_time / 10

        # Round to nice number
        magnitude = 10 ** int(len(str(int(raw_step))) - 1)
        nice_steps = [1, 2, 5, 10]

        for step in nice_steps:
            if step * magnitude >= raw_step:
                return step * magnitude

        return magnitude * 10

    def _draw_signal(self, signal, y_offset):
        """Draw a single signal waveform"""
        # Draw signal name background
        self.canvas.create_rectangle(
            0,
            y_offset - 5,
            self.left_margin - 5,
            y_offset + self.signal_height - 5,
            fill=self.colors["label_bg"],
            outline=self.colors["grid"],
        )

        # Draw signal name
        self.canvas.create_text(
            10,
            y_offset + self.signal_height // 2,
            text=signal.get_full_name(),
            anchor=tk.W,
            fill=self.colors["text"],
            font=("Courier", 10),
        )

        # Draw waveform
        if not signal.changes:
            return

        y_high = y_offset
        y_low = y_offset + self.signal_height - 10
        y_mid = y_offset + self.signal_height // 2

        prev_x = self.left_margin
        prev_value = None

        for timestamp, value in signal.changes:
            x = self.left_margin + int(timestamp * self.time_scale)

            # Draw transition
            if prev_value is not None:
                if signal.width == 1:
                    # Binary signal - draw as digital waveform
                    self._draw_digital_transition(
                        prev_x, x, y_high, y_low, prev_value, value
                    )
                else:
                    # Bus signal - draw as multi-bit
                    self._draw_bus_transition(
                        prev_x, x, y_high, y_low, y_mid, prev_value, value
                    )

            prev_x = x
            prev_value = value

        # Draw final value to end of canvas
        if prev_value is not None:
            end_x = self.left_margin + int(
                self.waveform_data.max_timestamp * self.time_scale
            )
            if signal.width == 1:
                self._draw_digital_value(prev_x, end_x, y_high, y_low, prev_value)
            else:
                self._draw_bus_value(prev_x, end_x, y_high, y_low, y_mid, prev_value)

    def _draw_digital_transition(self, x1, x2, y_high, y_low, old_val, new_val):
        """Draw digital signal transition"""
        color = self._get_signal_color(old_val)

        # Horizontal line at old value level
        y_old = y_low if old_val in ["0", "l", "L"] else y_high
        self.canvas.create_line(x1, y_old, x2, y_old, fill=color, width=2)

        # Vertical transition line
        y_new = y_low if new_val in ["0", "l", "L"] else y_high
        self.canvas.create_line(x2, y_old, x2, y_new, fill=color, width=2)

    def _draw_digital_value(self, x1, x2, y_high, y_low, value):
        """Draw digital signal value"""
        color = self._get_signal_color(value)
        y = y_low if value in ["0", "l", "L"] else y_high
        self.canvas.create_line(x1, y, x2, y, fill=color, width=2)

    def _draw_bus_transition(self, x1, x2, y_high, y_low, y_mid, old_val, new_val):
        """Draw bus signal transition"""
        color = self._get_signal_color(new_val)

        # Draw old value
        self.canvas.create_line(x1, y_high, x2 - 5, y_high, fill=color, width=2)
        self.canvas.create_line(x1, y_low, x2 - 5, y_low, fill=color, width=2)

        # Draw transition (X shape)
        self.canvas.create_line(x2 - 5, y_high, x2 + 5, y_low, fill=color, width=2)
        self.canvas.create_line(x2 - 5, y_low, x2 + 5, y_high, fill=color, width=2)

        # Draw value label
        if x2 - x1 > 40:
            self.canvas.create_text(
                (x1 + x2) // 2,
                y_mid,
                text=self._format_bus_value(old_val),
                fill=self.colors["text"],
                font=("Courier", 8),
            )

    def _draw_bus_value(self, x1, x2, y_high, y_low, y_mid, value):
        """Draw bus signal value"""
        color = self._get_signal_color(value)

        self.canvas.create_line(x1, y_high, x2, y_high, fill=color, width=2)
        self.canvas.create_line(x1, y_low, x2, y_low, fill=color, width=2)

        if x2 - x1 > 40:
            self.canvas.create_text(
                (x1 + x2) // 2,
                y_mid,
                text=self._format_bus_value(value),
                fill=self.colors["text"],
                font=("Courier", 8),
            )

    def _get_signal_color(self, value):
        """Get color for signal value"""
        if value in ["1", "h", "H"]:
            return self.colors["signal_high"]
        elif value in ["0", "l", "L"]:
            return self.colors["signal_low"]
        elif value in ["x", "X"]:
            return self.colors["signal_x"]
        elif value in ["z", "Z"]:
            return self.colors["signal_z"]
        return self.colors["signal_high"]

    def _format_bus_value(self, value):
        """Format bus value for display"""
        if not value or value in ["x", "X", "z", "Z"]:
            return value.upper()

        # Convert binary to hex if long enough
        if len(value) > 4:
            try:
                hex_val = hex(int(value, 2))[2:].upper()
                return f"0x{hex_val}"
            except ValueError:
                return value

        return value

    def _draw_markers(self, height):
        """Draw time markers"""
        for marker in self.waveform_data.markers:
            x = self.left_margin + int(marker.timestamp * self.time_scale)

            self.canvas.create_line(x, 0, x, height, fill=marker.color, width=2)

            if marker.label:
                self.canvas.create_text(
                    x + 5,
                    10,
                    text=marker.label,
                    anchor=tk.W,
                    fill=marker.color,
                    font=("Courier", 10, "bold"),
                )

    def set_time_scale(self, scale):
        """Set the time scale (zoom)"""
        self.time_scale = scale
        self.draw_waveforms()
