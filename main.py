import streamlit as st # type: ignore
import whisper # type: ignore
from docx import Document # type: ignore
from reportlab.pdfgen import canvas # type: ignore
import tempfile
import os
from pydub import AudioSegment


# Point to bundled ffmpeg binary (if on Streamlit Cloud)
ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg", "ffmpeg")
AudioSegment.converter = ffmpeg_path

def convert_to_wav(input_path):
    audio = AudioSegment.from_file(input_path)
    wav_path = input_path.replace(os.path.splitext(input_path)[1], ".wav")
    audio.export(wav_path, format="wav")
    return wav_path


# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # use "medium" or "large" for better accuracy
    result = model.transcribe(audio_path)
    return result['text']

# Function to save transcription as DOCX
def save_as_doc(text, filename):
    doc = Document()
    doc.add_paragraph(text)
    doc.save(filename)

# Function to save transcription as PDF
def save_as_pdf(text, filename):
    c = canvas.Canvas(filename)
    c.setFont("Helvetica", 12)
    x, y = 72, 800
    for line in text.split('\n'):
        for chunk in [line[i:i+100] for i in range(0, len(line), 100)]:
            c.drawString(x, y, chunk)
            y -= 20
            if y < 72:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
    c.save()

# Streamlit UI
st.title("🎙️ Speech-to-Text Transcriber (Long Audio Support)")
st.markdown("Upload a long audio file (MP3, WAV, M4A), transcribe it, and download the result.")

uploaded_file = st.file_uploader("Upload your audio file", type=["mp3", "wav", "m4a"])
output_format = st.selectbox("Choose Output Format", ["DOCX", "PDF"])
transcribe_button = st.button("Transcribe")

if transcribe_button and uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_audio:
        temp_audio.write(uploaded_file.read())
        temp_audio_path = temp_audio.name

    with st.spinner("Transcribing... This may take a while for long files."):
        try:
            wav_path = convert_to_wav(temp_audio_path)
            transcript = transcribe_audio(wav_path)
            st.success("Transcription completed!")

            # Save based on selected format
            if output_format == "DOCX":
                output_path = "transcription.docx"
                save_as_doc(transcript, output_path)
            else:
                output_path = "transcription.pdf"
                save_as_pdf(transcript, output_path)

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download {output_format}",
                    data=f,
                    file_name=output_path,
                    mime="application/octet-stream"
                )
        except Exception as e:
            st.error(f"Error: {e}")

    os.remove(temp_audio_path)

