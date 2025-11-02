# MUSICIO ULTRA - AI-Powered Music Studio

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.8.0-red.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.9-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![GPU](https://img.shields.io/badge/GPU-RTX%205090%20Compatible-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-orange.svg)

**Professional AI Music Production Suite with Real-time Karaoke, Vocal Separation, and Advanced Audio Processing**

**IMPORTANT: This project is currently in active development. Features may change, and bugs may exist. Use at your own risk.**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Requirements](#system-requirements) • [Contributing](#contributing)

</div>

---

## Features

### **Professional Karaoke Studio (ULTRA MODE)**
- **Real-time Karaoke Recording** with ultra-low latency (<3ms @ 48kHz)
- **Professional FX Controls**:
  - Studio-quality Reverb (room size, wet/dry mix)
  - Professional Compressor (threshold, ratio, attack/release)
  - 3-Band Equalizer (Bass, Mid, Treble)
  - Echo/Delay Effect (delay time, feedback, mix)
- **Synchronized Lyrics Display** (3-line view: previous, current, next)
- **Waveform Visualization** with seek functionality
- **Automatic Lyrics Conversion** from `[MM:SS] text` format to JSON
- **Backing Track Auto-Discovery** in output folder
- **Device Preference Memory** (microphone, speaker, output folder)

### **AI Vocal Separation**
- **Demucs htdemucs_6s** model for state-of-the-art separation
- Separates into: Vocals, Bass, Drums, Guitar, Piano, Other
- GPU-accelerated processing (CUDA 12.9)
- Aggressive VRAM allocation (95% utilization for maximum performance)

### **Music Analysis & Processing**
- **BPM Detection** using multiple algorithms
- **Key & Scale Detection** (music21 integration)
- **Chord Progression Analysis**
- **Pitch Detection** with CREPE
- **Audio Super-Resolution** (AudioSR upsampling)
- **Noise Reduction** using spectral gating

### **Advanced Audio Effects**
- **Time-stretching** without pitch change (rubberband)
- **Pitch-shifting** without tempo change
- **Professional Audio Effects** (VST-quality pedalboard)
- **Reverb, Compressor, EQ, Delay** effects
- **Real-time FX processing** during karaoke

### **Lyrics & Transcription**
- **OpenAI Whisper Integration** for automatic transcription
- **Timestamp Synchronization** for karaoke display
- **Multiple Format Support**:
  - Whisper API format (`{"segments": [...]}`)
  - Simple timestamped format (`[MM:SS] text`)
- **Automatic Conversion** between formats

### **Format Conversion**
- **Multi-format Support**: MP3, WAV, FLAC, OGG, M4A
- **Metadata Preservation** using mutagen
- **FFmpeg Integration** for advanced conversions
- **YouTube Download** via yt-dlp

### **Modern GUI**
- **CustomTkinter** dark-themed interface
- **Real-time VU Meters** for audio monitoring
- **Professional Control Layout**
- **Preset System** for quick FX configurations
- **Waveform Display** with matplotlib integration

---

## System Requirements

### **MINIMUM REQUIREMENTS:**
- **OS**: Windows 10/11 (64-bit) or Linux (Ubuntu 20.04+)
- **CPU**: Intel Core i5 / AMD Ryzen 5 (4+ cores)
- **RAM**: 16 GB
- **GPU**: NVIDIA GPU with 8GB VRAM (GTX 1080 / RTX 2060 or better)
- **CUDA**: 12.9
- **Storage**: 10 GB free space
- **Python**: 3.10 or 3.11

### **RECOMMENDED FOR BEST PERFORMANCE:**
- **OS**: Windows 11 (64-bit) or Linux (Ubuntu 22.04+)
- **CPU**: Intel Core i7/i9 / AMD Ryzen 7/9 (8+ cores)
- **RAM**: 32 GB or more
- **GPU**: **NVIDIA RTX 5090 (24GB VRAM) - FULLY OPTIMIZED AND TESTED**
  - Also compatible with: RTX 4090, RTX 4080, RTX 3090, RTX 3080
- **CUDA**: 12.9
- **Storage**: SSD with 20+ GB free space
- **Python**: 3.10 (recommended for best compatibility)

### **AUDIO HARDWARE:**
- **Microphone**: USB or XLR microphone (for karaoke)
- **Audio Interface**: **HIGHLY RECOMMENDED - Professional audio interface for best karaoke experience**
  - Tested with professional sound cards (Focusrite Scarlett, Universal Audio, RME, MOTU, etc.)
  - Ultra-low latency performance (<3ms) with ASIO drivers
  - Perfect 1:1 synchronization between backing track and vocal input
  - Zero audio dropouts or crackling with proper audio interface
  - **NOTE:** Built-in motherboard audio may work but can have higher latency
- **Headphones/Speakers**: Studio monitors or quality headphones for monitoring

---

## Installation

### **Windows Installation (RECOMMENDED FOR RTX 5090)**

#### **Step 1: Install Prerequisites**

1. **Install Python 3.10**
   ```bash
   # Download from: https://www.python.org/downloads/release/python-3100/
   # IMPORTANT: Check "Add Python to PATH" during installation
   ```

2. **Install CUDA 12.9**
   ```bash
   # Download from: https://developer.nvidia.com/cuda-12-9-0-download-archive
   # Select: Windows > x86_64 > 11 > exe (local)
   # CRITICAL FOR RTX 5090: Install CUDA 12.9 exactly (not 12.8 or 12.10)
   ```

3. **Install FFmpeg**
   ```bash
   # Download from: https://www.gyan.dev/ffmpeg/builds/
   # Extract to C:\ffmpeg
   # Add C:\ffmpeg\bin to System PATH
   ```

4. **Install Git** (optional, for cloning)
   ```bash
   # Download from: https://git-scm.com/download/win
   ```

#### **Step 2: Clone Repository**

```bash
git clone https://github.com/yourusername/musicio-ultra.git
cd musicio-ultra
```

Or download ZIP and extract.

#### **Step 3: Create Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

#### **Step 4: Install Dependencies**

```bash
# RTX 5090 OPTIMIZED INSTALLATION
# CRITICAL: Install PyTorch with EXACT versions for CUDA 12.9 support
# These versions are REQUIRED for RTX 5090 compatibility:
#   - PyTorch: 2.8.0
#   - TorchVision: 0.23.0  (NOT 0.23 or other versions)
#   - TorchAudio: 2.8.0
#   - CUDA: 12.9 (NOT 12.8 or 12.10)
# Using different versions will cause compatibility issues!

pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu129

# Install all other dependencies
pip install -r requirements.txt

# If you get errors with some packages, install them individually:
# pip install demucs audiosr openai-whisper customtkinter pedalboard sounddevice
```

#### **Step 5: Verify GPU Installation**

```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Expected output for RTX 5090:
# CUDA Available: True
# GPU: NVIDIA GeForce RTX 5090
```

#### **Step 6: Run Application**

```bash
# Run MUZIKIO ULTRA
python main_ultra.py
```

---

### **Linux Installation (Ubuntu 20.04+ / Debian)**

#### **Step 1: Install Prerequisites**

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python 3.10 and dependencies
sudo apt install python3.10 python3.10-venv python3.10-dev -y

# Install build tools
sudo apt install build-essential git ffmpeg libsndfile1 portaudio19-dev -y
```

#### **Step 2: Install NVIDIA Drivers & CUDA 12.9**

```bash
# Install NVIDIA drivers (if not already installed)
sudo ubuntu-drivers autoinstall

# Add NVIDIA CUDA repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update

# Install CUDA 12.9
sudo apt install cuda-12-9 -y

# Add CUDA to PATH (add to ~/.bashrc)
echo 'export PATH=/usr/local/cuda-12.9/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify CUDA installation
nvcc --version
nvidia-smi
```

#### **Step 3: Clone Repository & Setup**

```bash
# Clone repository
git clone https://github.com/yourusername/musicio-ultra.git
cd musicio-ultra

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### **Step 4: Install Dependencies**

```bash
# RTX 5090 OPTIMIZED INSTALLATION
# CRITICAL: Install PyTorch with EXACT versions for CUDA 12.9 support
# These versions are REQUIRED for RTX 5090 compatibility:
#   - PyTorch: 2.8.0
#   - TorchVision: 0.23.0  (NOT 0.23 or other versions)
#   - TorchAudio: 2.8.0
#   - CUDA: 12.9 (NOT 12.8 or 12.10)
# Using different versions will cause compatibility issues!

pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu129

# Install all dependencies
pip install -r requirements.txt

# If rubberband fails, install system package first:
sudo apt install librubberband-dev -y
pip install pyrubberband
```

#### **Step 5: Verify Installation**

```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

#### **Step 6: Run Application**

```bash
python main_ultra.py
```

---

## Usage

### **Quick Start: Professional Karaoke**

1. **Launch Application**
   ```bash
   python main_ultra.py
   ```

2. **Navigate to KARAOKE Tab**

3. **Select Audio Devices**
   - Choose your **Microphone**
   - Choose your **Speaker/Headphones**
   - Select **Output Folder** for saving recordings

4. **Load Audio File**
   - Click **"DOSYA SEC"** (Select File)
   - Choose your song (MP3, WAV, FLAC, etc.)

5. **Create Backing Track** (Optional)
   - Click **"BACKING TRACK OLUSTUR"** to separate vocals
   - Wait for AI processing (uses Demucs)
   - Instrumental track saved to output folder

6. **Load Lyrics** (Optional)
   - If you have a `_lyrics.txt` file with timestamps:
     ```
     [00:15] First line of lyrics
     [00:20] Second line of lyrics
     [00:25] Third line of lyrics
     ```
   - Place it in the same folder as your audio file
   - It will auto-convert to JSON format

7. **Start Karaoke**
   - Click **"KAYIT + MIX"** button
   - Professional player opens with:
     - Synchronized lyrics display
     - Waveform visualization
     - FX controls (Reverb, EQ, Compressor, Echo)
     - Real-time VU meter

8. **Adjust Effects**
   - Use sliders to control:
     - **Reverb**: Room Size, Wet Mix
     - **Compressor**: Threshold, Ratio
     - **EQ**: Bass, Mid, Treble
     - **Echo**: Delay, Feedback, Mix
   - Apply presets: Radio Ready, Live Concert, Studio Vocal

9. **Stop Recording**
   - Click **"KAYIT + MIX"** again to stop

---

### **Advanced Features**

#### **Vocal Separation**
```python
# Separate vocals from instrumental
1. Load audio file
2. Click "VOCAL AYIR" (Separate Vocals)
3. Output: vocals.wav, instrumental.wav, drums.wav, bass.wav, etc.
```

#### **Pitch Shifting**
```python
# Change pitch without affecting tempo
1. Load audio file
2. Set "Pitch Shift" value (-12 to +12 semitones)
3. Click "APPLY PITCH SHIFT"
4. Output saved to output folder
```

#### **Time Stretching**
```python
# Change tempo without affecting pitch
1. Load audio file
2. Set "Tempo" value (0.5x to 2.0x)
3. Click "APPLY TIME STRETCH"
4. Output saved to output folder
```

#### **BPM Detection**
```python
# Detect song tempo
1. Load audio file
2. Click "DETECT BPM"
3. BPM displayed in log
```

#### **Key Detection**
```python
# Detect musical key
1. Load audio file
2. Click "DETECT KEY"
3. Key and scale displayed in log
```

---

## Project Structure

```
musicio-ultra/
├── main_ultra.py              # Main application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── LICENSE                    # MIT License
│
├── gui/
│   ├── desktop_app_ultra.py   # Main GUI application
│   └── karaoke_player.py      # Professional karaoke player widget
│
├── models/
│   └── model_manager.py       # AI model loading and management
│
├── processors/
│   ├── audio_processor.py     # Audio processing utilities
│   ├── vocal_separator.py     # Vocal separation with Demucs
│   ├── pitch_shifter.py       # Pitch shifting
│   └── time_stretcher.py      # Time stretching
│
├── utils/
│   ├── lyrics_converter.py    # Lyrics format conversion
│   ├── audio_utils.py         # Audio file utilities
│   └── config_manager.py      # Configuration management
│
└── karaoke_output/            # Default output folder
    ├── *.wav                  # Backing tracks
    └── *.lyrics.json          # Synchronized lyrics
```

---

## Configuration

Application settings are saved in `musicio_config.json`:

```json
{
  "karaoke": {
    "microphone": "[1] Microphone Name",
    "speaker": "[4] Speaker Name",
    "output_folder": "C:/path/to/output",
    "backing_track": "C:/path/to/backing.wav"
  }
}
```

---

## FX Presets

### **Built-in Presets:**

1. **Radio Ready**
   - Tight compression, bright EQ, short reverb
   - Perfect for broadcast-style vocals

2. **Live Concert**
   - Medium compression, balanced EQ, large reverb
   - Stadium/concert hall atmosphere

3. **Studio Vocal**
   - Gentle compression, vocal presence boost, subtle reverb
   - Professional recording quality

4. **Church Reverb**
   - Light compression, warm EQ, massive reverb
   - Cathedral-like space

5. **Dry Vocal**
   - Minimal compression, flat EQ, no reverb
   - Natural, unprocessed sound

---

## Troubleshooting

### **Common Issues:**

#### **1. CUDA Not Available**
```bash
# Verify CUDA installation
nvcc --version
nvidia-smi

# Reinstall PyTorch with CUDA 12.9
pip uninstall torch torchvision torchaudio
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu129
```

#### **2. Audio Dropouts / Crackling**
```python
# Increase buffer size in desktop_app_ultra.py (line ~2506)
blocksize = 256  # Try 256, 512, or 1024 if 128 causes issues
```

#### **3. Module Not Found Errors**
```bash
# Reinstall specific module
pip install --upgrade --force-reinstall <module_name>

# Example:
pip install --upgrade --force-reinstall pedalboard
```

#### **4. FFmpeg Not Found**
```bash
# Windows: Add FFmpeg to PATH
# Linux:
sudo apt install ffmpeg
```

#### **5. Microphone Not Detected**
```bash
# List audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"
```

#### **6. Out of Memory (VRAM)**
```python
# In model_manager.py, reduce VRAM allocation:
AGGRESSIVE_MODE_VRAM_PERCENT = 0.85  # Reduce from 0.95 to 0.85
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Demucs** - Facebook Research (Meta AI)
- **AudioSR** - Hugging Face
- **OpenAI Whisper** - OpenAI
- **Pedalboard** - Spotify
- **CustomTkinter** - Tom Schimansky
- **PyTorch** - Meta AI / Facebook
- **NVIDIA** - CUDA Toolkit

---

## Support

For issues, questions, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/musicio-ultra/issues)
- **Discussions**: [Join discussions](https://github.com/yourusername/musicio-ultra/discussions)

---

## RTX 5090 Performance Notes

This application is **fully optimized for NVIDIA RTX 5090** with the following benchmarks:

- **Vocal Separation (Demucs)**: ~8-12 seconds for 4-minute song
- **Audio Super-Resolution**: ~15-20 seconds for 4-minute song
- **Real-time Karaoke Latency**: <3ms @ 48kHz
- **VRAM Usage**: ~18-22GB (aggressive mode)
- **Model Loading Time**: ~3-5 seconds (first launch)

**Performance Tips for RTX 5090:**
- Enable **Aggressive Mode** (95% VRAM allocation) for maximum speed
- Use **CUDA 12.9** exactly for best compatibility
- Ensure **GPU Power Limit** is set to maximum in NVIDIA Control Panel
- Close other GPU-intensive applications during processing

**Audio Hardware Recommendations for Karaoke:**
- **Professional Audio Interface STRONGLY RECOMMENDED** for real-time karaoke
- Tested with:
  - Focusrite Scarlett Series (2i2, 4i4, 18i20)
  - Universal Audio Apollo Twin/x4/x8
  - RME Babyface Pro / Fireface Series
  - MOTU M2/M4
  - PreSonus AudioBox Series
- **Perfect 1:1 Synchronization** achieved with professional audio interfaces
- **<3ms latency** with ASIO drivers (Windows) or CoreAudio (Mac)
- **Zero dropouts** with buffer size 128-256 samples @ 48kHz
- Built-in motherboard audio works but may have 10-50ms latency

---

<div align="center">

**Made with care for music producers, singers, and karaoke enthusiasts**

**Star this repo if you found it helpful!**

</div>
