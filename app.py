import streamlit as st
import os, librosa, numpy as np
from moviepy.editor import ImageClip, AudioFileClip, VideoClip, CompositeVideoClip
from natsort import natsorted
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

# FIX: Atasi error Pillow 10+ untuk tahun 2026
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

st.set_page_config(page_title="Studio Album 2026", layout="wide")

# FUNGSI TOTAL NON-IMAGEMAGICK UNTUK TEKS
def create_text_clip_pure_pillow(text, fontsize, color=(255, 255, 255), size=(1920, 1080), pos=(0,0), duration=1):
    # Buat gambar transparan menggunakan Pillow
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gunakan font standar yang pasti ada di server Linux Streamlit
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    draw.text(pos, text, fill=color, font=font)
    
    # Ubah gambar Pillow ke format yang dimengerti MoviePy (numpy array)
    img_array = np.array(img)
    
    # Kembalikan sebagai ImageClip, BUKAN TextClip
    return ImageClip(img_array).set_duration(duration)

st.title("🎵 YOUTUBE ALBUM STUDIO 2026")

col1, col2 = st.columns([1, 1.5])
with col1:
    bg_file = st.file_uploader("Upload Cover", type=["jpg", "png", "webp"])
    album_name = st.text_input("Nama Album", "GOLDEN HITS 2026")
with col2:
    audio_files = st.file_uploader("Upload MP3", type=["mp3"], accept_multiple_files=True)

if st.button("🚀 GENERATE VIDEO"):
    if not bg_file or not audio_files:
        st.error("⚠️ File belum lengkap!")
    else:
        try:
            with st.status("🏗️ Sedang Merender Video...", expanded=True):
                # 1. Audio
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
                
                # 2. Spectrum
                y, sr = librosa.load("master.mp3", sr=22050)
                fps = 15
                stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=int(sr/fps)))
                spec = librosa.amplitude_to_db(stft, ref=np.max)
                spec = (spec - spec.min()) / (spec.max() - spec.min())
                audio_features = np.array([np.mean(c, axis=0) for c in np.array_split(spec, 50)]).T

                # 3. Video
                duration = full_audio.duration_seconds
                with open("bg.png", "wb") as f: f.write(bg_file.getbuffer())
                
                # Background
                bg_clip = ImageClip("bg.png").set_duration(duration).resize((1920, 1080)).fl_image(lambda p: (p*0.3).astype('uint8'))
                
                # Judul menggunakan fungsi Pillow murni
                title_clip = create_text_clip_pure_pillow(album_name, 70, pos=(750, 70), duration=duration)
                
                overlays = [bg_clip, title_clip]

                # Daftar Lagu
                for i, tr in enumerate(track_meta):
                    y_p = 240 + ((i % 10) * 60)
                    x_p = 200 if i < 10 else 1100
                    # Teks Lagu (Off)
                    t_off = create_text_clip_pure_pillow(f"{i+1}. {tr['name']}", 25, color=(150, 150, 150), pos=(x_p, y_p), duration=duration)
                    # Teks Lagu (On/Highlight)
                    t_on = create_text_clip_pure_pillow(f"{i+1}. {tr['name']}", 25, color=(251, 191, 36), pos=(x_p, y_p), duration=tr['end']-tr['start']).set_start(tr['start'])
                    overlays.extend([t_off, t_on])

                # Bar Visualizer
                def make_spec(t):
                    idx = min(int(t*fps), len(audio_features)-1)
                    frame = np.zeros((220, 1920, 4), dtype=np.uint8)
                    for b in range(50):
                        bh = int(pow(audio_features[idx][b], 0.7) * 200)
                        frame[220-bh:220, 350+(b*25):350+(b*25)+18] = [251, 191, 36, 255]
                    return frame

                spec_clip = VideoClip(make_spec, duration=duration).set_position((0, 830))
                overlays.append(spec_clip)

                # Export Akhir
                final = CompositeVideoClip(overlays, size=(1920,1080)).set_audio(AudioFileClip("master.mp3"))
                final.write_videofile("hasil.mp4", fps=fps, codec="libx264", audio_codec="aac")

            st.success("✅ Video Berhasil Dibuat!")
            st.download_button("📥 Download Video", open("hasil.mp4", "rb"), "Album_2026.mp4")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

