"""
VCD Waveform Viewer - Main Viewer Window
Main application window with menu and canvas
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from parser import VCDParser
from canvas import WaveformCanvas
from models import WaveformData


class WaveformViewer:
    """Main application window"""

    def __init__(self, root):
        self.root = root
        self.root.title("VCD Waveform Viewer")
        self.root.geometry("1200x700")

        self.waveform_data = WaveformData()
        self.parser = VCDParser()
        self.canvas = None
        self.signal_listbox = None
        self.search_var = None

        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()

    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Open VCD...", command=self.open_file, accelerator="Ctrl+O"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Zoom In", command=self.zoom_in, accelerator="Ctrl++"
        )
        view_menu.add_command(
            label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-"
        )
        view_menu.add_command(
            label="Zoom Fit", command=self.zoom_fit, accelerator="Ctrl+0"
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Refresh", command=self.refresh_display, accelerator="F5"
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.zoom_fit())
        self.root.bind("<F5>", lambda e: self.refresh_display())
        self.root.bind("<c>", lambda e: self.toggle_cursor())
        self.root.bind("<Delete>", lambda e: self.clear_markers())

    def _create_toolbar(self):
        """Create toolbar with buttons"""
        toolbar = tk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Open button
        tk.Button(
            toolbar, text="Open VCD", command=self.open_file, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)  # Spacer

        # Zoom buttons
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in, padx=10, pady=5).pack(
            side=tk.LEFT, padx=2, pady=2
        )

        tk.Button(
            toolbar, text="Zoom Out", command=self.zoom_out, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Button(
            toolbar, text="Zoom Fit", command=self.zoom_fit, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)  # Spacer

        # Refresh button
        tk.Button(
            toolbar, text="Refresh", command=self.refresh_display, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)  # Spacer

        # Cursor and marker controls
        tk.Button(
            toolbar, text="Toggle Cursor", command=self.toggle_cursor, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Button(
            toolbar, text="Clear Markers", command=self.clear_markers, padx=10, pady=5
        ).pack(side=tk.LEFT, padx=2, pady=2)

        # Delta display
        self.delta_label = tk.Label(
            toolbar, text="", fg="yellow", font=("Courier", 10, "bold")
        )
        self.delta_label.pack(side=tk.RIGHT, padx=10)

    def _create_main_area(self):
        """Create main display area with canvas and signal list"""
        # Create main paned window for split view
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Signal list
        left_frame = tk.Frame(main_paned, width=250)
        main_paned.add(left_frame)

        # Signal list label
        tk.Label(left_frame, text="Signals", font=("Arial", 10, "bold")).pack(pady=5)

        # Search box
        search_frame = tk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        tk.Entry(search_frame, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )

        # Listbox with scrollbar
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.signal_listbox = tk.Listbox(
            list_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set
        )
        self.signal_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.signal_listbox.yview)

        self.signal_listbox.bind("<<ListboxSelect>>", self._on_signal_select)

        # Buttons for selection
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Select All", command=self._select_all_signals).pack(
            side=tk.LEFT, padx=2
        )
        tk.Button(btn_frame, text="Clear All", command=self._clear_all_signals).pack(
            side=tk.LEFT, padx=2
        )

        # Right panel - Canvas
        right_frame = tk.Frame(main_paned)
        main_paned.add(right_frame)

        # Create canvas
        self.canvas = WaveformCanvas(right_frame, self.waveform_data)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = tk.Label(
            self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_file(self):
        """Open VCD file dialog and load file"""
        filename = filedialog.askopenfilename(
            title="Open VCD File",
            filetypes=[("VCD files", "*.vcd"), ("All files", "*.*")],
        )

        if filename:
            self.load_vcd_file(filename)

    def load_vcd_file(self, filename):
        """Load and parse VCD file"""
        try:
            self.status_bar.config(text=f"Loading {filename}...")
            self.root.update()

            # Parse the file
            self.waveform_data = self.parser.parse_file(filename)

            # Update canvas with new data
            self.canvas.waveform_data = self.waveform_data

            # Calculate initial zoom to fit
            self._calculate_fit_zoom()

            # Draw waveforms
            self.canvas.draw_waveforms()

            # Update status
            signal_count = len(self.waveform_data.signals)
            max_time = self.waveform_data.max_timestamp
            self.status_bar.config(
                text=f"Loaded: {filename} | Signals: {signal_count} | "
                f"Time: 0 to {max_time} {self.waveform_data.timescale}"
            )

            messagebox.showinfo(
                "Success",
                f"Successfully loaded VCD file!\n\n"
                f"Signals: {signal_count}\n"
                f"Max Time: {max_time} {self.waveform_data.timescale}",
            )

            # Populate signal listbox
            self._populate_signal_list()

            # Initialize cursor
            from models import Cursor

            self.waveform_data.cursor = Cursor(0)

        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {filename}")
            self.status_bar.config(text="Error: File not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load VCD file:\n{str(e)}")
            self.status_bar.config(text=f"Error: {str(e)}")

    def _calculate_fit_zoom(self):
        """Calculate zoom level to fit all waveforms"""
        if self.waveform_data.max_timestamp > 0:
            # Get canvas width (minus margins)
            canvas_width = self.canvas.canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 1000  # Default if not yet rendered

            available_width = canvas_width - self.canvas.left_margin - 100
            self.canvas.time_scale = available_width / self.waveform_data.max_timestamp
        else:
            self.canvas.time_scale = 1.0

    def zoom_in(self):
        """Zoom in (increase time scale)"""
        if self.canvas and self.waveform_data.max_timestamp > 0:
            self.canvas.time_scale *= 1.5
            self.canvas.draw_waveforms()
            self.status_bar.config(text=f"Zoom: {self.canvas.time_scale:.6f}x")

    def zoom_out(self):
        """Zoom out (decrease time scale)"""
        if self.canvas and self.waveform_data.max_timestamp > 0:
            new_scale = self.canvas.time_scale / 1.5

            # Calculate minimum zoom to keep at least 50 pixels for entire timeline
            # This allows viewing the entire waveform in a reasonable window
            min_scale = 50.0 / self.waveform_data.max_timestamp

            # Apply the new scale if it's above the minimum
            if new_scale >= min_scale:
                self.canvas.time_scale = new_scale
                self.canvas.draw_waveforms()
                self.status_bar.config(text=f"Zoom: {self.canvas.time_scale:.6f}x")
            else:
                # Set to minimum and show message
                self.canvas.time_scale = min_scale
                self.canvas.draw_waveforms()
                self.status_bar.config(
                    text=f"Minimum zoom reached ({self.canvas.time_scale:.6f}x)"
                )

    def zoom_fit(self):
        """Zoom to fit all waveforms"""
        if self.canvas:
            self._calculate_fit_zoom()
            self.canvas.draw_waveforms()
            self.status_bar.config(text=f"Zoom: Fit")

    def refresh_display(self):
        """Refresh the waveform display"""
        if self.canvas:
            self.canvas.draw_waveforms()
            self.status_bar.config(text="Display refreshed")

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About VCD Waveform Viewer",
            "VCD Waveform Viewer v1.0\n\n"
            "A Python/Tkinter application for viewing\n"
            "Value Change Dump (VCD) waveform files.\n\n"
            "Features:\n"
            "• VCD file parsing\n"
            "• Digital and bus signal display\n"
            "• Zoom controls\n"
            "• Time grid\n"
            "• Signal selection\n"
            "• Pan with mouse drag\n",
        )

    def _populate_signal_list(self):
        """Populate the signal listbox with all signals"""
        self.signal_listbox.delete(0, tk.END)

        signals = self.waveform_data.get_all_signals()
        for i, signal in enumerate(signals):
            self.signal_listbox.insert(tk.END, signal.get_full_name())
            # Select all by default
            self.signal_listbox.select_set(i)

    def _on_signal_select(self, event):
        """Handle signal selection changes"""
        if not self.waveform_data:
            return

        # Get selected indices
        selected_indices = self.signal_listbox.curselection()
        signals = self.waveform_data.get_all_signals()

        # Update visibility
        for i, signal in enumerate(signals):
            signal.visible = i in selected_indices

        # Redraw
        self.canvas.draw_waveforms()

    def _select_all_signals(self):
        """Select all signals in the listbox"""
        self.signal_listbox.select_set(0, tk.END)
        self._on_signal_select(None)

    def _clear_all_signals(self):
        """Clear all signal selections"""
        self.signal_listbox.select_clear(0, tk.END)
        self._on_signal_select(None)

    def _on_search(self, *args):
        """Filter signals based on search text"""
        if not self.waveform_data:
            return

        search_text = self.search_var.get().lower()

        # Save currently selected signals before clearing listbox
        selected_signals = set()
        signals = self.waveform_data.get_all_signals()
        for i in self.signal_listbox.curselection():
            if i < len(signals):
                selected_signals.add(signals[i].get_full_name())

        self.signal_listbox.delete(0, tk.END)

        # Re-populate with filtered signals and restore selections
        for signal in signals:
            if search_text in signal.get_full_name().lower():
                idx = self.signal_listbox.size()
                self.signal_listbox.insert(tk.END, signal.get_full_name())
                # Re-select if it was previously selected
                if signal.get_full_name() in selected_signals:
                    self.signal_listbox.select_set(idx)

    def toggle_cursor(self):
        """Toggle cursor visibility"""
        if self.waveform_data.cursor:
            self.waveform_data.cursor.visible = not self.waveform_data.cursor.visible
            self.canvas.draw_waveforms()
            status = "visible" if self.waveform_data.cursor.visible else "hidden"
            self.status_bar.config(text=f"Cursor {status}")

    def clear_markers(self):
        """Clear all markers"""
        self.waveform_data.markers.clear()
        self.canvas.draw_waveforms()
        self.status_bar.config(text="All markers cleared")
        self.delta_label.config(text="")

    def update_delta_display(self):
        """Update the delta display between selected markers"""
        selected = self.waveform_data.get_selected_markers()
        if len(selected) >= 2:
            delta = abs(selected[1].timestamp - selected[0].timestamp)
            # Format delta with units
            delta_text = self.canvas._format_time_with_units(delta)
            self.delta_label.config(text=f"Δ: {delta_text}")
        else:
            self.delta_label.config(text="")

        search_text = self.search_var.get().lower()
        self.signal_listbox.delete(0, tk.END)

        signals = self.waveform_data.get_all_signals()
        for signal in signals:
            if search_text in signal.get_full_name().lower():
                self.signal_listbox.insert(tk.END, signal.get_full_name())
