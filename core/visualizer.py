"""
Professional Audio Visualizer
Waveform, Spectrogram, Real-time VU meter
"""
import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Backend for PIL
import matplotlib.pyplot as plt
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioVisualizer:
    """Profesyonel ses görselleştirme"""

    def __init__(self, figsize=(12, 6), dpi=100):
        self.figsize = figsize
        self.dpi = dpi
        plt.style.use('dark_background')

    def generate_waveform(self, audio_path: str, output_path: str = None) -> Image.Image:
        """
        Waveform (dalga formu) görselleştirme
        """
        try:
            logger.info(f"📊 Waveform oluşturuluyor...")

            y, sr = librosa.load(audio_path, sr=None)

            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            # Waveform çiz
            librosa.display.waveshow(y, sr=sr, ax=ax, color='#667eea')

            ax.set_title('Waveform', fontsize=16, color='white')
            ax.set_xlabel('Zaman (s)', fontsize=12, color='white')
            ax.set_ylabel('Genlik', fontsize=12, color='white')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            # PIL Image'e çevir
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            img = Image.open(buf)

            if output_path:
                img.save(output_path)
                logger.info(f"✓ Waveform kaydedildi: {output_path}")

            plt.close(fig)
            return img

        except Exception as e:
            logger.error(f"Waveform hatası: {e}")
            return None

    def generate_spectrogram(self, audio_path: str, output_path: str = None) -> Image.Image:
        """
        Spectrogram (frekans analizi) görselleştirme
        """
        try:
            logger.info(f"📊 Spectrogram oluşturuluyor...")

            y, sr = librosa.load(audio_path, sr=None)

            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            # STFT
            D = librosa.stft(y)
            S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

            # Spectrogram çiz
            img_spec = librosa.display.specshow(
                S_db,
                sr=sr,
                x_axis='time',
                y_axis='hz',
                ax=ax,
                cmap='magma'
            )

            ax.set_title('Spectrogram', fontsize=16, color='white')
            ax.set_xlabel('Zaman (s)', fontsize=12, color='white')
            ax.set_ylabel('Frekans (Hz)', fontsize=12, color='white')

            # Colorbar
            cbar = fig.colorbar(img_spec, ax=ax, format='%+2.0f dB')
            cbar.ax.tick_params(colors='white')

            plt.tight_layout()

            # PIL Image'e çevir
            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            img = Image.open(buf)

            if output_path:
                img.save(output_path)
                logger.info(f"✓ Spectrogram kaydedildi: {output_path}")

            plt.close(fig)
            return img

        except Exception as e:
            logger.error(f"Spectrogram hatası: {e}")
            return None

    def generate_mel_spectrogram(self, audio_path: str, output_path: str = None) -> Image.Image:
        """
        Mel Spectrogram (insan işitmesine göre)
        """
        try:
            logger.info(f"📊 Mel Spectrogram oluşturuluyor...")

            y, sr = librosa.load(audio_path, sr=None)

            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            # Mel spectrogram
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
            S_db = librosa.power_to_db(S, ref=np.max)

            # Görselleştir
            img_spec = librosa.display.specshow(
                S_db,
                sr=sr,
                x_axis='time',
                y_axis='mel',
                ax=ax,
                cmap='viridis'
            )

            ax.set_title('Mel Spectrogram', fontsize=16, color='white')
            ax.set_xlabel('Zaman (s)', fontsize=12, color='white')
            ax.set_ylabel('Mel Frekans', fontsize=12, color='white')

            cbar = fig.colorbar(img_spec, ax=ax, format='%+2.0f dB')
            cbar.ax.tick_params(colors='white')

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            img = Image.open(buf)

            if output_path:
                img.save(output_path)
                logger.info(f"✓ Mel Spectrogram kaydedildi: {output_path}")

            plt.close(fig)
            return img

        except Exception as e:
            logger.error(f"Mel Spectrogram hatası: {e}")
            return None

    def generate_chromagram(self, audio_path: str, output_path: str = None) -> Image.Image:
        """
        Chromagram (müzik notaları görselleştirme)
        """
        try:
            logger.info(f"📊 Chromagram oluşturuluyor...")

            y, sr = librosa.load(audio_path, sr=None)

            fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            # Chromagram
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

            img_chroma = librosa.display.specshow(
                chroma,
                sr=sr,
                x_axis='time',
                y_axis='chroma',
                ax=ax,
                cmap='coolwarm'
            )

            ax.set_title('Chromagram', fontsize=16, color='white')
            ax.set_xlabel('Zaman (s)', fontsize=12, color='white')
            ax.set_ylabel('Pitch Class', fontsize=12, color='white')

            cbar = fig.colorbar(img_chroma, ax=ax)
            cbar.ax.tick_params(colors='white')

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none')
            buf.seek(0)
            img = Image.open(buf)

            if output_path:
                img.save(output_path)
                logger.info(f"✓ Chromagram kaydedildi: {output_path}")

            plt.close(fig)
            return img

        except Exception as e:
            logger.error(f"Chromagram hatası: {e}")
            return None

    def create_vu_meter_image(self, level: float, peak: float) -> Image.Image:
        """
        VU Meter görüntüsü oluştur (real-time için)
        level: 0.0-1.0
        peak: 0.0-1.0
        """
        try:
            fig, ax = plt.subplots(figsize=(6, 1), dpi=self.dpi)

            # Level bar
            colors = ['green'] * 60 + ['yellow'] * 20 + ['red'] * 20
            bar_count = int(level * 100)

            ax.barh(0, bar_count, height=0.5, color=colors[:bar_count])
            ax.barh(0, 100, height=0.5, fill=False, edgecolor='white', linewidth=2)

            # Peak marker
            if peak > 0:
                ax.axvline(x=peak * 100, color='red', linewidth=3, linestyle='--')

            ax.set_xlim(0, 100)
            ax.set_ylim(-0.5, 0.5)
            ax.axis('off')

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', facecolor='#1a1a2e', edgecolor='none', transparent=True)
            buf.seek(0)
            img = Image.open(buf)

            plt.close(fig)
            return img

        except Exception as e:
            logger.error(f"VU meter hatası: {e}")
            return None


if __name__ == "__main__":
    # Test
    vis = AudioVisualizer()
    print("Visualizer hazır!")
