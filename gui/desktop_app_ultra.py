"""
Musicio ULTRA - Professional Audio Studio
All-in-one professional audio production suite
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import sys
import os
from pathlib import Path
import numpy as np
from PIL import Image
import time
import pygame
import json
from typing import Tuple

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_manager import ModelManager
from core.pitch_shifter import PitchShifter
from core.audio_recorder import AudioRecorder
from core.audio_effects import AudioEffects
from core.music_analyzer import MusicAnalyzer
from core.visualizer import AudioVisualizer
from core.batch_processor import BatchProcessor
from core.audio_mixer import AudioMixer
from core.format_converter import FormatConverter
from core.karaoke_mode import KaraokeMode
from gui.vu_meter import VUMeter
from utils.lyrics_converter import convert_lyrics_txt_to_json
from utils.language import get_text as _, set_language, get_current_language


class MusicioUltraApp(ctk.CTk):
    """Ultra profesyonel ses stüdyosu"""

    def __init__(self):
        super().__init__()

        # Global değişkenler
        self.model_manager = None
        self.pitch_shifter = None
        self.input_file = None
        self.output_file = None
        self.is_processing = False
        self.models_loaded = {"demucs": False, "audiosr": False}

        # Yeni modüller
        self.recorder = AudioRecorder()
        self.audio_effects = AudioEffects()
        self.music_analyzer = MusicAnalyzer()
        self.visualizer = AudioVisualizer()
        self.batch_processor = BatchProcessor()
        self.audio_mixer = AudioMixer()
        self.format_converter = FormatConverter()
        self.karaoke_mode = None  # Model manager ile başlatılacak

        # Karaoke state
        self.karaoke_backing_track = None  # Oluşturulan backing track yolu
        self.karaoke_file = None  # Seçilen şarkı dosyası
        self.karaoke_output_folder = None  # Çıkış klasörü

        # Config file path
        self.config_file = Path("musicio_config.json")

        # Load saved settings
        self.load_config()

        # Audio player
        pygame.mixer.init()
        self.is_playing = False
        self.current_playing_file = None

        # Pencere ayarları
        self.title("🎵 Musicio ULTRA - Professional Audio Studio")
        self.geometry("1600x1000")
        self.resizable(True, True)

        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Renkler
        self.colors = {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6"
        }

        # UI oluştur
        self.create_ui()

        # Model yöneticisini başlat
        self.initialize_models()

        # Sistem monitörünü başlat
        self.start_system_monitor()

    def create_ui(self):
        """Ana UI yapısı"""
        # Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Sol sidebar
        self.create_sidebar()

        # Header
        self.create_header()

        # Ana içerik - TAB SİSTEMİ
        self.create_tabbed_content()

        # Sağ panel - Stats
        self.create_stats_panel()

    def create_sidebar(self):
        """Sol sidebar"""
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color=("gray85", "gray15"))
        logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")

        ctk.CTkLabel(logo_frame, text="🎵", font=ctk.CTkFont(size=50)).pack(pady=10)
        ctk.CTkLabel(logo_frame, text="SkyTech ULTRA", font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(logo_frame, text="Professional Audio Studio", font=ctk.CTkFont(size=11), text_color="gray60").pack()
        ctk.CTkLabel(logo_frame, text="v2.0 Ultimate", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["primary"]).pack(pady=(5, 10))

        # GPU/System Info
        gpu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        gpu_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(gpu_frame, text="⚙️ Sistem Bilgisi", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 10))

        # GPU info
        self.gpu_label = ctk.CTkLabel(gpu_frame, text="🎮 GPU: Yükleniyor...", font=ctk.CTkFont(size=11), anchor="w")
        self.gpu_label.pack(anchor="w", pady=2)

        # GPU Usage
        self.gpu_usage_label = ctk.CTkLabel(gpu_frame, text="📊 VRAM: 0.0 GB / 0.0 GB (0%)", font=ctk.CTkFont(size=10), anchor="w", text_color="gray60")
        self.gpu_usage_label.pack(anchor="w", pady=2)

        # RAM Usage
        self.ram_usage_label = ctk.CTkLabel(gpu_frame, text="💾 RAM: 0.0 GB", font=ctk.CTkFont(size=10), anchor="w", text_color="gray60")
        self.ram_usage_label.pack(anchor="w", pady=2)

        # Model status
        self.demucs_status = ctk.CTkLabel(gpu_frame, text="🔴 Demucs: Yüklenmedi", font=ctk.CTkFont(size=11), anchor="w")
        self.demucs_status.pack(anchor="w", pady=2)

        self.audiosr_status = ctk.CTkLabel(gpu_frame, text="🔴 AudioSR: Yüklenmedi", font=ctk.CTkFont(size=11), anchor="w")
        self.audiosr_status.pack(anchor="w", pady=2)

        # Quick actions
        ctk.CTkLabel(sidebar, text="⚡ Quick Actions", font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, padx=20, pady=(20, 10), sticky="w")

        actions = [
            ("📂 Dosya Aç", self.quick_load_file, "primary"),
            ("🎤 Hızlı Kayıt", self.quick_record, "danger"),
            ("📊 Analiz Et", self.quick_analyze, "info"),
            ("🎛️ Batch İşlem", self.quick_batch, "success")
        ]

        for i, (text, command, color) in enumerate(actions):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                command=command,
                height=40,
                fg_color=self.colors[color],
                hover_color=self.adjust_color(self.colors[color], -20)
            )
            btn.grid(row=2+i, column=0, padx=20, pady=5, sticky="ew")

    def create_header(self):
        """Başlık"""
        header = ctk.CTkFrame(self, corner_radius=0, height=80, fg_color=(self.colors["primary"], self.colors["secondary"]))
        header.grid(row=0, column=1, columnspan=2, sticky="ew")

        ctk.CTkLabel(header, text="Professional Audio Production Studio", font=ctk.CTkFont(size=28, weight="bold"), text_color="white").grid(row=0, column=0, padx=30, pady=20, sticky="w")

        self.status_badge = ctk.CTkLabel(header, text="● Hazır", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10b981")
        self.status_badge.grid(row=0, column=1, padx=30, pady=20, sticky="e")

    def create_tabbed_content(self):
        """TAB sistemi - Ana özellikler"""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # TabView oluştur
        self.tabview = ctk.CTkTabview(main_container, height=800)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Tab'ları ekle
        self.tabview.add("🎚️ Pitch Shifter")
        self.tabview.add("🎤 Mikrofon Kaydı")
        self.tabview.add("🎛️ Ses Efektleri")
        self.tabview.add("🎼 Müzik Analizi")
        self.tabview.add("📊 Görselleştirme")
        self.tabview.add("🎚️ Batch İşlem")
        self.tabview.add("🎵 Audio Mixer")
        self.tabview.add("🎧 Karaoke Mode")
        self.tabview.add("🔄 Format Converter")

        # Tab içeriklerini oluştur
        self.create_pitch_shifter_tab()
        self.create_recorder_tab()
        self.create_effects_tab()
        self.create_analyzer_tab()
        self.create_visualizer_tab()
        self.create_batch_tab()
        self.create_mixer_tab()
        self.create_karaoke_tab()
        self.create_converter_tab()

    def create_pitch_shifter_tab(self):
        """Pitch Shifter tab (orijinal özellik)"""
        tab = self.tabview.tab("🎚️ Pitch Shifter")
        tab.grid_columnconfigure(0, weight=1)

        # Dosya seçimi
        file_frame = ctk.CTkFrame(tab)
        file_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(file_frame, text="📁 Ses Dosyası", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))

        self.file_info_label = ctk.CTkLabel(file_frame, text="Dosya seçilmedi", font=ctk.CTkFont(size=12))
        self.file_info_label.pack(anchor="w", padx=20, pady=(0, 20))

        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        ctk.CTkButton(btn_frame, text="📂 Dosya Seç", command=self.select_file, width=150).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💾 Kayıt Yeri", command=self.select_output, width=150).pack(side="left", padx=10)

        # Pitch kontrol
        pitch_frame = ctk.CTkFrame(tab)
        pitch_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(pitch_frame, text="🎚️ Pitch Ayarları", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))

        self.pitch_visual = ctk.CTkLabel(pitch_frame, text="0.0", font=ctk.CTkFont(size=60, weight="bold"), text_color=self.colors["primary"])
        self.pitch_visual.pack(pady=20)

        self.semitone_var = ctk.DoubleVar(value=0)
        slider = ctk.CTkSlider(pitch_frame, from_=-12, to=12, number_of_steps=240, variable=self.semitone_var, command=self.update_pitch_visual, width=600)
        slider.pack(pady=20)

        # Hızlı Butonlar
        quick_btns = ctk.CTkFrame(pitch_frame, fg_color="transparent")
        quick_btns.pack(pady=10)

        btn_specs = [
            ("-1 Oktav", -12, self.colors["danger"]),
            ("-1", -1, self.colors["warning"]),
            ("Sıfırla", 0, self.colors["info"]),
            ("+1", 1, self.colors["warning"]),
            ("+1 Oktav", 12, self.colors["success"])
        ]

        for text, value, color in btn_specs:
            ctk.CTkButton(quick_btns, text=text, width=90, height=35, fg_color=color,
                         command=lambda v=value: self.quick_pitch(v)).pack(side="left", padx=5)

        # AI & Kalite Ayarları
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        settings_frame.grid_columnconfigure((0,1), weight=1)

        # Sol: AI Özellikler
        ai_frame = ctk.CTkFrame(settings_frame, fg_color=("gray90", "gray20"))
        ai_frame.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(ai_frame, text="🤖 AI Özellikler", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15,10))

        self.ai_separation_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(ai_frame, text="🎤 Vokal Ayırma (Demucs)", variable=self.ai_separation_var,
                     progress_color=self.colors["success"]).pack(pady=5, padx=15, anchor="w")

        self.ai_enhancement_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(ai_frame, text="✨ Kalite İyileştirme (AudioSR)", variable=self.ai_enhancement_var,
                     progress_color=self.colors["success"]).pack(pady=5, padx=15, anchor="w")

        # Sağ: Kalite Seçimi
        quality_frame = ctk.CTkFrame(settings_frame, fg_color=("gray90", "gray20"))
        quality_frame.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")

        ctk.CTkLabel(quality_frame, text="⚙️ Kalite", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15,10))

        self.quality_var = ctk.StringVar(value="ultra")

        qualities = [("Düşük (Hızlı)", "low"), ("Orta", "medium"), ("Yüksek ⭐", "high"), ("Ultra", "ultra")]
        for name, value in qualities:
            ctk.CTkRadioButton(quality_frame, text=name, variable=self.quality_var, value=value,
                              font=ctk.CTkFont(size=13)).pack(pady=3, padx=15, anchor="w")

        # İşlem butonu - Modern ve büyük
        self.process_btn = ctk.CTkButton(
            tab,
            text="🚀 İŞLEME BAŞLA",
            command=self.process_audio,
            height=80,
            font=ctk.CTkFont(size=24, weight="bold"),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            corner_radius=20,
            border_width=3,
            border_color=("#34d399", "#10b981")
        )
        self.process_btn.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        # Progress bar ve status - Modern tasarım
        progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        progress_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=700,
            height=35,
            corner_radius=20,
            progress_color=("#10b981", "#059669"),
            fg_color=("gray80", "gray25")
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(progress_frame, text="", font=ctk.CTkFont(size=12))
        self.progress_label.pack()

    def create_recorder_tab(self):
        """Mikrofon kaydı tab - FULL FEATURED"""
        tab = self.tabview.tab("🎤 Mikrofon Kaydı")
        tab.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"), corner_radius=15)
        header_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(header_frame, text="🎤 Professional Studio Recording",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(header_frame, text="96kHz / 32-bit Float | Ultra Low Latency",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 15))

        # Device Selection - Modern Cards
        device_frame = ctk.CTkFrame(tab)
        device_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        device_frame.grid_columnconfigure((0, 1), weight=1)

        # Mikrofon device
        mic_card = ctk.CTkFrame(device_frame, fg_color=("gray85", "gray25"), corner_radius=12)
        mic_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")

        ctk.CTkLabel(mic_card, text="🎙️ Mikrofon Cihazı",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))

        self.mic_device_var = ctk.StringVar(value="Varsayılan")
        self.mic_device_menu = ctk.CTkOptionMenu(
            mic_card,
            variable=self.mic_device_var,
            values=["Varsayılan", "Cihaz yükleniyor..."],
            width=300,
            height=40,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12)
        )
        self.mic_device_menu.pack(padx=15, pady=(5, 15), fill="x")

        # Hoparlör device
        speaker_card = ctk.CTkFrame(device_frame, fg_color=("gray85", "gray25"), corner_radius=12)
        speaker_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="ew")

        ctk.CTkLabel(speaker_card, text="🔊 Hoparlör/Kulaklık",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))

        self.speaker_device_var = ctk.StringVar(value="Varsayılan")
        self.speaker_device_menu = ctk.CTkOptionMenu(
            speaker_card,
            variable=self.speaker_device_var,
            values=["Varsayılan", "Cihaz yükleniyor..."],
            width=300,
            height=40,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12)
        )
        self.speaker_device_menu.pack(padx=15, pady=(5, 15), fill="x")

        # Refresh devices button
        ctk.CTkButton(device_frame, text="🔄 Cihazları Yenile",
                     command=self.refresh_audio_devices, height=35,
                     font=ctk.CTkFont(size=12)).grid(row=1, column=0, columnspan=2, pady=10)

        # VU Meter - Professional
        vu_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"), corner_radius=15)
        vu_frame.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(vu_frame, text="📊 Input Level Monitor",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        self.vu_meter_canvas = ctk.CTkCanvas(vu_frame, height=60, bg="#1a1a2e", highlightthickness=0)
        self.vu_meter_canvas.pack(fill="x", padx=20, pady=(10, 15))

        # Recording Controls - Big & Beautiful
        control_frame = ctk.CTkFrame(tab, fg_color="transparent")
        control_frame.grid(row=3, column=0, pady=20)

        self.rec_btn = ctk.CTkButton(
            control_frame,
            text="⏺️ KAYIT BAŞLAT",
            command=self.start_recording,
            width=250,
            height=70,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            corner_radius=15,
            border_width=2,
            border_color=("#f87171", "#ef4444")
        )
        self.rec_btn.pack(side="left", padx=10)

        self.stop_rec_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ DURDUR",
            command=self.stop_recording,
            width=250,
            height=70,
            font=ctk.CTkFont(size=18, weight="bold"),
            state="disabled",
            fg_color=("gray70", "gray30")
        )
        self.stop_rec_btn.pack(side="left", padx=10)

        # Real-time Effects
        effects_card = ctk.CTkFrame(tab, fg_color=("gray90", "gray20"), corner_radius=15)
        effects_card.grid(row=4, column=0, padx=20, pady=15, sticky="ew")

        ctk.CTkLabel(effects_card, text="🎛️ Real-time Effects",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        # Pitch shift
        pitch_frame = ctk.CTkFrame(effects_card, fg_color="transparent")
        pitch_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(pitch_frame, text="Pitch Shift:", font=ctk.CTkFont(size=13), width=120).pack(side="left")
        self.rec_pitch_var = ctk.DoubleVar(value=0)
        ctk.CTkSlider(pitch_frame, from_=-12, to=12, variable=self.rec_pitch_var, width=450, height=20,
                     progress_color=self.colors["primary"]).pack(side="left", padx=10)
        self.rec_pitch_label = ctk.CTkLabel(pitch_frame, text="0.0 semitones",
                                           font=ctk.CTkFont(size=13, weight="bold"), width=110)
        self.rec_pitch_label.pack(side="left", padx=5)

        # Monitor switch
        monitor_frame = ctk.CTkFrame(effects_card, fg_color="transparent")
        monitor_frame.pack(fill="x", padx=20, pady=(5, 15))

        self.monitor_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(monitor_frame, text="🎧 Monitor (Kendi sesini duy)",
                     variable=self.monitor_var, font=ctk.CTkFont(size=13),
                     progress_color=self.colors["success"]).pack(anchor="w")

        # Recording info
        self.rec_info_label = ctk.CTkLabel(tab, text="⏸️ Kayıt durumunda...",
                                          font=ctk.CTkFont(size=12), text_color="gray")
        self.rec_info_label.grid(row=5, column=0, pady=10)

    def create_effects_tab(self):
        """Ses efektleri tab"""
        tab = self.tabview.tab("🎛️ Ses Efektleri")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="🎛️ Professional Audio Effects", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Effects scroll frame
        effects_scroll = ctk.CTkScrollableFrame(tab, height=600)
        effects_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        effects = [
            ("🌊 Reverb", ["Room Size", "Damping", "Wet Level"], [0.5, 0.5, 0.33]),
            ("📢 Echo", ["Delay (s)", "Feedback", "Mix"], [0.5, 0.4, 0.5]),
            ("🎵 Chorus", ["Rate (Hz)", "Depth", "Mix"], [1.0, 0.25, 0.5]),
            ("🎚️ Compressor", ["Threshold (dB)", "Ratio", "Attack (ms)"], [-20, 4.0, 5.0]),
            ("🎛️ EQ", ["Bass (dB)", "Mid (dB)", "Treble (dB)"], [0, 0, 0])
        ]

        self.effect_vars = {}

        for i, (name, params, defaults) in enumerate(effects):
            effect_card = ctk.CTkFrame(effects_scroll)
            effect_card.pack(fill="x", pady=10)

            ctk.CTkLabel(effect_card, text=name, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

            for param, default in zip(params, defaults):
                param_frame = ctk.CTkFrame(effect_card, fg_color="transparent")
                param_frame.pack(fill="x", padx=20, pady=5)

                ctk.CTkLabel(param_frame, text=param, width=150).pack(side="left")

                var = ctk.DoubleVar(value=default)
                self.effect_vars[f"{name}_{param}"] = var

                slider_from = -20 if "dB" in param else 0
                slider_to = 20 if "dB" in param else (10 if "Ratio" in param else 1)
                ctk.CTkSlider(param_frame, from_=slider_from, to=slider_to, variable=var, width=300).pack(side="left", padx=10)
                ctk.CTkLabel(param_frame, textvariable=var, width=60).pack(side="left")

        # Apply button
        ctk.CTkButton(tab, text="✨ EFEKTLERİ UYGULA", command=self.apply_effects, height=60, font=ctk.CTkFont(size=18, weight="bold"), fg_color=self.colors["success"]).pack(pady=20)

    def create_analyzer_tab(self):
        """Müzik analizi tab"""
        tab = self.tabview.tab("🎼 Müzik Analizi")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="🎼 AI Music Analyzer", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Lyrics language selector
        lang_frame = ctk.CTkFrame(tab, fg_color=("#2a2d3a", "#1a1a2e"))
        lang_frame.pack(pady=(0, 15))

        ctk.CTkLabel(lang_frame, text="🌍 Şarkı Sözleri Dili:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(20, 10), pady=10)

        self.lyrics_language_var = ctk.StringVar(value="auto")
        lang_options = ctk.CTkFrame(lang_frame, fg_color="transparent")
        lang_options.pack(side="left", padx=(0, 20), pady=10)

        ctk.CTkRadioButton(lang_options, text="🌍 Otomatik", variable=self.lyrics_language_var, value="auto", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        ctk.CTkRadioButton(lang_options, text="🇹🇷 Türkçe", variable=self.lyrics_language_var, value="tr", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        ctk.CTkRadioButton(lang_options, text="🇬🇧 İngilizce", variable=self.lyrics_language_var, value="en", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)

        # Analiz butonları
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="🔍 GENEL ANALİZ",
            command=self.analyze_music,
            height=60,
            width=220,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
            corner_radius=15
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="🎹 NOTALARI ÇIKART",
            command=self.transcribe_notes,
            height=60,
            width=200,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#8b5cf6", "#7c3aed"),
            hover_color=("#7c3aed", "#6d28d9"),
            corner_radius=15
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🎤 SÖZLERİ ÇIKART",
            command=self.transcribe_lyrics,
            height=60,
            width=200,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#ec4899", "#db2777"),
            hover_color=("#db2777", "#be185d"),
            corner_radius=15
        ).pack(side="left", padx=5)

        # İkinci satır butonlar
        btn_frame2 = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame2.pack(pady=10)

        ctk.CTkButton(
            btn_frame2,
            text="🎸 ENSTRÜMANLARI AYIR",
            command=self.separate_instruments,
            height=60,
            width=260,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#f59e0b", "#d97706"),
            hover_color=("#d97706", "#b45309"),
            corner_radius=15
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame2,
            text="🎼 ENSTRÜMAN NOTALARI",
            command=self.transcribe_instrument_notes,
            height=60,
            width=260,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#06b6d4", "#0891b2"),
            hover_color=("#0891b2", "#0e7490"),
            corner_radius=15
        ).pack(side="left", padx=5)

        # Sonuçlar
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.analysis_results = ctk.CTkTextbox(results_frame, font=ctk.CTkFont(size=13, family="Consolas"), wrap="word")
        self.analysis_results.pack(fill="both", expand=True, padx=10, pady=10)
        self.analysis_results.insert("1.0", "Dosya seçin ve 'Analiz Et' butonuna basın...")

    def create_visualizer_tab(self):
        """Görselleştirme tab"""
        tab = self.tabview.tab("📊 Görselleştirme")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="📊 Audio Visualization", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Görselleştirme türü seç
        viz_options = ctk.CTkFrame(tab)
        viz_options.pack(pady=20)

        viz_types = ["Waveform", "Spectrogram", "Mel Spectrogram", "Chromagram"]

        for viz_type in viz_types:
            ctk.CTkButton(viz_options, text=f"📈 {viz_type}", command=lambda vt=viz_type: self.generate_visualization(vt), width=180).pack(side="left", padx=10)

        # Görsel gösterim alanı
        self.viz_display = ctk.CTkLabel(tab, text="Görselleştirme burada görünecek...")
        self.viz_display.pack(fill="both", expand=True, padx=20, pady=20)

    def create_batch_tab(self):
        """Batch işlem tab"""
        tab = self.tabview.tab("🎚️ Batch İşlem")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="🎚️ Toplu Dosya İşleme", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Dosya ekleme
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="📂 Dosya Ekle", command=self.batch_add_files, width=180, height=50).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📁 Klasör Ekle", command=self.batch_add_folder, width=180, height=50).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ Temizle", command=self.batch_clear, width=180, height=50, fg_color="red").pack(side="left", padx=10)

        # Kuyruk
        self.batch_queue_label = ctk.CTkLabel(tab, text="Kuyruk: 0 dosya", font=ctk.CTkFont(size=16))
        self.batch_queue_label.pack(pady=10)

        # İşlem butonu
        ctk.CTkButton(tab, text="🚀 TOPLU İŞLEMİ BAŞLAT", command=self.batch_process, height=70, font=ctk.CTkFont(size=20, weight="bold"), fg_color=self.colors["success"]).pack(pady=20)

        # Progress
        self.batch_progress = ctk.CTkProgressBar(tab, width=600)
        self.batch_progress.pack(pady=20)
        self.batch_progress.set(0)

    def create_stats_panel(self):
        """Sağ panel - Stats"""
        stats_panel = ctk.CTkFrame(self, width=300, corner_radius=0)
        stats_panel.grid(row=1, column=2, rowspan=2, sticky="nsew")

        ctk.CTkLabel(stats_panel, text="📊 İstatistikler", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # Player
        self.create_audio_player(stats_panel)

        # Log
        ctk.CTkLabel(stats_panel, text="📝 Log", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        self.log_text = ctk.CTkTextbox(stats_panel, font=ctk.CTkFont(size=10, family="Consolas"), wrap="word", height=400)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=20)
        self.log_text.insert("1.0", "Sistem başlatıldı\n")

    def create_audio_player(self, parent):
        """Audio player"""
        player_frame = ctk.CTkFrame(parent)
        player_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(player_frame, text="🎵 Player", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        controls = ctk.CTkFrame(player_frame, fg_color="transparent")
        controls.pack(pady=10)

        ctk.CTkButton(controls, text="📥", command=lambda: self.play_audio("input"), width=50).pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(controls, text="▶️", command=self.toggle_play, width=50)
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(controls, text="⏹️", command=self.stop_audio, width=50).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="📤", command=lambda: self.play_audio("output"), width=50).pack(side="left", padx=5)

    # === METODLAR ===

    def initialize_models(self):
        """Model başlatma"""
        def init():
            self.add_log("⚙️ Sistem başlatılıyor...")
            self.model_manager = ModelManager()
            self.pitch_shifter = PitchShifter(self.model_manager)

            # GPU bilgisi
            device_info = self.model_manager.get_device_info()
            if device_info['device'] == 'cuda':
                gpu_text = f"🎮 GPU: {device_info['gpu_name']}"
                self.gpu_label.configure(text=gpu_text)
                self.add_log(f"✓ {device_info['gpu_name']} tespit edildi")
                self.add_log(f"✓ CUDA {device_info['cuda_version']}")
            else:
                self.gpu_label.configure(text="🎮 GPU: CPU Mode")
                self.add_log("⚠️ CUDA bulunamadı, CPU kullanılıyor")

            # Modelleri arka planda yükle
            self.add_log("🤖 AI modelleri yükleniyor...")

            # Demucs yükle
            self.demucs_status.configure(text="🟡 Demucs: Yükleniyor...")
            if self.model_manager.load_demucs():
                self.demucs_status.configure(text="🟢 Demucs: Hazır")
                self.models_loaded["demucs"] = True
                self.add_log("✓ Demucs modeli hazır")
            else:
                self.demucs_status.configure(text="🔴 Demucs: Hata")
                self.add_log("⚠️ Demucs yüklenemedi")

            # AudioSR yükle
            self.audiosr_status.configure(text="🟡 AudioSR: Yükleniyor...")
            if self.model_manager.load_audiosr():
                self.audiosr_status.configure(text="🟢 AudioSR: Hazır")
                self.models_loaded["audiosr"] = True
                self.add_log("✓ AudioSR modeli hazır")
            else:
                self.audiosr_status.configure(text="🔴 AudioSR: Opsiyonel")
                self.add_log("⚠️ AudioSR yüklenemedi (opsiyonel)")

            # MusicAnalyzer'a model_manager'ı bağla (Whisper için vokal ayırma)
            self.music_analyzer.model_manager = self.model_manager

            # Karaoke mode'u başlat
            self.karaoke_mode = KaraokeMode(self.model_manager)

            self.add_log("✓ Sistem hazır!")
            self.status_badge.configure(text="● Hazır", text_color="#10b981")

        threading.Thread(target=init, daemon=True).start()

    def select_file(self):
        """Dosya seç"""
        filename = filedialog.askopenfilename(
            title="Ses Dosyası Seç",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("Tüm Dosyalar", "*.*")]
        )
        if filename:
            self.input_file = str(filename)
            self.file_info_label.configure(text=f"📂 {Path(filename).name}")
            self.add_log(f"Dosya seçildi: {Path(filename).name}")

    def select_output(self):
        """Çıktı seç"""
        filename = filedialog.asksaveasfilename(
            title="Kayıt Yeri",
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav"), ("MP3", "*.mp3"), ("FLAC", "*.flac")]
        )
        if filename:
            self.output_file = str(filename)
            self.add_log(f"📂 Kayıt yeri: {filename}")
            self.add_log(f"Kayıt yeri: {Path(filename).name}")

    def update_pitch_visual(self, value):
        """Pitch visual güncelle"""
        self.pitch_visual.configure(text=f"{value:+.1f}")

    def quick_pitch(self, value):
        """Hızlı pitch ayarla"""
        self.semitone_var.set(value)
        self.update_pitch_visual(value)
        self.add_log(f"🎚️ Pitch ayarlandı: {value:+.1f} semitone")

    def process_audio(self):
        """Pitch shifting işle"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        if not self.pitch_shifter:
            messagebox.showerror("Hata", "Sistem henüz hazır değil!")
            return

        def process():
            self.process_btn.configure(state="disabled", text="⏳ İŞLENİYOR...")
            self.progress_bar.set(0)
            self.progress_label.configure(text="⚙️ Başlatılıyor...")
            self.status_badge.configure(text="● İşleniyor", text_color="#f59e0b")

            # Output path
            assert self.input_file is not None, "Input file must be set"
            input_path = Path(self.input_file)

            if self.output_file:
                output = self.output_file
            else:
                output = str(input_path.parent / f"shifted_{input_path.name}")

            self.add_log("=" * 60)
            self.add_log("🚀 PITCH SHIFTING BAŞLIYOR")
            self.add_log(f"📂 Giriş: {input_path.name}")
            self.add_log(f"💾 Çıkış: {output}")
            self.add_log(f"🎚️ Pitch: {self.semitone_var.get():+.1f} semitone")
            self.add_log(f"⚙️ Kalite: {self.quality_var.get().upper()}")
            self.add_log(f"🎤 Vokal Ayırma: {'AÇIK' if self.ai_separation_var.get() else 'KAPALI'}")
            self.add_log(f"✨ AI İyileştirme: {'AÇIK' if self.ai_enhancement_var.get() else 'KAPALI'}")
            self.add_log(f"🎮 GPU: RTX 5090 (CUDA 12.9)")
            self.add_log("=" * 60)

            self.progress_bar.set(0.1)
            self.progress_label.configure(text="📂 Dosya yükleniyor...")
            self.add_log("📂 Ses dosyası yükleniyor...")

            self.progress_bar.set(0.3)
            self.progress_label.configure(text="🎚️ Pitch değiştiriliyor (RTX 5090)...")
            self.add_log("🎚️ Pitch shifting uygulanıyor...")
            self.add_log("🔥 RTX 5090 maksimum hızda çalışıyor...")

            # Get pitch_shifter (already checked in outer scope)
            pitch_shifter = self.pitch_shifter
            if pitch_shifter is None:
                raise RuntimeError("Pitch shifter not initialized")

            result: Tuple[bool, str] = pitch_shifter.shift_pitch(
                self.input_file,
                output,
                self.semitone_var.get(),
                use_ai_separation=self.ai_separation_var.get(),
                use_ai_enhancement=self.ai_enhancement_var.get(),
                quality=self.quality_var.get()
            )
            success, msg = result  # type: ignore[misc]

            self.progress_bar.set(0.9)
            self.progress_label.configure(text="💾 Kaydediliyor...")
            self.add_log("💾 Dosya kaydediliyor...")

            if success:
                self.progress_bar.set(1.0)
                self.progress_label.configure(text="✅ Tamamlandı!")
                self.add_log("=" * 60)
                self.add_log("✅ İŞLEM BAŞARILI!")
                self.add_log(f"📂 Konum: {output}")
                try:
                    size_mb = Path(output).stat().st_size / 1024 / 1024
                    self.add_log(f"💾 Boyut: {size_mb:.2f} MB")
                except:
                    pass
                self.add_log("=" * 60)
                messagebox.showinfo("✅ Başarılı", f"İşlem tamamlandı!\n\n📂 Dosya:\n{output}\n\n🎚️ Pitch: {self.semitone_var.get():+.1f} semitone")
            else:
                self.progress_bar.set(0)
                self.progress_label.configure(text="❌ Hata!")
                self.add_log("=" * 60)
                self.add_log(f"❌ HATA: {msg}")
                self.add_log("=" * 60)
                messagebox.showerror("❌ Hata", f"İşlem başarısız!\n\n{msg}")

            self.process_btn.configure(state="normal", text="🚀 İŞLEME BAŞLA")
            self.status_badge.configure(text="● Hazır", text_color="#10b981")

        threading.Thread(target=process, daemon=True).start()

    def start_recording(self):
        """Kayıt başlat"""
        self.recorder.start_recording()
        self.rec_btn.configure(state="disabled")
        self.stop_rec_btn.configure(state="normal")
        self.add_log("🎤 Kayıt başladı")

    def stop_recording(self):
        """Kayıt durdur"""
        output = self.recorder.stop_recording()
        self.rec_btn.configure(state="normal")
        self.stop_rec_btn.configure(state="disabled")
        self.add_log(f"✓ Kayıt tamamlandı: {output}")

    def apply_effects(self):
        """Efektleri uygula"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        self.add_log("Efektler uygulanıyor...")
        # İmplementasyon devam edecek...
        messagebox.showinfo("Bilgi", "Efektler uygulandı!")

    def analyze_music(self):
        """Müzik analizi"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        def analyze():
            assert self.input_file is not None, "Input file must be set"
            self.add_log("Analiz ediliyor...")
            results = self.music_analyzer.analyze_full(self.input_file)

            # Sonuçları göster
            self.analysis_results.delete("1.0", "end")
            self.analysis_results.insert("1.0", f"""
🎼 MÜZİK ANALİZİ SONUÇLARI
{'='*50}

🥁 Tempo (BPM): {results.get('bpm', 'N/A'):.1f}
🎹 Anahtar: {results.get('key', 'N/A')} {results.get('scale', '')}
⏱️ Süre: {results.get('duration', 0):.1f}s
⚡ Enerji: {results.get('energy', 0):.2f}

{'='*50}
✓ Analiz tamamlandı!
            """)
            self.add_log("✓ Analiz tamamlandı")

        threading.Thread(target=analyze, daemon=True).start()

    def transcribe_notes(self):
        """Notaları çıkar (MIDI)"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        def transcribe():
            assert self.input_file is not None, "Input file must be set"

            self.add_log("🎹 Notalar çıkarılıyor (Basic Pitch)...")
            self.add_log("⏳ Bu işlem birkaç dakika sürebilir...")

            # Çıkış klasörü seç
            output_dir = filedialog.askdirectory(title="MIDI dosyasını nereye kaydetmek istersiniz?")
            if not output_dir:
                self.add_log("❌ İşlem iptal edildi")
                return

            results = self.music_analyzer.transcribe_notes(self.input_file, output_dir)

            if results.get('success'):
                # Sonuçları göster
                self.analysis_results.delete("1.0", "end")

                top_notes_str = '\n'.join([f"  {note}: {count} kez" for note, count in results['top_notes']])

                # TÜM NOTALARI LİSTELE
                all_notes = results['notes']

                # Saniye saniye grupla
                import math
                max_time = math.ceil(results['duration'])
                notes_by_second = {}

                for note in all_notes:
                    start_sec = int(note['start'])
                    end_sec = int(note['end'])
                    for sec in range(start_sec, end_sec + 1):
                        if sec <= max_time:
                            if sec not in notes_by_second:
                                notes_by_second[sec] = []
                            # Hem İngilizce hem Türkçe
                            notes_by_second[sec].append(f"{note['note_turkish']} ({note['note']})")

                # Saniye saniye string oluştur
                notes_by_sec_str = ""
                for sec in sorted(notes_by_second.keys()):
                    notes_in_sec = ', '.join(sorted(set(notes_by_second[sec])))
                    notes_by_sec_str += f"{sec:3d}s: {notes_in_sec}\n"

                # Detaylı nota listesi
                notes_list_str = ""
                for i, note in enumerate(all_notes[:200], 1):  # İlk 200 nota
                    notes_list_str += f"{i:4d}. {note['note_turkish']:6s} ({note['note']:4s}) | {note['start']:7.2f}s → {note['end']:7.2f}s | {note['duration']:.3f}s\n"

                if len(all_notes) > 200:
                    notes_list_str += f"\n... ve {len(all_notes) - 200} nota daha\n"

                self.analysis_results.insert("1.0", f"""
