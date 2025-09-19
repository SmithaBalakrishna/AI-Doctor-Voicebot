# gradio_app.py
import os
import logging
import gradio as gr

# Optional .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from voice_of_the_patient import transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_elevenlabs, text_to_speech_with_gtts

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_KEY = (
    os.getenv("ELEVEN_API_KEY")
    or os.getenv("ELEVENLABS_API_KEY")
    or os.getenv("ELEVANLABS_API_KEY")  # supports your earlier typo
)

SYSTEM_PROMPT = (
    "You are a professional doctor (for learning). "
    "Be concise (max 2 sentences), no markdown, no preamble. "
    "Speak directly to the patient."
)

def doctor_reply_text(transcript: str) -> str:
    # Try Groq chat. If anything fails, fall back to a template.
    try:
        if GROQ_API_KEY:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            out = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Patient said: {transcript or '(no speech)'}"},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            return (out.choices[0].message.content or "").strip()
    except Exception as e:
        logging.warning(f"LLM generation failed: {e}")

    if not transcript:
        return "I couldn't hear you clearly. Please record again close to the microphone."
    return (
        "Based on what you said, try simple measures and monitor symptoms; "
        "if anything worsens (fever, severe pain, breathing issues), seek in-person care."
    )

def process_inputs(audio_filepath: str | None, image_filepath: str | None):
    if not audio_filepath:
        return "No audio provided.", "Please record a message.", None

    # 1) STT (note: kw name is groq_api_key, and language is optional)
    transcript = transcribe_with_groq(
        stt_model="whisper-large-v3",
        audio_filepath=audio_filepath,
        groq_api_key=GROQ_API_KEY,
        language="en",
    )

    # 2) Doctor text
    reply = doctor_reply_text(transcript)

    # 3) TTS
    out_mp3 = "doctor_reply.mp3"
    try:
        if ELEVEN_KEY:
            text_to_speech_with_elevenlabs(reply, out_path=out_mp3, autoplay=False)
        else:
            text_to_speech_with_gtts(reply, out_path=out_mp3, autoplay=False)
    except Exception as e:
        logging.warning(f"TTS failed: {e}")
        out_mp3 = None

    return transcript, reply, out_mp3

with gr.Blocks(title="AI Doctor with Vision and Voice") as demo:
    gr.Markdown("# AI Doctor with Vision and Voice")

    with gr.Row():
        audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath", label="audio_filepath")
        stt_out = gr.Textbox(label="Speech to Text")
        doc_text_out = gr.Textbox(label="Doctor's Response")

    with gr.Row():
        image_in = gr.Image(type="filepath", label="image_filepath")  # currently unused
        doc_audio_out = gr.Audio(type="filepath", label="Doctor's Voice", autoplay=True)

    run_btn = gr.Button("Run")
    run_btn.click(process_inputs, [audio_in, image_in], [stt_out, doc_text_out, doc_audio_out])

    gr.ClearButton([audio_in, image_in, stt_out, doc_text_out, doc_audio_out])

if __name__ == "__main__":
    demo.launch()
