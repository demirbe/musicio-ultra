"""
Language Configuration for Musicio ULTRA
Supports English and Turkish
"""

class Language:
    """Language manager with English and Turkish support"""

    def __init__(self, lang='en'):
        self.current_lang = lang
        self.translations = {
            'en': {
                # System messages
                'system_starting': 'System starting...',
                'system_ready': 'System ready!',
                'gpu_detected': 'GPU detected',
                'cuda_version': 'CUDA',
                'ai_models_loading': 'AI models loading...',
                'demucs_ready': 'Demucs model ready',
                'audiosr_ready': 'AudioSR model ready',
                'mic_restored': 'Microphone restored',
                'speaker_restored': 'Speaker restored',
                'devices_found': 'microphones, speakers found',
                'backing_track_loaded': 'Backing track loaded',
                'backing_tracks_found': 'backing tracks found',

                # GUI - Main tabs
                'tab_karaoke': 'KARAOKE',
                'tab_vocal_sep': 'VOCAL SEPARATION',
                'tab_analysis': 'ANALYSIS',
                'tab_effects': 'EFFECTS',

                # GUI - Karaoke section
                'karaoke_title': 'PROFESSIONAL KARAOKE STUDIO',
                'select_file': 'SELECT FILE',
                'select_output': 'SELECT OUTPUT FOLDER',
                'create_backing': 'CREATE BACKING TRACK',
                'record_mix': 'RECORD + MIX',
                'microphone': 'Microphone',
                'speaker': 'Speaker',
                'output_folder': 'Output Folder',
                'volume': 'Volume',
                'pitch_shift': 'Pitch Shift',
                'tempo': 'Tempo',
                'semitones': 'semitones',

                # GUI - Buttons
                'load_backing': 'LOAD BACKING TRACK',
                'apply_pitch': 'APPLY PITCH SHIFT',
                'apply_tempo': 'APPLY TEMPO',
                'detect_bpm': 'DETECT BPM',
                'detect_key': 'DETECT KEY',
                'separate_vocals': 'SEPARATE VOCALS',

                # GUI - Presets
                'preset_radio': 'Radio Ready',
                'preset_concert': 'Live Concert',
                'preset_studio': 'Studio Vocal',
                'preset_church': 'Church Reverb',
                'preset_dry': 'Dry Vocal',

                # Status messages
                'processing': 'Processing...',
                'completed': 'Completed',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Info',
                'success': 'Success',

                # Karaoke messages
                'karaoke_starting': 'Karaoke mode starting (PROFESSIONAL MODE)...',
                'karaoke_active': 'Karaoke active! (PROFESSIONAL MODE)',
                'karaoke_stopped': 'Karaoke stopped',
                'karaoke_completed': 'Karaoke completed!',
                'backing_track': 'Backing track',
                'latency': 'Latency',
                'fx_active': 'PROFESSIONAL FX + ULTRA LOW LATENCY!',
                'stop_instruction': 'Click RECORD + MIX again to stop',

                # File operations
                'file_selected': 'File selected',
                'folder_selected': 'Folder selected',
                'file_saved': 'File saved',
                'loading_file': 'Loading file...',

                # Audio processing
                'separating_vocals': 'Separating vocals...',
                'vocals_separated': 'Vocals separated successfully!',
                'creating_backing': 'Creating backing track...',
                'backing_created': 'Backing track created!',
                'applying_effects': 'Applying effects...',
                'effects_applied': 'Effects applied!',

                # Lyrics
                'lyrics_loading': 'Loading lyrics',
                'lyrics_loaded': 'Lyrics loaded',
                'lyrics_not_found': 'Lyrics not found (karaoke player will show plain view)',
                'lyrics_converting': 'Converting lyrics...',
                'lyrics_converted': 'Lyrics JSON created!',
                'lyrics_found': 'lyrics.txt files found!',

                # Errors
                'error_no_file': 'Please select a file first!',
                'error_no_output': 'Please select output folder!',
                'error_no_backing': 'Please click CREATE BACKING TRACK first!',
                'error_backing_not_found': 'Backing track file not found!',
                'error_no_mic': 'Please select microphone!',
                'error_no_speaker': 'Please select speaker!',
                'error_processing': 'Processing error',

                # Player controls
                'play': 'Play',
                'pause': 'Pause',
                'stop': 'Stop',
                'seek': 'Seek',

                # FX controls
                'reverb': 'Reverb',
                'compressor': 'Compressor',
                'equalizer': 'Equalizer',
                'echo': 'Echo',
                'room_size': 'Room Size',
                'wet_mix': 'Wet Mix',
                'threshold': 'Threshold',
                'ratio': 'Ratio',
                'bass': 'Bass',
                'mid': 'Mid',
                'treble': 'Treble',
                'delay': 'Delay',
                'feedback': 'Feedback',
                'mix': 'Mix',

                # Analysis
                'bpm_detected': 'BPM detected',
                'key_detected': 'Key detected',
                'analyzing': 'Analyzing...',

                # Default
                'default': 'Default',
            },

            'tr': {
                # System messages
                'system_starting': 'Sistem başlatılıyor...',
                'system_ready': 'Sistem hazır!',
                'gpu_detected': 'GPU tespit edildi',
                'cuda_version': 'CUDA',
                'ai_models_loading': 'AI modelleri yükleniyor...',
                'demucs_ready': 'Demucs modeli hazır',
                'audiosr_ready': 'AudioSR modeli hazır',
                'mic_restored': 'Mikrofon geri yüklendi',
                'speaker_restored': 'Hoparlör geri yüklendi',
                'devices_found': 'mikrofon, hoparlör bulundu',
                'backing_track_loaded': 'Backing track yüklendi',
                'backing_tracks_found': 'backing track bulundu',

                # GUI - Main tabs
                'tab_karaoke': 'KARAOKE',
                'tab_vocal_sep': 'VOKAL AYIRMA',
                'tab_analysis': 'ANALİZ',
                'tab_effects': 'EFEKTLER',

                # GUI - Karaoke section
                'karaoke_title': 'PROFESYONEL KARAOKE STÜDYOSU',
                'select_file': 'DOSYA SEÇ',
                'select_output': 'ÇIKTI KLASÖRÜ SEÇ',
                'create_backing': 'BACKING TRACK OLUŞTUR',
                'record_mix': 'KAYIT + MİX',
                'microphone': 'Mikrofon',
                'speaker': 'Hoparlör',
                'output_folder': 'Çıktı Klasörü',
                'volume': 'Ses Seviyesi',
                'pitch_shift': 'Perde Kayması',
                'tempo': 'Tempo',
                'semitones': 'yarım ton',

                # GUI - Buttons
                'load_backing': 'BACKING TRACK YÜKLE',
                'apply_pitch': 'PERDE UYGULA',
                'apply_tempo': 'TEMPO UYGULA',
                'detect_bpm': 'BPM ALGI',
                'detect_key': 'ANAHTAR ALGI',
                'separate_vocals': 'VOKAL AYIR',

                # GUI - Presets
                'preset_radio': 'Radyo Hazır',
                'preset_concert': 'Canlı Konser',
                'preset_studio': 'Stüdyo Vokal',
                'preset_church': 'Kilise Yankısı',
                'preset_dry': 'Kuru Vokal',

                # Status messages
                'processing': 'İşleniyor...',
                'completed': 'Tamamlandı',
                'error': 'Hata',
                'warning': 'Uyarı',
                'info': 'Bilgi',
                'success': 'Başarılı',

                # Karaoke messages
                'karaoke_starting': 'Karaoke modu başlatılıyor (PROFESYONEL MODE)...',
                'karaoke_active': 'Karaoke aktif! (PROFESYONEL MODE)',
                'karaoke_stopped': 'Karaoke durduruldu',
                'karaoke_completed': 'Karaoke tamamlandı!',
                'backing_track': 'Backing track',
                'latency': 'Gecikme',
                'fx_active': 'PROFESYONEL FX + ULTRA DÜŞÜK GECİKME!',
                'stop_instruction': 'Durdurmak için KAYIT + MİX butonuna tekrar tıkla',

                # File operations
                'file_selected': 'Dosya seçildi',
                'folder_selected': 'Klasör seçildi',
                'file_saved': 'Dosya kaydedildi',
                'loading_file': 'Dosya yükleniyor...',

                # Audio processing
                'separating_vocals': 'Vokaller ayrılıyor...',
                'vocals_separated': 'Vokaller başarıyla ayrıldı!',
                'creating_backing': 'Backing track oluşturuluyor...',
                'backing_created': 'Backing track oluşturuldu!',
                'applying_effects': 'Efektler uygulanıyor...',
                'effects_applied': 'Efektler uygulandı!',

                # Lyrics
                'lyrics_loading': 'Şarkı sözleri yükleniyor',
                'lyrics_loaded': 'Şarkı sözleri yüklendi',
                'lyrics_not_found': 'Şarkı sözleri bulunamadı (karaoke player sade görünecek)',
                'lyrics_converting': 'Sözler dönüştürülüyor...',
                'lyrics_converted': 'Lyrics JSON oluşturuldu!',
                'lyrics_found': 'adet _lyrics.txt dosyası bulundu!',

                # Errors
                'error_no_file': 'Lütfen önce bir dosya seçin!',
                'error_no_output': 'Lütfen çıktı klasörü seçin!',
                'error_no_backing': 'Lütfen önce BACKING TRACK OLUŞTUR butonuna tıklayın!',
                'error_backing_not_found': 'Backing track dosyası bulunamadı!',
                'error_no_mic': 'Lütfen mikrofon seçin!',
                'error_no_speaker': 'Lütfen hoparlör seçin!',
                'error_processing': 'İşleme hatası',

                # Player controls
                'play': 'Oynat',
                'pause': 'Duraklat',
                'stop': 'Durdur',
                'seek': 'Atla',

                # FX controls
                'reverb': 'Yankı',
                'compressor': 'Sıkıştırıcı',
                'equalizer': 'Ekolayzer',
                'echo': 'Eko',
                'room_size': 'Oda Boyutu',
                'wet_mix': 'Islak Karışım',
                'threshold': 'Eşik',
                'ratio': 'Oran',
                'bass': 'Bas',
                'mid': 'Orta',
                'treble': 'Tiz',
                'delay': 'Gecikme',
                'feedback': 'Geri Besleme',
                'mix': 'Karışım',

                # Analysis
                'bpm_detected': 'BPM algılandı',
                'key_detected': 'Anahtar algılandı',
                'analyzing': 'Analiz ediliyor...',

                # Default
                'default': 'Varsayılan',
            }
        }

    def get(self, key, *args):
        """Get translated text for current language"""
        text = self.translations.get(self.current_lang, {}).get(key, key)
        if args:
            return text.format(*args)
        return text

    def set_language(self, lang):
        """Change current language"""
        if lang in self.translations:
            self.current_lang = lang
            return True
        return False

    def get_current_language(self):
        """Get current language code"""
        return self.current_lang

# Global language instance
lang = Language('en')  # Default to English for GitHub release

def get_text(key, *args):
    """Shortcut function to get translated text"""
    return lang.get(key, *args)

def set_language(language_code):
    """Shortcut function to set language"""
    return lang.set_language(language_code)

def get_current_language():
    """Shortcut function to get current language"""
    return lang.get_current_language()