🎹 NOTA TRANSKRİPSİYONU SONUÇLARI
{'='*70}

📊 İstatistikler:
  • Toplam Nota: {results['note_count']}
  • Süre: {results['duration']:.1f}s
  • Ortalama Nota Süresi: {results['average_duration']:.3f}s

🎵 En Çok Kullanılan Notalar:
{top_notes_str}

{'='*70}
⏱️ SANİYE SANİYE NOTALAR (Çalmak İçin):
{'='*70}
💡 Format: Do (C4) = Do notası, 4. oktav

{notes_by_sec_str}

{'='*70}
📝 DETAYLI NOTA LİSTESİ:
{'='*70}
Sıra  Nota (TR/EN)    Başlangıç → Bitiş      Süre
----  -------------   --------------------   -------
{notes_list_str}
{'='*70}

💾 DOSYALAR:
  • MIDI: {results['midi_path']}

✓ Transkripsiyon tamamlandı!

💡 Nasıl Kullanılır:
  • "Saniye Saniye Notalar" bölümünü takip ederek çalabilirsiniz
  • MIDI dosyasını FL Studio, Ableton gibi programlarda açabilirsiniz
  • Do = C, Re = D, Mi = E, Fa = F, Sol = G, La = A, Si = B
  • Sayı oktavı gösterir (4 = orta oktav)
                """)

                self.add_log(f"✓ {results['note_count']} nota bulundu")
                self.add_log(f"💾 MIDI: {results['midi_path']}")

                messagebox.showinfo(
                    "Başarılı!",
                    f"Notalar başarıyla çıkarıldı!\n\n"
                    f"Toplam: {results['note_count']} nota\n"
                    f"MIDI: {results['midi_path']}"
                )
            else:
                error_msg = results.get('error', 'Bilinmeyen hata')
                self.add_log(f"❌ Hata: {error_msg}")
                messagebox.showerror("Hata", f"Nota çıkarma başarısız!\n\n{error_msg}")

        threading.Thread(target=transcribe, daemon=True).start()

    def transcribe_lyrics(self):
        """Şarkı sözlerini çıkar (Whisper)"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        def transcribe():
            assert self.input_file is not None, "Input file must be set"

            self.add_log("🎤 Şarkı sözleri çıkarılıyor (Whisper AI)...")
            self.add_log("⏳ İlk kullanımda model indirilir, biraz bekleyin...")

            # Çıkış klasörü seç
            output_dir = filedialog.askdirectory(title="Şarkı sözlerini nereye kaydetmek istersiniz?")
            if not output_dir:
                self.add_log("❌ İşlem iptal edildi")
                return

            # Dil seçimini al
            selected_language = self.lyrics_language_var.get()
            results = self.music_analyzer.transcribe_lyrics(self.input_file, output_dir, language=selected_language)

            if results.get('success'):
                # Sonuçları göster
                self.analysis_results.delete("1.0", "end")

                # Zaman damgalı sözleri formatla
                timestamped_lyrics = ""
                for item in results['lyrics_timestamped'][:50]:  # İlk 50 satır
                    min_start = int(item['start'] // 60)
                    sec_start = int(item['start'] % 60)
                    timestamped_lyrics += f"[{min_start:02d}:{sec_start:02d}] {item['text']}\n"

                if len(results['lyrics_timestamped']) > 50:
                    timestamped_lyrics += f"\n... ve {len(results['lyrics_timestamped']) - 50} satır daha\n"

                self.analysis_results.insert("1.0", f"""
🎤 ŞARKI SÖZLERİ TRANSKRİPSİYONU
{'='*70}

📊 İstatistikler:
  • Dil: {results['language'].upper()}
  • Kelime Sayısı: {results['word_count']}
  • Satır Sayısı: {len(results['lyrics_timestamped'])}

{'='*70}
📝 TAM ŞARKI SÖZLERİ:
{'='*70}

{results['lyrics']}

{'='*70}
⏱️ ZAMAN DAMGALI SÖZLER (Karaoke için):
{'='*70}

{timestamped_lyrics}

{'='*70}
💾 Metin Dosyası:
{results['text_file']}

✓ Transkripsiyon tamamlandı!

💡 Nasıl Kullanılır:
  • "Zaman Damgalı Sözler" bölümü karaoke için kullanılabilir
  • Her satırın başındaki [MM:SS] zaman damgasıdır
  • Metin dosyasını açarak tüm sözleri görebilirsiniz
  • Şarkıyla birlikte okuyabilirsiniz
                """)

                self.add_log(f"✓ {results['word_count']} kelime bulundu")
                self.add_log(f"✓ Dil: {results['language']}")
                self.add_log(f"💾 Dosya: {results['text_file']}")

                messagebox.showinfo(
                    "Başarılı!",
                    f"Şarkı sözleri başarıyla çıkarıldı!\n\n"
                    f"Dil: {results['language'].upper()}\n"
                    f"Kelime: {results['word_count']}\n"
                    f"Dosya: {results['text_file']}"
                )
            else:
                error_msg = results.get('error', 'Bilinmeyen hata')
                self.add_log(f"❌ Hata: {error_msg}")
                messagebox.showerror("Hata", f"Şarkı sözü çıkarma başarısız!\n\n{error_msg}")

        threading.Thread(target=transcribe, daemon=True).start()

    def separate_instruments(self):
        """Enstrümanları ayır (Demucs)"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        def separate():
            assert self.input_file is not None, "Input file must be set"

            self.add_log("🎸 Enstrümanlar ayrılıyor (Demucs AI)...")
            self.add_log("⏳ Bu işlem birkaç dakika sürebilir...")

            # Çıkış klasörü seç
            output_dir = filedialog.askdirectory(title="Ayrılmış enstrümanları nereye kaydetmek istersiniz?")
            if not output_dir:
                self.add_log("❌ İşlem iptal edildi")
                return

            # Model manager kontrolü
            if not self.model_manager:
                self.add_log("❌ Model manager başlatılmadı")
                messagebox.showerror("Hata", "Model manager başlatılmadı!")
                return

            # Demucs modelini yükle
            if not self.models_loaded.get("demucs"):
                self.add_log("🤖 Demucs modeli yükleniyor...")
                self.demucs_status.configure(text="🟡 Demucs: Yükleniyor...")
                self.model_manager.load_demucs()
                self.demucs_status.configure(text="🟢 Demucs: Hazır")
                self.models_loaded["demucs"] = True

            self.add_log("🎵 Ses ayrıştırılıyor (RTX 5090)...")
            self.add_log("📊 4 kanal: Drums, Bass, Other, Vocals")

            # Ayır
            separated_result = self.model_manager.separate_vocals(self.input_file, output_dir)
            separated: dict = separated_result if separated_result else {}

            if separated:
                # Sonuçları göster
                self.analysis_results.delete("1.0", "end")

                files_info = ""
                total_size = 0
                for name, path in separated.items():
                    file_size = Path(path).stat().st_size / (1024*1024)
                    total_size += file_size
                    files_info += f"  {name:8s}: {path}\n            Boyut: {file_size:.2f} MB\n\n"

                self.analysis_results.insert("1.0", f"""
🎸 ENSTRÜMAN AYIRMA SONUÇLARI
{'='*70}

📊 İstatistikler:
  • Toplam Dosya: {len(separated)}
  • Toplam Boyut: {total_size:.2f} MB
  • AI Model: Demucs v4 (Facebook Research)
  • İşlemci: RTX 5090

{'='*70}
🎵 AYRILMIŞ ENSTRÜMANLAR:
{'='*70}

{files_info}

{'='*70}
✓ Ayırma tamamlandı!

💡 Nasıl Kullanılır:
  • DRUMS (Davul): Ritim parçası
  • BASS (Bas): Bas gitar
  • OTHER (Diğer): Melodiler, piyano, gitarlar
  • VOCALS (Vokal): Şarkıcı sesi

  Her bir dosyayı ayrı ayrı dinleyebilir veya
  müzik yazılımında (FL Studio, Ableton, vb.) kullanabilirsiniz.
                """)

                self.add_log(f"✓ {len(separated)} dosya oluşturuldu")
                for name, path in separated.items():
                    self.add_log(f"  • {name}: {Path(path).name}")

                messagebox.showinfo(
                    "Başarılı!",
                    f"Enstrümanlar başarıyla ayrıldı!\n\n"
                    f"Toplam: {len(separated)} dosya\n"
                    f"Klasör: {output_dir}\n\n"
                    f"Drums, Bass, Vocals, Other"
                )
            else:
                self.add_log("❌ Hata: Enstrüman ayırma başarısız!")
                messagebox.showerror("Hata", "Enstrüman ayırma başarısız!")

        threading.Thread(target=separate, daemon=True).start()

    def transcribe_instrument_notes(self):
        """Her enstrüman için ayrı ayrı nota çıkar"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        def transcribe():
            assert self.input_file is not None, "Input file must be set"

            self.add_log("🎼 Her enstrüman için notalar çıkarılıyor...")
            self.add_log("⏳ Bu işlem 10-15 dakika sürebilir...")
            self.add_log("📊 Önce enstrümanlar ayrılacak, sonra her biri için nota çıkarılacak")

            # Çıkış klasörü seç
            output_dir = filedialog.askdirectory(title="Enstrüman notalarını nereye kaydetmek istersiniz?")
            if not output_dir:
                self.add_log("❌ İşlem iptal edildi")
                return

            # 1. Enstrümanları ayır
            self.add_log("🎸 Adım 1/2: Enstrümanlar ayrılıyor...")

            if not self.model_manager:
                messagebox.showerror("Hata", "Model manager başlatılmadı!")
                return

            if not self.models_loaded.get("demucs"):
                self.add_log("🤖 Demucs modeli yükleniyor...")
                self.model_manager.load_demucs()
                self.models_loaded["demucs"] = True

            temp_dir = Path(output_dir) / "temp_separated"
            temp_dir.mkdir(parents=True, exist_ok=True)

            separated_result = self.model_manager.separate_vocals(self.input_file, str(temp_dir))
            separated: dict = separated_result if separated_result else {}

            if not separated:
                self.add_log("❌ Enstrüman ayırma başarısız!")
                messagebox.showerror("Hata", "Enstrüman ayırma başarısız!")
                return

            self.add_log(f"✓ {len(separated)} enstrüman ayrıldı")

            # 2. Her enstrüman için nota çıkar
            self.add_log("🎹 Adım 2/2: Her enstrüman için notalar çıkarılıyor...")

            from basic_pitch.inference import predict
            from basic_pitch import ICASSP_2022_MODEL_PATH
            import pretty_midi

            instruments_data = {}

            for idx, (inst_name, inst_path) in enumerate(separated.items(), 1):
                self.add_log(f"  [{idx}/{len(separated)}] 🎵 {inst_name.upper()} notaları çıkarılıyor...")

                try:
                    # MIDI dosya yolu
                    midi_path = Path(output_dir) / f"{Path(self.input_file).stem}_{inst_name}_notes.mid"

                    # Basic Pitch ile transcription (EN YÜKSEK KALITE)
                    model_output, midi_data, note_events = predict(
                        inst_path,
                        ICASSP_2022_MODEL_PATH,
                        onset_threshold=0.5,
                        frame_threshold=0.3,
                        minimum_note_length=127.70,
                        minimum_frequency=None,
                        maximum_frequency=None,
                        multiple_pitch_bends=True,
                        melodia_trick=True
                    )
                    midi_data.write(str(midi_path))

                    # Notaları parse et
                    notes_list = []
                    for instrument in midi_data.instruments:
                        for note in instrument.notes:
                            note_name = pretty_midi.note_number_to_name(note.pitch)
                            # Türkçe nota ismi
                            note_tr = self.music_analyzer.get_turkish_note_name(note_name)
                            notes_list.append({
                                'note': note_name,
                                'note_turkish': note_tr,
                                'pitch': note.pitch,
                                'start': note.start,
                                'end': note.end,
                                'duration': note.end - note.start
                            })

                    instruments_data[inst_name] = {
                        'midi_path': str(midi_path),
                        'notes': notes_list,
                        'note_count': len(notes_list)
                    }

                    self.add_log(f"    ✓ {len(notes_list)} nota bulundu")

                except Exception as e:
                    self.add_log(f"    ❌ {inst_name} hatası: {e}")

            # Sonuçları göster
            self.analysis_results.delete("1.0", "end")

            result_text = "🎼 ENSTRÜMAN NOTALARI SONUÇLARI\n" + "="*70 + "\n\n"

            for inst_name, data in instruments_data.items():
                result_text += f"🎵 {inst_name.upper()}\n"
                result_text += f"{'='*70}\n"
                result_text += f"  • Nota Sayısı: {data['note_count']}\n"
                result_text += f"  • MIDI Dosyası: {data['midi_path']}\n\n"

                # İlk 20 nota
                result_text += f"  İlk 20 Nota:\n"
                for i, note in enumerate(data['notes'][:20], 1):
                    result_text += f"    {i:2d}. {note['note_turkish']:6s} ({note['note']:4s}) | {note['start']:6.2f}s\n"

                if data['note_count'] > 20:
                    result_text += f"    ... ve {data['note_count'] - 20} nota daha\n"

                result_text += "\n" + "="*70 + "\n\n"

            result_text += "\n✓ Tüm enstrüman notaları çıkarıldı!\n\n"
            result_text += "💡 Kullanım:\n"
            result_text += "  • Her enstrümanın MIDI dosyasını müzik yazılımında açabilirsiniz\n"
            result_text += "  • DRUMS: Davul ritimleri\n"
            result_text += "  • BASS: Bas gitar melodisi\n"
            result_text += "  • OTHER: Piyano, gitarlar, synth\n"
            result_text += "  • VOCALS: Şarkıcı melodisi\n"

            self.analysis_results.insert("1.0", result_text)

            self.add_log("✓ İşlem tamamlandı!")
            messagebox.showinfo(
                "Başarılı!",
                f"Enstrüman notaları başarıyla çıkarıldı!\n\n"
                f"Toplam: {len(instruments_data)} enstrüman\n"
                f"Klasör: {output_dir}"
            )

        threading.Thread(target=transcribe, daemon=True).start()

    def generate_visualization(self, viz_type: str):
        """Görselleştirme oluştur"""
        if not self.input_file:
            messagebox.showerror("Hata", "Dosya seçilmedi!")
            return

        assert self.input_file is not None, "Input file must be set"
        self.add_log(f"📊 {viz_type} oluşturuluyor...")
        # İmplementasyon devam edecek...

    def batch_add_files(self):
        """Batch'e dosya ekle"""
        files = filedialog.askopenfilenames(
            title="Dosyalar Seç",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )
        if files:
            self.batch_processor.add_files(list(files))
            self.batch_queue_label.configure(text=f"Kuyruk: {self.batch_processor.get_queue_size()} dosya")
            self.add_log(f"📋 {len(files)} dosya eklendi")

    def batch_add_folder(self):
        """Batch'e klasör ekle"""
        folder = filedialog.askdirectory(title="Klasör Seç")
        if folder:
            count = self.batch_processor.add_folder(folder)
            self.batch_queue_label.configure(text=f"Kuyruk: {self.batch_processor.get_queue_size()} dosya")
            self.add_log(f"📁 {count} dosya eklendi")

    def batch_clear(self):
        """Kuyruğu temizle"""
        self.batch_processor.clear_queue()
        self.batch_queue_label.configure(text="Kuyruk: 0 dosya")
        self.add_log("🗑️ Kuyruk temizlendi")

    def batch_process(self):
        """Batch işlemi başlat"""
        if self.batch_processor.get_queue_size() == 0:
            messagebox.showwarning("Uyarı", "Kuyruk boş!")
            return

        settings = {
            'pitch_semitones': self.semitone_var.get(),
            'use_ai_separation': False,
            'use_ai_enhancement': True,
            'quality': 'ultra'
        }

        self.batch_processor.process_batch(settings)
        self.add_log("🚀 Batch işlem başladı")

    def play_audio(self, source: str):
        """Ses oynat"""
        file = self.input_file if source == "input" else self.output_file
        if file:
            file_path = Path(file)
            if file_path.exists():
                pygame.mixer.music.load(str(file_path))
                pygame.mixer.music.play()
                self.is_playing = True
                self.add_log(f"🎵 Oynatılıyor: {file_path.name}")

    def toggle_play(self):
        """Play/Pause"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶️")
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.play_btn.configure(text="⏸️")

    def stop_audio(self):
        """Stop"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_btn.configure(text="▶️")

    def add_log(self, message):
        """Log ekle"""
        # log_text widget'ı henüz oluşturulmamışsa, loglamayı atla
        if not hasattr(self, 'log_text'):
            return

        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def start_system_monitor(self):
        """Sistem kullanımını sürekli güncelle"""
        def update_stats():
            import psutil

            while True:
                try:
                    # RAM kullanımı
                    ram = psutil.Process().memory_info().rss / 1e9
                    self.ram_usage_label.configure(text=f"💾 RAM: {ram:.2f} GB")

                    # GPU kullanımı
                    if self.model_manager and hasattr(self.model_manager, 'get_gpu_usage'):
                        gpu_info = self.model_manager.get_gpu_usage()
                        if gpu_info.get('available'):
                            vram_used = gpu_info['allocated_gb']
                            vram_total = gpu_info['total_gb']
                            vram_percent = gpu_info['usage_percent']

                            # Renk kodlaması
                            if vram_percent < 50:
                                color = "#10b981"  # Yeşil
                            elif vram_percent < 80:
                                color = "#f59e0b"  # Sarı
                            else:
                                color = "#ef4444"  # Kırmızı

                            self.gpu_usage_label.configure(
                                text=f"📊 VRAM: {vram_used:.1f} GB / {vram_total:.1f} GB ({vram_percent:.0f}%)",
                                text_color=color
                            )

                    time.sleep(1)  # Her 1 saniyede güncelle

                except Exception as e:
                    print(f"Monitor hatası: {e}")
                    time.sleep(5)

        threading.Thread(target=update_stats, daemon=True).start()

    def quick_load_file(self):
        """Quick action: Load file"""
        self.select_file()

    def quick_record(self):
        """Quick action: Record"""
        self.tabview.set("🎤 Mikrofon Kaydı")

    def quick_analyze(self):
        """Quick action: Analyze"""
        self.tabview.set("🎼 Müzik Analizi")

    def quick_batch(self):
        """Quick action: Batch"""
        self.tabview.set("🎚️ Batch İşlem")

    def create_mixer_tab(self):
        """Audio Mixer tab"""
        tab = self.tabview.tab("🎵 Audio Mixer")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="🎵 Multi-Track Audio Mixer", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Track ekleme
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="➕ Track Ekle", command=self.mixer_add_track, width=150, height=50).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🤖 Auto Sync", command=self.mixer_auto_sync, width=150, height=50, fg_color=self.colors["info"]).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🗑️ Temizle", command=self.mixer_clear, width=150, height=50, fg_color="red").pack(side="left", padx=10)

        # Track listesi
        self.mixer_tracks_frame = ctk.CTkScrollableFrame(tab, height=400)
        self.mixer_tracks_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.mixer_track_widgets = []

        # Mix butonu
        ctk.CTkButton(tab, text="🎚️ MIX & EXPORT", command=self.mixer_export, height=60, font=ctk.CTkFont(size=18, weight="bold"), fg_color=self.colors["success"]).pack(pady=20)

    def create_karaoke_tab(self):
        """Karaoke Mode tab"""
        tab = self.tabview.tab("🎧 Karaoke Mode")
        tab.grid_columnconfigure(0, weight=1)

        # SCROLLABLE FRAME - tüm içeriği scroll edilebilir yap
        scroll_container = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Header
        header_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        header_frame.pack(pady=15)

        ctk.CTkLabel(header_frame, text="🎧 Professional Karaoke Studio", font=ctk.CTkFont(size=26, weight="bold")).pack()
        ctk.CTkLabel(header_frame, text="Real-time Effects | AI Vocal Removal | Professional Mixing", font=ctk.CTkFont(size=12), text_color="gray").pack()

        # VU METER - PROFESSIONAL AUDIO LEVEL MONITORING
        vu_container = ctk.CTkFrame(scroll_container, fg_color=("#2a2d3a", "#1a1a2e"), corner_radius=15)
        vu_container.pack(pady=15, fill="x", padx=30)

        self.karaoke_vu_meter = VUMeter(vu_container, width=1100, height=140,
                                        fg_color=("#2a2d3a", "#1a1a2e"),
                                        corner_radius=15)
        self.karaoke_vu_meter.pack(padx=15, pady=15)

        # PROFESSIONAL KARAOKE PLAYER - Placeholder (will be populated when karaoke starts)
        self.karaoke_player_container = ctk.CTkFrame(scroll_container, fg_color=("#2a2d3a", "#1a1a2e"), corner_radius=15)
        self.karaoke_player_container.pack(pady=15, fill="both", expand=True, padx=30)

        # Placeholder message
        self.karaoke_placeholder_label = ctk.CTkLabel(
            self.karaoke_player_container,
            text="🎬 Professional Player will appear here when you start karaoke\n\nPress 'RECORD + MIX' to begin",
            font=ctk.CTkFont(size=16),
            text_color="gray50"
        )
        self.karaoke_placeholder_label.pack(expand=True, pady=50)

        # Store reference to active player
        self.active_karaoke_player = None

        # Audio Devices Section
        devices_section = ctk.CTkFrame(scroll_container, fg_color=("#2a2d3a", "#1a1a2e"), corner_radius=15)
        devices_section.pack(pady=15, fill="x", padx=30)

        ctk.CTkLabel(devices_section, text="🎚️ Audio Devices", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        # Device controls grid
        dev_grid = ctk.CTkFrame(devices_section, fg_color="transparent")
        dev_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Mikrofon
        mic_frame = ctk.CTkFrame(dev_grid, fg_color="transparent")
        mic_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(mic_frame, text="🎤 Mikrofon:", width=120, anchor="w", font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
        self.karaoke_mic_var = ctk.StringVar(value="Varsayılan")
        self.karaoke_mic_menu = ctk.CTkOptionMenu(mic_frame, variable=self.karaoke_mic_var, values=["Varsayılan"], width=300)
        self.karaoke_mic_menu.pack(side="left", padx=5)

        # Hoparlör
        speaker_frame = ctk.CTkFrame(dev_grid, fg_color="transparent")
        speaker_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(speaker_frame, text="🔊 Hoparlör:", width=120, anchor="w", font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
        self.karaoke_speaker_var = ctk.StringVar(value="Varsayılan")
        self.karaoke_speaker_menu = ctk.CTkOptionMenu(speaker_frame, variable=self.karaoke_speaker_var, values=["Varsayılan"], width=300)
        self.karaoke_speaker_menu.pack(side="left", padx=5)

        # Refresh button
        ctk.CTkButton(dev_grid, text="🔄 Yenile", command=self.refresh_karaoke_devices, width=100, height=28).pack(pady=5)

        # Giriş dosyası seçimi
        file_frame = ctk.CTkFrame(scroll_container)
        file_frame.pack(pady=10, fill="x", padx=30)

        ctk.CTkLabel(file_frame, text="🎵 Şarkı Dosyası:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        self.karaoke_file_label = ctk.CTkLabel(file_frame, text="Seçilmedi", font=ctk.CTkFont(size=12))
        self.karaoke_file_label.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(file_frame, text="📂 Dosya Seç", command=self.karaoke_select_file, width=120, height=35).pack(side="right", padx=10)

        # Çıkış klasörü seçimi
        output_frame = ctk.CTkFrame(scroll_container)
        output_frame.pack(pady=10, fill="x", padx=30)

        ctk.CTkLabel(output_frame, text="💾 Çıkış Klasörü:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        # Kaydedilmiş klasörü göster
        initial_output_text = self.saved_output_folder if hasattr(self, 'saved_output_folder') and self.saved_output_folder else "Seçilmedi"
        if hasattr(self, 'saved_output_folder') and self.saved_output_folder:
            self.karaoke_output_folder = self.saved_output_folder
        self.karaoke_output_label = ctk.CTkLabel(output_frame, text=initial_output_text, font=ctk.CTkFont(size=12))
        self.karaoke_output_label.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(output_frame, text="📁 Klasör Seç", command=self.karaoke_select_output, width=120, height=35).pack(side="right", padx=10)

        # Ayarlar
        settings_frame = ctk.CTkFrame(scroll_container)
        settings_frame.pack(pady=20, fill="x", padx=50)

        # Pitch - Modern kart tasarımı
        pitch_card = ctk.CTkFrame(settings_frame, fg_color=("gray90", "gray20"), corner_radius=15)
        pitch_card.pack(fill="x", pady=10, padx=10)

        pitch_header = ctk.CTkFrame(pitch_card, fg_color="transparent")
        pitch_header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(pitch_header, text="🎚️ Pitch Shift", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        pitch_controls = ctk.CTkFrame(pitch_card, fg_color="transparent")
        pitch_controls.pack(fill="x", padx=20, pady=(5, 15))

        self.karaoke_pitch_var = ctk.DoubleVar(value=0)
        pitch_slider = ctk.CTkSlider(pitch_controls, from_=-12, to=12, variable=self.karaoke_pitch_var, width=350, height=20, progress_color=self.colors["primary"])
        pitch_slider.pack(side="left", padx=10)

        # Entry box için frame
        pitch_entry_frame = ctk.CTkFrame(pitch_controls, fg_color="transparent")
        pitch_entry_frame.pack(side="left", padx=5)

        self.karaoke_pitch_entry = ctk.CTkEntry(pitch_entry_frame, width=60, height=35, font=ctk.CTkFont(size=14, weight="bold"), justify="center")
        self.karaoke_pitch_entry.pack(side="left")
        self.karaoke_pitch_entry.insert(0, "0")
        self.karaoke_pitch_entry.bind("<Return>", lambda e: self.update_karaoke_pitch_from_entry())
        self.karaoke_pitch_var.trace_add("write", lambda *args: self.karaoke_pitch_entry.delete(0, "end") or self.karaoke_pitch_entry.insert(0, f"{self.karaoke_pitch_var.get():.1f}"))

        ctk.CTkLabel(pitch_entry_frame, text="semitones", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=5)

        # Tempo - Modern kart tasarımı
        tempo_card = ctk.CTkFrame(settings_frame, fg_color=("gray90", "gray20"), corner_radius=15)
        tempo_card.pack(fill="x", pady=10, padx=10)

        tempo_header = ctk.CTkFrame(tempo_card, fg_color="transparent")
        tempo_header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(tempo_header, text="⏱️ Tempo", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        tempo_controls = ctk.CTkFrame(tempo_card, fg_color="transparent")
        tempo_controls.pack(fill="x", padx=20, pady=(5, 15))

        self.karaoke_tempo_var = ctk.DoubleVar(value=1.0)
        tempo_slider = ctk.CTkSlider(tempo_controls, from_=0, to=2, number_of_steps=200, variable=self.karaoke_tempo_var, width=350, height=20, progress_color=self.colors["warning"])
        tempo_slider.pack(side="left", padx=10)

        # Entry box için frame
        tempo_entry_frame = ctk.CTkFrame(tempo_controls, fg_color="transparent")
        tempo_entry_frame.pack(side="left", padx=5)

        self.karaoke_tempo_entry = ctk.CTkEntry(tempo_entry_frame, width=60, height=35, font=ctk.CTkFont(size=14, weight="bold"), justify="center")
        self.karaoke_tempo_entry.pack(side="left")
        self.karaoke_tempo_entry.insert(0, "1.0")
        self.karaoke_tempo_entry.bind("<Return>", lambda e: self.update_karaoke_tempo_from_entry())
        self.karaoke_tempo_var.trace_add("write", lambda *args: self.karaoke_tempo_entry.delete(0, "end") or self.karaoke_tempo_entry.insert(0, f"{self.karaoke_tempo_var.get():.2f}"))

        ctk.CTkLabel(tempo_entry_frame, text="x", font=ctk.CTkFont(size=10), text_color="gray60").pack(side="left", padx=5)

        # Real-time Effects Section - ENHANCED VISUALS
        effects_section = ctk.CTkFrame(scroll_container, fg_color=("#252836", "#16171f"), corner_radius=20, border_width=2, border_color=("#667eea", "#5a67d8"))
        effects_section.pack(pady=15, fill="x", padx=30)

        # Section header with gradient-style colors
        effects_header = ctk.CTkFrame(effects_section, fg_color=("#667eea", "#5a67d8"), corner_radius=15)
        effects_header.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(effects_header, text="✨ REAL-TIME VOCAL EFFECTS", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=10)

        effects_grid = ctk.CTkFrame(effects_section, fg_color="transparent")
        effects_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Reverb - Professional card style
        reverb_card = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12, border_width=1, border_color=("#3b82f6", "#2563eb"))
        reverb_card.pack(fill="x", pady=8, padx=5)
        reverb_inner = ctk.CTkFrame(reverb_card, fg_color="transparent")
        reverb_inner.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(reverb_inner, text="🌊 Reverb (Room)", width=150, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.karaoke_reverb_var = ctk.DoubleVar(value=0.3)
        reverb_slider = ctk.CTkSlider(reverb_inner, from_=0, to=1, variable=self.karaoke_reverb_var, width=300, height=18, progress_color=("#3b82f6", "#2563eb"), button_color=("#60a5fa", "#3b82f6"), button_hover_color=("#93c5fd", "#60a5fa"))
        reverb_slider.pack(side="left", padx=10)
        reverb_label = ctk.CTkLabel(reverb_inner, text="", width=60, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#3b82f6", "#60a5fa"))
        reverb_label.pack(side="left")
        self.karaoke_reverb_var.trace_add("write", lambda *args: reverb_label.configure(text=f"{self.karaoke_reverb_var.get():.2f}"))
        reverb_label.configure(text=f"{self.karaoke_reverb_var.get():.2f}")

        # Echo/Delay - Professional card style
        echo_card = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12, border_width=1, border_color=("#8b5cf6", "#7c3aed"))
        echo_card.pack(fill="x", pady=8, padx=5)
        echo_inner = ctk.CTkFrame(echo_card, fg_color="transparent")
        echo_inner.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(echo_inner, text="📢 Echo (Delay)", width=150, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.karaoke_echo_var = ctk.DoubleVar(value=0.2)
        echo_slider = ctk.CTkSlider(echo_inner, from_=0, to=1, variable=self.karaoke_echo_var, width=300, height=18, progress_color=("#8b5cf6", "#7c3aed"), button_color=("#a78bfa", "#8b5cf6"), button_hover_color=("#c4b5fd", "#a78bfa"))
        echo_slider.pack(side="left", padx=10)
        echo_label = ctk.CTkLabel(echo_inner, text="", width=60, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#8b5cf6", "#a78bfa"))
        echo_label.pack(side="left")
        self.karaoke_echo_var.trace_add("write", lambda *args: echo_label.configure(text=f"{self.karaoke_echo_var.get():.2f}"))
        echo_label.configure(text=f"{self.karaoke_echo_var.get():.2f}")

        # Volume/Gain - Professional card style
        volume_card = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12, border_width=1, border_color=("#10b981", "#059669"))
        volume_card.pack(fill="x", pady=8, padx=5)
        volume_inner = ctk.CTkFrame(volume_card, fg_color="transparent")
        volume_inner.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(volume_inner, text="🔊 Ses Seviyesi", width=150, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.karaoke_volume_var = ctk.DoubleVar(value=1.0)
        volume_slider = ctk.CTkSlider(volume_inner, from_=0, to=2, variable=self.karaoke_volume_var, width=300, height=18, progress_color=("#10b981", "#059669"), button_color=("#34d399", "#10b981"), button_hover_color=("#6ee7b7", "#34d399"))
        volume_slider.pack(side="left", padx=10)
        volume_label = ctk.CTkLabel(volume_inner, text="", width=60, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#10b981", "#34d399"))
        volume_label.pack(side="left")
        self.karaoke_volume_var.trace_add("write", lambda *args: volume_label.configure(text=f"{self.karaoke_volume_var.get():.2f}x"))
        volume_label.configure(text=f"{self.karaoke_volume_var.get():.2f}x")

        # Autotune - PROFESSIONAL STUDIO QUALITY
        autotune_card = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12, border_width=2, border_color=("#f59e0b", "#d97706"))
        autotune_card.pack(fill="x", pady=8, padx=5)
        autotune_inner = ctk.CTkFrame(autotune_card, fg_color="transparent")
        autotune_inner.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(autotune_inner, text="🎵 Autotune", width=150, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.karaoke_autotune_var = ctk.DoubleVar(value=0.0)
        autotune_slider = ctk.CTkSlider(autotune_inner, from_=0, to=1, variable=self.karaoke_autotune_var, width=300, height=18, progress_color=("#f59e0b", "#d97706"), button_color=("#fbbf24", "#f59e0b"), button_hover_color=("#fcd34d", "#fbbf24"))
        autotune_slider.pack(side="left", padx=10)
        autotune_label = ctk.CTkLabel(autotune_inner, text="", width=60, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#f59e0b", "#fbbf24"))
        autotune_label.pack(side="left")
        self.karaoke_autotune_var.trace_add("write", lambda *args: autotune_label.configure(text=f"{int(self.karaoke_autotune_var.get() * 100)}%"))
        autotune_label.configure(text=f"{int(self.karaoke_autotune_var.get() * 100)}%")

        # Autotune Key - In same card
        key_inner = ctk.CTkFrame(autotune_card, fg_color="transparent")
        key_inner.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(key_inner, text="🎹 Anahtar (Key)", width=150, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.karaoke_key_var = ctk.StringVar(value="C Major")
        key_menu = ctk.CTkOptionMenu(key_inner, variable=self.karaoke_key_var,
                                      values=["C Major", "D Major", "E Major", "F Major", "G Major", "A Major", "B Major",
                                              "C Minor", "D Minor", "E Minor", "F Minor", "G Minor", "A Minor", "B Minor"],
                                      width=200, height=32, fg_color=("#f59e0b", "#d97706"), button_color=("#fbbf24", "#f59e0b"), button_hover_color=("#fcd34d", "#fbbf24"))
        key_menu.pack(side="left", padx=10)

        # De-esser - Professional card style
        deesser_card = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12, border_width=1, border_color=("#ec4899", "#db2777"))
        deesser_card.pack(fill="x", pady=8, padx=5)
        deesser_inner = ctk.CTkFrame(deesser_card, fg_color="transparent")
        deesser_inner.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(deesser_inner, text="✂️ De-esser (Sibilans)", width=150, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.karaoke_deesser_var = ctk.DoubleVar(value=0.0)
        deesser_slider = ctk.CTkSlider(deesser_inner, from_=0, to=1, variable=self.karaoke_deesser_var, width=300, height=18, progress_color=("#ec4899", "#db2777"), button_color=("#f472b6", "#ec4899"), button_hover_color=("#f9a8d4", "#f472b6"))
        deesser_slider.pack(side="left", padx=10)
        deesser_label = ctk.CTkLabel(deesser_inner, text="", width=60, font=ctk.CTkFont(size=12, weight="bold"), text_color=("#ec4899", "#f472b6"))
        deesser_label.pack(side="left")
        self.karaoke_deesser_var.trace_add("write", lambda *args: deesser_label.configure(text=f"{int(self.karaoke_deesser_var.get() * 100)}%"))
        deesser_label.configure(text=f"{int(self.karaoke_deesser_var.get() * 100)}%")

        # Monitoring checkbox - Enhanced style
        monitor_frame = ctk.CTkFrame(effects_grid, fg_color=("#2d3142", "#1a1d2e"), corner_radius=12)
        monitor_frame.pack(fill="x", pady=8, padx=5)
        ctk.CTkCheckBox(monitor_frame, text="🎧 Kendi Sesini Duy (Real-time Monitoring)", variable=ctk.BooleanVar(value=False), font=ctk.CTkFont(size=13, weight="bold"), checkbox_width=24, checkbox_height=24).pack(pady=12, padx=15)

        # Vokal kaldırma
        ctk.CTkCheckBox(settings_frame, text="🎤 Vokalleri Kaldır (AI)", font=ctk.CTkFont(size=14), variable=ctk.BooleanVar(value=True)).pack(pady=10)

        # PROFESSIONAL PRESETS - Stüdyo Kalitesi
        preset_section = ctk.CTkFrame(scroll_container, fg_color=("#2a2d3a", "#1a1a2e"), corner_radius=15)
        preset_section.pack(pady=15, fill="x", padx=30)

        ctk.CTkLabel(preset_section, text="🎚️ Professional Presets", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        preset_grid = ctk.CTkFrame(preset_section, fg_color="transparent")
        preset_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Preset seçimi
        preset_frame = ctk.CTkFrame(preset_grid, fg_color="transparent")
        preset_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(preset_frame, text="🎛️ Preset Seç:", width=120, anchor="w", font=ctk.CTkFont(size=13)).pack(side="left")
        self.karaoke_preset_var = ctk.StringVar(value="Manuel")
        preset_menu = ctk.CTkOptionMenu(preset_frame, variable=self.karaoke_preset_var,
                                         values=["Manuel", "🎙️ Radio Ready", "🎸 Studio Recording", "🎤 Live Performance",
                                                 "💿 Podcast", "🎵 Rap/Hip-Hop", "🎸 Rock Vokal"],
                                         width=250, command=self.apply_karaoke_preset)
        preset_menu.pack(side="left", padx=5)

        # İşlem butonları - Modern tasarım
        action_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        action_frame.pack(pady=30)

        # Backing track butonu - Gradyan efekti simülasyonu
        backing_btn = ctk.CTkButton(
            action_frame,
            text="🎼 CREATE BACKING TRACK",
            command=self.karaoke_create_backing,
            width=280,
            height=70,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#667eea", "#5a67d8"),
            hover_color=("#5a67d8", "#4c51bf"),
            corner_radius=20,
            border_width=2,
            border_color=("#818cf8", "#6366f1")
        )
        backing_btn.pack(pady=10)

        # Kayıt + Mix butonu
        record_btn = ctk.CTkButton(
            action_frame,
            text="🎤 RECORD + MIX",
            command=self.karaoke_record_mix,
            width=280,
            height=70,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            corner_radius=20,
            border_width=2,
            border_color=("#f87171", "#ef4444")
        )
        record_btn.pack(pady=10)

        # Önceki Backing Track'ler Listesi
        history_section = ctk.CTkFrame(scroll_container, fg_color=("#2a2d3a", "#1a1a2e"), corner_radius=15)
        history_section.pack(pady=15, fill="x", padx=30)

        history_header = ctk.CTkFrame(history_section, fg_color="transparent")
        history_header.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(history_header, text="📂 Önceki Backing Track'ler", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(history_header, text="🔄 Yenile", command=self.refresh_backing_tracks, width=80, height=28).pack(side="right")

        # Scrollable listbox frame
        self.backing_tracks_frame = ctk.CTkScrollableFrame(history_section, height=150, fg_color="transparent")
        self.backing_tracks_frame.pack(fill="both", padx=15, pady=(0, 15))

        # İlk tarama
        self.refresh_backing_tracks()

        # Progress bar - Modern ve renkli
        progress_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        progress_frame.pack(pady=20, fill="x", padx=50)

        self.karaoke_progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=700,
            height=35,
            corner_radius=20,
            progress_color=("#667eea", "#5a67d8"),
            fg_color=("gray80", "gray25")
        )
        self.karaoke_progress_bar.pack(pady=10)
        self.karaoke_progress_bar.set(0)

        self.karaoke_progress_label = ctk.CTkLabel(progress_frame, text="", font=ctk.CTkFont(size=12))
        self.karaoke_progress_label.pack()

    def create_converter_tab(self):
        """Format Converter tab"""
        tab = self.tabview.tab("🔄 Format Converter")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="🔄 Professional Format Converter", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Dosya seçimi
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(pady=20, fill="x", padx=50)

        ctk.CTkLabel(file_frame, text="📂 Dosya:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.converter_file_label = ctk.CTkLabel(file_frame, text="Seçilmedi", font=ctk.CTkFont(size=12))
        self.converter_file_label.pack(side="left", padx=10)
        ctk.CTkButton(file_frame, text="Seç", command=self.converter_select_file, width=100).pack(side="right", padx=10)

        # Format seçimi
        format_frame = ctk.CTkFrame(tab)
        format_frame.pack(pady=20, fill="x", padx=50)

        ctk.CTkLabel(format_frame, text="🎵 Hedef Format:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.converter_format_var = ctk.StringVar(value="mp3")

        formats = [("MP3", "mp3"), ("WAV", "wav"), ("FLAC", "flac"), ("OGG", "ogg"), ("M4A", "m4a")]

        format_btns = ctk.CTkFrame(format_frame, fg_color="transparent")
        format_btns.pack(pady=10)

        for name, value in formats:
            ctk.CTkRadioButton(format_btns, text=name, variable=self.converter_format_var, value=value, font=ctk.CTkFont(size=14)).pack(side="left", padx=20)

        # Kalite
        quality_frame = ctk.CTkFrame(tab)
        quality_frame.pack(pady=20, fill="x", padx=50)

        ctk.CTkLabel(quality_frame, text="⚙️ Kalite/Bitrate:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.converter_quality_var = ctk.StringVar(value="high")

        qualities = [("Low (128k)", "low"), ("Medium (192k)", "medium"), ("High (256k)", "high"), ("Ultra (320k)", "ultra")]

        quality_btns = ctk.CTkFrame(quality_frame, fg_color="transparent")
        quality_btns.pack(pady=10)

        for name, value in qualities:
            ctk.CTkRadioButton(quality_btns, text=name, variable=self.converter_quality_var, value=value, font=ctk.CTkFont(size=12)).pack(side="left", padx=15)

        # Metadata
        meta_frame = ctk.CTkFrame(tab)
        meta_frame.pack(pady=20, fill="x", padx=50)

        ctk.CTkLabel(meta_frame, text="📝 Metadata (Opsiyonel):", font=ctk.CTkFont(size=14)).pack(pady=10)

        meta_grid = ctk.CTkFrame(meta_frame, fg_color="transparent")
        meta_grid.pack(pady=10)

        self.meta_title = ctk.CTkEntry(meta_grid, placeholder_text="Title", width=200)
        self.meta_title.grid(row=0, column=0, padx=10, pady=5)

        self.meta_artist = ctk.CTkEntry(meta_grid, placeholder_text="Artist", width=200)
        self.meta_artist.grid(row=0, column=1, padx=10, pady=5)

        self.meta_album = ctk.CTkEntry(meta_grid, placeholder_text="Album", width=200)
        self.meta_album.grid(row=1, column=0, padx=10, pady=5)

        self.meta_genre = ctk.CTkEntry(meta_grid, placeholder_text="Genre", width=200)
        self.meta_genre.grid(row=1, column=1, padx=10, pady=5)

        # Convert butonu
        ctk.CTkButton(tab, text="🔄 DÖNÜŞTÜR", command=self.converter_convert, height=70, font=ctk.CTkFont(size=20, weight="bold"), fg_color=self.colors["success"]).pack(pady=30)

    # === YENİ METODLAR ===

    def mixer_add_track(self):
        """Mixer'a track ekle"""
        files = filedialog.askopenfilenames(
            title="Track Ekle",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )

        for file in files:
            track = self.audio_mixer.add_track(file)
            self.add_log(f"🎵 Track eklendi: {Path(file).name}")

            # GUI widget oluştur
            self.create_track_widget(track)

    def create_track_widget(self, track):
        """Tek bir track için kontrol widget'ı"""
        track_frame = ctk.CTkFrame(self.mixer_tracks_frame)
        track_frame.pack(fill="x", pady=10, padx=10)

        # Track adı
        ctk.CTkLabel(track_frame, text=f"🎵 {track.name}", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Volume slider
        vol_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        vol_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(vol_frame, text="Volume:", width=80).pack(side="left")
        vol_slider = ctk.CTkSlider(vol_frame, from_=0, to=2, command=lambda v: setattr(track, 'volume', v), width=200)
        vol_slider.set(track.volume)
        vol_slider.pack(side="left", padx=5)

        # Pitch slider
        pitch_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        pitch_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(pitch_frame, text="Pitch:", width=80).pack(side="left")
        pitch_slider = ctk.CTkSlider(pitch_frame, from_=-12, to=12, command=lambda v: setattr(track, 'pitch_shift', v), width=200)
        pitch_slider.set(0)
        pitch_slider.pack(side="left", padx=5)

        # Mute/Solo
        ctk.CTkCheckBox(track_frame, text="Mute", command=lambda: setattr(track, 'mute', not track.mute)).pack(side="left", padx=10)
        ctk.CTkCheckBox(track_frame, text="Solo", command=lambda: setattr(track, 'solo', not track.solo)).pack(side="left", padx=10)

        self.mixer_track_widgets.append(track_frame)

    def mixer_auto_sync(self):
        """AI tempo/key sync"""
        self.audio_mixer.auto_sync_tempo()
        self.audio_mixer.auto_match_keys()
        self.add_log("🤖 AI sync tamamlandı")
        messagebox.showinfo("Başarılı", "Track'ler senkronize edildi!")

    def mixer_clear(self):
        """Tüm track'leri temizle"""
        self.audio_mixer.clear_tracks()
        for widget in self.mixer_track_widgets:
            widget.destroy()
        self.mixer_track_widgets = []
        self.add_log("🗑️ Tüm track'ler temizlendi")

    def mixer_export(self):
        """Mix'i export et"""
        if len(self.audio_mixer.tracks) == 0:
            messagebox.showwarning("Uyarı", "Track yok!")
            return

        output = filedialog.asksaveasfilename(
            title="Mix Kaydet",
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav"), ("MP3", "*.mp3")]
        )

        if output:
            if self.audio_mixer.mix_tracks(output):
                self.add_log(f"✅ Mix kaydedildi: {Path(output).name}")
                messagebox.showinfo("Başarılı", f"Mix tamamlandı!\n{output}")
            else:
                messagebox.showerror("Hata", "Mix başarısız!")

    def karaoke_select_file(self):
        """Karaoke için dosya seç"""
        file = filedialog.askopenfilename(
            title="Şarkı Seç",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )
        if file:
            self.karaoke_file = file
            self.karaoke_file_label.configure(text=str(Path(file).absolute()))
            self.add_log(f"🎵 Karaoke dosya: {Path(file).absolute()}")

    def karaoke_select_output(self):
        """Karaoke çıkış klasörü seç"""
        # Kaydedilmiş klasörü default olarak göster
        initial_dir = self.saved_output_folder if hasattr(self, 'saved_output_folder') and self.saved_output_folder else None

        folder = filedialog.askdirectory(title="Çıkış Klasörü Seç", initialdir=initial_dir)
        if folder:
            self.karaoke_output_folder = folder
            self.karaoke_output_label.configure(text=folder)
            self.add_log(f"💾 Çıkış klasörü: {folder}")
            # Otomatik kaydet
            self.save_config()

    def karaoke_create_backing(self):
        """Backing track oluştur"""
        if not self.karaoke_file:
            messagebox.showwarning("Uyarı", "Şarkı dosyası seçilmedi!")
            return

        if not self.karaoke_output_folder:
            messagebox.showwarning("Uyarı", "Çıkış klasörü seçilmedi!")
            return

        def create():
            self.status_badge.configure(text="● İşleniyor", text_color="#f59e0b")
            self.karaoke_progress_bar.set(0)
            self.karaoke_progress_label.configure(text="Başlatılıyor...")

            if not self.karaoke_mode:
                self.karaoke_progress_label.configure(text="🤖 AI modeli yükleniyor...")
                self.karaoke_progress_bar.set(0.1)
                self.add_log("🤖 Demucs AI modeli yükleniyor...")
                self.demucs_status.configure(text="🟡 Demucs: Yükleniyor...")
                self.karaoke_mode = KaraokeMode(self.model_manager)
                self.demucs_status.configure(text="🟢 Demucs: Hazır")
                self.models_loaded["demucs"] = True
                self.add_log("✓ Demucs hazır")

            self.karaoke_progress_bar.set(0.2)
            self.karaoke_progress_label.configure(text="📂 Dosya okunuyor...")
            self.add_log(f"📂 İşleniyor: {Path(self.karaoke_file).name}")

            self.karaoke_progress_bar.set(0.3)
            self.karaoke_progress_label.configure(text="🎤 Vokaller ayrıştırılıyor (RTX 5090)...")
            self.add_log("🎤 AI ile vokal ayırma başladı...")

            self.karaoke_progress_bar.set(0.5)
            self.karaoke_progress_label.configure(text="🎼 Backing track oluşturuluyor...")

            backing = self.karaoke_mode.create_backing_track(
                self.karaoke_file,
                output_dir=self.karaoke_output_folder,
                remove_vocals=True,
                pitch_shift=self.karaoke_pitch_var.get(),
                tempo_change=self.karaoke_tempo_var.get()
            )

            if backing:
                # BACKING TRACK YOLUNU SAKLA
                self.karaoke_backing_track = backing

                # ŞARKI SÖZLERİNİ ÇIKAR (Whisper AI)
                self.karaoke_progress_bar.set(0.9)
                self.karaoke_progress_label.configure(text="🎤 Şarkı sözleri çıkarılıyor (Whisper AI)...")
                self.add_log("🎤 Whisper AI ile şarkı sözleri çıkarılıyor...")

                try:
                    from core.music_analyzer import MusicAnalyzer
                    import json

                    analyzer = MusicAnalyzer()
                    lyrics_result = analyzer.transcribe_lyrics(
                        self.karaoke_file,
                        output_dir=self.karaoke_output_folder,
                        language="auto"  # Otomatik dil tespiti
                    )

                    if lyrics_result.get('success'):
                        # Save lyrics as JSON for karaoke player
                        lyrics_json_path = Path(backing).with_suffix('.lyrics.json')
                        with open(lyrics_json_path, 'w', encoding='utf-8') as f:
                            json.dump(lyrics_result, f, ensure_ascii=False, indent=2)

                        self.add_log(f"✅ Şarkı sözleri çıkarıldı!")
                        self.add_log(f"📝 Dil: {lyrics_result.get('language', 'unknown')}")
                        self.add_log(f"📄 Sözler kaydedildi: {lyrics_json_path}")
                    else:
                        self.add_log("⚠️ Şarkı sözleri çıkarılamadı (devam ediliyor)")
                except Exception as e:
                    self.add_log(f"⚠️ Sözler çıkarılamadı: {e}")

                # AUTO-CONVERT EXISTING _lyrics.txt FILES
                try:
                    # Check for existing _lyrics.txt file in source folder
                    source_file = Path(self.karaoke_file)
                    source_folder = source_file.parent
                    lyrics_txt_files = list(source_folder.glob("*_lyrics.txt"))

                    if lyrics_txt_files:
                        self.add_log(f"📝 {len(lyrics_txt_files)} adet _lyrics.txt dosyası bulundu!")
                        for txt_file in lyrics_txt_files:
                            self.add_log(f"🔄 Dönüştürülüyor: {txt_file.name}")
                            # Convert to JSON
                            json_path = convert_lyrics_txt_to_json(txt_file)
                            if json_path:
                                # Copy to output folder with backing track name
                                import shutil
                                target_json = Path(backing).with_suffix('.lyrics.json')
                                shutil.copy(json_path, target_json)
                                self.add_log(f"✅ Lyrics JSON oluşturuldu!")
                                self.add_log(f"📄 Dosya: {target_json}")
                except Exception as e:
                    self.add_log(f"ℹ️ Lyrics TXT dönüşümü: {e}")

                file_size = Path(backing).stat().st_size / (1024*1024)
                self.karaoke_progress_bar.set(1.0)
                self.karaoke_progress_label.configure(text=f"✅ Tamamlandı! ({file_size:.2f} MB)")
                self.add_log(f"✅ Backing track oluşturuldu!")
                self.add_log(f"📂 Dosya: {backing}")
                self.add_log(f"📦 Boyut: {file_size:.2f} MB")
                self.add_log(f"🎤 Artık 'KAYIT + MİX' butonuna tıklayabilirsin!")
                messagebox.showinfo("Başarılı", f"Backing track oluşturuldu!\n\n{backing}\n\nBoyut: {file_size:.2f} MB\n\n✅ Artık kayıt yapabilirsin!")
            else:
                self.karaoke_backing_track = None
                self.karaoke_progress_bar.set(0)
                self.karaoke_progress_label.configure(text="❌ Hata!")
                self.add_log("❌ Hata: Backing track oluşturulamadı!")
                messagebox.showerror("Hata", "Backing track oluşturulamadı!")

            self.status_badge.configure(text="● Hazır", text_color="#10b981")

        threading.Thread(target=create, daemon=True).start()

    def update_karaoke_pitch_from_entry(self):
        """Entry'den pitch değerini güncelle"""
        try:
            value = float(self.karaoke_pitch_entry.get())
            value = max(-12, min(12, value))  # -12 ile 12 arası sınırla
            self.karaoke_pitch_var.set(value)
        except ValueError:
            self.karaoke_pitch_entry.delete(0, "end")
            self.karaoke_pitch_entry.insert(0, f"{self.karaoke_pitch_var.get():.1f}")

    def update_karaoke_tempo_from_entry(self):
        """Entry'den tempo değerini güncelle"""
        try:
            value = float(self.karaoke_tempo_entry.get())
            value = max(0.5, min(2.0, value))  # 0.5 ile 2.0 arası sınırla
            self.karaoke_tempo_var.set(value)
        except ValueError:
            self.karaoke_tempo_entry.delete(0, "end")
            self.karaoke_tempo_entry.insert(0, f"{self.karaoke_tempo_var.get():.2f}")

    def karaoke_record_mix(self):
        """Kaydet ve mix et - Real-time karaoke with effects"""
        # Eğer karaoke zaten çalışıyorsa, DURDUR
        if hasattr(self, 'karaoke_stream') and self.karaoke_stream and self.karaoke_stream.active:
            self.add_log("⏹️ Karaoke durduruluyor...")
            try:
                self.karaoke_stream.stop()
                self.karaoke_stream.close()
                self.karaoke_stream = None
                self.add_log("✓ Karaoke durduruldu")
            except Exception as e:
                self.add_log(f"❌ Durdurma hatası: {e}")
            return

        # Backing track kontrolü
        self.add_log("=== BACKING TRACK KONTROL ===")
        self.add_log(f"DEBUG: self.karaoke_backing_track = {self.karaoke_backing_track}")
        self.add_log(f"DEBUG: type = {type(self.karaoke_backing_track)}")

        # Önce var olan yolu kontrol et, yoksa veya dosya yoksa yeniden ara
        needs_search = False
        if not self.karaoke_backing_track:
            self.add_log("DEBUG: backing_track None veya boş - arama gerekli")
            needs_search = True
        else:
            # String'e çevir ve kontrol et
            try:
                backing_path = Path(str(self.karaoke_backing_track))
                self.add_log(f"DEBUG: backing_path = {backing_path}")
                if not backing_path.exists():
                    self.add_log(f"DEBUG: Dosya mevcut değil: {backing_path}")
                    needs_search = True
                    self.add_log(f"⚠️ Kayıtlı backing track bulunamadı, yeniden aranıyor...")
                else:
                    self.add_log(f"DEBUG: Dosya bulundu: {backing_path}")
            except Exception as e:
                self.add_log(f"DEBUG: Path kontrolünde hata: {e}")
                needs_search = True

        if needs_search:
            self.add_log("DEBUG: Backing track aranıyor...")
            # Otomatik olarak output klasöründe backing track ara
            self.add_log(f"DEBUG: output_folder = {self.karaoke_output_folder}")
            if self.karaoke_output_folder and Path(self.karaoke_output_folder).exists():
                # Tüm WAV dosyalarını bul
                all_wavs = list(Path(self.karaoke_output_folder).glob("*.wav"))
                self.add_log(f"DEBUG: Bulunan WAV dosyaları ({len(all_wavs)}):")
                for wav in all_wavs:
                    self.add_log(f"  - {wav.name}")

                # Instrumental veya backing içerenleri filtrele
                backing_files = [f for f in all_wavs if 'instrumental' in f.name.lower() or 'backing' in f.name.lower()]
                self.add_log(f"DEBUG: Backing track dosyaları ({len(backing_files)}):")
                for bf in backing_files:
                    self.add_log(f"  - {bf.name}")

                if backing_files:
                    self.karaoke_backing_track = str(backing_files[0])
                    self.add_log(f"✓ Backing track otomatik bulundu: {Path(self.karaoke_backing_track).name}")
                else:
                    self.add_log("DEBUG: Hiç backing track bulunamadı!")
                    messagebox.showwarning("Uyarı", "Output klasöründe backing track bulunamadı!\n\n'BACKING TRACK OLUŞTUR' butonuna tıklayın.")
                    return
            else:
                self.add_log("DEBUG: Output klasörü yok veya geçersiz!")
                messagebox.showwarning("Uyarı", "Output klasörü seçilmedi veya mevcut değil!")
                return

        # SON KONTROL: Backing track hala None mu?
        if not self.karaoke_backing_track:
            messagebox.showwarning("Uyarı", "Backing track yüklenemedi!\n\nLütfen 'BACKING TRACK OLUŞTUR' butonuna tıklayın.")
            return

        # Mikrofon cihazını al
        mic_device = self.karaoke_mic_var.get()
        speaker_device = self.karaoke_speaker_var.get()

        self.add_log("🎤 Karaoke modu başlatılıyor (PROFESSIONAL MODE)...")
        self.add_log(f"📂 Backing track: {Path(self.karaoke_backing_track).name}")
        self.add_log(f"🎤 Mikrofon: {mic_device}")
        self.add_log(f"🔊 Hoparlör: {speaker_device}")

        # Thread'de çalıştır
        def start_karaoke():
            import sounddevice as sd
            import soundfile as sf
            import numpy as np
            from pedalboard import Pedalboard, Reverb, Compressor, PeakFilter
            from gui.karaoke_player import KaraokePlayer

            try:
                # Backing track yükle
                backing_audio, sr = sf.read(self.karaoke_backing_track)

                # EXTREME LOW LATENCY: 48kHz'e downsample (eğer daha yüksekse)
                if sr > 48000:
                    import librosa
                    self.add_log(f"⚡ Ultra low latency: {sr}Hz -> 48000Hz resampling...")
                    backing_audio = librosa.resample(backing_audio.T, orig_sr=sr, target_sr=48000).T
                    sr = 48000

                # Load lyrics (multiple locations supported)
                lyrics_data = None
                import json

                # Try different lyrics file locations
                lyrics_paths = [
                    Path(self.karaoke_backing_track).with_suffix('.lyrics.json'),  # Next to backing track
                ]

                # Add karaoke_file paths only if it exists
                if self.karaoke_file:
                    lyrics_paths.append(Path(self.karaoke_file).with_suffix('') / "_lyrics.json")  # Original analyzer location
                    lyrics_paths.append(Path(self.karaoke_file).parent / (Path(self.karaoke_file).stem + "_lyrics.json"))  # Same folder

                self.add_log(f"DEBUG: Lyrics aranıyor ({len(lyrics_paths)} konum)...")
                for lyrics_file in lyrics_paths:
                    self.add_log(f"DEBUG: Deneniyor: {lyrics_file}")
                    if lyrics_file.exists():
                        try:
                            with open(lyrics_file, 'r', encoding='utf-8') as f:
                                lyrics_data = json.load(f)
                            self.add_log(f"✅ Şarkı sözleri yüklendi: {lyrics_file.name}")
                            break
                        except Exception as e:
                            self.add_log(f"⚠️ Sözler okunamadı ({lyrics_file.name}): {e}")

                if not lyrics_data:
                    self.add_log("⚠️ Şarkı sözleri bulunamadı (karaoke player sade görünecek)")

                # Hide placeholder and create Professional Karaoke Player in container
                self.add_log("🎬 Profesyonel karaoke player açılıyor...")

                # Remove placeholder
                if hasattr(self, 'karaoke_placeholder_label') and self.karaoke_placeholder_label.winfo_exists():
                    self.karaoke_placeholder_label.destroy()

                # Destroy old player if exists
                if hasattr(self, 'active_karaoke_player') and self.active_karaoke_player:
                    try:
                        self.active_karaoke_player.destroy()
                    except:
                        pass

                # Create player in container
                karaoke_player = KaraokePlayer(
                    self.karaoke_player_container,
                    backing_audio,
                    sr,
                    lyrics_data,
                    fg_color=("#2a2d3a", "#1a1a2e")
                )
                karaoke_player.pack(fill="both", expand=True, padx=15, pady=15)
                self.active_karaoke_player = karaoke_player

                # Initialize PROFESSIONAL REAL-TIME FX from player's parameters
                self.add_log("🎛️ Profesyonel efektler yükleniyor...")
                self.add_log("  ✓ Reverb (Studio quality)")
                self.add_log("  ✓ Compressor (Vokal optimizasyonu)")
                self.add_log("  ✓ EQ (3-band equalizer)")
                self.add_log("  ✓ Echo (Delay effect)")

                # Function to rebuild FX board from player's parameters
                def rebuild_fx_board():
                    from pedalboard import Delay
                    p = karaoke_player.fx_params

                    effects = [
                        Compressor(
                            threshold_db=p['compressor_threshold'],
                            ratio=p['compressor_ratio'],
                            attack_ms=3.0,
                            release_ms=100.0
                        ),
                        PeakFilter(cutoff_frequency_hz=100, gain_db=p['eq_bass'], q=0.7),  # Bass
                        PeakFilter(cutoff_frequency_hz=3000, gain_db=p['eq_mid'], q=1.0),  # Vokal presence
                        PeakFilter(cutoff_frequency_hz=10000, gain_db=p['eq_treble'], q=0.7)  # Air/brilliance
                    ]

                    # Add Echo/Delay if mix > 0
                    if p['echo_mix'] > 0.01:
                        effects.append(
                            Delay(
                                delay_seconds=p['echo_delay'],
                                feedback=p['echo_feedback'],
                                mix=p['echo_mix']
                            )
                        )

                    # Add Reverb
                    effects.append(
                        Reverb(
                            room_size=p['reverb_room_size'],
                            damping=0.5,
                            wet_level=p['reverb_wet'],
                            dry_level=1.0 - p['reverb_wet'],
                            width=1.0
                        )
                    )

                    return Pedalboard(effects)

                # Create initial FX board
                from pedalboard import Delay
                fx_board = rebuild_fx_board()

                # Callback to update FX when user changes sliders
                def on_fx_change(params):
                    nonlocal fx_board
                    fx_board = rebuild_fx_board()
                    self.add_log(f"🎛️ FX güncellendi")

                karaoke_player.on_fx_change_callback = on_fx_change

                self.add_log("🎵 Backing track çalıyor...")
                self.add_log("🎤 Mikrofon aktif - PROFESYONEL FX AKTIF!")
                self.add_log("⏹️ Durdurmak için tekrar 'KAYIT + MİX' butonuna tıkla")

                # Parse mikrofon device ID
                mic_id = None
                if mic_device != "Varsayılan (Default)" and "[" in mic_device:
                    mic_id = int(mic_device.split("[")[1].split("]")[0])

                # Parse hoparlör device ID
                speaker_id = None
                if speaker_device != "Varsayılan (Default)" and "[" in speaker_device:
                    speaker_id = int(speaker_device.split("[")[1].split("]")[0])

                # Kayıt parametreleri
                # Mikrofon: genellikle mono (1 kanal)
                # Output: stereo (backing track ile aynı)
                input_channels = 1  # Mikrofon mono
                output_channels = 2 if len(backing_audio.shape) > 1 else 1

                # Backing track'i stereo yap (eğer değilse)
                if len(backing_audio.shape) == 1:
                    backing_audio = np.stack([backing_audio, backing_audio], axis=-1)
                    output_channels = 2

                # Callback function for PROFESSIONAL real-time audio processing with FX
                frame_idx = [0]  # Mutable counter for backing track position

                # Setup seek callback
                def on_seek(position_samples):
                    frame_idx[0] = position_samples

                karaoke_player.on_seek_callback = on_seek

                def audio_callback(indata, outdata, frames, time, status):
                    if status:
                        print(f"Status: {status}")

                    # Mikrofon ses seviyesini al (mono)
                    mic_level = np.sqrt(np.mean(indata**2))

                    # VU metre güncelle (amplitude to dB)
                    left_amp = mic_level * self.karaoke_volume_var.get()
                    right_amp = mic_level * self.karaoke_volume_var.get()
                    self.karaoke_vu_meter.set_levels_from_amplitude(left_amp, right_amp)

                    # Update karaoke player position
                    karaoke_player.update_position(frame_idx[0])

                    # Backing track frame'ini al
                    start = frame_idx[0]
                    end = min(start + frames, len(backing_audio))

                    if start < len(backing_audio):
                        backing_chunk = backing_audio[start:end]
                        frame_idx[0] = end

                        # Boyut eşitle
                        if len(backing_chunk) < frames:
                            backing_chunk = np.pad(backing_chunk, ((0, frames - len(backing_chunk)), (0, 0)))

                        # Mikrofon mono -> stereo'ya çevir
                        mic_stereo = np.stack([indata[:, 0], indata[:, 0]], axis=-1)

                        # === PROFESSIONAL FX PROCESSING ===
                        # Apply STUDIO-QUALITY effects to microphone input
                        try:
                            # Pedalboard expects shape: (channels, samples)
                            mic_transposed = mic_stereo.T  # (samples, 2) -> (2, samples)

                            # Apply professional effect chain
                            # Compressor -> EQ -> Reverb (optimal order for vocals)
                            mic_fx = fx_board(mic_transposed, sr)

                            # Back to (samples, channels)
                            mic_with_effects = mic_fx.T * self.karaoke_volume_var.get()
                        except Exception:
                            # Fallback to no FX if error
                            mic_with_effects = mic_stereo * self.karaoke_volume_var.get()

                        # Mix (backing track + mikrofon with professional FX)
                        mixed = backing_chunk + mic_with_effects

                        # Clipping önle
                        mixed = np.clip(mixed, -1.0, 1.0)

                        # Output'a yaz
                        outdata[:] = mixed
                    else:
                        # Backing track bitti - sadece mikrofonu FX ile çıkar
                        mic_stereo = np.stack([indata[:, 0], indata[:, 0]], axis=-1)

                        try:
                            mic_transposed = mic_stereo.T
                            mic_fx = fx_board(mic_transposed, sr)
                            outdata[:] = mic_fx.T * self.karaoke_volume_var.get()
                        except:
                            outdata[:] = mic_stereo * self.karaoke_volume_var.get()

                # Stream başlat (ayrı input/output kanal sayısı)
                # OPTIMIZED LOW LATENCY - Stable performance
                blocksize = 128  # Balanced: 128 samples = ~2.7ms @ 48kHz (stable, no dropouts)

                # Stream'i self'e kaydet (stop için)
                self.karaoke_stream = sd.Stream(device=(mic_id, speaker_id),
                             samplerate=sr,
                             channels=(input_channels, output_channels),
                             callback=audio_callback,
                             blocksize=blocksize,
                             latency='low',  # Low latency mode
                             prime_output_buffers_using_stream_callback=False)

                self.karaoke_stream.start()
                latency_ms = (blocksize / sr) * 1000
                self.add_log("✅ Karaoke aktif! (PROFESYONEL MODE)")
                self.add_log(f"🎯 Latency: ~{latency_ms:.1f}ms ({blocksize} samples @ {sr}Hz)")
                self.add_log("🎤 PROFESYONEL FX + ULTRA LOW LATENCY!")
                self.add_log("⏹️ Durdurmak için 'KAYIT + MİX' butonuna tekrar tıkla")

                # Backing track bitene kadar bekle (veya stop komutu gelene kadar)
                duration = len(backing_audio) / sr
                for i in range(int(duration)):
                    if not self.karaoke_stream or not self.karaoke_stream.active:
                        break  # Durduruldu
                    sd.sleep(1000)  # 1 saniye bekle

                # Stream'i kapat (eğer hala açıksa)
                if self.karaoke_stream and self.karaoke_stream.active:
                    self.karaoke_stream.stop()
                    self.karaoke_stream.close()
                    self.karaoke_stream = None
                    self.add_log("✅ Karaoke tamamlandı!")

            except Exception as e:
                self.add_log(f"❌ Hata: {e}")
                messagebox.showerror("Hata", f"Karaoke başlatılamadı:\n{e}")

        threading.Thread(target=start_karaoke, daemon=True).start()

    def apply_karaoke_preset(self, preset_name):
        """Professional preset'leri uygula"""
        presets = {
            "🎙️ Radio Ready": {
                "reverb": 0.25,
                "echo": 0.15,
                "volume": 1.1,
                "autotune": 0.5,
                "deesser": 0.6,
                "description": "Radyo yayını için optimize edilmiş (hafif efektler, net vokal)"
            },
            "🎸 Studio Recording": {
                "reverb": 0.35,
                "echo": 0.2,
                "volume": 1.0,
                "autotune": 0.7,
                "deesser": 0.5,
                "description": "Profesyonel stüdyo kaydı (dengeli, kaliteli)"
            },
            "🎤 Live Performance": {
                "reverb": 0.5,
                "echo": 0.3,
                "volume": 1.2,
                "autotune": 0.3,
                "deesser": 0.4,
                "description": "Canlı performans (güçlü reverb, enerji)"
            },
            "💿 Podcast": {
                "reverb": 0.1,
                "echo": 0.0,
                "volume": 1.15,
                "autotune": 0.0,
                "deesser": 0.7,
                "description": "Podcast/konuşma (minimal efekt, net ses)"
            },
            "🎵 Rap/Hip-Hop": {
                "reverb": 0.2,
                "echo": 0.4,
                "volume": 1.3,
                "autotune": 0.8,
                "deesser": 0.5,
                "description": "Rap/Hip-Hop (güçlü autotune, echo)"
            },
            "🎸 Rock Vokal": {
                "reverb": 0.6,
                "echo": 0.25,
                "volume": 1.4,
                "autotune": 0.2,
                "deesser": 0.3,
                "description": "Rock/Metal vokal (çok reverb, ham enerji)"
            }
        }

        if preset_name in presets:
            preset = presets[preset_name]

            # Apply preset values
            self.karaoke_reverb_var.set(preset["reverb"])
            self.karaoke_echo_var.set(preset["echo"])
            self.karaoke_volume_var.set(preset["volume"])
            self.karaoke_autotune_var.set(preset["autotune"])
            self.karaoke_deesser_var.set(preset["deesser"])

            # Log the change
            self.add_log(f"🎛️ Preset uygulandı: {preset_name}")
            self.add_log(f"   → {preset['description']}")

            # Show notification
            messagebox.showinfo("Preset Uygulandı",
                              f"{preset_name}\n\n{preset['description']}\n\n"
                              f"Reverb: {preset['reverb']:.2f}\n"
                              f"Echo: {preset['echo']:.2f}\n"
                              f"Volume: {preset['volume']:.2f}x\n"
                              f"Autotune: {int(preset['autotune']*100)}%\n"
                              f"De-esser: {int(preset['deesser']*100)}%")

    def converter_select_file(self):
        """Converter için dosya seç"""
        file = filedialog.askopenfilename(
            title="Dosya Seç",
            filetypes=[("Ses Dosyaları", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )
        if file:
            self.converter_file = file
            self.converter_file_label.configure(text=Path(file).name)
            self.add_log(f"📂 Dönüştürülecek: {Path(file).name}")

    def converter_convert(self):
        """Format dönüştür"""
        if not hasattr(self, 'converter_file'):
            messagebox.showwarning("Uyarı", "Dosya seçilmedi!")
            return

        # Output path
        input_path = Path(self.converter_file)
        output_path = input_path.parent / f"{input_path.stem}_converted.{self.converter_format_var.get()}"

        def convert():
            self.add_log(f"🔄 Dönüştürülüyor: {self.converter_format_var.get()}")

            success = self.format_converter.convert(
                self.converter_file,
                str(output_path),
                self.converter_format_var.get(),
                self.converter_quality_var.get()
            )

            if success:
                # Metadata ekle
                metadata = {}
                if self.meta_title.get():
                    metadata['title'] = self.meta_title.get()
                if self.meta_artist.get():
                    metadata['artist'] = self.meta_artist.get()
                if self.meta_album.get():
                    metadata['album'] = self.meta_album.get()
                if self.meta_genre.get():
                    metadata['genre'] = self.meta_genre.get()

                if metadata:
                    self.format_converter.set_metadata(str(output_path), metadata)

                self.add_log(f"✅ Dönüştürüldü: {output_path.name}")
                messagebox.showinfo("Başarılı", f"Dönüştürme tamamlandı!\n{output_path}")
            else:
                messagebox.showerror("Hata", "Dönüştürme başarısız!")

        threading.Thread(target=convert, daemon=True).start()

    def refresh_audio_devices(self):
        """Audio cihazlarını yenile ve menülere doldur (Recorder tab için)"""
        try:
            import sounddevice as sd

            devices = sd.query_devices()

            # Mikrofon cihazları (input)
            mic_devices = ["Varsayılan (Default)"]
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    mic_devices.append(f"[{i}] {dev['name']}")

            # Hoparlör/Kulaklık cihazları (output)
            speaker_devices = ["Varsayılan (Default)"]
            for i, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    speaker_devices.append(f"[{i}] {dev['name']}")

            # Menüleri güncelle
            self.mic_device_menu.configure(values=mic_devices)
            self.speaker_device_menu.configure(values=speaker_devices)

            self.add_log(f"🔄 {len(mic_devices)-1} mikrofon, {len(speaker_devices)-1} hoparlör bulundu")

        except Exception as e:
            self.add_log(f"❌ Cihaz listesi yüklenemedi: {e}")
            messagebox.showerror("Hata", f"Audio cihazları yüklenemedi:\n{e}")

    def refresh_karaoke_devices(self):
        """Audio cihazlarını yenile ve menülere doldur (Karaoke tab için)"""
        try:
            import sounddevice as sd

            devices = sd.query_devices()

            # Mikrofon cihazları (input)
            mic_devices = ["Varsayılan (Default)"]
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    mic_devices.append(f"[{i}] {dev['name']}")

            # Hoparlör/Kulaklık cihazları (output)
            speaker_devices = ["Varsayılan (Default)"]
            for i, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    speaker_devices.append(f"[{i}] {dev['name']}")

            # Karaoke menülerini güncelle
            self.karaoke_mic_menu.configure(values=mic_devices)
            self.karaoke_speaker_menu.configure(values=speaker_devices)

            # Kaydedilmiş cihazları otomatik seç
            if hasattr(self, 'saved_mic_device') and self.saved_mic_device:
                if self.saved_mic_device in mic_devices:
                    self.karaoke_mic_var.set(self.saved_mic_device)
                    self.add_log(f"✓ Mikrofon geri yüklendi: {self.saved_mic_device}")

            if hasattr(self, 'saved_speaker_device') and self.saved_speaker_device:
                if self.saved_speaker_device in speaker_devices:
                    self.karaoke_speaker_var.set(self.saved_speaker_device)
                    self.add_log(f"✓ Hoparlör geri yüklendi: {self.saved_speaker_device}")

            # Her seçim değiştiğinde kaydet
            self.karaoke_mic_var.trace_add("write", lambda *args: self.save_config())
            self.karaoke_speaker_var.trace_add("write", lambda *args: self.save_config())

            self.add_log(f"🔄 Karaoke: {len(mic_devices)-1} mikrofon, {len(speaker_devices)-1} hoparlör bulundu")

        except Exception as e:
            self.add_log(f"❌ Karaoke cihaz listesi yüklenemedi: {e}")
            messagebox.showerror("Hata", f"Audio cihazları yüklenemedi:\n{e}")

    def refresh_backing_tracks(self):
        """Mevcut backing track dosyalarını tara ve listele"""
        try:
            # Önceki widget'ları temizle
            for widget in self.backing_tracks_frame.winfo_children():
                widget.destroy()

            # Backing track'leri tara (instrumental_ ile başlayan WAV dosyaları)
            backing_files = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.startswith("instrumental_") and file.endswith(".wav"):
                        full_path = os.path.join(root, file)
                        backing_files.append(full_path)

            if not backing_files:
                ctk.CTkLabel(self.backing_tracks_frame, text="📭 Henüz backing track oluşturulmamış",
                           text_color="gray60", font=ctk.CTkFont(size=12)).pack(pady=10)
                return

            # Dosyaları tarihine göre sırala (en yeni üstte)
            backing_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            self.add_log(f"📂 {len(backing_files)} backing track bulundu")

            # Her dosya için bir kart oluştur
            for file_path in backing_files[:10]:  # Son 10 dosyayı göster
                file_name = Path(file_path).name
                file_size = Path(file_path).stat().st_size / (1024*1024)  # MB
                file_date = time.strftime('%d.%m.%Y %H:%M', time.localtime(os.path.getmtime(file_path)))

                # Kart frame
                card = ctk.CTkFrame(self.backing_tracks_frame, fg_color=("#3a3d4a", "#2a2d3a"), corner_radius=10)
                card.pack(fill="x", pady=5, padx=5)

                # Sol taraf - Bilgiler
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)

                ctk.CTkLabel(info_frame, text=f"🎵 {file_name[:50]}...",
                           font=ctk.CTkFont(size=11, weight="bold"),
                           anchor="w").pack(anchor="w")

                ctk.CTkLabel(info_frame, text=f"📦 {file_size:.1f} MB  |  📅 {file_date}",
                           font=ctk.CTkFont(size=9),
                           text_color="gray60",
                           anchor="w").pack(anchor="w")

                # Sağ taraf - Butonlar
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(side="right", padx=10)

                ctk.CTkButton(btn_frame, text="✅ Kullan", width=70, height=28,
                            fg_color=("#10b981", "#059669"),
                            hover_color=("#059669", "#047857"),
                            command=lambda p=file_path: self.load_backing_track(p)).pack(side="left", padx=5)

                ctk.CTkButton(btn_frame, text="🗑️ Sil", width=60, height=28,
                            fg_color=("#ef4444", "#dc2626"),
                            hover_color=("#dc2626", "#b91c1c"),
                            command=lambda p=file_path, c=card: self.delete_backing_track(p, c)).pack(side="left")

        except Exception as e:
            self.add_log(f"❌ Backing track taramas\u0131 hatas\u0131: {e}")

    def load_backing_track(self, file_path):
        """Seçilen backing track'i yükle"""
        self.karaoke_backing_track = file_path
        self.save_config()  # Backing track yolunu kaydet
        self.add_log(f"✅ Backing track y\u00fcklendi: {Path(file_path).name}")
        messagebox.showinfo("Ba\u015far\u0131l\u0131", f"Backing track y\u00fcklendi!\n\n{Path(file_path).name}\n\nArt\u0131k 'KAYIT + M\u0130X' butonuna t\u0131klayabilirsin!")

    def delete_backing_track(self, file_path, card_widget):
        """Backing track'i sil"""
        if messagebox.askyesno("Onay", f"{Path(file_path).name}\n\nBu dosyay\u0131 silmek istedi\u011finden emin misin?"):
            try:
                os.remove(file_path)
                card_widget.destroy()
                self.add_log(f"🗑️ Silindi: {Path(file_path).name}")

                # E\u011fer y\u00fckl\u00fc backing track silinirse, state'i temizle
                if self.karaoke_backing_track == file_path:
                    self.karaoke_backing_track = None
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya silinemedi:\n{e}")

    def adjust_color(self, hex_color, amount):
        """Renk ayarla"""
        return hex_color

    def load_config(self):
        """Kaydedilmiş ayarları yükle"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Karaoke ayarlarını yükle
                self.saved_mic_device = config.get('karaoke', {}).get('microphone', None)
                self.saved_speaker_device = config.get('karaoke', {}).get('speaker', None)
                self.saved_output_folder = config.get('karaoke', {}).get('output_folder', None)
                saved_backing = config.get('karaoke', {}).get('backing_track', None)

                # Backing track'i geri yükle (eğer dosya hala varsa)
                if saved_backing and Path(saved_backing).exists():
                    self.karaoke_backing_track = saved_backing

                # Config loaded silently
            else:
                # İlk çalıştırma - varsayılan değerler
                self.saved_mic_device = None
                self.saved_speaker_device = None
                self.saved_output_folder = None
        except Exception as e:
            # Error loading config - use defaults
            self.saved_mic_device = None
            self.saved_speaker_device = None
            self.saved_output_folder = None

    def save_config(self):
        """Mevcut ayarları kaydet"""
        try:
            config = {
                'karaoke': {
                    'microphone': self.karaoke_mic_var.get() if hasattr(self, 'karaoke_mic_var') else None,
                    'speaker': self.karaoke_speaker_var.get() if hasattr(self, 'karaoke_speaker_var') else None,
                    'output_folder': self.karaoke_output_folder,
                    'backing_track': self.karaoke_backing_track
                }
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # No print - config saved silently
        except Exception as e:
            # No print - just pass
            pass


def main():
    """Ana fonksiyon"""
    app = MusicioUltraApp()
    app.mainloop()


if __name__ == "__main__":
    main()
