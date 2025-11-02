"""
Professional VU Meter Widget
Real-time audio level visualization with peak hold
"""
import customtkinter as ctk
from tkinter import Canvas
import numpy as np
import threading
import time


class VUMeter(ctk.CTkFrame):
    """Professional VU meter with stereo channels"""

    def __init__(self, master, width=400, height=120, **kwargs):
        super().__init__(master, **kwargs)

        self.width = width
        self.height = height
        self.fg_color = kwargs.get('fg_color', ('#2a2d3a', '#1a1a2e'))

        # Audio levels (dB scale)
        self.left_level = -60.0  # dB
        self.right_level = -60.0  # dB
        self.left_peak = -60.0
        self.right_peak = -60.0
        self.peak_hold_time = 1.5  # seconds
        self.last_peak_time = {"L": 0, "R": 0}

        # Colors for VU meter zones
        self.colors = {
            'green': '#10b981',   # -60 to -18 dB
            'yellow': '#f59e0b',  # -18 to -6 dB
            'red': '#ef4444',     # -6 to 0 dB
            'peak': '#8b5cf6',    # Peak indicator
            'bg': '#1a1a2e',
            'border': '#374151'
        }

        self.create_ui()
        self.update_animation()

    def create_ui(self):
        """Create VU meter UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(header, text="🎚️ VU METER",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        # dB scale label
        ctk.CTkLabel(header, text="Real-time Audio Levels",
                    font=ctk.CTkFont(size=10),
                    text_color="gray60").pack(side="right")

        # Canvas for drawing meters
        self.canvas = Canvas(self,
                            width=self.width - 20,
                            height=self.height - 40,
                            bg=self.colors['bg'],
                            highlightthickness=0)
        self.canvas.pack(padx=10, pady=(5, 10))

        # Draw initial meters
        self.draw_meters()

    def draw_meters(self):
        """Draw stereo VU meters"""
        self.canvas.delete("all")

        # Dimensions
        meter_height = 25
        meter_y_left = 10
        meter_y_right = meter_y_left + meter_height + 15
        meter_width = self.width - 100  # Leave space for labels and dB marks
        meter_x = 50

        # Draw scale marks and dB labels
        db_marks = [-60, -40, -20, -10, -6, -3, 0]
        for db in db_marks:
            x = self.db_to_x(db, meter_x, meter_width)

            # Vertical line
            self.canvas.create_line(x, meter_y_left - 5,
                                   x, meter_y_right + meter_height + 5,
                                   fill=self.colors['border'],
                                   width=1)

            # dB label
            color = self.colors['red'] if db >= -6 else self.colors['yellow'] if db >= -18 else self.colors['green']
            self.canvas.create_text(x, meter_y_right + meter_height + 15,
                                   text=f"{db}",
                                   fill=color,
                                   font=('Arial', 8, 'bold'))

        # Draw LEFT channel
        self.draw_channel("L", self.left_level, self.left_peak,
                         meter_x, meter_y_left, meter_width, meter_height)

        # Draw RIGHT channel
        self.draw_channel("R", self.right_level, self.right_peak,
                         meter_x, meter_y_right, meter_width, meter_height)

    def draw_channel(self, channel, level, peak, x, y, width, height):
        """Draw a single channel meter"""
        # Channel label
        self.canvas.create_text(x - 20, y + height/2,
                               text=channel,
                               fill="white",
                               font=('Arial', 10, 'bold'))

        # Background
        self.canvas.create_rectangle(x, y, x + width, y + height,
                                    fill=self.colors['bg'],
                                    outline=self.colors['border'],
                                    width=2)

        # Calculate level bar width
        level_x = self.db_to_x(level, x, width)

        # Draw colored segments (green, yellow, red zones)
        zones = [
            (-60, -18, self.colors['green']),
            (-18, -6, self.colors['yellow']),
            (-6, 0, self.colors['red'])
        ]

        for db_start, db_end, color in zones:
            zone_x_start = self.db_to_x(db_start, x, width)
            zone_x_end = self.db_to_x(db_end, x, width)

            # Only draw if level reaches this zone
            if level >= db_start:
                actual_end = min(level_x, zone_x_end)
                if actual_end > zone_x_start:
                    # Gradient effect (simulate with overlapping rectangles)
                    self.canvas.create_rectangle(zone_x_start, y + 2,
                                                actual_end, y + height - 2,
                                                fill=color,
                                                outline="")

        # Peak hold indicator
        if peak > -60:
            peak_x = self.db_to_x(peak, x, width)
            self.canvas.create_line(peak_x, y + 2,
                                   peak_x, y + height - 2,
                                   fill=self.colors['peak'],
                                   width=3)

        # dB value text
        db_text = f"{level:.1f} dB" if level > -60 else "-∞ dB"
        text_color = self.colors['red'] if level >= -6 else self.colors['yellow'] if level >= -18 else self.colors['green']
        self.canvas.create_text(x + width + 35, y + height/2,
                               text=db_text,
                               fill=text_color,
                               font=('Arial', 9, 'bold'))

    def db_to_x(self, db, x_start, width):
        """Convert dB value to x coordinate"""
        # Map -60dB to 0dB -> 0 to width
        if db <= -60:
            return x_start
        if db >= 0:
            return x_start + width

        # Logarithmic scale
        normalized = (db + 60) / 60.0  # 0 to 1
        return x_start + (normalized * width)

    def set_levels(self, left_db, right_db):
        """
        Update audio levels
        Args:
            left_db: Left channel level in dB (-60 to 0)
            right_db: Right channel level in dB (-60 to 0)
        """
        current_time = time.time()

        # Clamp values
        left_db = max(-60, min(0, left_db))
        right_db = max(-60, min(0, right_db))

        self.left_level = left_db
        self.right_level = right_db

        # Update peak hold
        if left_db > self.left_peak:
            self.left_peak = left_db
            self.last_peak_time["L"] = current_time

        if right_db > self.right_peak:
            self.right_peak = right_db
            self.last_peak_time["R"] = current_time

        # Decay peak hold after hold time
        if current_time - self.last_peak_time["L"] > self.peak_hold_time:
            self.left_peak = max(self.left_peak - 0.5, -60)

        if current_time - self.last_peak_time["R"] > self.peak_hold_time:
            self.right_peak = max(self.right_peak - 0.5, -60)

    def set_levels_from_amplitude(self, left_amp, right_amp):
        """
        Update levels from amplitude (0.0 to 1.0)
        Args:
            left_amp: Left channel amplitude (0.0 to 1.0)
            right_amp: Right channel amplitude (0.0 to 1.0)
        """
        # Convert amplitude to dB
        left_db = self.amplitude_to_db(left_amp)
        right_db = self.amplitude_to_db(right_amp)
        self.set_levels(left_db, right_db)

    def amplitude_to_db(self, amplitude):
        """Convert amplitude (0-1) to dB (-60 to 0)"""
        if amplitude <= 0:
            return -60.0
        db = 20 * np.log10(amplitude)
        return max(-60, min(0, db))

    def update_animation(self):
        """Smooth animation update"""
        self.draw_meters()
        self.after(50, self.update_animation)  # 20 FPS

    def reset(self):
        """Reset VU meter"""
        self.left_level = -60.0
        self.right_level = -60.0
        self.left_peak = -60.0
        self.right_peak = -60.0


if __name__ == "__main__":
    # Test VU meter
    app = ctk.CTk()
    app.title("VU Meter Test")
    app.geometry("500x200")
    ctk.set_appearance_mode("dark")

    vu = VUMeter(app, width=480, height=140, fg_color=("#2a2d3a", "#1a1a2e"))
    vu.pack(padx=10, pady=10)

    # Simulate audio levels
    def simulate():
        import random
        while True:
            left = random.uniform(0.1, 0.9)
            right = random.uniform(0.1, 0.9)
            vu.set_levels_from_amplitude(left, right)
            time.sleep(0.05)

    threading.Thread(target=simulate, daemon=True).start()

    app.mainloop()
