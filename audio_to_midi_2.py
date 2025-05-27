import numpy as np
import librosa
import pretty_midi
import soundfile as sf
import os

def audio_to_midi(input_file, output_midi, output_audio, 
                 instrument=0, min_note_duration=0.15, 
                 min_note_gap=0.1, threshold=0.1, 
                 sample_rate=22050):
    """
    Convert audio to MIDI with realistic piano timing constraints.
    
    Parameters:
        input_file: Input audio file path
        output_midi: Output MIDI file path
        output_audio: Output audio file path
        instrument: MIDI program number (0-127)
        min_note_duration: Minimum duration for any note (seconds)
        min_note_gap: Minimum time between note onsets (seconds)
        threshold: Amplitude threshold for note detection
        sample_rate: Audio sample rate
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
    last_note_time = -min_note_gap  # Ensures first note can be placed at 0
    active_notes = {}  # {pitch: (start_time, velocity)}
    
    # Process each time frame
    for i in range(magnitude.shape[1]):
        current_time = i * hop_length / sr
        
        # Find prominent frequencies
        frame = magnitude[:, i]
        max_mag = np.max(frame)
        if max_mag < threshold:
            continue  # Skip quiet frames
        
        prominent_freq = freqs[np.argmax(frame)]
        if prominent_freq <= 0:
            continue
        
        # Convert to MIDI note
        note_number = int(round(librosa.hz_to_midi(prominent_freq)))
        velocity = int(min(127, max_mag * 100))
        
        # Check if we should start a new note
        if current_time - last_note_time >= min_note_gap:
            # End any existing note of the same pitch
            if note_number in active_notes:
                start_time, old_velocity = active_notes.pop(note_number)
                duration = current_time - start_time
                
                # Only keep notes that meet minimum duration
                if duration >= min_note_duration:
                    note = pretty_midi.Note(
                        velocity=old_velocity,
                        pitch=note_number,
                        start=start_time,
                        end=current_time
                    )
                    midi_instrument.notes.append(note)
            
            # Start new note
            active_notes[note_number] = (current_time, velocity)
            last_note_time = current_time
    
    # Add any remaining active notes
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
    
    # Add instrument to MIDI object
    midi.instruments.append(midi_instrument)
    
    # Save MIDI file
    midi.write(output_midi)
    print(f"MIDI file saved to {output_midi}")
    
    # Synthesize audio
    try:
        soundfont_path = 'FluidR3_GM.sf2'
        if os.path.exists(soundfont_path):
            audio_data = midi.fluidsynth(fs=44100, sf2_path=soundfont_path)
        else:
            print("SoundFont not found, using basic synthesis")
            audio_data = midi.synthesize(fs=44100)
        
        sf.write(output_audio, audio_data, 44100)
        print(f"Audio file saved to {output_audio}")
    except Exception as e:
        print(f"Error synthesizing audio: {e}")

if __name__ == "__main__":
    # Example usage with realistic piano timing
    input_audio = "nature.wav"
    output_midi = f"output_{input_audio.split('.')[0]}.mid"
    output_audio = f"output_{input_audio.split('.')[0]}.wav"
    
    audio_to_midi(
        input_audio, 
        output_midi, 
        output_audio,
        instrument=0,  # Acoustic Grand Piano
        min_note_duration=0.15,  # Minimum note duration (seconds)
        min_note_gap=0.2,  # Minimum time between notes (seconds)
        threshold=0.05  # Sensitivity
    )