AI Doctor 2.0 – Voicebot

An intelligent **multimodal medical chatbot** that listens, understands, and speaks back like a doctor.  
Built with cutting-edge **Large Language Models (LLMs)**, **speech-to-text**, **text-to-speech**, and a clean **Gradio UI**.  

Disclaimer**: This project is for **research and educational purposes only**. It is **not a substitute for professional medical advice, diagnosis, or treatment**.

---

Features
- 🎙️ Voice Input (Patient)**: Capture audio using ffmpeg + portaudio, transcribe with **Whisper (Groq inference)**.  
- 🧠 Doctor’s Brain**: Powered by **LLaMA 3 Vision** + Groq for multimodal reasoning (text + images).  
- 🗣️ Doctor’s Voice**: Responses spoken back using **gTTS** or **ElevenLabs TTS**.  
- 🌐 Interactive UI**: Built with **Gradio** for easy demo and testing.  
- 🔒 Environment-based secrets**: API keys handled securely via `.env`.

 🛠️ Tech Stack
- Programming: Python  
- LLM: LLaMA 3 Vision (Meta), Groq for inference  
- Speech-to-Text: OpenAI Whisper  
- Text-to-Speech: gTTS, ElevenLabs  
- Frontend: Gradio  
- Environment: VS Code, pipenv/venv  

🧩 Project Layout
- Phase 1 – Setup the brain of the doctor (multimodal LLM with Groq)  
- Phase 2 – Setup the patient’s voice (record + STT with Whisper)  
- Phase 3 – Setup the doctor’s voice (TTS with gTTS & ElevenLabs)  
- Phase 4 – Build the UI (Gradio):contentReference[oaicite:1]{index=1}  
