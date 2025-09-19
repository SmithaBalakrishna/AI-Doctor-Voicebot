# ============================================
# Doctor TTS helpers: gTTS + ElevenLabs
# ============================================
import os
import logging
import platform
import subprocess

# Optional: load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---- gTTS (Google Text-to-Speech) ----
try:
    from gtts import gTTS
except Exception:
    gTTS = None  # we'll error nicely if someone calls it without gTTS installed

# ---- ElevenLabs SDK ----
import elevenlabs
from elevenlabs.client import ElevenLabs
try:
    # for nicer error messages (only in newer SDKs)
    from elevenlabs.core.api_error import ApiError
except Exception:
    ApiError = Exception

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Accept any of these env var names (including your earlier typo)
ELEVEN_KEY = (
    os.getenv("ELEVEN_API_KEY")
    or os.getenv("ELEVENLABS_API_KEY")
    or os.getenv("ELEVANLABS_API_KEY")
)

def play_audio(path: str) -> None:
    """Simple cross-platform audio player."""
    try:
        os_name = platform.system()
        if os_name == "Darwin":            # macOS
            subprocess.run(["afplay", path])
        elif os_name == "Windows":
            subprocess.run(["powershell", "-c", f'(New-Object Media.SoundPlayer "{path}").PlaySync();'])
        else:                               # Linux
            # 'aplay' works for WAV; for MP3 try mpg123/ffplay if installed
            try:
                subprocess.run(["aplay", path], check=True)
            except Exception:
                subprocess.run(["mpg123", path])
    except Exception as e:
        logging.warning(f"Autoplay failed: {e}")

# -----------------------------
# gTTS helper
# -----------------------------
def text_to_speech_with_gtts(
    text: str,
    out_path: str = "gtts_testing.mp3",
    lang: str = "en",
    slow: bool = False,
    autoplay: bool = False,
) -> str:
    """
    Convert text to speech with gTTS and save to MP3.
    """
    if gTTS is None:
        raise RuntimeError("gTTS is not installed. Install with: pipenv install gTTS")
    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.save(out_path)
    logging.info(f"gTTS audio saved to {out_path}")
    if autoplay:
        play_audio(out_path)
    return out_path

# -----------------------------
# ElevenLabs helper
# -----------------------------
def text_to_speech_with_elevenlabs(
    text: str,
    out_path: str = "elevenlabs_testing.mp3",
    voice_id_or_name: str = "21m00Tcm4TlvDq8ikWAM",  # prefer your own voice_id
    model_id: str = "eleven_turbo_v2",
    fmt: str = "mp3_22050_32",
    autoplay: bool = True,
) -> str:
    """
    Create speech using ElevenLabs. Tries the new streaming API first; falls back to legacy generate/save.
    """
    if not ELEVEN_KEY:
        raise RuntimeError("Missing API key. Put it in ELEVEN_API_KEY / ELEVENLABS_API_KEY / ELEVANLABS_API_KEY")

    client = ElevenLabs(api_key=ELEVEN_KEY)

    try:
        # --- New SDK path (streaming chunks) ---
        stream = client.text_to_speech.convert(
            voice_id=voice_id_or_name,      # prefers a voice_id; names may not work here
            model_id=model_id,
            text=text,                      # IMPORTANT: 'text' (not 'input')
            output_format=fmt,
        )
        with open(out_path, "wb") as f:
            for chunk in stream:
                f.write(chunk)
        logging.info(f"Saved ElevenLabs audio (new API) to {out_path}")

    except (TypeError, AttributeError):
        # --- Old SDK fallback ---
        audio = client.generate(
            text=text,
            voice=voice_id_or_name,         # can be a name (e.g., "Aria") or a voice_id
            output_format=fmt,
            model=model_id,
        )
        elevenlabs.save(audio, out_path)
        logging.info(f"Saved ElevenLabs audio (legacy API) to {out_path}")

    except ApiError as e:
        # Common cause: key missing the Text-to-Speech scope
        msg = str(e)
        if getattr(e, "status_code", None) == 401 and "missing_permissions" in msg.lower():
            raise RuntimeError(
                "ElevenLabs 401: your API key is missing the Text-to-Speech permission.\n"
                "Create a new key in Developers → API Keys with 'Text to Speech' set to Access, "
                "put it in .env, then run again."
            ) from e
        raise

    if autoplay:
        play_audio(out_path)

    return out_path

# Re-export for clean imports in other files
__all__ = ["text_to_speech_with_gtts", "text_to_speech_with_elevenlabs", "play_audio"]

# =====================
# Example: run directly
# =====================
if __name__ == "__main__":
    # Quick demo runs—comment out what you don't need
    text_to_speech_with_gtts("Hi, this is AI with Smitha (gTTS)!", out_path="gtts_testing.mp3", autoplay=False)
    text_to_speech_with_elevenlabs(
        "Hi, this is AI with Smitha via ElevenLabs!",
        out_path="elevenlabs_testing.mp3",
        voice_id_or_name="21m00Tcm4TlvDq8ikWAM",  # change to your voice's ID (recommended)
        model_id="eleven_turbo_v2",
        fmt="mp3_22050_32",
        autoplay=True,
    )
    print("Done.")
