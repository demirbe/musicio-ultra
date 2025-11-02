"""
Advanced Music Analyzer
BPM, Key, Chord detection, Genre classification, Note Transcription
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import crepe
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicAnalyzer:
    """Profesyonel müzik analiz motoru"""

    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.key_map = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        # Nota isimleri (Türkçe)
        self.note_names_turkish = {
            'C': 'Do', 'C#': 'Do#', 'Db': 'Reb',
            'D': 'Re', 'D#': 'Re#', 'Eb': 'Mib',
            'E': 'Mi',
            'F': 'Fa', 'F#': 'Fa#', 'Gb': 'Solb',
            'G': 'Sol', 'G#': 'Sol#', 'Ab': 'Lab',
            'A': 'La', 'A#': 'La#', 'Bb': 'Sib',
            'B': 'Si'
        }

    def get_turkish_note_name(self, note_name: str) -> str:
        """İngilizce nota ismini Türkçe'ye çevir (C4 -> Do4)"""
        # Nota ismini ayrıştır (örn: C#4 -> C#, 4)
        note_base = ''.join([c for c in note_name if not c.isdigit()])
        octave = ''.join([c for c in note_name if c.isdigit()])

        turkish = self.note_names_turkish.get(note_base, note_base)
        return f"{turkish}{octave}" if octave else turkish

    def analyze_full(self, audio_path: str) -> Dict:
        """
        Tam müzik analizi
        Returns: {
            'bpm': float,
            'key': str,
            'scale': str (major/minor),
            'tempo_confidence': float,
            'beats': list,
            'duration': float,
            'energy': float
        }
        """
        logger.info(f"🎼 Müzik analiz ediliyor: {audio_path}")

        try:
            # Audio yükle
            y, sr = librosa.load(audio_path, sr=22050)
            duration = librosa.get_duration(y=y, sr=sr)

            analysis = {
                'duration': duration,
                'sample_rate': sr
            }

            # BPM tespiti
            bpm_data = self.detect_bpm(y, sr)
            analysis.update(bpm_data)

            # Key detection
            key_data = self.detect_key(y, sr)
            analysis.update(key_data)

            # Energy analysis
            energy = self.calculate_energy(y)
            analysis['energy'] = energy

            # Spectral features
            spectral = self.analyze_spectral_features(y, sr)
            analysis['spectral'] = spectral

            logger.info(f"✓ Analiz tamamlandı: BPM={analysis.get('bpm', 'N/A'):.1f}, Key={analysis.get('key', 'N/A')}")
            return analysis

        except Exception as e:
            logger.error(f"Analiz hatası: {e}")
            return {'error': str(e)}

    def detect_bpm(self, y: np.ndarray, sr: int) -> Dict:
        """
        BPM (Tempo) tespiti
        """
        try:
            logger.info("  🥁 BPM tespit ediliyor...")

            # Onset strength envelope
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)

            # Tempo estimation
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

            # Beat times
            beat_times = librosa.frames_to_time(beats, sr=sr)

            # Dynamic tempo
            dtempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, aggregate=None)

            logger.info(f"    ✓ BPM: {tempo:.1f}")

            return {
                'bpm': float(tempo),
                'beats': beat_times.tolist(),
                'beat_count': len(beats),
                'tempo_stability': float(np.std(dtempo))
            }

        except Exception as e:
            logger.error(f"BPM tespit hatası: {e}")
            return {'bpm': 0, 'beats': [], 'beat_count': 0}

    def detect_key(self, y: np.ndarray, sr: int) -> Dict:
        """
        Anahtar (Key) tespiti - Krumhansl-Schmuckler algoritması
        """
        try:
            logger.info("  🎹 Anahtar tespit ediliyor...")

            # Chromagram
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

            # Her chroma için ortalama enerji
            chroma_vals = np.mean(chroma, axis=1)

            # Krumhansl-Schmuckler major ve minor profilleri
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

            # Her anahtar için korelasyon hesapla
            major_correlations = []
            minor_correlations = []

            for i in range(12):
                # Rotate chroma to match key
                rotated = np.roll(chroma_vals, -i)

                major_corr = np.corrcoef(rotated, major_profile)[0, 1]
                minor_corr = np.corrcoef(rotated, minor_profile)[0, 1]

                major_correlations.append(major_corr)
                minor_correlations.append(minor_corr)

            # En yüksek korelasyonu bul
            max_major = max(major_correlations)
            max_minor = max(minor_correlations)

            if max_major > max_minor:
                key_idx = major_correlations.index(max_major)
                scale = 'major'
                confidence = max_major
            else:
                key_idx = minor_correlations.index(max_minor)
                scale = 'minor'
                confidence = max_minor

            key = self.key_map[key_idx]

            logger.info(f"    ✓ Anahtar: {key} {scale} (confidence: {confidence:.2f})")

            return {
                'key': key,
                'scale': scale,
                'key_confidence': float(confidence)
            }

        except Exception as e:
            logger.error(f"Key tespit hatası: {e}")
            return {'key': 'Unknown', 'scale': 'unknown', 'key_confidence': 0.0}

    def detect_chords(self, audio_path: str, hop_length: int = 512) -> List[Tuple[float, str]]:
        """
        Chord (Akor) tespiti
        Returns: [(time, chord_name), ...]
        """
        try:
            logger.info("  🎸 Akorlar tespit ediliyor...")

            y, sr = librosa.load(audio_path, sr=22050)

            # Chromagram
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

            # Basit chord detection (template matching)
            chord_templates = self._get_chord_templates()

            chords = []
            times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)

            for i in range(chroma.shape[1]):
                frame = chroma[:, i]

                # En yakın chord template'i bul
                best_chord = 'N'
                best_score = 0

                for chord_name, template in chord_templates.items():
                    score = np.dot(frame, template)
                    if score > best_score:
                        best_score = score
                        best_chord = chord_name

                chords.append((float(times[i]), best_chord))

            # Ardışık aynı chordları birleştir
            merged = []
            prev_chord = None
            for time, chord in chords:
                if chord != prev_chord:
                    merged.append((time, chord))
                    prev_chord = chord

            logger.info(f"    ✓ {len(merged)} akor tespit edildi")
            return merged

        except Exception as e:
            logger.error(f"Chord tespit hatası: {e}")
            return []

    def _get_chord_templates(self) -> Dict[str, np.ndarray]:
        """Temel chord template'leri"""
        templates = {}

        # Major chords
        for i, root in enumerate(self.key_map):
            template = np.zeros(12)
            # Root, major third, fifth
            template[i] = 1.0
            template[(i + 4) % 12] = 0.8
            template[(i + 7) % 12] = 0.6
            templates[root] = template

            # Minor chords
            template_m = np.zeros(12)
            template_m[i] = 1.0
            template_m[(i + 3) % 12] = 0.8  # Minor third
            template_m[(i + 7) % 12] = 0.6
            templates[f"{root}m"] = template_m

        return templates

    def calculate_energy(self, y: np.ndarray) -> float:
        """Ses enerjisi hesapla (0-1 arası normalize)"""
        rms = librosa.feature.rms(y=y)[0]
        mean_energy = np.mean(rms)
        # Normalize to 0-1
        return min(1.0, float(mean_energy * 10))

    def analyze_spectral_features(self, y: np.ndarray, sr: int) -> Dict:
        """Spectral özellikler analizi"""
        try:
            # Spectral centroid (brightness)
            centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            centroid_mean = float(np.mean(centroid))

            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            rolloff_mean = float(np.mean(rolloff))

            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            zcr_mean = float(np.mean(zcr))

            return {
                'brightness': centroid_mean,
                'rolloff': rolloff_mean,
                'zcr': zcr_mean
            }

        except Exception as e:
            logger.error(f"Spectral analiz hatası: {e}")
            return {}

    def transcribe_notes(self, audio_path: str, output_dir: str = "transcriptions") -> Dict:
        """
        Şarkıdaki tüm notaları çıkarır (MIDI formatında)
        Spotify'ın Basic Pitch modeli kullanılır - en doğru sonuç

        Returns:
            {
                'midi_path': str,  # MIDI dosya yolu
                'notes': List[Dict],  # [{'note': 'C4', 'start': 0.5, 'end': 1.2, 'velocity': 80}]
                'note_count': int,
                'duration': float
            }
        """
        try:
            from basic_pitch.inference import predict
            from basic_pitch import ICASSP_2022_MODEL_PATH
            import pretty_midi

            logger.info("🎹 Notalar çıkarılıyor (Basic Pitch)...")

            # Çıkış klasörü oluştur
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # MIDI dosya yolu
            file_stem = Path(audio_path).stem
            midi_path = output_path / f"{file_stem}_notes.mid"

            # Basic Pitch ile transcription (EN YÜKSEK KALITE AYARLARI)
            model_output, midi_data, note_events = predict(
                audio_path,
                ICASSP_2022_MODEL_PATH,
                onset_threshold=0.5,      # Daha hassas nota başlangıcı (0-1, default: 0.5)
                frame_threshold=0.3,      # Daha hassas nota tespiti (0-1, default: 0.3)
                minimum_note_length=127.70,  # Minimum nota süresi (ms, default: 127.70)
                minimum_frequency=None,   # Minimum frekans (Hz, None = tüm notalar)
                maximum_frequency=None,   # Maximum frekans (Hz, None = tüm notalar)
                multiple_pitch_bends=True,  # Birden fazla pitch bend (daha detaylı)
                melodia_trick=True        # Melodia trick (daha iyi melodi tespiti)
            )

            # MIDI kaydet
            midi_data.write(str(midi_path))

            # Notaları parse et
            notes_list = []
            for instrument in midi_data.instruments:
                for note in instrument.notes:
                    note_name = pretty_midi.note_number_to_name(note.pitch)
                    note_turkish = self.get_turkish_note_name(note_name)
                    notes_list.append({
                        'note': note_name,
                        'note_turkish': note_turkish,
                        'pitch': note.pitch,
                        'start': note.start,
                        'end': note.end,
                        'duration': note.end - note.start,
                        'velocity': note.velocity
                    })

            # İstatistikler
            note_count = len(notes_list)
            duration = max([n['end'] for n in notes_list]) if notes_list else 0

            # En çok kullanılan notalar
            note_freq = {}
            for n in notes_list:
                note_freq[n['note']] = note_freq.get(n['note'], 0) + 1

            top_notes = sorted(note_freq.items(), key=lambda x: x[1], reverse=True)[:10]

            logger.info(f"✓ {note_count} nota bulundu")
            logger.info(f"✓ MIDI kaydedildi: {midi_path}")

            return {
                'success': True,
                'midi_path': str(midi_path),
                'notes': notes_list,
                'note_count': note_count,
                'duration': duration,
                'top_notes': top_notes,
                'average_duration': np.mean([n['duration'] for n in notes_list]) if notes_list else 0
            }

        except Exception as e:
            logger.error(f"Nota çıkarma hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def transcribe_lyrics(self, audio_path: str, output_dir: str = "lyrics", language: str = "auto") -> Dict:
        """
        Şarkı sözlerini çıkar (Whisper AI ile)
        OpenAI'ın Whisper modeli - en doğru konuşma tanıma

        Args:
            audio_path: Ses dosyası yolu
            output_dir: Çıkış klasörü
            language: Dil seçimi ("tr", "en", "auto")

        Returns:
            {
                'success': bool,
                'lyrics': str,  # Tam şarkı sözleri
                'lyrics_timestamped': List[Dict],  # Zaman damgalı sözler
                'language': str,  # Tespit edilen dil
                'text_file': str  # Kaydedilen metin dosyası
            }
        """
        try:
            import whisper

            logger.info("🎤 Şarkı sözleri çıkarılıyor (Whisper large-v3)...")
            logger.info("⏳ Model yükleniyor (ilk kullanımda biraz sürer)...")

            # Whisper modelini yükle (large-v3 = EN YÜKSEK KALITE)
            # RTX 5090 OPTIMIZATION: FP16 + device=cuda
            model = whisper.load_model("large-v3", device="cuda", download_root=None)

            # NOT: model.half() KULLANMA - Whisper transcribe() fp16=True parametresi ile hallediliyor
            # Manual half() çağrısı dtype uyumsuzluğuna neden oluyor

            logger.info(f"🎵 Ses analiz ediliyor (Dil: {language.upper()})...")

            # HIZLI MOD: Direkt transcribe et (vokal ayırma çok uzun sürüyor)
            vocals_path = audio_path

            # Dil ayarını belirle
            whisper_language = None  # Otomatik

            if language == "tr":
                whisper_language = "tr"
                logger.info("  🇹🇷 Türkçe dil zorlaması aktif")
            elif language == "en":
                whisper_language = "en"
                logger.info("  🇬🇧 İngilizce dil zorlaması aktif")
            else:
                logger.info("  🌍 Otomatik dil tespiti aktif")

            # Transcribe et - DİL SEÇİMİNE GÖRE (RTX 5090 FULL POWER)
            # NOT: initial_prompt KULLANMA - Whisper bunu şarkı sözü sanıp tekrar ediyor!
            result = model.transcribe(
                vocals_path,
                language=whisper_language,  # Kullanıcı seçimine göre
                task="transcribe",
                verbose=False,  # Log kalabalığını azalt
                word_timestamps=True,
                condition_on_previous_text=False,  # Tekrarları engellemek için False
                temperature=0.0,
                no_speech_threshold=0.6,  # Müzik kısmını atla
                logprob_threshold=-1.0,  # Düşük kaliteli tespitleri atla
                compression_ratio_threshold=2.4,  # Tekrarları engelle
                beam_size=10,  # 5 -> 10 (daha iyi kalite, RTX 5090 için)
                best_of=10,  # Beam search - en iyi sonuçları seç
                fp16=True  # FP16 precision - RTX 5090'da 2x hızlı
            )

            # Sonuçlar
            lyrics_full = result['text']
            language = result.get('language', 'unknown')

            # Zaman damgalı sözler (kelime kelime)
            lyrics_timestamped = []
            for segment in result['segments']:
                lyrics_timestamped.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })

            # Çıkış klasörü
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Metin dosyasına kaydet
            file_stem = Path(audio_path).stem
            lyrics_file = output_path / f"{file_stem}_lyrics.txt"

            with open(lyrics_file, 'w', encoding='utf-8') as f:
                f.write(f"🎵 ŞARKI SÖZLERİ: {file_stem}\n")
                f.write(f"{'='*60}\n\n")
                f.write(lyrics_full)
                f.write(f"\n\n{'='*60}\n")
                f.write("📝 ZAMAN DAMGALI SÖZLER:\n")
                f.write(f"{'='*60}\n\n")
                for item in lyrics_timestamped:
                    min_start = int(item['start'] // 60)
                    sec_start = int(item['start'] % 60)
                    f.write(f"[{min_start:02d}:{sec_start:02d}] {item['text']}\n")

            logger.info(f"✓ Şarkı sözleri çıkarıldı")
            logger.info(f"✓ Dil: {language}")
            logger.info(f"✓ Metin dosyası: {lyrics_file}")

            return {
                'success': True,
                'lyrics': lyrics_full,
                'lyrics_timestamped': lyrics_timestamped,
                'language': language,
                'text_file': str(lyrics_file),
                'word_count': len(lyrics_full.split())
            }

        except Exception as e:
            logger.error(f"Şarkı sözü çıkarma hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def detect_pitch_contour(self, audio_path: str) -> Dict:
        """
        Pitch contour tespiti (vokal analizi için)
        CREPE kullanarak yüksek doğrulukta pitch detection
        """
        try:
            logger.info("  🎤 Pitch contour tespit ediliyor (CREPE)...")

            y, sr = librosa.load(audio_path, sr=16000)  # CREPE 16kHz ister

            # CREPE ile pitch detection
            time, frequency, confidence, activation = crepe.predict(
                y,
                sr,
                viterbi=True,
                model_capacity='tiny'  # 'tiny', 'small', 'medium', 'large', 'full'
            )

            # Sadece yüksek confidence olanları al
            valid_indices = confidence > 0.5
            valid_times = time[valid_indices]
            valid_freqs = frequency[valid_indices]
            valid_conf = confidence[valid_indices]

            logger.info(f"    ✓ {len(valid_freqs)} pitch noktası tespit edildi")

            return {
                'times': valid_times.tolist(),
                'frequencies': valid_freqs.tolist(),
                'confidence': valid_conf.tolist(),
                'mean_pitch_hz': float(np.mean(valid_freqs)) if len(valid_freqs) > 0 else 0,
                'pitch_range': float(np.ptp(valid_freqs)) if len(valid_freqs) > 0 else 0
            }

        except Exception as e:
            logger.error(f"Pitch contour hatası: {e}")
            return {}

    def suggest_optimal_pitch_shift(self, audio_path: str, target_key: str = 'C') -> float:
        """
        AI öneri: Bu şarkı için optimal pitch shift değeri
        """
        try:
            logger.info(f"  🤖 Optimal pitch shift hesaplanıyor (target: {target_key})...")

            # Mevcut key'i tespit et
            y, sr = librosa.load(audio_path, sr=22050)
            key_data = self.detect_key(y, sr)
            current_key = key_data['key']

            # Key'ler arası farkı hesapla
            current_idx = self.key_map.index(current_key)
            target_idx = self.key_map.index(target_key.upper())

            # En kısa yolu bul (circular)
            diff = target_idx - current_idx
            if abs(diff) > 6:
                diff = diff - 12 * np.sign(diff)

            logger.info(f"    ✓ Öneri: {current_key} → {target_key} = {diff:+d} semitone")

            return float(diff)

        except Exception as e:
            logger.error(f"Optimal pitch shift hatası: {e}")
            return 0.0


if __name__ == "__main__":
    # Test
    analyzer = MusicAnalyzer()

    # Test ile basit bir audio oluştur
    print("Music Analyzer hazır!")
    print("Kullanım: analyzer.analyze_full('song.mp3')")
