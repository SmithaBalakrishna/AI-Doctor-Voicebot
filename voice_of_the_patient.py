# ==============================================
# Step 0: Imports, logging, and configuration
# ==============================================
import os
import logging
from pathlib import Path
from io import BytesIO

import speech_recognition as sr          # mic + WAV bytes via SpeechRecognition (uses PyAudio)
from pydub import AudioSegment           # convert WAV bytes -> MP3 (requires ffmpeg installed)
from groq import Groq                    # Groq SDK

# (Optional) Load .env if python-dotenv is installed; otherwise it's fine.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
STT_MODEL = "whisper-large-v3"


# =================================================================
# Step 1: Record audio from the microphone and save it (MP3 by default)
# =================================================================
def record_audio(file_path: str, timeout: int = 20, phrase_time_limit: int | None = None) -> str:
    """
    Record from the default microphone and save to an audio file.

    Args:
        file_path (str): Path to save the recorded audio file (e.g., 'patient.mp3' or 'patient.wav').
        timeout (int): Max seconds to wait for a phrase to start.
        phrase_time_limit (int | None): Max seconds to capture after speech starts.

    Returns:
        str: The path where the audio was saved.
    """
    recognizer = sr.Recognizer()

    # Ensure parent folder exists
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sr.Microphone() as source:
            logging.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logging.info("Start speaking now...")
            audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            logging.info("Recording complete.")

        # SpeechRecognition gives WAV bytes; convert to desired format
        wav_data = audio_data.get_wav_data()
        segment = AudioSegment.from_wav(BytesIO(wav_data))

        if file_path.lower().endswith(".wav"):
            segment.export(path.as_posix(), format="wav")
        else:
            segment.export(path.as_posix(), format="mp3", bitrate="128k")

        logging.info(f"Audio saved to {path.as_posix()}")
        return path.as_posix()

    except Exception as e:
        logging.exception(f"Recording failed: {e}")
        raise


# ======================================================================
# Step 2: Transcribe the audio file with Groq Whisper (STT)
# ======================================================================
def transcribe_with_groq(
    stt_model: str,
    audio_filepath: str,
    groq_api_key: str | None = None,
    language: str | None = None,
) -> str:
    """
    Transcribe an audio file using Groq Whisper.

    Args:
        stt_model (str): e.g., "whisper-large-v3"
        audio_filepath (str): Path to the audio file (mp3/wav/m4a/…)
        groq_api_key (str | None): If None, uses GROQ_API_KEY from environment.
        language (str | None): Optional language hint, e.g. "en". If None, omit.

    Returns:
        str: The transcribed text.
    """
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment or a .env file.")

    client = Groq(api_key=api_key)

    with open(audio_filepath, "rb") as audio_file:
        logging.info("Uploading audio to Groq Whisper for transcription...")
        args = {"model": stt_model, "file": audio_file}
        if language:  # only include if provided to avoid older-SDK surprises
            args["language"] = language
        resp = client.audio.transcriptions.create(**args)

    text = getattr(resp, "text", str(resp))
    logging.info("Transcription complete.")
    return text


# ==============================================
# Step 3: Run both steps together (direct execution)
# ==============================================
if __name__ == "__main__":
    output_audio = "patient_voice_test_for_patient.mp3"  # use ".wav" if you want to skip ffmpeg conversion

    # --- Step 1: Record ---
    saved_path = record_audio(file_path=output_audio, timeout=20, phrase_time_limit=5)

    # --- Step 2: Transcribe ---
    transcript = transcribe_with_groq(
        stt_model=STT_MODEL,
        audio_filepath=saved_path,
        groq_api_key=GROQ_API_KEY,
        language="en",  # safe to keep; ignored if you remove it in callers
    )
    print("\n=== TRANSCRIPT ===")
    print(transcript)
