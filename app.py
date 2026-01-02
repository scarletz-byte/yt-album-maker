import streamlit as st
import os, librosa, numpy as np
from moviepy.editor import *
from moviepy.config import change_settings
from natsort import natsorted
from pydub import AudioSegment

# KONFIGURASI SERVER CLOUD (Wajib untuk Linux/Streamlit Cloud)
if os.path.exists("/usr/bin/convert"):
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

st.set_page_config(page_title="Studio Album 2026", layout="wide")

# Tema Dark Glassmorphism 2026
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    .stButton > button {
        background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
        color: black !important; font-weight: bold; border-radius: 10px; width: 100%; height: 3em;
    }
    .stFileUploader section { background: rgba(255,255,255,0.05) !important; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 YOUTUBE ALBUM STUDIO 2026")
st.write("---")

col1, col2 = st.columns([1, 1.5])
with col1:
    st.subheader("🎨 Visual Art")
    bg_file = st.file_uploader("Upload Cover (1920x1080)", type=["jpg", "png", "webp"])
    album_name = st.text_input("Nama Album", "GOLDEN HITS 2026")

with col2:
    st.subheader("🎶 Audio Tracks")
    audio_files = st.file_uploader("Upload MP3 (Pilih Banyak)", type=["mp3"], accept_multiple_files=True)

if st.button("🚀 GENERATE MASTERPIECE VIDEO"):
    if not bg_file or not audio_files:
        st.error("⚠️ Mohon unggah Cover dan Lagu terlebih dahulu!")
    else:
        try:
            with st.status("🏗️ Sedang Memproses Album...", expanded=True) as status:
                # 1. Audio Processing
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
                    os.remove(temp_p) # Hapus temp audio setelah digabung

                full_audio.export("master.mp3", format="mp3")
                duration = full_audio.duration_seconds

                # 2. Real FFT Analysis
                st.write("📊 Menganalisa Spektrum Musik...")
                y, sr = librosa.load("master.mp3", sr=22050)
                fps = 15 # FPS rendah agar render di Cloud stabil
                stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=int(sr/fps)))
                spec = librosa.amplitude_to_db(stft, ref=np.max)
                spec = (spec - spec.min()) / (spec.max() - spec.min())
                audio_features = np.array([np.mean(c, axis=0) for c in np.array_split(spec, 50)]).T

                # 3. Video Compositing
                st.write("🎬 Merakit Video (Ini butuh waktu)...")
                with open("bg.png", "wb") as f: f.write(bg_file.getbuffer())
                
                # Background & Title
                bg_clip = ImageClip("bg.png").set_duration(duration).resize((1920, 1080)).fl_image(lambda p: (p*0.3).astype('uint8'))
                title_clip = TextClip(album_name, fontsize=70, color='white', font='Arial-Bold').set_position(('center', 70)).set_duration(duration)

                overlays = [bg_clip, title_clip]
                
                # Tracklist Overlay
                for i, tr in enumerate(track_meta):
                    y_p = 240 + ((i % 10) * 60)
                    x_p = 200 if i < 10 else 1100
                    
                    t_off = TextClip(f"{i+1}. {tr['name']}", fontsize=28, color='white', font='Arial').set_position((x_p, y_p)).set_duration(duration).set_opacity(0.3)
                    t_on = TextClip(f"{i+1}. {tr['name']}", fontsize=28, color='#fbbf24', font='Arial-Bold').set_position((x_p, y_p)).set_start(tr['start']).set_end(tr['end'])
                    
                    overlays.extend([t_off, t_on])

                # Audio Spectrum Visualizer Function
                def make_spec(t):
                    idx = min(int(t*fps), len(audio_features)-1)
                    frame = np.zeros((220, 1920, 4), dtype=np.uint8)
                    for b in range(50):
                        bh = int(pow(audio_features[idx][b], 0.7) * 200)
                        frame[220-bh:220, 350+(b*25):350+(b*25)+18] = [251, 191, 36, 255]
                    return frame

                spec_clip = VideoClip(make_spec, duration=duration).set_position(('center', 830))
                overlays.append(spec_clip)

                # Final Export
                final = CompositeVideoClip(overlays, size=(1920,1080)).set_audio(AudioFileClip("master.mp3"))
                final.write_videofile("hasil_album.mp4", fps=fps, codec="libx264", audio_codec="aac", threads=4)

                st.success("🎉 Video Berhasil Dibuat!")
                with open("hasil_album.mp4", "rb") as v_file:
                    st.download_button("📥 DOWNLOAD HASIL VIDEO (.MP4)", v_file, "Album_2026.mp4")
                    
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")
            st.info("Saran: Coba kurangi jumlah lagu atau durasi untuk menghindari batas memori server.")
