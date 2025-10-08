"""
VCD Waveform Viewer - Waveform Canvas
Handles rendering of waveforms on a Tkinter canvas
"""

import tkinter as tk
import re
from math import log10


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

        # Mouse drag state for panning and interactions
        self.drag_start_x = None
        self.drag_start_y = None
        self.is_dragging = False
        self.dragged_object = (
            None  # What we're dragging: None, 'cursor', 'marker', or 'pan'
        )
        self.dragged_marker = None
        self.alt_pressed = False

        # Bind mouse events for panning and interactions
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # Keyboard events for Alt key
        self.canvas.bind("<KeyPress-Alt_L>", self._on_alt_press)
        self.canvas.bind("<KeyRelease-Alt_L>", self._on_alt_release)
        self.canvas.bind("<KeyPress-Alt_R>", self._on_alt_press)
        self.canvas.bind("<KeyRelease-Alt_R>", self._on_alt_release)

        # Make canvas focusable for keyboard events
        self.canvas.config(takefocus=True)

    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)

    def draw_waveforms(self):
        """Draw all visible waveforms"""
        self.canvas.delete("all")

        if not self.waveform_data or not self.waveform_data.signals:
            return

        # Get signals in display order (respects user reordering)
        if hasattr(self.waveform_data, "get_signals_in_display_order"):
            signals = self.waveform_data.get_signals_in_display_order()
        else:
            signals = self.waveform_data.get_all_signals()

        visible_signals = [s for s in signals if s.visible]

        if not visible_signals:
            # Draw message when no signals are selected
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="No signals selected\n\nSelect signals from the list on the left",
                fill=self.colors["text"],
                font=("Arial", 12),
                justify=tk.CENTER,
            )
            return

        # Calculate canvas size with bounds checking
        max_time = self.waveform_data.max_timestamp
        if max_time <= 0:
            return

        canvas_width = max(
            200, int(max_time * self.time_scale) + self.left_margin + 100
        )
        canvas_height = max(
            100, len(visible_signals) * (self.signal_height + self.signal_spacing) + 100
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

        # Draw cursor
        self._draw_cursor(canvas_height)

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

            # Time label with units
            time_label = self._format_time_with_units(t)
            self.canvas.create_text(
                x, 20, text=time_label, fill=self.colors["text"], font=("Courier", 8)
            )

            t += time_step

    def _calculate_time_step(self, max_time):
        """Calculate appropriate time step for grid based on zoom level"""
        if max_time <= 0:
            return 100

        # Calculate the visible time range based on canvas width and time scale
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1000

        # Calculate how much time is visible in the current viewport
        visible_time = (canvas_width - self.left_margin) / self.time_scale

        # Aim for 8-12 grid lines in the visible area
        raw_step = visible_time / 10

        # Handle very small time steps
        if raw_step < 1:
            # Find the nearest power of 10
            magnitude = 10 ** (int(abs(round(log10(raw_step)))) if raw_step > 0 else 0)
            nice_steps = [0.1, 0.2, 0.5, 1, 2, 5, 10]

            for step in nice_steps:
                test_step = step / magnitude if magnitude > 1 else step * magnitude
                if test_step >= raw_step:
                    return test_step
            return 1.0 / magnitude

        # For larger time steps, use the original logic
        magnitude = 10 ** int(len(str(int(raw_step))) - 1)
        nice_steps = [1, 2, 5, 10]

        for step in nice_steps:
            if step * magnitude >= raw_step:
                return step * magnitude

        return magnitude * 10

    def _format_time_with_units(self, time_value):
        """Format time value with appropriate units and remove trailing zeros"""
        # Parse the timescale from waveform_data
        timescale = self.waveform_data.timescale

        # Extract base unit and multiplier (e.g., "1ns" -> 1, "ns")
        match = re.match(r"(\d+)\s*(\w+)", timescale)
        if not match:
            return str(int(time_value))

        multiplier = int(match.group(1))
        base_unit = match.group(2)

        # Calculate actual time in base units
        actual_time = time_value * multiplier

        # Define unit conversions (in ascending order)
        units = {
            "fs": 1e-15,
            "ps": 1e-12,
            "ns": 1e-9,
            "us": 1e-6,
            "ms": 1e-3,
            "s": 1,
        }

        # Get the base unit value
        if base_unit not in units:
            return str(int(time_value))

        base_value = units[base_unit]
        time_in_seconds = actual_time * base_value

        # Check if user has selected a specific time base
        time_base = self.waveform_data.time_base

        if time_base != "auto" and time_base in units:
            # Use the user-selected time base
            best_unit = time_base
            best_value = time_in_seconds / units[time_base]
        else:
            # Auto-select the most appropriate unit
            best_unit = base_unit
            best_value = actual_time

            for unit, factor in sorted(units.items(), key=lambda x: x[1], reverse=True):
                converted = time_in_seconds / factor
                if converted >= 1.0:
                    best_unit = unit
                    best_value = converted
                    break

        # Determine precision based on zoom level
        if self.time_scale >= 100:
            precision = 4  # Very zoomed in
        elif self.time_scale >= 10:
            precision = 3  # Zoomed in
        elif self.time_scale >= 1:
            precision = 2  # Normal
        elif self.time_scale >= 0.1:
            precision = 1  # Zoomed out
        else:
            precision = 0  # Very zoomed out

        # Format the value
        if best_value == int(best_value) and precision == 0:
            formatted = f"{int(best_value)}{best_unit}"
        else:
            # Format with appropriate precision, then remove trailing zeros
            formatted = f"{best_value:.{precision}f}".rstrip("0").rstrip(".")
            formatted = f"{formatted}{best_unit}"

        return formatted

    def _format_time_precise(self, time_value):
        """Format time value with higher precision for cursor/marker measurements"""
        # Parse the timescale from waveform_data
        timescale = self.waveform_data.timescale

        # Extract base unit and multiplier (e.g., "1ns" -> 1, "ns")
        match = re.match(r"(\d+)\s*(\w+)", timescale)
        if not match:
            return str(int(time_value))

        multiplier = int(match.group(1))
        base_unit = match.group(2)

        # Calculate actual time in base units
        actual_time = time_value * multiplier

        # Define unit conversions (in ascending order)
        units = {
            "fs": 1e-15,
            "ps": 1e-12,
            "ns": 1e-9,
            "us": 1e-6,
            "ms": 1e-3,
            "s": 1,
        }

        # Get the base unit value
        if base_unit not in units:
            return str(int(time_value))

        base_value = units[base_unit]
        time_in_seconds = actual_time * base_value

        # Always prefer the smallest unit that keeps the value under 10000
        # This ensures measurements are always more granular than grid labels
        best_unit = base_unit
        best_value = actual_time

        for unit, factor in sorted(
            units.items(), key=lambda x: x[1]
        ):  # Sort ascending (smallest first)
            converted = time_in_seconds / factor
            if converted < 10000:  # Use this unit if value is reasonable
                best_unit = unit
                best_value = converted
                break

        # Determine precision based on magnitude
        if best_value >= 1000:
            precision = 1  # e.g., 1234.5
        elif best_value >= 100:
            precision = 2  # e.g., 123.45
        elif best_value >= 10:
            precision = 3  # e.g., 12.345
        elif best_value >= 1:
            precision = 4  # e.g., 1.2345
        else:
            precision = 5  # e.g., 0.12345

        # Format the value
        if best_value == int(best_value):
            formatted = f"{int(best_value)}{best_unit}"
        else:
            formatted = f"{best_value:.{precision}f}".rstrip("0").rstrip(".")
            formatted = f"{formatted}{best_unit}"

        return formatted

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
                        prev_x, x, y_high, y_low, prev_value, value, signal
                    )
                else:
                    # Bus signal - draw as multi-bit
                    self._draw_bus_transition(
                        prev_x, x, y_high, y_low, y_mid, prev_value, value, signal
                    )

            prev_x = x
            prev_value = value

        # Draw final value to end of canvas
        if prev_value is not None:
            end_x = self.left_margin + int(
                self.waveform_data.max_timestamp * self.time_scale
            )
            if signal.width == 1:
                self._draw_digital_value(
                    prev_x, end_x, y_high, y_low, prev_value, signal
                )
            else:
                self._draw_bus_value(
                    prev_x, end_x, y_high, y_low, y_mid, prev_value, signal
                )

    def _draw_digital_transition(self, x1, x2, y_high, y_low, old_val, new_val, signal):
        """Draw digital signal transition"""
        color = self._get_signal_color(old_val, signal)

        # Horizontal line at old value level
        y_old = y_low if old_val in ["0", "l", "L"] else y_high
        self.canvas.create_line(x1, y_old, x2, y_old, fill=color, width=2)

        # Vertical transition line
        y_new = y_low if new_val in ["0", "l", "L"] else y_high
        self.canvas.create_line(x2, y_old, x2, y_new, fill=color, width=2)

    def _draw_digital_value(self, x1, x2, y_high, y_low, value, signal):
        """Draw digital signal value"""
        color = self._get_signal_color(value, signal)
        y = y_low if value in ["0", "l", "L"] else y_high
        self.canvas.create_line(x1, y, x2, y, fill=color, width=2)

    def _draw_bus_transition(
        self, x1, x2, y_high, y_low, y_mid, old_val, new_val, signal
    ):
        """Draw bus signal transition"""
        color = signal.color  # Use signal's custom color for buses

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

    def _draw_bus_value(self, x1, x2, y_high, y_low, y_mid, value, signal):
        """Draw bus signal value"""
        color = signal.color  # Use signal's custom color for buses

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

    def _get_signal_color(self, value, signal):
        """Get color for signal value"""
        # For special values (x, z), use default colors
        if value in ["x", "X"]:
            return self.colors["signal_x"]
        elif value in ["z", "Z"]:
            return self.colors["signal_z"]

        # Otherwise use the signal's custom color
        return signal.color

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

            # Marker color - brighter if selected
            color = marker.color
            width = 3 if marker.selected else 2

            self.canvas.create_line(
                x, 0, x, height, fill=color, width=width, tags="marker"
            )

            if marker.label:
                self.canvas.create_text(
                    x + 5,
                    10,
                    text=marker.label,
                    anchor=tk.W,
                    fill=color,
                    font=("Courier", 10, "bold"),
                    tags="marker",
                )

            # Show timestamp
            time_label = self._format_time_precise(marker.timestamp)
            self.canvas.create_text(
                x - 5,
                height - 10,
                text=time_label,
                anchor=tk.E,
                fill=color,
                font=("Courier", 9, "bold"),
                tags="marker",
            )

    def _draw_cursor(self, height):
        """Draw the time cursor"""
        if not self.waveform_data.cursor or not self.waveform_data.cursor.visible:
            return

        cursor = self.waveform_data.cursor
        x = self.left_margin + int(cursor.timestamp * self.time_scale)

        # Draw cursor line
        self.canvas.create_line(
            x, 0, x, height, fill="yellow", width=2, dash=(4, 2), tags="cursor"
        )

        # Draw cursor time label
        time_label = self._format_time_precise(cursor.timestamp)
        self.canvas.create_rectangle(
            x - 40, 35, x + 40, 50, fill="#444444", outline="yellow", tags="cursor"
        )
        self.canvas.create_text(
            x,
            42,
            text=time_label,
            fill="yellow",
            font=("Courier", 9, "bold"),
            tags="cursor",
        )

        # Show delta if markers are selected
        selected_markers = self.waveform_data.get_selected_markers()
        if len(selected_markers) > 0:
            marker_time = selected_markers[0].timestamp
            delta = abs(cursor.timestamp - marker_time)
            delta_label = f"Δ {self._format_time_precise(delta)}"

            self.canvas.create_rectangle(
                x - 50, 55, x + 50, 70, fill="#444444", outline="yellow", tags="cursor"
            )
            self.canvas.create_text(
                x,
                62,
                text=delta_label,
                fill="#ffff00",
                font=("Courier", 8),
                tags="cursor",
            )

    def set_time_scale(self, scale):
        """Set the time scale (zoom)"""
        self.time_scale = scale
        self.draw_waveforms()

    def _on_mouse_down(self, event):
        """Handle mouse button press for panning or dragging"""
        self.canvas.focus_set()  # Get keyboard focus

        # Convert canvas coordinates to time
        canvas_x = self.canvas.canvasx(event.x)

        # Check if clicking near cursor (within 10 pixels)
        if self.waveform_data.cursor and self.waveform_data.cursor.visible:
            cursor_x = self._time_to_x(self.waveform_data.cursor.timestamp)
            if abs(canvas_x - cursor_x) < 10:
                self.dragged_object = "cursor"
                self.waveform_data.cursor.dragging = True
                self.canvas.config(cursor="sb_h_double_arrow")
                return

        # Check if clicking near a marker (within 10 pixels)
        for marker in self.waveform_data.markers:
            marker_x = self._time_to_x(marker.timestamp)
            if abs(canvas_x - marker_x) < 10:
                self.dragged_object = "marker"
                self.dragged_marker = marker
                marker.dragging = True
                # Toggle selection
                marker.selected = not marker.selected
                self.canvas.config(cursor="sb_h_double_arrow")
                self.draw_waveforms()
                return

        # Otherwise, start panning
        self.dragged_object = "pan"
        self.canvas.config(cursor="fleur")
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True

    def _on_mouse_drag(self, event):
        """Handle mouse drag for panning or dragging cursor/markers"""
        canvas_x = self.canvas.canvasx(event.x)

        # Dragging cursor
        if self.dragged_object == "cursor":
            time = self._x_to_time(canvas_x)
            time = max(0, min(self.waveform_data.max_timestamp, time))

            # Snap to edges unless Alt is pressed
            if not self.alt_pressed:
                time = self._snap_to_edge(time)

            self.waveform_data.cursor.timestamp = time
            self.draw_waveforms()
            return

        # Dragging marker
        if self.dragged_object == "marker" and self.dragged_marker:
            time = self._x_to_time(canvas_x)
            time = max(0, min(self.waveform_data.max_timestamp, time))

            # Snap to edges unless Alt is pressed
            if not self.alt_pressed:
                time = self._snap_to_edge(time)

            self.dragged_marker.timestamp = time
            self.waveform_data.markers.sort(key=lambda m: m.timestamp)
            self.draw_waveforms()
            return

        # Panning
        if self.dragged_object == "pan":
            if (
                not self.is_dragging
                or self.drag_start_x is None
                or self.drag_start_y is None
            ):
                return

            # Calculate delta
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # Get current view
            x_view = self.canvas.xview()
            y_view = self.canvas.yview()

            # Calculate scroll amounts (inverted for natural dragging)
            scroll_region = self.canvas.cget("scrollregion")
            if scroll_region:
                scroll_coords = [float(x) for x in scroll_region.split()]
                if len(scroll_coords) == 4:
                    total_width = scroll_coords[2] - scroll_coords[0]
                    total_height = scroll_coords[3] - scroll_coords[1]
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()

                    # Only scroll if content is larger than viewport
                    if total_width > canvas_width and canvas_width > 0:
                        x_scroll = -dx / total_width
                        new_x = max(0.0, min(1.0, x_view[0] + x_scroll))
                        self.canvas.xview_moveto(new_x)

                    if total_height > canvas_height and canvas_height > 0:
                        y_scroll = -dy / total_height
                        new_y = max(0.0, min(1.0, y_view[0] + y_scroll))
                        self.canvas.yview_moveto(new_y)

            # Update start position for next drag event
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def _on_mouse_up(self, event):
        """Handle mouse button release"""
        self.canvas.config(cursor="")  # Reset cursor

        if self.waveform_data.cursor:
            self.waveform_data.cursor.dragging = False

        if self.dragged_marker:
            self.dragged_marker.dragging = False
            self.dragged_marker = None

        self.drag_start_x = None
        self.drag_start_y = None
        self.is_dragging = False
        self.dragged_object = None

    def _on_double_click(self, event):
        """Handle double-click to place marker"""
        canvas_x = self.canvas.canvasx(event.x)
        time = self._x_to_time(canvas_x)
        time = max(0, min(self.waveform_data.max_timestamp, time))

        # Snap to edge
        if not self.alt_pressed:
            time = self._snap_to_edge(time)

        # Add marker
        from models import Marker

        marker = Marker(time, f"M{len(self.waveform_data.markers) + 1}", "cyan")
        self.waveform_data.add_marker(marker)
        self.draw_waveforms()

    def _on_alt_press(self, event):
        """Handle Alt key press"""
        self.alt_pressed = True

    def _on_alt_release(self, event):
        """Handle Alt key release"""
        self.alt_pressed = False

    def _time_to_x(self, time):
        """Convert time value to canvas x coordinate"""
        return self.left_margin + int(time * self.time_scale)

    def _x_to_time(self, x):
        """Convert canvas x coordinate to time value"""
        return (x - self.left_margin) / self.time_scale

    def _snap_to_edge(self, time, threshold=None):
        """Snap time to nearest signal edge"""
        if threshold is None:
            # Snap threshold is 5 pixels in time units
            threshold = 5.0 / self.time_scale

        edges = self.waveform_data.get_all_edges()
        if not edges:
            return time

        # Find closest edge
        closest_edge = min(edges, key=lambda e: abs(e - time))

        # Snap if within threshold
        if abs(closest_edge - time) <= threshold:
            return closest_edge

        return time
