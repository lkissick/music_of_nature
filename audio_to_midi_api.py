from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
import uuid
from audio_to_midi_2 import audio_to_midi  # Import your function
from less_dissonance import process_midi # Import other function
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/convert/")
async def convert_audio(
    file: UploadFile = File(...),
    instrument: int = Form(0),
    min_note_duration: float = Form(0.15),
    min_note_gap: float = Form(0.2),
    threshold: float = Form(0.05)
):
    # Save the uploaded file
    input_filename = f"temp_{uuid.uuid4().hex}.wav"
    with open(input_filename, "wb") as buffer:
        buffer.write(await file.read())

    # Output filenames
    base_name = os.path.splitext(input_filename)[0]
    output_midi = f"{base_name}.mid"
    output_audio = f"{base_name}_synth.wav"
    harmonized_audio = f"{base_name}_harmonized.wav"

    try:
        # Step 1: Audio to MIDI + synth
        audio_to_midi(
            input_file=input_filename,
            output_midi=output_midi,
            output_audio=output_audio,
            instrument=instrument,
            min_note_duration=min_note_duration,
            min_note_gap=min_note_gap,
            threshold=threshold
        )

        # Step 2: Harmonize the MIDI into a new WAV file
        success = process_midi(output_midi, harmonized_audio)
        if not success:
            raise Exception("Harmonization failed")

        return JSONResponse({
            "midi_file": output_midi,
            "audio_file": output_audio,
            "harmonized_audio_file": harmonized_audio
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Optional cleanup can go here
        pass

@app.get("/download/midi/{filename}")
def download_midi(filename: str):
    return FileResponse(path=filename, media_type="audio/midi", filename=filename)

@app.get("/download/audio/{filename}")
def download_audio(filename: str):
    return FileResponse(path=filename, media_type="audio/wav", filename=filename)

if __name__ == "__main__":
    uvicorn.run("audio_to_midi_api:app", host="0.0.0.0", port=8000, reload=True)