"""
Professional Multi-Track Audio Mixer
Çoklu dosya karıştırma, AI tempo/key matching
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Track:
    """Tek bir ses track'i"""

    def __init__(self, file_path: str, track_id: int):
        self.track_id = track_id
        self.file_path = file_path
        self.name = Path(file_path).name

        # Audio data
        self.audio = None
        self.sr = None
        self.duration = 0

        # Controls
        self.volume = 1.0  # 0.0-2.0
        self.pitch_shift = 0.0  # semitones
        self.pan = 0.0  # -1.0 (left) to 1.0 (right)
        self.mute = False
        self.solo = False

        # Load audio
        self.load()

    def load(self):
        """Track'i yükle"""
        try:
            self.audio, self.sr = librosa.load(self.file_path, sr=48000, mono=False)

            if self.audio.ndim == 1:
                # Mono to stereo
                self.audio = np.stack([self.audio, self.audio], axis=0)

            self.duration = librosa.get_duration(y=self.audio, sr=self.sr)
            logger.info(f"✓ Track {self.track_id} yüklendi: {self.name} ({self.duration:.1f}s)")
        except Exception as e:
            logger.error(f"Track yükleme hatası: {e}")

    def get_audio(self, target_length: int = None) -> np.ndarray:
        """İşlenmiş audio'yu al"""
        if self.audio is None or self.mute:
            return np.zeros((2, target_length or 1))

        audio = self.audio.copy()

        # Pitch shift
        if self.pitch_shift != 0:
            audio = librosa.effects.pitch_shift(
                audio,
                sr=self.sr,
                n_steps=self.pitch_shift
            )

        # Volume
        audio = audio * self.volume

        # Pan (stereo positioning)
        if self.pan != 0:
            left_gain = 1.0 - max(0, self.pan)
            right_gain = 1.0 - max(0, -self.pan)
            audio[0] *= left_gain
            audio[1] *= right_gain

        # Length matching
        if target_length:
            if audio.shape[1] < target_length:
                # Pad
                padding = target_length - audio.shape[1]
                audio = np.pad(audio, ((0, 0), (0, padding)), mode='constant')
            else:
                # Crop
                audio = audio[:, :target_length]

        return audio


class AudioMixer:
    """Multi-track audio mixer"""

    def __init__(self, sample_rate: int = 48000):
        self.sr = sample_rate
        self.tracks: List[Track] = []
        self.master_volume = 1.0

    def add_track(self, file_path: str) -> Track:
        """Yeni track ekle"""
        track = Track(file_path, len(self.tracks))
        self.tracks.append(track)
        logger.info(f"Track eklendi: {track.name}")
        return track

    def remove_track(self, track_id: int):
        """Track'i kaldır"""
        self.tracks = [t for t in self.tracks if t.track_id != track_id]
        logger.info(f"Track {track_id} kaldırıldı")

    def clear_tracks(self):
        """Tüm track'leri temizle"""
        self.tracks = []
        logger.info("Tüm track'ler temizlendi")

    def mix_tracks(self, output_path: str, normalize: bool = True) -> bool:
        """Track'leri karıştır ve kaydet"""
        try:
            if len(self.tracks) == 0:
                logger.warning("Track yok!")
                return False

            logger.info(f"🎚️ {len(self.tracks)} track karıştırılıyor...")

            # En uzun track'i bul
            max_length = max(t.audio.shape[1] for t in self.tracks if t.audio is not None)

            # Solo kontrolü
            has_solo = any(t.solo for t in self.tracks)

            # Mix
            mixed = np.zeros((2, max_length))

            for track in self.tracks:
                if has_solo and not track.solo:
                    continue  # Solo olmayan track'leri atla

                track_audio = track.get_audio(max_length)
                mixed += track_audio

            # Master volume
            mixed *= self.master_volume

            # Normalize (clipping prevention)
            if normalize:
                max_val = np.abs(mixed).max()
                if max_val > 1.0:
                    mixed = mixed / max_val * 0.95
                    logger.info("Audio normalize edildi")

            # Clip (-1 to 1)
            mixed = np.clip(mixed, -1.0, 1.0)

            # Kaydet
            sf.write(output_path, mixed.T, self.sr)
            logger.info(f"✅ Mix tamamlandı: {output_path}")

            return True

        except Exception as e:
            logger.error(f"Mix hatası: {e}")
            return False

    def auto_sync_tempo(self):
        """AI ile tempo eşitleme (basit)"""
        try:
            logger.info("🤖 AI tempo sync...")

            # İlk track'in temposunu referans al
            if len(self.tracks) < 2:
                return

            ref_track = self.tracks[0]
            ref_tempo, _ = librosa.beat.beat_track(y=ref_track.audio[0], sr=ref_track.sr)

            logger.info(f"  Referans tempo: {ref_tempo:.1f} BPM")

            # Diğer track'leri time-stretch ile eşitle
            for i, track in enumerate(self.tracks[1:], 1):
                track_tempo, _ = librosa.beat.beat_track(y=track.audio[0], sr=track.sr)

                if abs(track_tempo - ref_tempo) > 5:  # 5 BPM fark varsa
                    rate = track_tempo / ref_tempo
                    logger.info(f"  Track {i}: {track_tempo:.1f} -> {ref_tempo:.1f} BPM (rate={rate:.3f})")

                    # Time stretch
                    track.audio = librosa.effects.time_stretch(track.audio, rate=rate)

            logger.info("✓ Tempo sync tamamlandı")

        except Exception as e:
            logger.error(f"Tempo sync hatası: {e}")

    def auto_match_keys(self):
        """AI ile anahtar eşitleme"""
        try:
            logger.info("🤖 AI key matching...")

            if len(self.tracks) < 2:
                return

            # Key detection için basit chroma analizi
            from core.music_analyzer import MusicAnalyzer
            analyzer = MusicAnalyzer()

            # Referans track
            ref_key = analyzer.detect_key(self.tracks[0].audio[0], self.tracks[0].sr)
            logger.info(f"  Referans key: {ref_key['key']} {ref_key['scale']}")

            # Diğer track'leri eşitle
            key_map = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            ref_idx = key_map.index(ref_key['key'])

            for i, track in enumerate(self.tracks[1:], 1):
                track_key = analyzer.detect_key(track.audio[0], track.sr)
                track_idx = key_map.index(track_key['key'])

                # Pitch shift hesapla
                diff = ref_idx - track_idx
                if abs(diff) > 6:
                    diff = diff - 12 * np.sign(diff)

                if diff != 0:
                    logger.info(f"  Track {i}: {track_key['key']} -> {ref_key['key']} ({diff:+d} semitones)")
                    track.pitch_shift = diff

            logger.info("✓ Key matching tamamlandı")

        except Exception as e:
            logger.error(f"Key matching hatası: {e}")

    def get_track_info(self) -> List[Dict]:
        """Track bilgilerini al"""
        return [
            {
                'id': t.track_id,
                'name': t.name,
                'duration': t.duration,
                'volume': t.volume,
                'pitch': t.pitch_shift,
                'pan': t.pan,
                'mute': t.mute,
                'solo': t.solo
            }
            for t in self.tracks
        ]


if __name__ == "__main__":
    # Test
    mixer = AudioMixer()
    print("Audio Mixer hazır!")
