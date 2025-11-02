"""
Professional Audio Recorder
Canlı mikrofon kaydı ve real-time pitch preview
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import queue
from pathlib import Path
from typing import Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioRecorder:
    """Profesyonel ses kaydedici - real-time pitch shifting ile"""

    def __init__(self, sample_rate: int = 96000, channels: int = 2):
        """
        EN YÜKSEK KALITE AYARLARI:
        - 96kHz sample rate (studio kalitesi, 48kHz -> 96kHz)
        - 2 kanal (stereo)
        - 32-bit float precision (sounddevice varsayılan)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.is_monitoring = False
        self.audio_queue = queue.Queue()
        self.recorded_frames = []
        self.stream = None

        # Real-time processing
        self.pitch_shift_semitones = 0
        self.apply_realtime_pitch = False
        self.callback_func: Optional[Callable] = None

    def list_devices(self):
        """Ses cihazlarını listele"""
        devices = sd.query_devices()
        logger.info("🎤 Kullanılabilir ses cihazları:")
        for i, device in enumerate(devices):
            logger.info(f"  [{i}] {device['name']} - Giriş: {device['max_input_channels']}, Çıkış: {device['max_output_channels']}")
        return devices

    def start_recording(self, device: Optional[int] = None):
        """Kaydı başlat"""
        if self.is_recording:
            logger.warning("Kayıt zaten devam ediyor!")
            return False

        try:
            self.is_recording = True
            self.recorded_frames = []

            logger.info(f"🎙️ Kayıt başladı: {self.sample_rate}Hz, {self.channels} kanal")

            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Kayıt hatası: {status}")

                # Veriyi kuyruğa ekle
                self.audio_queue.put(indata.copy())
                self.recorded_frames.append(indata.copy())

                # Real-time pitch shift (eğer aktifse)
                if self.apply_realtime_pitch and self.pitch_shift_semitones != 0:
                    shifted = self._realtime_pitch_shift(indata)
                    # Callback function varsa çağır (GUI güncelleme için)
                    if self.callback_func:
                        self.callback_func(shifted)

            # Stream başlat (EN YÜKSEK KALITE)
            self.stream = sd.InputStream(
                device=device,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback,
                blocksize=4096,  # Daha büyük buffer (2048 -> 4096) = daha az CPU, daha stabil
                dtype='float32'  # 32-bit float (en yüksek precision)
            )
            self.stream.start()
            logger.info("✓ Kayıt aktif")
            return True

        except Exception as e:
            logger.error(f"Kayıt başlatma hatası: {e}")
            self.is_recording = False
            return False

    def stop_recording(self, output_path: Optional[str] = None) -> Optional[str]:
        """Kaydı durdur ve kaydet"""
        if not self.is_recording:
            logger.warning("Kayıt zaten durmuş!")
            return None

        try:
            self.is_recording = False

            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            # Tüm frame'leri birleştir
            if len(self.recorded_frames) == 0:
                logger.warning("Kayıtlı veri yok!")
                return None

            audio_data = np.concatenate(self.recorded_frames, axis=0)

            # Dosyaya kaydet
            if output_path is None:
                output_path = f"recordings/recording_{int(time.time())}.wav"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # EN YÜKSEK KALITE: 32-bit float PCM WAV
            sf.write(str(output_path), audio_data, self.sample_rate, subtype='FLOAT')

            duration = len(audio_data) / self.sample_rate
            logger.info(f"✓ Kayıt tamamlandı: {output_path} ({duration:.1f}s)")

            return str(output_path)

        except Exception as e:
            logger.error(f"Kayıt durdurma hatası: {e}")
            return None

    def start_monitoring(self, pitch_semitones: float = 0):
        """Real-time monitoring başlat (kendi sesini duy)"""
        self.is_monitoring = True
        self.pitch_shift_semitones = pitch_semitones
        self.apply_realtime_pitch = True
        logger.info(f"🎧 Monitoring aktif (Pitch: {pitch_semitones:+.1f})")

    def stop_monitoring(self):
        """Monitoring durdur"""
        self.is_monitoring = False
        self.apply_realtime_pitch = False
        logger.info("🎧 Monitoring durduruldu")

    def _realtime_pitch_shift(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Real-time pitch shift (hızlı algoritma gerekli)
        Bu basit bir implementasyon - production'da daha gelişmiş kullanılabilir
        """
        try:
            # Basit pitch shift - phase vocoder veya time-stretch kullanılabilir
            # Şimdilik basit bir resampling yapıyoruz
            shift_factor = 2 ** (self.pitch_shift_semitones / 12.0)

            # Scipy ile resample
            from scipy import signal
            num_samples = int(len(audio_chunk) / shift_factor)
            shifted = signal.resample(audio_chunk, num_samples)

            # Orijinal uzunluğa getir (padding/cropping)
            if len(shifted) < len(audio_chunk):
                # Pad
                padding = len(audio_chunk) - len(shifted)
                shifted = np.pad(shifted, ((0, padding), (0, 0)), mode='constant')
            else:
                # Crop
                shifted = shifted[:len(audio_chunk)]

            return shifted

        except Exception as e:
            logger.error(f"Real-time pitch shift hatası: {e}")
            return audio_chunk

    def get_input_volume(self) -> float:
        """Giriş seviyesini al (VU meter için)"""
        try:
            if not self.audio_queue.empty():
                chunk = self.audio_queue.get_nowait()
                rms = np.sqrt(np.mean(chunk ** 2))
                db = 20 * np.log10(rms + 1e-10)
                # -60dB ile 0dB arası normalize et
                normalized = (db + 60) / 60
                return max(0, min(1, normalized))
        except:
            pass
        return 0.0

    def set_pitch_callback(self, callback: Callable):
        """Real-time pitch shifted audio için callback ayarla"""
        self.callback_func = callback


if __name__ == "__main__":
    # Test
    recorder = AudioRecorder()
    recorder.list_devices()

    print("\n3 saniye kayıt yapılacak...")
    recorder.start_recording()

    import time
    time.sleep(3)

    output = recorder.stop_recording("test_recording.wav")
    print(f"Kaydedildi: {output}")
