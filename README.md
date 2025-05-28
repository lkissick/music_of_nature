!! BEFORE USING, YOU MUST INSTALL fluidsynth ONTO YOUR SYSTEM !!
Download here: https://www.fluidsynth.org/download/

See requirements.txt for required libraries
You must have the .sf2 file in the same directory as your scripts

Each Python script broken down:

audio_to_midi_music.py
1. Takes any sound recording as an input .wav file
2. Detects most prominent frequency at a given moment
3. Maps that note to a midi file
4. Outputs a .mid file and a .wav file that plays as a piano

harmonize.py
1. Takes a .mid file as an input
2. Detects the most likely key based on the notes in the file
3. Maps notes to the new key that don't already match
4. Outputs a .wav file playing the notes as a piano

harmonize_choose_key.py
1. Takes a .mid file as an input
2. Lets user choose key and instrument (LINK TO INSTRUMENT VALUES HERE: https://en.wikipedia.org/wiki/General_MIDI#Program_change_events)
3. Outputs a .wav file with the desired key and instrument

mix.py
1. Takes an arbitrary amount of .wav files in the command line as inputs
2. Stitches them together
3. Outputs a .wav file that plays everything at once
