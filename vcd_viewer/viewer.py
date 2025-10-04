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

    def _create_main_area(self):
        """Create main display area with canvas"""
        # Create canvas (initially with empty data)
        self.canvas = WaveformCanvas(self.root, self.waveform_data)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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
        if self.canvas:
            self.canvas.time_scale *= 1.5
            self.canvas.draw_waveforms()
            self.status_bar.config(text=f"Zoom: {self.canvas.time_scale:.2f}x")

    def zoom_out(self):
        """Zoom out (decrease time scale)"""
        if self.canvas:
            self.canvas.time_scale /= 1.5
            if self.canvas.time_scale < 0.01:
                self.canvas.time_scale = 0.01
            self.canvas.draw_waveforms()
            self.status_bar.config(text=f"Zoom: {self.canvas.time_scale:.2f}x")

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
            "• Time grid\n",
        )
