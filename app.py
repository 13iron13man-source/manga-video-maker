import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import os
from moviepy.editor import ImageClip, AudioFileClip
from pdf2image import convert_from_path

# --- PASSWORD CHECK ---
try:
    GENAI_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Error: I cannot find the API Key. Please put it in the Secrets settings.")
    st.stop()

genai.configure(api_key=GENAI_KEY)

# --- FUNCTIONS ---

async def generate_voice(text, output_file="voice.mp3"):
    """Creates the audio file"""
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_file)

def analyze_image(image_path):
    """Sends image to Google AI to get text"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    sample_file = genai.upload_file(path=image_path, display_name="Manga Page")
    
    prompt = "Look at this manga page. Write a short, dramatic narration script (max 3 sentences) describing the action. Do not use character names, just the story text."
    
    response = model.generate_content([sample_file, prompt])
    return response.text

def create_video(image_path, audio_path, output_path="final_output.mp4"):
    """Stitches image and audio together"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration + 1.0
    
    clip = ImageClip(image_path).set_duration(duration)
    clip = clip.resize(height=720)
    
    video = clip.set_audio(audio)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    return output_path

# --- THE WEBSITE SCREEN ---
st.set_page_config(page_title="Manga Maker", page_icon="🎬")
st.title("🎬 Manga-to-Video Generator")
st.write("Upload a JPG, PNG, or PDF!")

# 1. CHANGED: Added "pdf" to the allowed types
uploaded_file = st.file_uploader("Upload File", type=["jpg", "png", "jpeg", "pdf"])

if uploaded_file is not None:
    # 2. CHANGED: Check if it is a PDF
    if uploaded_file.type == "application/pdf":
        with st.spinner("Converting PDF to Image..."):
            # Save PDF temporarily
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Convert first page to image
            images = convert_from_path("temp.pdf")
            images[0].save("temp_manga.jpg", "JPEG")
            st.success("PDF Converted! Using Page 1.")
            
    else:
        # Standard Image Save
        with open("temp_manga.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
    st.image("temp_manga.jpg", caption="Preview", width=350)
    
    if st.button("Generate Video"):
        with st.spinner('Reading the manga...'):
            try:
                script = analyze_image("temp_manga.jpg")
                st.success("Script created!")
                st.write(f"**AI Read:** {script}")
                
                with st.spinner('Creating Voice...'):
                    asyncio.run(generate_voice(script, "temp_voice.mp3"))
                
                with st.spinner('Rendering Video...'):
                    video_file = create_video("temp_manga.jpg", "temp_voice.mp3")
                
                st.video(video_file)
                
            except Exception as e:
                st.error(f"Something went wrong: {e}")
