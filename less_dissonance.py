import pretty_midi
import numpy as np
import soundfile as sf
from music21 import key, stream, note, pitch, scale

def detect_key(midi_data):
    """Robust key detection with proper note objects"""
    s = stream.Stream()
    
    for instrument in midi_data.instruments:
        for midi_note in instrument.notes:
            # Create note with proper duration
            n = note.Note()
            try:
                n.pitch = pitch.Pitch(midi=midi_note.pitch)
                n.duration.quarterLength = max(0.25, (midi_note.end - midi_note.start) * 4)
                s.append(n)
            except:
                continue  # Skip problematic pitches
    
    if len(s.notes) == 0:
        return key.Key('C')  # Default if no notes found
    
    return s.analyze('key.krumhansl')

def get_diatonic_pitches(current_key):
    """Get all diatonic pitches for a key across octaves"""
    sc = current_key.getScale('major' if current_key.mode == 'major' else 'minor')
    pitches = []
    for octave in range(0, 10):  # Cover full MIDI range
        for p in sc.pitches:
            midi_pitch = p.midi + (octave * 12)
            if 0 <= midi_pitch <= 127:
                pitches.append(midi_pitch)
    return sorted(list(set(pitches)))

def adjust_to_diatonic(pitch_num, diatonic_pitches):
    """Find nearest diatonic pitch with binary search"""
    # Binary search for nearest diatonic pitch
    left = 0
    right = len(diatonic_pitches) - 1
    while left <= right:
        mid = (left + right) // 2
        if diatonic_pitches[mid] < pitch_num:
            left = mid + 1
        else:
            right = mid - 1
    
    # Check nearest candidates
    candidates = []
    for i in [right, left]:
        if 0 <= i < len(diatonic_pitches):
            candidates.append(diatonic_pitches[i])
    
    if not candidates:
        return pitch_num  # Fallback
    
    return min(candidates, key=lambda x: abs(x - pitch_num))

def process_midi(input_midi_path, output_wav_path):
    """Complete MIDI processing pipeline"""
    try:
        # Load MIDI
        midi_data = pretty_midi.PrettyMIDI(input_midi_path)
        
        # Detect key
        current_key = detect_key(midi_data)
        print(f"Detected key: {current_key}")
        
        # Get all diatonic pitches for this key
        diatonic_pitches = get_diatonic_pitches(current_key)
        
        # Create new harmonized MIDI
        new_midi = pretty_midi.PrettyMIDI()
        
        for instrument in midi_data.instruments:
            new_instr = pretty_midi.Instrument(program=instrument.program)
            
            for n in instrument.notes:
                # Adjust pitch while preserving octave
                original_octave = n.pitch // 12
                adjusted_pitch = adjust_to_diatonic(n.pitch, diatonic_pitches)
                
                # Ensure we stay in a reasonable octave
                adjusted_octave = adjusted_pitch // 12
                if abs(adjusted_octave - original_octave) > 1:
                    adjusted_pitch = (original_octave * 12) + (adjusted_pitch % 12)
                
                new_note = pretty_midi.Note(
                    velocity=n.velocity,
                    pitch=adjusted_pitch,
                    start=n.start,
                    end=n.end
                )
                new_instr.notes.append(new_note)
            
            new_midi.instruments.append(new_instr)
        
        # Synthesize audio
        try:
            audio_data = new_midi.fluidsynth(fs=44100, sf2_path='FluidR3_GM.sf2')
        except:
            print("Using basic synthesis")
            audio_data = new_midi.synthesize(fs=44100)
        
        # Save WAV
        sf.write(output_wav_path, audio_data, 44100)
        print(f"Successfully saved to {output_wav_path}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "output_cardinal.mid"
    output_file = f"harmonized_{input_file.split('.')[0]}.wav"
    
    if process_midi(input_file, output_file):
        print("Success!")
    else:
        print("Failed")