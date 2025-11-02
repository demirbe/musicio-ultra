"""
AI-Enhanced Pitch Shifter Engine
Kusursuz ses kalitesi için çoklu algoritma kullanır
"""
import os
import numpy as np
import librosa
import soundfile as sf
import pyrubberband as pyrb
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PitchShifter:
    """Profesyonel AI-destekli pitch shifting"""

    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.supported_formats = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']

    def shift_pitch(
        self,
        input_path: str,
        output_path: str,
        semitones: float,
        use_ai_separation: bool = True,
        use_ai_enhancement: bool = True,
        quality: str = "high"
    ) -> Tuple[bool, str]:
        """
        Pitch shifting ana fonksiyon

        Args:
            input_path: Giriş dosya yolu
            output_path: Çıkış dosya yolu
            semitones: Kaç yarım ton değiştirilecek (-12 ile +12 arası)
            use_ai_separation: Vokal/enstrüman ayır (daha temiz sonuç)
            use_ai_enhancement: AI ile kalite artır
            quality: "low", "medium", "high", "ultra"

        Returns:
            (başarılı_mı, mesaj)
        """
        try:
            logger.info(f"Pitch shifting başladı: {semitones} semitones")
            logger.info(f"AI Separation: {use_ai_separation}, AI Enhancement: {use_ai_enhancement}")

            # Dosya kontrolü
            if not os.path.exists(input_path):
                return False, "Dosya bulunamadı!"

            # Geçici dizin
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            # AI ile vokal/enstrüman ayırma (opsiyonel ama önerilen)
            if use_ai_separation and self.model_manager:
                logger.info("🎵 AI ile ses kaynakları ayrıştırılıyor...")
                separated = self.model_manager.separate_vocals(input_path, str(temp_dir))

                if separated:
                    # Her bir kaynağı ayrı ayrı pitch shift yap
                    shifted_sources = []

                    for source_name, source_path in separated.items():
                        logger.info(f"  → {source_name} pitch shifting...")
                        shifted_path = temp_dir / f"{source_name}_shifted.wav"

                        success = self._shift_single_file(
                            source_path,
                            str(shifted_path),
                            semitones,
                            quality
                        )

                        if success:
                            shifted_sources.append(str(shifted_path))

                    # Tüm kaynakları birleştir
                    logger.info("🎼 Kaynaklar birleştiriliyor...")
                    final_audio = self._mix_sources(shifted_sources)

                    # Geçici dosyaya kaydet
                    temp_output = temp_dir / "temp_shifted.wav"
                    sf.write(str(temp_output), final_audio[0], final_audio[1])
                    current_file = str(temp_output)

                else:
                    # Ayırma başarısız, normal yöntem
                    logger.warning("AI ayırma başarısız, standart yöntem kullanılıyor")
                    current_file = input_path
                    self._shift_single_file(input_path, str(temp_dir / "temp_shifted.wav"), semitones, quality)
                    current_file = str(temp_dir / "temp_shifted.wav")
            else:
                # Direkt pitch shift (AI ayırma yok)
                logger.info("📝 Standart pitch shifting...")
                temp_output = temp_dir / "temp_shifted.wav"
                self._shift_single_file(input_path, str(temp_output), semitones, quality)
                current_file = str(temp_output)

            # AI Enhancement (opsiyonel)
            if use_ai_enhancement and self.model_manager and self.model_manager.audiosr_model:
                logger.info("✨ AI ile ses kalitesi artırılıyor...")
                enhanced_path = temp_dir / "enhanced.wav"

                if self.model_manager.enhance_audio(current_file, str(enhanced_path)):
                    current_file = str(enhanced_path)

            # Final output'a kopyala
            logger.info(f"💾 Kaydediliyor: {output_path}")

            # Format dönüşümü
            self._convert_format(current_file, output_path)

            # Temizlik
            self._cleanup_temp(temp_dir)

            logger.info("✅ Pitch shifting tamamlandı!")
            return True, "Başarıyla tamamlandı!"

        except Exception as e:
            error_msg = f"Hata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _shift_single_file(
        self,
        input_path: str,
        output_path: str,
        semitones: float,
        quality: str = "high"
    ) -> bool:
        """Tek bir dosyayı pitch shift yapar"""
        try:
            # Audio yükle (yüksek kalite)
            y, sr = librosa.load(input_path, sr=None, mono=False)

            # Librosa pitch shift (daha stabil)
            y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)

            # Kaydet - stereo/mono kontrolü
            if y_shifted.ndim > 1:
                # Stereo - transpose
                sf.write(output_path, y_shifted.T, sr)
            else:
                # Mono
                sf.write(output_path, y_shifted, sr)

            return True

        except Exception as e:
            logger.error(f"Shift hatası: {e}")
            return False

    def _mix_sources(self, source_paths: list) -> Tuple[np.ndarray, int]:
        """Birden fazla ses kaynağını karıştırır"""
        mixed = None
        sr = None

        for path in source_paths:
            if os.path.exists(path):
                y, current_sr = librosa.load(path, sr=None, mono=False)

                if mixed is None:
                    mixed = y
                    sr = current_sr
                else:
                    # Uzunlukları eşitle
                    min_len = min(mixed.shape[-1], y.shape[-1])
                    mixed = mixed[..., :min_len] + y[..., :min_len]

        return mixed, sr

    def _convert_format(self, input_path: str, output_path: str):
        """Format dönüşümü yapar"""
        y, sr = librosa.load(input_path, sr=None, mono=False)

        # Çıktı formatına göre kaydet
        if output_path.endswith('.mp3'):
            # MP3 için yüksek bitrate
            import subprocess
            subprocess.run([
                'ffmpeg', '-i', input_path,
                '-codec:a', 'libmp3lame',
                '-b:a', '320k',
                '-y', output_path
            ], check=True, capture_output=True)
        else:
            sf.write(output_path, y.T if y.ndim > 1 else y, sr)

    def _cleanup_temp(self, temp_dir: Path):
        """Geçici dosyaları temizler"""
        try:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("🧹 Geçici dosyalar temizlendi")
        except Exception as e:
            logger.warning(f"Temizlik hatası: {e}")

    def get_audio_info(self, file_path: str) -> dict:
        """Ses dosyası bilgilerini döndürür"""
        try:
            y, sr = librosa.load(file_path, sr=None, mono=False)
            duration = librosa.get_duration(y=y, sr=sr)

            return {
                "sample_rate": sr,
                "duration": f"{duration:.2f} saniye",
                "channels": "Stereo" if y.ndim > 1 else "Mono",
                "format": Path(file_path).suffix.upper()
            }
        except Exception as e:
            logger.error(f"Bilgi alma hatası: {e}")
            return {}


# Kolay kullanım için yardımcı fonksiyonlar
def semitones_to_note(semitones: int) -> str:
    """Semitone sayısını nota ismine çevirir"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octaves = semitones // 12
    note_index = semitones % 12

    if octaves > 0:
        return f"+{octaves} oktav, {notes[note_index]}"
    elif octaves < 0:
        return f"{octaves} oktav, {notes[note_index]}"
    else:
        return notes[note_index]


if __name__ == "__main__":
    # Test
    shifter = PitchShifter()
    print("Pitch Shifter Engine hazır!")
