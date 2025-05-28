import pretty_midi
import numpy as np
import soundfile as sf
from music21 import key
import re

def parse_user_key(user_input):
    try:
        tonic, mode = user_input.strip().split()
        return key.Key(tonic.capitalize(), mode.lower())
    except Exception:
        raise ValueError("Invalid key format. Use 'C major', 'A minor', etc.")

def sanitize_key_string(user_input):
    return re.sub(r'\s+', '_', user_input.strip().lower())

def get_diatonic_pitches(current_key):
    sc = current_key.getScale('major' if current_key.mode == 'major' else 'minor')
    pitches = []
    for octave in range(0, 10):
        for p in sc.pitches:
            midi_pitch = p.midi + (octave * 12)
            if 0 <= midi_pitch <= 127:
                pitches.append(midi_pitch)
    return sorted(list(set(pitches)))

def adjust_to_diatonic(pitch_num, diatonic_pitches):
    left = 0
    right = len(diatonic_pitches) - 1
    while left <= right:
        mid = (left + right) // 2
        if diatonic_pitches[mid] < pitch_num:
            left = mid + 1
        else:
            right = mid - 1

    candidates = []
    for i in [right, left]:
        if 0 <= i < len(diatonic_pitches):
            candidates.append(diatonic_pitches[i])

    if not candidates:
        return pitch_num

    return min(candidates, key=lambda x: abs(x - pitch_num))

def parse_instrument(user_input):
    try:
        prog = int(user_input)
        if 0 <= prog <= 127:
            return prog
        else:
            raise ValueError
    except:
        raise ValueError("Instrument must be an integer between 0 and 127 (MIDI program number).")

def process_midi(input_midi_path, output_wav_path, user_key_str, instrument_prog):
    try:
        midi_data = pretty_midi.PrettyMIDI(input_midi_path)

        current_key = parse_user_key(user_key_str)
        print(f"🎼 Using key: {current_key}")

        diatonic_pitches = get_diatonic_pitches(current_key)

        new_midi = pretty_midi.PrettyMIDI()

        for instrument in midi_data.instruments:
            new_instr = pretty_midi.Instrument(program=instrument_prog)

            for n in instrument.notes:
                original_octave = n.pitch // 12
                adjusted_pitch = adjust_to_diatonic(n.pitch, diatonic_pitches)

                adjusted_octave = adjusted_pitch // 12
                if abs(adjusted_octave - original_octave) > 1:
                    adjusted_pitch = (original_octave * 12) + (adjusted_pitch % 12)

                start = n.start
                end = n.end

                # Cut all notes that haven't ended before this note starts
                for note in new_instr.notes:
                    if note.end > start:
                        note.end = start

                new_note = pretty_midi.Note(
                    velocity=n.velocity,
                    pitch=adjusted_pitch,
                    start=start,
                    end=end
                )
                new_instr.notes.append(new_note)

            new_midi.instruments.append(new_instr)

        try:
            audio_data = new_midi.fluidsynth(fs=44100, sf2_path='FluidR3_GM.sf2')
        except:
            print("⚠️ fluidsynth failed, falling back to basic synth")
            audio_data = new_midi.synthesize(fs=44100)

        sf.write(output_wav_path, audio_data, 44100)
        print(f"✅ Successfully saved to {output_wav_path}")
        return True

    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "output_input-3.mid"
    user_key = input("🎹 Enter your desired key (e.g., 'C major', 'A minor'): ")
    user_instr = input("🎸 Enter instrument program number (0-127, e.g. 0=Acoustic Grand Piano): ")

    try:
        instrument_prog = parse_instrument(user_instr)
    except ValueError as e:
        print(f"❌ {e}")
        exit(1)

    key_filename = sanitize_key_string(user_key)
    output_file = f"{key_filename}_prog{instrument_prog}_{input_file.split('.')[0]}.wav"

    if process_midi(input_file, output_file, user_key, instrument_prog):
        print("🎉 Success!")
    else:
        print("❌ Failed.")