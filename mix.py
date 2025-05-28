import soundfile as sf
import numpy as np
import sys
import os

def mix_wavs(wav_paths, output_path):
    if not wav_paths:
        print("⚠️ No input files provided.")
        return

    audio_data = []
    sample_rates = []

    for path in wav_paths:
        data, sr = sf.read(path)
        audio_data.append(data)
        sample_rates.append(sr)

    # Make sure all sample rates are the same
    if len(set(sample_rates)) > 1:
        raise ValueError("🚨 All input WAV files must have the same sample rate.")

    # Pad shorter arrays with zeros so they all have the same length
    max_len = max(len(data) for data in audio_data)
    padded_data = [
        np.pad(data, ((0, max_len - len(data)), (0, 0)) if data.ndim > 1 else (0, max_len - len(data))) 
        for data in audio_data
    ]

    # Sum all tracks together and normalize
    combined = np.sum(padded_data, axis=0)
    combined /= np.max(np.abs(combined))  # Normalize to prevent clipping

    # Save output
    sf.write(output_path, combined, sample_rates[0])
    print(f"✅ Output saved as: {output_path}")

if __name__ == "__main__":
    # Example usage: python combine.py file1.wav file2.wav ...
    if len(sys.argv) < 2:
        print("⚠️ Please provide some .wav files as arguments.")
        sys.exit(1)

    wav_files = sys.argv[1:]
    output_name = input("💾 Enter desired output filename (with .wav extension): ").strip()

    # Basic check to make sure it ends with .wav
    if not output_name.lower().endswith(".wav"):
        print("⚠️ Filename must end with .wav")
        sys.exit(1)

    mix_wavs(wav_files, output_name)