"""
Professional Karaoke Player Widget
Transport controls, waveform visualization, synchronized lyrics
"""
import customtkinter as ctk
from tkinter import Canvas
import numpy as np
import threading
import time


class KaraokePlayer(ctk.CTkFrame):
    """Professional karaoke player widget with transport controls and lyrics"""

    def __init__(self, master, backing_audio, sample_rate, lyrics_data=None, **kwargs):
        super().__init__(master, **kwargs)

        # Audio data
        self.backing_audio = backing_audio
        self.sample_rate = sample_rate
        self.duration = len(backing_audio) / sample_rate
        self.current_position = 0  # Current playback position in samples
        self.is_playing = False

        # Lyrics data (from Whisper)
        self.lyrics_data = lyrics_data or {"segments": []}

        # Colors
        self.colors = {
            'bg_dark': '#0a0a0f',
            'bg_medium': '#1a1a2e',
            'accent': '#6366f1',
            'accent_bright': '#818cf8',
            'text': '#e5e7eb',
            'text_dim': '#9ca3af',
            'success': '#10b981',
            'waveform': '#4f46e5',
            'waveform_progress': '#818cf8',
            'lyrics_current': '#fbbf24',
            'lyrics_next': '#d1d5db',
            'lyrics_prev': '#6b7280'
        }

        self.configure(fg_color=self.colors['bg_dark'])

        # Callbacks
        self.on_seek_callback = None
        self.on_play_pause_callback = None
        self.on_stop_callback = None
        self.on_fx_change_callback = None  # FX parameter değişikliği callback

        # FX Parameters (kullanıcı kontrol edebilir)
        self.fx_params = {
            'reverb_room_size': 0.6,
            'reverb_wet': 0.25,
            'echo_delay': 0.3,
            'echo_feedback': 0.3,
            'echo_mix': 0.0,  # Default: off
            'compressor_threshold': -18,
            'compressor_ratio': 3.5,
            'eq_bass': 2.0,
            'eq_mid': 3.0,
            'eq_treble': 1.5
        }

        self.create_ui()
        self.start_update_loop()

    def create_ui(self):
        """Create professional UI"""

        # === TOP SECTION: Song Info ===
        header = ctk.CTkFrame(self, fg_color=self.colors['bg_medium'], height=80)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        # Song title
        title_label = ctk.CTkLabel(
            header,
            text="Karaoke Mode - Professional Player",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors['text']
        )
        title_label.pack(pady=(15, 5))

        # Time display
        self.time_label = ctk.CTkLabel(
            header,
            text="00:00 / 00:00",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_dim']
        )
        self.time_label.pack()

        # === WAVEFORM SECTION ===
        waveform_frame = ctk.CTkFrame(self, fg_color=self.colors['bg_medium'])
        waveform_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Waveform canvas
        self.waveform_canvas = Canvas(
            waveform_frame,
            bg=self.colors['bg_dark'],
            highlightthickness=0,
            height=200
        )
        self.waveform_canvas.pack(fill="both", expand=True, padx=15, pady=15)

        # Bind click to seek
        self.waveform_canvas.bind("<Button-1>", self.on_waveform_click)

        # Draw waveform
        self.draw_waveform()

        # === TRANSPORT CONTROLS ===
        controls_frame = ctk.CTkFrame(self, fg_color=self.colors['bg_medium'], height=120)
        controls_frame.pack(fill="x", padx=20, pady=10)
        controls_frame.pack_propagate(False)

        # Control buttons container
        btn_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_container.pack(expand=True)

        # Skip backward button
        self.btn_skip_back = ctk.CTkButton(
            btn_container,
            text="⏮",
            width=60,
            height=60,
            font=ctk.CTkFont(size=24),
            fg_color=self.colors['accent'],
            hover_color=self.colors['accent_bright'],
            command=self.skip_backward
        )
        self.btn_skip_back.pack(side="left", padx=5)

        # Play/Pause button
        self.btn_play_pause = ctk.CTkButton(
            btn_container,
            text="⏸",
            width=80,
            height=80,
            font=ctk.CTkFont(size=32),
            fg_color=self.colors['success'],
            hover_color="#059669",
            command=self.toggle_play_pause
        )
        self.btn_play_pause.pack(side="left", padx=10)

        # Skip forward button
        self.btn_skip_forward = ctk.CTkButton(
            btn_container,
            text="⏭",
            width=60,
            height=60,
            font=ctk.CTkFont(size=24),
            fg_color=self.colors['accent'],
            hover_color=self.colors['accent_bright'],
            command=self.skip_forward
        )
        self.btn_skip_forward.pack(side="left", padx=5)

        # === LYRICS SECTION ===
        lyrics_frame = ctk.CTkFrame(self, fg_color=self.colors['bg_medium'])
        lyrics_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Lyrics title
        ctk.CTkLabel(
            lyrics_frame,
            text="LYRICS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['text_dim']
        ).pack(pady=(15, 10))

        # Previous line
        self.lyrics_prev = ctk.CTkLabel(
            lyrics_frame,
            text="",
            font=ctk.CTkFont(size=18),
            text_color=self.colors['lyrics_prev']
        )
        self.lyrics_prev.pack(pady=5)

        # Current line (large and highlighted)
        self.lyrics_current = ctk.CTkLabel(
            lyrics_frame,
            text="♪ Lyrics will appear here ♪",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors['lyrics_current']
        )
        self.lyrics_current.pack(pady=15)

        # Next line
        self.lyrics_next = ctk.CTkLabel(
            lyrics_frame,
            text="",
            font=ctk.CTkFont(size=18),
            text_color=self.colors['lyrics_next']
        )
        self.lyrics_next.pack(pady=5)

        # === PROFESSIONAL FX CONTROLS ===
        fx_frame = ctk.CTkFrame(self, fg_color=self.colors['bg_medium'])
        fx_frame.pack(fill="x", padx=20, pady=(10, 20))

        # FX title
        ctk.CTkLabel(
            fx_frame,
            text="🎛️ PROFESSIONAL EFFECTS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['accent_bright']
        ).pack(pady=(15, 5))

        # Scrollable frame for FX controls
        fx_scroll = ctk.CTkScrollableFrame(fx_frame, height=200, fg_color="transparent")
        fx_scroll.pack(fill="both", expand=True, padx=15, pady=10)

        # Reverb Controls
        self.create_fx_section(fx_scroll, "🌊 REVERB (Hall Effect)",
                               [("Room Size", "reverb_room_size", 0.0, 1.0, 0.6),
                                ("Wet Level", "reverb_wet", 0.0, 1.0, 0.25)])

        # Echo Controls
        self.create_fx_section(fx_scroll, "📢 ECHO (Delay Effect)",
                               [("Delay Time (s)", "echo_delay", 0.1, 1.0, 0.3),
                                ("Feedback", "echo_feedback", 0.0, 0.9, 0.3),
                                ("Mix", "echo_mix", 0.0, 1.0, 0.0)])

        # Compressor Controls
        self.create_fx_section(fx_scroll, "🎚️ COMPRESSOR (Dynamics)",
                               [("Threshold (dB)", "compressor_threshold", -40, 0, -18),
                                ("Ratio", "compressor_ratio", 1.0, 20.0, 3.5)])

        # EQ Controls
        self.create_fx_section(fx_scroll, "🎵 3-BAND EQ (Equalizer)",
                               [("Bass Gain (dB)", "eq_bass", -20, 20, 2.0),
                                ("Mid Gain (dB)", "eq_mid", -20, 20, 3.0),
                                ("Treble Gain (dB)", "eq_treble", -20, 20, 1.5)])

    def create_fx_section(self, parent, title, params):
        """Create FX control section with sliders"""
        section = ctk.CTkFrame(parent, fg_color=self.colors['bg_dark'], corner_radius=10)
        section.pack(fill="x", pady=10)

        # Section title
        ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text']
        ).pack(pady=(10, 5))

        # Parameters
        for param_label, param_key, min_val, max_val, default_val in params:
            param_frame = ctk.CTkFrame(section, fg_color="transparent")
            param_frame.pack(fill="x", padx=15, pady=5)

            # Label
            label = ctk.CTkLabel(
                param_frame,
                text=f"{param_label}: {default_val:.2f}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors['text_dim'],
                width=180,
                anchor="w"
            )
            label.pack(side="left")

            # Slider
            slider = ctk.CTkSlider(
                param_frame,
                from_=min_val,
                to=max_val,
                number_of_steps=100,
                fg_color=self.colors['bg_medium'],
                progress_color=self.colors['accent'],
                button_color=self.colors['accent_bright'],
                button_hover_color=self.colors['accent']
            )
            slider.set(default_val)
            slider.pack(side="left", fill="x", expand=True, padx=(10, 0))

            # Update callback
            def on_slider_change(value, key=param_key, lbl=label, p_label=param_label):
                self.fx_params[key] = value
                lbl.configure(text=f"{p_label}: {value:.2f}")
                # Notify parent app
                if self.on_fx_change_callback:
                    self.on_fx_change_callback(self.fx_params)

            slider.configure(command=on_slider_change)

    def draw_waveform(self):
        """Draw audio waveform"""
        self.waveform_canvas.delete("all")

        width = self.waveform_canvas.winfo_width()
        height = self.waveform_canvas.winfo_height()

        if width < 10:  # Canvas not ready yet
            self.after(100, self.draw_waveform)
            return

        # Downsample waveform for visualization
        # Use left channel if stereo
        if self.backing_audio.ndim > 1:
            waveform_data = self.backing_audio[:, 0]
        else:
            waveform_data = self.backing_audio

        # Downsample to fit canvas width
        samples_per_pixel = len(waveform_data) // width
        if samples_per_pixel < 1:
            samples_per_pixel = 1

        downsampled = []
        for i in range(0, len(waveform_data), samples_per_pixel):
            chunk = waveform_data[i:i+samples_per_pixel]
            if len(chunk) > 0:
                downsampled.append(np.max(np.abs(chunk)))

        # Draw waveform bars
        mid_y = height / 2
        max_amplitude = max(downsampled) if downsampled else 1.0

        for i, amplitude in enumerate(downsampled):
            if i >= width:
                break

            # Normalize amplitude
            normalized = (amplitude / max_amplitude) * (height * 0.4)

            # Determine color (progress vs unplayed)
            progress_ratio = self.current_position / len(self.backing_audio)
            pixel_ratio = i / width

            if pixel_ratio <= progress_ratio:
                color = self.colors['waveform_progress']
            else:
                color = self.colors['waveform']

            # Draw vertical bar
            self.waveform_canvas.create_line(
                i, mid_y - normalized,
                i, mid_y + normalized,
                fill=color,
                width=1
            )

        # Draw playhead
        playhead_x = int((self.current_position / len(self.backing_audio)) * width)
        self.waveform_canvas.create_line(
            playhead_x, 0,
            playhead_x, height,
            fill=self.colors['accent_bright'],
            width=3
        )

    def on_waveform_click(self, event):
        """Handle click on waveform to seek"""
        width = self.waveform_canvas.winfo_width()
        click_ratio = event.x / width
        new_position = int(click_ratio * len(self.backing_audio))

        self.seek_to(new_position)

    def seek_to(self, position_samples):
        """Seek to specific position"""
        self.current_position = max(0, min(position_samples, len(self.backing_audio) - 1))

        # Callback to audio engine
        if self.on_seek_callback:
            self.on_seek_callback(self.current_position)

        self.update_display()

    def skip_backward(self):
        """Skip backward 5 seconds"""
        skip_samples = int(5 * self.sample_rate)
        self.seek_to(self.current_position - skip_samples)

    def skip_forward(self):
        """Skip forward 5 seconds"""
        skip_samples = int(5 * self.sample_rate)
        self.seek_to(self.current_position + skip_samples)

    def toggle_play_pause(self):
        """Toggle play/pause"""
        self.is_playing = not self.is_playing

        # Update button
        self.btn_play_pause.configure(text="▶" if not self.is_playing else "⏸")

        # Callback
        if self.on_play_pause_callback:
            self.on_play_pause_callback(self.is_playing)

    def update_position(self, position_samples):
        """Update current position (called from audio callback)"""
        self.current_position = position_samples

    def update_display(self):
        """Update all display elements"""
        # Update time
        current_time = self.current_position / self.sample_rate
        total_time = self.duration

        self.time_label.configure(
            text=f"{self.format_time(current_time)} / {self.format_time(total_time)}"
        )

        # Update waveform
        self.draw_waveform()

        # Update lyrics
        self.update_lyrics()

    def update_lyrics(self):
        """Update lyrics based on current position"""
        if not self.lyrics_data:
            return

        current_time = self.current_position / self.sample_rate

        # Support both formats:
        # 1. Whisper API format: {"segments": [...]}
        # 2. MusicAnalyzer format: {"lyrics_timestamped": [...]}
        segments = None
        if "segments" in self.lyrics_data:
            segments = self.lyrics_data["segments"]
        elif "lyrics_timestamped" in self.lyrics_data:
            # Convert MusicAnalyzer format to Whisper format
            segments = []
            for item in self.lyrics_data["lyrics_timestamped"]:
                segments.append({
                    "start": item.get("timestamp", 0.0),
                    "end": item.get("timestamp", 0.0) + 3.0,  # Estimate 3 sec duration
                    "text": item.get("text", "")
                })

        if not segments:
            return

        # Find current segment
        current_idx = -1
        for i, segment in enumerate(segments):
            if segment["start"] <= current_time < segment["end"]:
                current_idx = i
                break

        if current_idx >= 0:
            # Current line
            self.lyrics_current.configure(text=segments[current_idx]["text"].strip())

            # Previous line
            if current_idx > 0:
                self.lyrics_prev.configure(text=segments[current_idx - 1]["text"].strip())
            else:
                self.lyrics_prev.configure(text="")

            # Next line
            if current_idx < len(segments) - 1:
                self.lyrics_next.configure(text=segments[current_idx + 1]["text"].strip())
            else:
                self.lyrics_next.configure(text="")
        else:
            # No current segment
            if current_time < segments[0]["start"] if segments else 0:
                self.lyrics_current.configure(text="♪ Music Intro ♪")
            else:
                self.lyrics_current.configure(text="♪ Music Outro ♪")

    def start_update_loop(self):
        """Start update loop for display"""
        def update_loop():
            while True:
                try:
                    if self.winfo_exists():
                        self.update_display()
                        time.sleep(0.05)  # 20 FPS
                    else:
                        break
                except:
                    break

        threading.Thread(target=update_loop, daemon=True).start()

    def format_time(self, seconds):
        """Format time as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


if __name__ == "__main__":
    # Test
    app = ctk.CTk()
    app.withdraw()

    # Generate test audio
    duration = 30
    sr = 48000
    test_audio = np.random.randn(duration * sr, 2) * 0.1

    # Test lyrics
    test_lyrics = {
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "This is the first line"},
            {"start": 3.0, "end": 6.0, "text": "This is the second line"},
            {"start": 6.0, "end": 9.0, "text": "This is the third line"},
        ]
    }

    player = KaraokePlayer(app, test_audio, sr, test_lyrics)
    player.is_playing = True

    app.mainloop()
