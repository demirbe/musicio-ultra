"""
Professional Format Converter & Metadata Editor
MP3, WAV, FLAC, OGG, M4A conversion + ID3 tags
"""
from pathlib import Path
import subprocess
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FormatConverter:
    """Format dönüştürücü ve metadata editörü"""

    SUPPORTED_FORMATS = ['mp3', 'wav', 'flac', 'ogg', 'm4a']

    def __init__(self):
        self.bitrate_options = {
            'low': '128k',
            'medium': '192k',
            'high': '256k',
            'ultra': '320k'
        }

    def convert(self, input_path: str, output_path: str,
                target_format: str, quality: str = 'high') -> bool:
        """
        Dosya formatını dönüştür
        Args:
            input_path: Kaynak dosya
            output_path: Hedef dosya
            target_format: mp3, wav, flac, ogg, m4a
            quality: low, medium, high, ultra
        """
        try:
            logger.info(f"🔄 Dönüştürülüyor: {Path(input_path).name} -> {target_format}")

            # Load audio
            audio = AudioSegment.from_file(input_path)

            # Export parameters
            export_params = {}

            if target_format == 'mp3':
                export_params['format'] = 'mp3'
                export_params['bitrate'] = self.bitrate_options[quality]
                export_params['parameters'] = ['-q:a', '0']  # Best quality VBR

            elif target_format == 'wav':
                export_params['format'] = 'wav'

            elif target_format == 'flac':
                export_params['format'] = 'flac'
                # FLAC is lossless, no bitrate

            elif target_format == 'ogg':
                export_params['format'] = 'ogg'
                quality_map = {'low': '4', 'medium': '6', 'high': '8', 'ultra': '10'}
                export_params['parameters'] = ['-q:a', quality_map[quality]]

            elif target_format == 'm4a':
                export_params['format'] = 'mp4'
                export_params['bitrate'] = self.bitrate_options[quality]
                export_params['codec'] = 'aac'

            # Export
            audio.export(output_path, **export_params)

            logger.info(f"✅ Dönüştürme tamamlandı: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Dönüştürme hatası: {e}")
            return False

    def get_metadata(self, file_path: str) -> dict:
        """Metadata oku"""
        try:
            ext = Path(file_path).suffix.lower()

            metadata = {}

            if ext == '.mp3':
                audio = MP3(file_path, ID3=EasyID3)
            elif ext == '.flac':
                audio = FLAC(file_path)
            elif ext == '.ogg':
                audio = OggVorbis(file_path)
            elif ext == '.m4a':
                audio = MP4(file_path)
            else:
                return {}

            # Common tags
            for key in ['title', 'artist', 'album', 'date', 'genre']:
                value = audio.get(key)
                if value:
                    metadata[key] = value[0] if isinstance(value, list) else value

            # Duration
            metadata['duration'] = getattr(audio.info, 'length', 0)

            # Bitrate
            metadata['bitrate'] = getattr(audio.info, 'bitrate', 0)

            logger.info(f"📋 Metadata okundu: {Path(file_path).name}")
            return metadata

        except Exception as e:
            logger.error(f"Metadata okuma hatası: {e}")
            return {}

    def set_metadata(self, file_path: str, metadata: dict) -> bool:
        """Metadata yaz"""
        try:
            ext = Path(file_path).suffix.lower()

            if ext == '.mp3':
                audio = MP3(file_path, ID3=EasyID3)
            elif ext == '.flac':
                audio = FLAC(file_path)
            elif ext == '.ogg':
                audio = OggVorbis(file_path)
            elif ext == '.m4a':
                audio = MP4(file_path)
            else:
                logger.warning(f"Desteklenmeyen format: {ext}")
                return False

            # Update tags
            for key, value in metadata.items():
                if key in ['title', 'artist', 'album', 'date', 'genre'] and value:
                    audio[key] = value

            audio.save()

            logger.info(f"✅ Metadata kaydedildi: {Path(file_path).name}")
            return True

        except Exception as e:
            logger.error(f"Metadata yazma hatası: {e}")
            return False

    def batch_convert(self, input_folder: str, output_folder: str,
                      target_format: str, quality: str = 'high') -> int:
        """Toplu dönüştürme"""
        try:
            input_path = Path(input_folder)
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Desteklenen dosyaları bul
            files = []
            for ext in self.SUPPORTED_FORMATS:
                files.extend(input_path.glob(f"*.{ext}"))

            logger.info(f"📁 {len(files)} dosya bulundu")

            converted = 0
            for file in files:
                output_file = output_path / f"{file.stem}.{target_format}"

                if self.convert(str(file), str(output_file), target_format, quality):
                    converted += 1

            logger.info(f"✅ Toplu dönüştürme tamamlandı: {converted}/{len(files)}")
            return converted

        except Exception as e:
            logger.error(f"Toplu dönüştürme hatası: {e}")
            return 0

    def change_bitrate(self, input_path: str, output_path: str,
                       target_bitrate: str) -> bool:
        """Bitrate değiştir (MP3 için)"""
        try:
            logger.info(f"🔄 Bitrate değiştiriliyor: {target_bitrate}")

            audio = AudioSegment.from_file(input_path)
            audio.export(
                output_path,
                format='mp3',
                bitrate=target_bitrate,
                parameters=['-q:a', '0']
            )

            logger.info(f"✅ Bitrate değiştirildi: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Bitrate değiştirme hatası: {e}")
            return False


if __name__ == "__main__":
    # Test
    converter = FormatConverter()
    print("Format Converter hazır!")
    print(f"Desteklenen formatlar: {', '.join(converter.SUPPORTED_FORMATS)}")
