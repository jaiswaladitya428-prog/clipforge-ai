import wave
import struct
import math
from pathlib import Path
from app.services.ffmpeg_utils import get_ffmpeg_binary
from app.services.audio_extractor import extract_audio_wav

def test_ffmpeg_binary_available():
    binary = get_ffmpeg_binary()
    assert binary is not None
    assert Path(binary).exists()

def test_audio_extraction_from_synthetic_wav(tmp_path):
    # Create a 1-second 44.1kHz stereo WAV file
    input_wav = tmp_path / "input_stereo.wav"
    output_wav = tmp_path / "output_16k_mono.wav"

    sample_rate = 44100
    duration = 1.0  # seconds
    frequency = 440.0  # Hz tone

    with wave.open(str(input_wav), "w") as wav_file:
        wav_file.setnchannels(2)  # stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        num_frames = int(sample_rate * duration)
        for i in range(num_frames):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
            data = struct.pack("<hh", value, value)
            wav_file.writeframesraw(data)

    # Run extraction to 16kHz mono WAV
    extracted = extract_audio_wav(input_wav, output_wav)
    assert extracted.exists()

    with wave.open(str(extracted), "r") as out_wav:
        assert out_wav.getnchannels() == 1  # mono
        assert out_wav.getframerate() == 16000  # 16kHz
        assert out_wav.getsampwidth() == 2  # 16-bit
