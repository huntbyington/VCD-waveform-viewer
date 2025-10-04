"""
VCD Waveform Viewer - Main Application
Entry point for the waveform viewer
"""

import tkinter as tk
from viewer import WaveformViewer


def main():
    root = tk.Tk()
    app = WaveformViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
