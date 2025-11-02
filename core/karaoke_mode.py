"""
Professional Karaoke Mode
Vocal removal, pitch shift, tempo change, real-time sing-along
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import logging

# EN YÜKSEK KALITE: Rubberband kullan (professional pitch/tempo shifting)
try:
    import pyrubberband as pyrb
    RUBBERBAND_AVAILABLE = True
except ImportError:
    RUBBERBAND_AVAILABLE = False
    logger.warning("pyrubberband bulunamadı, librosa fallback kullanılacak")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KaraokeMode:
    """Profesyonel karaoke sistemi"""

    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.instrumental = None
        self.vocals = None
        self.sr = 96000  # EN YÜKSEK KALITE (48kHz -> 96kHz studio quality)

    def prepare_karaoke_track(self, audio_path: str,
                               pitch_shift: float = 0,
                               tempo_change: float = 1.0) -> tuple:
        """
        Karaoke track'i hazırla
        Args:
            audio_path: Şarkı dosyası
            pitch_shift: Pitch değişikliği (semitone)
            tempo_change: Tempo değişikliği (1.0 = normal, 0.9 = %10 yavaş)
        Returns:
            (instrumental_path, vocals_path)
        """
        try:
            logger.info(f"🎤 Karaoke track hazırlanıyor...")

            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sr, mono=False)

            # Demucs ile vokal ayırma
            if self.model_manager:
                logger.info("  Vokaller ayırılıyor (Demucs)...")
                separated = self.model_manager.separate_vocals(audio_path)

                if separated:
                    # Vocals yükle
                    vocals, _ = librosa.load(separated['vocals'], sr=self.sr, mono=False)

                    # Instrumental oluştur - TÜM enstrümanları birleştir (vocals hariç)
                    instrumental = None
                    instrument_names = []

                    # Tüm enstrümanları topla
                    for stem_name, stem_path in separated.items():
                        if stem_name != 'vocals':  # Vocals hariç hepsi
                            stem_audio, _ = librosa.load(stem_path, sr=self.sr, mono=False)

                            if instrumental is None:
                                instrumental = stem_audio
                            else:
                                instrumental += stem_audio

                            instrument_names.append(stem_name)

                    logger.info(f"  ✓ Backing track: {', '.join(instrument_names)}")

                else:
                    # Fallback: Basit vokal removal (phase inversion)
                    logger.warning("  Demucs başarısız, basit yöntem kullanılıyor...")
                    instrumental, vocals = self._simple_vocal_removal(y)
            else:
                # Model manager yoksa basit yöntem
                instrumental, vocals = self._simple_vocal_removal(y)

            # Pitch shift uygula (EN YÜKSEK KALITE - Rubberband)
            if pitch_shift != 0:
                logger.info(f"  Pitch kaydırılıyor: {pitch_shift:+.1f} semitone (Rubberband)")
                if RUBBERBAND_AVAILABLE:
                    # Rubberband = professional kalite, daha az artifact
                    instrumental = pyrb.pitch_shift(instrumental.T, self.sr, pitch_shift).T
                    vocals = pyrb.pitch_shift(vocals.T, self.sr, pitch_shift).T
                else:
                    # Fallback: librosa
                    instrumental = librosa.effects.pitch_shift(
                        instrumental, sr=self.sr, n_steps=pitch_shift
                    )
                    vocals = librosa.effects.pitch_shift(
                        vocals, sr=self.sr, n_steps=pitch_shift
                    )

            # Tempo change (EN YÜKSEK KALITE - Rubberband)
            if tempo_change != 1.0:
                logger.info(f"  Tempo değiştiriliyor: {tempo_change:.2f}x (Rubberband)")
                if RUBBERBAND_AVAILABLE:
                    # Rubberband = professional kalite, pitch korunur
                    instrumental = pyrb.time_stretch(instrumental.T, self.sr, tempo_change).T
                    vocals = pyrb.time_stretch(vocals.T, self.sr, tempo_change).T
                else:
                    # Fallback: librosa
                    instrumental = librosa.effects.time_stretch(instrumental, rate=tempo_change)
                    vocals = librosa.effects.time_stretch(vocals, rate=tempo_change)

            # Kaydet
            output_path = Path(getattr(self, 'output_dir', 'karaoke_output'))
            output_path.mkdir(parents=True, exist_ok=True)

            instrumental_path = output_path / f"instrumental_{Path(audio_path).stem}.wav"
            vocals_path = output_path / f"vocals_{Path(audio_path).stem}.wav"

            # EN YÜKSEK KALITE: 32-bit float WAV
            sf.write(str(instrumental_path), instrumental.T if instrumental.ndim > 1 else instrumental, self.sr, subtype='FLOAT')
            sf.write(str(vocals_path), vocals.T if vocals.ndim > 1 else vocals, self.sr, subtype='FLOAT')

            self.instrumental = instrumental
            self.vocals = vocals

            logger.info(f"✅ Karaoke track hazır!")
            logger.info(f"  Instrumental: {instrumental_path}")
            logger.info(f"  Vocals: {vocals_path}")

            return str(instrumental_path), str(vocals_path)

        except Exception as e:
            logger.error(f"Karaoke hazırlama hatası: {e}")
            return None, None

    def _simple_vocal_removal(self, audio: np.ndarray) -> tuple:
        """
        Basit vokal kaldırma (stereo phase inversion)
        Orta kanalı (vokaller genelde ortadadır) azaltır
        """
        try:
            if audio.ndim == 1:
                # Mono - vokal removal yapılamaz
                return audio, np.zeros_like(audio)

            # Stereo
            left = audio[0]
            right = audio[1]

            # Instrumental (side): L - R
            # Center channel'ı kaldırır (vokaller genelde ortada)
            instrumental_left = (left - right) / 2
            instrumental_right = (right - left) / 2
            instrumental = np.stack([instrumental_left, instrumental_right], axis=0)

            # Vocals (center): (L + R) / 2
            vocals_mono = (left + right) / 2
            vocals = np.stack([vocals_mono, vocals_mono], axis=0)

            return instrumental, vocals

        except Exception as e:
            logger.error(f"Basit vokal removal hatası: {e}")
            return audio, np.zeros_like(audio)

    def create_backing_track(self, audio_path: str,
                             output_dir: str = "karaoke_output",
                             remove_vocals: bool = True,
                             pitch_shift: float = 0,
                             tempo_change: float = 1.0) -> str:
        """
        Karaoke backing track oluştur (sadece instrumental)
        """
        try:
            logger.info("🎼 Backing track oluşturuluyor...")

            # Çıkış klasörünü kaydet (prepare_karaoke_track için)
            self.output_dir = output_dir

            # Karaoke track hazırla
            instrumental_path, _ = self.prepare_karaoke_track(
                audio_path,
                pitch_shift=pitch_shift,
                tempo_change=tempo_change
            )

            if instrumental_path:
                logger.info(f"✅ Backing track: {instrumental_path}")
                return instrumental_path
            else:
                return None

        except Exception as e:
            logger.error(f"Backing track hatası: {e}")
            return None

    def mix_with_microphone(self, backing_track_path: str,
                            mic_recording_path: str,
                            output_path: str,
                            mic_volume: float = 1.0) -> bool:
        """
        Backing track ile mikrofon kaydını karıştır
        """
        try:
            logger.info("🎤 Backing track + mikrofon karıştırılıyor...")

            # Load tracks
            backing, sr_back = librosa.load(backing_track_path, sr=self.sr, mono=False)
            mic, sr_mic = librosa.load(mic_recording_path, sr=self.sr, mono=False)

            # Resample if needed
            if sr_mic != self.sr:
                mic = librosa.resample(mic, orig_sr=sr_mic, target_sr=self.sr)

            # Stereo conversion
            if backing.ndim == 1:
                backing = np.stack([backing, backing], axis=0)

            if mic.ndim == 1:
                mic = np.stack([mic, mic], axis=0)

            # Length matching
            max_len = max(backing.shape[1], mic.shape[1])

            if backing.shape[1] < max_len:
                backing = np.pad(backing, ((0, 0), (0, max_len - backing.shape[1])))

            if mic.shape[1] < max_len:
                mic = np.pad(mic, ((0, 0), (0, max_len - mic.shape[1])))

            # Mix
            mic = mic * mic_volume
            mixed = backing + mic

            # Normalize
            max_val = np.abs(mixed).max()
            if max_val > 1.0:
                mixed = mixed / max_val * 0.95

            # Save
            sf.write(output_path, mixed.T, self.sr)

            logger.info(f"✅ Mix tamamlandı: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Mix hatası: {e}")
            return False

    def analyze_vocal_range(self, audio_path: str) -> dict:
        """
        Vokal aralığı analiz et (hangi pitch range'de söyleniyor)
        """
        try:
            logger.info("🎤 Vokal aralığı analiz ediliyor...")

            y, sr = librosa.load(audio_path, sr=self.sr)

            # Pitch detection
            import crepe
            time, frequency, confidence, activation = crepe.predict(
                y, sr, viterbi=True, model_capacity='tiny'
            )

            # Valid pitches (high confidence)
            valid_idx = confidence > 0.7
            valid_freqs = frequency[valid_idx]

            if len(valid_freqs) == 0:
                return {'error': 'No vocals detected'}

            # Convert to MIDI notes
            midi_notes = librosa.hz_to_midi(valid_freqs)

            # Stats
            min_note = int(np.min(midi_notes))
            max_note = int(np.max(midi_notes))
            mean_note = int(np.mean(midi_notes))

            note_names = librosa.midi_to_note([min_note, mean_note, max_note])

            result = {
                'min_note': note_names[0],
                'mean_note': note_names[1],
                'max_note': note_names[2],
                'range_semitones': max_note - min_note,
                'min_hz': float(np.min(valid_freqs)),
                'max_hz': float(np.max(valid_freqs))
            }

            logger.info(f"  Vokal aralığı: {note_names[0]} - {note_names[2]} ({result['range_semitones']} semitones)")

            return result

        except Exception as e:
            logger.error(f"Vokal analiz hatası: {e}")
            return {}


if __name__ == "__main__":
    # Test
    karaoke = KaraokeMode()
    print("Karaoke Mode hazır!")
