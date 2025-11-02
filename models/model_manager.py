"""
AI Model Yöneticisi - Otomatik model indirme ve yükleme
"""
import os
import torch
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """AI modellerini yönetir ve yükler"""

    def __init__(self, models_dir: str = "models/weights"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # CUDA kontrolü
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            logger.info(f"CUDA {torch.version.cuda} tespit edildi")
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"PyTorch: {torch.__version__}")

            # RTX 5090 AGGRESSIVE MEMORY ALLOCATION
            # VRAM'i önceden ayır (cache'i temizle ve yeniden ayır)
            torch.cuda.empty_cache()

            # PyTorch memory allocator ayarları - Agresif
            torch.cuda.set_per_process_memory_fraction(0.95)  # %95 VRAM kullan

            # Cudnn benchmark - En hızlı algoritmaları bul
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False  # Speed > reproducibility

            logger.info("🚀 AGGRESSIVE MODE: %95 VRAM tahsis edildi")
        else:
            logger.warning("CUDA bulunamadı! CPU modunda çalışılıyor.")

        self.demucs_model = None
        self.audiosr_model = None

    def load_demucs(self, model_name: str = "htdemucs_6s") -> object:
        """
        Demucs v4 modelini yükler (Facebook Research)
        EN YÜKSEK KALITE: 6-stem model
        - drums (davul)
        - bass (bas)
        - vocals (vokal)
        - guitar (gitar)
        - piano (piyano)
        - other (diğer enstrümanlar)
        """
        try:
            from demucs.pretrained import get_model
            from demucs.apply import apply_model

            logger.info(f"Demucs modeli yükleniyor: {model_name}")

            # Model indir ve yükle
            self.demucs_model = get_model(model_name)
            self.demucs_model.to(self.device)
            self.demucs_model.eval()

            logger.info(f"✓ Demucs başarıyla yüklendi ({self.device})")
            return self.demucs_model

        except Exception as e:
            logger.error(f"Demucs yükleme hatası: {e}")
            return None

    def load_audiosr(self) -> object:
        """
        AudioSR modelini yükler - AI tabanlı ses iyileştirme
        48kHz upsampling ve kalite artırma
        """
        try:
            from audiosr import build_model, super_resolution

            logger.info("AudioSR modeli yükleniyor (EN YÜKSEK KALITE)...")

            # Model otomatik indirilir
            # AudioSR'da sadece 'basic' ve 'speech' var, 'basic' en iyisi
            self.audiosr_model = build_model(model_name="basic", device=self.device)

            logger.info(f"✓ AudioSR başarıyla yüklendi ({self.device})")
            return self.audiosr_model

        except Exception as e:
            logger.error(f"AudioSR yükleme hatası: {e}")
            logger.info("AudioSR olmadan devam edilecek (opsiyonel)")
            return None

    def separate_vocals(self, audio_path: str, output_dir: str = "temp") -> dict:
        """
        Vokal ve enstrümanları ayırır (Demucs ile)
        Daha temiz pitch shifting için
        """
        if self.demucs_model is None:
            self.load_demucs()

        try:
            import torchaudio
            from demucs.apply import apply_model
            import librosa
            import numpy as np

            logger.info(f"Ses ayrıştırılıyor: {audio_path}")

            # Dosya yolunu normalize et (Windows için)
            audio_path_normalized = str(Path(audio_path).resolve())

            # Audio yükle - librosa kullan (daha uyumlu)
            try:
                wav_np, sr = librosa.load(audio_path_normalized, sr=44100, mono=False)

                # Numpy'dan torch'a çevir
                if wav_np.ndim == 1:
                    wav_np = np.stack([wav_np, wav_np])  # Mono -> Stereo

                wav = torch.from_numpy(wav_np).float().to(self.device)

            except Exception as e:
                logger.error(f"Librosa ile yükleme başarısız, torchaudio deneniyor: {e}")
                wav, sr = torchaudio.load(audio_path_normalized)
                wav = wav.to(self.device)

            # Stereo'ya çevir (gerekirse)
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)

            # Model uygula - RTX 5090 AGGRESSIVE OPTIMIZATION
            with torch.no_grad():
                # Mixed precision için autocast
                with torch.amp.autocast('cuda'):
                    sources = apply_model(
                        self.demucs_model,
                        wav.unsqueeze(0),
                        device=self.device,
                        shifts=10,  # 1 -> 10 (daha yüksek kalite, daha fazla GPU kullanımı)
                        split=False,  # True -> False (Tüm audio'yu tek seferde işle - daha fazla RAM/VRAM)
                        overlap=0.5,  # 0.25 -> 0.5 (Daha fazla overlap - daha iyi kalite, daha fazla hesaplama)
                        progress=True,
                        num_workers=16  # 8 -> 16 (Daha fazla paralel thread - CPU/RAM kullanımı artar)
                    )[0]

            # Kaynak isimleri - Demucs modelinin source sayısına göre
            # htdemucs_6s: drums, bass, other, vocals, guitar, piano (6 stem)
            # htdemucs_ft: drums, bass, other, vocals (4 stem)

            # Model'in sources attribute'unu kontrol et
            if hasattr(self.demucs_model, 'sources'):
                source_names = self.demucs_model.sources
            else:
                # Fallback: sources sayısına göre tahmin et
                num_sources = sources.shape[0]
                if num_sources == 6:
                    source_names = ['drums', 'bass', 'other', 'vocals', 'guitar', 'piano']
                elif num_sources == 4:
                    source_names = ['drums', 'bass', 'other', 'vocals']
                else:
                    source_names = [f'source_{i}' for i in range(num_sources)]

            logger.info(f"🎵 {len(source_names)} enstrüman ayrılıyor: {', '.join(source_names)}")

            output_paths = {}
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            for i, name in enumerate(source_names):
                output_file = output_path / f"{name}.wav"
                torchaudio.save(
                    str(output_file),
                    sources[i].cpu(),
                    sr
                )
                output_paths[name] = str(output_file)
                logger.info(f"  ✓ {name} kaydedildi")

            return output_paths

        except Exception as e:
            logger.error(f"Vokal ayırma hatası: {e}")
            return {}

    def enhance_audio(self, audio_path: str, output_path: str) -> bool:
        """
        AudioSR ile ses kalitesini artırır
        Büyük dosyalar için parça parça işleme (chunk-based)
        """
        if self.audiosr_model is None:
            logger.info("AudioSR yüklenmemiş, atlanıyor...")
            return False

        try:
            import soundfile as sf
            import librosa
            import numpy as np
            from audiosr import super_resolution

            logger.info("Ses kalitesi artırılıyor (AI)...")

            # Ses dosyasını yükle
            audio, sr = librosa.load(audio_path, sr=None, mono=False)

            # Dosya uzunluğunu kontrol et (saniye)
            if audio.ndim > 1:
                duration = len(audio[0]) / sr
                channels = audio.shape[0]
            else:
                duration = len(audio) / sr
                channels = 1

            logger.info(f"📊 Dosya süresi: {duration:.1f}s, {channels} kanal")

            # 8 saniyelik parçalar halinde işle (bellek güvenliği için)
            chunk_duration = 8  # saniye
            chunk_samples = int(chunk_duration * sr)
            overlap_samples = int(0.5 * sr)  # 0.5 saniye overlap (geçiş yumuşatma için)

            # Kısa dosyalar direkt işle
            if duration <= chunk_duration:
                logger.info("Kısa dosya, tek seferde işleniyor (FULL KALITE)...")
                enhanced = super_resolution(
                    self.audiosr_model,
                    audio_path,
                    seed=42,
                    guidance_scale=3.5,  # Kalite kontrolü (varsayılan)
                    ddim_steps=200,      # EN YÜKSEK KALITE (50 -> 200)
                    latent_t_per_second=12.8
                )
                sf.write(output_path, enhanced, 48000)
                logger.info(f"✓ Kalite artırıldı: {output_path}")
                return True

            # Uzun dosyalar için chunk-based işleme
            logger.info(f"🔄 Uzun dosya tespit edildi. {int(duration/chunk_duration)+1} parçada işlenecek...")

            # Temp dizini oluştur
            temp_dir = Path("temp") / "audiosr_chunks"
            temp_dir.mkdir(parents=True, exist_ok=True)

            enhanced_chunks = []
            total_samples = audio.shape[-1] if audio.ndim > 1 else len(audio)

            chunk_count = 0
            start_idx = 0

            while start_idx < total_samples:
                end_idx = min(start_idx + chunk_samples, total_samples)
                chunk_count += 1

                # Chunk'ı ayıkla
                if audio.ndim > 1:
                    chunk = audio[:, start_idx:end_idx]
                else:
                    chunk = audio[start_idx:end_idx]

                # Chunk'ı geçici dosyaya kaydet
                chunk_path = temp_dir / f"chunk_{chunk_count}.wav"
                sf.write(str(chunk_path), chunk.T if audio.ndim > 1 else chunk, sr)

                logger.info(f"  🎵 Parça {chunk_count} işleniyor... ({start_idx/sr:.1f}s - {end_idx/sr:.1f}s)")

                try:
                    # AudioSR ile işle (FULL KALITE)
                    enhanced_chunk = super_resolution(
                        self.audiosr_model,
                        str(chunk_path),
                        seed=42,
                        guidance_scale=3.5,
                        ddim_steps=200,  # EN YÜKSEK KALITE (50 -> 200)
                        latent_t_per_second=12.8
                    )

                    enhanced_chunks.append(enhanced_chunk)
                    logger.info(f"  ✓ Parça {chunk_count} tamamlandı")

                except Exception as e:
                    logger.error(f"  ❌ Parça {chunk_count} hatası: {e}")
                    logger.info("  ⚠️ Bu parça orijinal kalitede bırakılacak")
                    # Hata durumunda orijinal chunk'ı kullan
                    if audio.ndim > 1:
                        enhanced_chunks.append(chunk.T)
                    else:
                        enhanced_chunks.append(chunk)

                finally:
                    # Temp chunk'ı sil
                    if chunk_path.exists():
                        chunk_path.unlink()

                # Overlap ile ilerle (daha yumuşak geçişler için)
                start_idx += chunk_samples - overlap_samples

                # CUDA belleğini temizle
                if self.device == "cuda":
                    torch.cuda.empty_cache()

            # Tüm chunk'ları birleştir
            logger.info("🔗 Parçalar birleştiriliyor...")

            # Overlap bölgelerinde cross-fade uygula
            final_audio = enhanced_chunks[0]

            for i in range(1, len(enhanced_chunks)):
                # Cross-fade için overlap bölgesi
                fade_samples = min(overlap_samples, len(final_audio), len(enhanced_chunks[i]))

                if fade_samples > 0:
                    # Fade out (önceki chunk'ın sonu)
                    fade_out = np.linspace(1, 0, fade_samples)
                    # Fade in (yeni chunk'ın başı)
                    fade_in = np.linspace(0, 1, fade_samples)

                    # Son chunk'ı kısalt ve fade uygula
                    final_audio = final_audio[:-fade_samples]

                    # Overlap bölgesini karıştır
                    overlap_part = (final_audio[-fade_samples:].T * fade_out +
                                   enhanced_chunks[i][:fade_samples].T * fade_in).T

                    # Birleştir
                    final_audio = np.concatenate([
                        final_audio,
                        overlap_part,
                        enhanced_chunks[i][fade_samples:]
                    ], axis=0)
                else:
                    # Overlap yoksa direkt ekle
                    final_audio = np.concatenate([final_audio, enhanced_chunks[i]], axis=0)

            # Final audio'yu kaydet
            sf.write(output_path, final_audio, 48000)

            # Temp dizinini temizle
            try:
                temp_dir.rmdir()
            except:
                pass

            logger.info(f"✅ Tüm parçalar işlendi ve birleştirildi: {output_path}")
            logger.info(f"📊 Toplam {chunk_count} parça, {duration:.1f}s ses kalitesi artırıldı")
            return True

        except Exception as e:
            logger.error(f"Ses iyileştirme hatası: {e}")
            logger.info("⚠️ AudioSR olmadan devam ediliyor...")
            return False

    def get_device_info(self) -> dict:
        """Sistem bilgilerini döndürür"""
        info = {
            "device": self.device,
            "pytorch_version": torch.__version__,
        }

        if self.device == "cuda":
            info.update({
                "cuda_version": torch.version.cuda,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB",
                "cudnn_version": torch.backends.cudnn.version(),
            })

        return info

    def get_gpu_usage(self) -> dict:
        """Anlık GPU kullanım bilgilerini döndürür"""
        if self.device != "cuda":
            return {"available": False}

        try:
            # GPU bellek kullanımı
            allocated = torch.cuda.memory_allocated(0) / 1e9  # GB
            reserved = torch.cuda.memory_reserved(0) / 1e9  # GB
            total = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB

            usage_percent = (allocated / total) * 100

            return {
                "available": True,
                "allocated_gb": allocated,
                "reserved_gb": reserved,
                "total_gb": total,
                "usage_percent": usage_percent,
                "free_gb": total - allocated
            }
        except Exception as e:
            logger.error(f"GPU kullanım bilgisi alınamadı: {e}")
            return {"available": False}


if __name__ == "__main__":
    # Test
    manager = ModelManager()
    print("\n=== Sistem Bilgileri ===")
    for key, value in manager.get_device_info().items():
        print(f"{key}: {value}")

    print("\n=== Model Yükleme ===")
    manager.load_demucs()
    manager.load_audiosr()
