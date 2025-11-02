"""
Batch Audio Processor
Toplu dosya işleme sistemi
"""
from pathlib import Path
from typing import List, Dict, Callable
import threading
import queue
import logging
from core.pitch_shifter import PitchShifter
from models.model_manager import ModelManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Toplu işlem yöneticisi"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.pitch_shifter = PitchShifter(self.model_manager)
        self.queue = queue.Queue()
        self.is_processing = False
        self.current_job = None
        self.progress_callback: Callable = None

    def add_files(self, file_paths: List[str]):
        """İşlem kuyruğuna dosya ekle"""
        for path in file_paths:
            self.queue.put(path)
        logger.info(f"📋 {len(file_paths)} dosya kuyruğa eklendi")

    def add_folder(self, folder_path: str, extensions: List[str] = None):
        """Klasördeki tüm dosyaları ekle"""
        if extensions is None:
            extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']

        folder = Path(folder_path)
        files = []

        for ext in extensions:
            files.extend(folder.glob(f"*{ext}"))

        file_paths = [str(f) for f in files]
        self.add_files(file_paths)

        return len(file_paths)

    def process_batch(self, settings: Dict, output_folder: str = None):
        """
        Toplu işlemi başlat
        settings: {
            'pitch_semitones': float,
            'use_ai_separation': bool,
            'use_ai_enhancement': bool,
            'quality': str
        }
        """
        if self.is_processing:
            logger.warning("İşlem zaten devam ediyor!")
            return False

        def process():
            self.is_processing = True
            total = self.queue.qsize()
            processed = 0

            logger.info(f"🚀 Toplu işlem başlıyor: {total} dosya")

            while not self.queue.empty():
                try:
                    input_file = self.queue.get()
                    self.current_job = input_file

                    # Output path
                    input_path = Path(input_file)
                    if output_folder:
                        output_path = Path(output_folder) / f"processed_{input_path.name}"
                    else:
                        output_path = input_path.parent / f"processed_{input_path.name}"

                    # İşle
                    logger.info(f"  [{processed+1}/{total}] İşleniyor: {input_path.name}")

                    success, message = self.pitch_shifter.shift_pitch(
                        str(input_path),
                        str(output_path),
                        settings['pitch_semitones'],
                        settings.get('use_ai_separation', False),
                        settings.get('use_ai_enhancement', False),
                        settings.get('quality', 'high')
                    )

                    processed += 1

                    # Progress callback
                    if self.progress_callback:
                        self.progress_callback(processed, total, input_path.name, success)

                    if success:
                        logger.info(f"    ✓ Başarılı: {output_path.name}")
                    else:
                        logger.error(f"    ✗ Hata: {message}")

                except Exception as e:
                    logger.error(f"İşlem hatası: {e}")

                finally:
                    self.queue.task_done()

            self.is_processing = False
            self.current_job = None
            logger.info(f"✅ Toplu işlem tamamlandı: {processed}/{total}")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()
        return True

    def get_queue_size(self) -> int:
        """Kuyruktaki dosya sayısı"""
        return self.queue.qsize()

    def clear_queue(self):
        """Kuyruğu temizle"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                break
        logger.info("🗑️ Kuyruk temizlendi")

    def set_progress_callback(self, callback: Callable):
        """Progress callback ayarla"""
        self.progress_callback = callback


if __name__ == "__main__":
    # Test
    processor = BatchProcessor()
    print("Batch Processor hazır!")
