import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import os
# We import everything from MoviePy v2 to avoid "ImportError"
from moviepy import *
from pdf2image import convert_from_path

# --- PASSWORD CHECK ---
try:
    GENAI_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Error: API Key not found. Please check Advanced Settings.")
    st.stop()

genai.configure(api_key=GENAI_KEY)

# --- FUNCTIONS ---

# Fixed: Asyncio Loop Handler for Streamlit
def run_voice_generation(text, output_file):
    async def _generate():
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(output_file)
    
    # Create a new loop explicitly for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_generate())
    loop.close()

def analyze_image(image_path):
    model = genai.GenerativeModel('gemini-1.5-flash')
    sample_file = genai.upload_file(path=image_path, display_name="Manga Page")
    prompt = "Look at this manga page. Write a short, dramatic narration script (max 3 sentences). No names, just story."
    response = model.generate_content([sample_file, prompt])
    return response.text

def create_video(image_path, audio_path, output_path="final_output.mp4"):
    # Load Audio
    audio = AudioFileClip(audio_path)
    duration = audio.duration + 1.0
    
    # MOVIEPY V2 LOGIC
    # 1. Create Image Clip with duration
    clip = ImageClip(image_path).with_duration(duration)
    
    # 2. Resize (Using 'resized', not 'resize')
    # We ensure width is even to prevent FFmpeg errors
    clip = clip.resized(height=720)
    
    # 3. Set Audio (Using 'with_audio')
    video = clip.with_audio(audio)
    
    # 4. Write File
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    return output_path

# --- UI ---
st.set_page_config(page_title="Manga Maker", page_icon="🎬")
st.title("🎬 Manga-to-Video Generator")

uploaded_file = st.file_uploader("Upload Manga (Image or PDF)", type=["jpg", "png", "jpeg", "pdf"])

if uploaded_file is not None:
    # Handle PDF vs Image
    if uploaded_file.type == "application/pdf":
        with st.spinner("Converting PDF..."):
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            images = convert_from_path("temp.pdf")
            images[0].save("temp_manga.jpg", "JPEG")
            st.success("PDF Ready!")
    else:
        with open("temp_manga.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())

    st.image("temp_manga.jpg", caption="Preview", width=350)
    
    if st.button("Generate Video"):
        try:
            with st.spinner('1. AI Reading Script...'):
                script = analyze_image("temp_manga.jpg")
                st.info(f"Script: {script}")
            
            with st.spinner('2. Generating Voice...'):
                # Using the fixed loop function
                run_voice_generation(script, "temp_voice.mp3")
                
            with st.spinner('3. Rendering Video...'):
                video_file = create_video("temp_manga.jpg", "temp_voice.mp3")
                
            st.success("Done!")
            st.video(video_file)
            
        except Exception as e:
            st.error(f"Error: {e}")
