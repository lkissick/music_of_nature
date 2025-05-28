import numpy as np
import librosa
import pretty_midi
import os
import soundfile as sf

def audio_to_midi(input_file, output_midi, 
                 instrument=0, min_note_duration=0.15, 
                 min_note_gap=0.1, threshold=0.1, 
                 sample_rate=22050,
                 output_wav=None,
                 soundfont_path="FluidR3_GM.sf2"):
    """
    Convert audio to MIDI with realistic piano timing constraints,
    then synthesize MIDI to WAV using fluidsynth.
    
    Parameters:
        input_file: Input audio file path
        output_midi: Output MIDI file path
        output_wav: Output WAV file path
        soundfont_path: Path to .sf2 SoundFont for MIDI synthesis
    """
    # Load audio file
    y, sr = librosa.load(input_file, sr=sample_rate)
    
    # Create PrettyMIDI object with realistic tempo (80-120 BPM)
    midi = pretty_midi.PrettyMIDI(initial_tempo=100)
    
    # Create instrument
    instrument_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    if 0 <= instrument <= 127:
        instrument_program = instrument
    midi_instrument = pretty_midi.Instrument(program=instrument_program)
    
    # STFT parameters
    n_fft = 2048
    hop_length = n_fft // 4
    win_length = n_fft
    
    # Compute STFT
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, win_length=win_length)
    magnitude = np.abs(stft)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    # Variables to track timing constraints
    last_note_time = -min_note_gap
    active_notes = {}

    # Process each time frame
    for i in range(magnitude.shape[1]):
        current_time = i * hop_length / sr
        frame = magnitude[:, i]
        max_mag = np.max(frame)
        if max_mag < threshold:
            continue
        prominent_freq = freqs[np.argmax(frame)]
        if prominent_freq <= 0:
            continue
        note_number = int(round(librosa.hz_to_midi(prominent_freq)))
        velocity = int(min(127, max_mag * 100))
        
        if current_time - last_note_time >= min_note_gap:
            if note_number in active_notes:
                start_time, old_velocity = active_notes.pop(note_number)
                duration = current_time - start_time
                if duration >= min_note_duration:
                    note = pretty_midi.Note(
                        velocity=old_velocity,
                        pitch=note_number,
                        start=start_time,
                        end=current_time
                    )
                    midi_instrument.notes.append(note)
            active_notes[note_number] = (current_time, velocity)
            last_note_time = current_time

    for note_number, (start_time, velocity) in active_notes.items():
        duration = (len(magnitude[0]) * hop_length / sr) - start_time
        if duration >= min_note_duration:
            note = pretty_midi.Note(
                velocity=velocity,
                pitch=note_number,
                start=start_time,
                end=start_time + duration
            )
            midi_instrument.notes.append(note)

    midi.instruments.append(midi_instrument)
    midi.write(output_midi)
    print(f"✅ MIDI saved to {output_midi}")

    # Synthesize MIDI to audio
    if output_wav:
        try:
            audio = midi.fluidsynth(fs=sample_rate, sf2_path=soundfont_path)
            sf.write(output_wav, audio, sample_rate)
            print(f"✅ WAV saved to {output_wav}")
        except Exception as e:
            print(f"⚠️ Failed to render WAV: {e}")

if __name__ == "__main__":
    input_audio = "input-3.wav"  # CHANGE INPUT FILE NAME HERE
    output_midi = f"output_{os.path.splitext(input_audio)[0]}.mid"
    output_wav = f"output_{os.path.splitext(input_audio)[0]}.wav"
    sf2_path = "FluidR3_GM.sf2"  # Update path if needed
    
    audio_to_midi(
        input_file=input_audio,
        output_midi=output_midi,
        output_wav=output_wav,
        soundfont_path=sf2_path,
        instrument=0,
        min_note_duration=0.15,
        min_note_gap=0.2,
        threshold=0.05
    )