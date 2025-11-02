"""
Automatic Lyrics Converter
Converts [MM:SS] format lyrics to JSON for karaoke player
"""
import re
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str):
    """
    Parse [MM:SS] or [MM:SS.ms] timestamp to seconds
    Args:
        timestamp_str: String like "[00:21]" or "[01:23.45]"
    Returns:
        Float seconds (e.g., 21.0 or 83.45)
    """
    # Remove brackets and split
    time_str = timestamp_str.strip('[]')

    # Handle MM:SS or MM:SS.ms
    parts = time_str.split(':')
    if len(parts) != 2:
        return None

    minutes = int(parts[0])

    # Handle seconds with optional milliseconds
    if '.' in parts[1]:
        seconds_parts = parts[1].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) / 100.0  # Convert to fraction
        total_seconds = minutes * 60 + seconds + milliseconds
    else:
        seconds = int(parts[1])
        total_seconds = minutes * 60 + seconds

    return total_seconds


def convert_lyrics_txt_to_json(txt_path, output_json_path=None):
    """
    Convert timestamped lyrics.txt to JSON format for karaoke player

    Args:
        txt_path: Path to lyrics.txt file (format: [MM:SS] text)
        output_json_path: Optional custom output path (default: same name with .lyrics.json)

    Returns:
        Path to created JSON file or None if failed
    """
    try:
        txt_path = Path(txt_path)

        if not txt_path.exists():
            logger.error(f"Lyrics file not found: {txt_path}")
            return None

        # Read lyrics file
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse timestamped lines
        segments = []
        pattern = r'^\[(\d{2}:\d{2}(?:\.\d+)?)\]\s*(.*)$'

        for line in lines:
            line = line.strip()
            match = re.match(pattern, line)

            if match:
                timestamp_str = f"[{match.group(1)}]"
                text = match.group(2).strip()

                # Skip empty lines or "Müzik" markers
                if not text or text.lower() == 'müzik':
                    continue

                start_time = parse_timestamp(timestamp_str)
                if start_time is not None:
                    segments.append({
                        'start': start_time,
                        'text': text
                    })

        if not segments:
            logger.warning(f"No valid lyrics found in {txt_path}")
            return None

        # Calculate end times (next segment's start, or +3 seconds for last)
        for i in range(len(segments)):
            if i < len(segments) - 1:
                segments[i]['end'] = segments[i + 1]['start']
            else:
                # Last segment: +3 seconds
                segments[i]['end'] = segments[i]['start'] + 3.0

        # Create JSON structure (Whisper API format)
        lyrics_data = {
            "segments": segments
        }

        # Determine output path
        if output_json_path is None:
            # Same directory, same name, .lyrics.json extension
            output_json_path = txt_path.parent / f"{txt_path.stem}.lyrics.json"
        else:
            output_json_path = Path(output_json_path)

        # Save JSON
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(lyrics_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Lyrics converted successfully!")
        logger.info(f"  Segments: {len(segments)}")
        logger.info(f"  Duration: {segments[-1]['end']:.1f}s")
        logger.info(f"  Output: {output_json_path}")

        return output_json_path

    except Exception as e:
        logger.error(f"Error converting lyrics: {e}")
        return None


def auto_convert_lyrics_in_folder(folder_path):
    """
    Automatically convert all *_lyrics.txt files in a folder to JSON

    Args:
        folder_path: Path to folder containing lyrics files

    Returns:
        List of created JSON file paths
    """
    folder_path = Path(folder_path)
    created_files = []

    # Find all *_lyrics.txt files
    lyrics_files = list(folder_path.glob("*_lyrics.txt"))

    if not lyrics_files:
        logger.info(f"No *_lyrics.txt files found in {folder_path}")
        return created_files

    logger.info(f"Found {len(lyrics_files)} lyrics file(s)")

    for txt_file in lyrics_files:
        logger.info(f"\nConverting: {txt_file.name}")
        json_path = convert_lyrics_txt_to_json(txt_file)

        if json_path:
            created_files.append(json_path)

    return created_files


if __name__ == "__main__":
    # Test with the adiyaman folder
    test_folder = Path("C:/Users/lorrd/Downloads/MediaHuman/Music/ilahi/adiyaman")

    if test_folder.exists():
        print(f"Auto-converting lyrics in: {test_folder}\n")
        created = auto_convert_lyrics_in_folder(test_folder)

        print(f"\n{'='*60}")
        print(f"Created {len(created)} JSON file(s):")
        for f in created:
            print(f"  - {f.name}")
    else:
        print(f"Test folder not found: {test_folder}")
