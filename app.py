import streamlit as st
import os, librosa, numpy as np
from moviepy import ImageClip, AudioFileClip, VideoClip, CompositeVideoClip
from natsort import natsorted
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# --- 1. KONFIGURASI DASAR & PATCH ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

st.set_page_config(page_title="Studio Album 2026", layout="wide")

# --- 2. TAMPILAN UI GLASSMORPHISM 2026 ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #0f172a, #020617);
        color: #f8fafc;
    }
    h1 {
        text-align: center; color: #fbbf24;
        text-shadow: 0px 0px 15px rgba(251, 191, 36, 0.5);
        font-weight: 800 !important;
    }
    div[data-testid="stColumn"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px; border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    .stButton > button {
        background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%);
        color: #000 !important; border: none;
        padding: 15px 30px; border-radius: 12px;
        font-weight: 700; width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0px 0px 25px rgba(251, 191, 36, 0.6);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🎵 YOUTUBE ALBUM STUDIO 2026</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; opacity:0.7;'>Automated Video Engine • 720p Optimized</p>", unsafe_allow_html=True)
st.write("---")

# --- 3. FUNGSI PENDUKUNG (Logika Teks & Video) ---
def create_text_image(text, fontsize, color=(255, 255, 255), size=(1280, 720), pos=(0,0), duration=1):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    draw.text(pos, text, fill=color, font=font)
    clip = ImageClip(np.array(img))
    clip.duration = duration
    return clip

# --- 4. INPUT SECTION ---
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown("### 🎨 Visual Art")
    bg_file = st.file_uploader("Upload Cover Album", type=["jpg", "png", "webp"])
    album_name = st.text_input("Nama Album", "GOLDEN HITS 2026")

with col2:
    st.markdown("### 🎶 Audio Tracks")
    audio_files = st.file_uploader("Upload MP3 (Pilih Banyak)", type=["mp3"], accept_multiple_files=True)

st.write("---")
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    generate_btn = st.button("🚀 GENERATE MASTERPIECE VIDEO")

# --- 5. LOGIKA EKSEKUSI (Dijalankan saat tombol diklik) ---
if generate_btn:
    if not bg_file or not audio_files:
        st.error("⚠️ Mohon unggah Cover dan MP3 terlebih dahulu!")
    else:
        try:
            with st.status("🏗️ Sedang Memproses Album...", expanded=True):
                # A. Audio Processing
                sorted_files = natsorted(audio_files, key=lambda x: x.name)
                full_audio = AudioSegment.empty()
                track_meta = []
                curr_ms = 0
                for f in sorted_files:
                    temp_p = f"temp_{f.name}"
                    with open(temp_p, "wb") as w: w.write(f.getbuffer())
                    seg = AudioSegment.from_file(temp_p)
                    track_meta.append({
                        "name": f.name.rsplit('.', 1)[0].replace("_", " ").upper(),
                        "start": curr_ms/1000.0, "end": (curr_ms+len(seg))/1000.0
                    })
                    full_audio += seg
                    curr_ms += len(seg)
                    os.remove(temp_p)
                full_audio.export("master.mp3", format="mp3")
                duration = full_audio.duration_seconds

                # B. Spectrum Analysis
                y, sr = librosa.load("master.mp3", sr=22050)
                fps = 10 
                stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=int(sr/fps)))
                spec = librosa.amplitude_to_db(stft, ref=np.max)
                spec = (spec - spec.min()) / (spec.max() - spec.min())
                audio_features = np.array([np.mean(c, axis=0) for c in np.array_split(spec, 50)]).T

                # C. Video Compositing
                with open("bg.png", "wb") as f: f.write(bg_file.getbuffer())
                orig_bg = Image.open("bg.png").convert("RGB").resize((1280, 720))
                dark_bg = (np.array(orig_bg) * 0.3).astype('uint8')
                
                bg_clip = ImageClip(dark_bg)
                bg_clip.duration = duration
                
                title_clip = create_text_image(album_name, 50, pos=(480, 50), duration=duration)
                overlays = [bg_clip, title_clip]

                for i, tr in enumerate(track_meta):
                    y_p = 160 + ((i % 10) * 40)
                    x_p = 100 if i < 10 else 750
                    t_off = create_text_image(f"{i+1}. {tr['name']}", 20, color=(120, 120, 120), pos=(x_p, y_p), duration=duration)
                    t_on = create_text_image(f"{i+1}. {tr['name']}", 20, color=(251, 191, 36), pos=(x_p, y_p), duration=tr['end']-tr['start'])
                    t_on = t_on.with_start(tr['start'])
                    overlays.extend([t_off, t_on])

                def make_spec(t):
                    idx = min(int(t*fps), len(audio_features)-1)
                    frame = np.zeros((150, 1280, 4), dtype=np.uint8)
                    for b in range(50):
                        bh = int(pow(audio_features[idx][b], 0.7) * 130)
                        frame[150-bh:150, 240+(b*16):240+(b*16)+12] = [251, 191, 36, 255]
                    return frame

                spec_clip = VideoClip(make_spec, duration=duration).with_position((0, 550))
                overlays.append(spec_clip)

                # D. Export
                final = CompositeVideoClip(overlays, size=(1280, 720))
                final.duration = duration
                final = final.with_audio(AudioFileClip("master.mp3"))
                final.write_videofile("hasil.mp4", fps=fps, codec="libx264", audio_codec="aac")

            st.success("✅ Video Berhasil Dibuat!")
            st.download_button("📥 Download MP4 (720p)", open("hasil.mp4", "rb"), "Album_2026.mp4")
            
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")

