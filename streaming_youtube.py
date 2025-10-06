import sys
import subprocess
import threading
import os
import tempfile
import streamlit.components.v1 as components

# Install streamlit jika belum ada
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st

# Pastikan batas ukuran file besar (hingga 5GB)
st.runtime.legacy_caching.clear_cache()
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "5000"  # 5GB

def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    """Jalankan proses streaming FFmpeg ke YouTube Live"""
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""

    cmd = [
        "ffmpeg", "-re", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv"
    ]
    if scale:
        cmd += scale.split()
    cmd.append(output_url)

    log_callback(f"Menjalankan FFmpeg: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming selesai atau dihentikan.")


def main():
    st.set_page_config(page_title="🎥 YouTube Live Stream", page_icon="📡", layout="wide")
    st.title("🎥 Live Streaming ke YouTube")

    # Optional Iklan / Sponsor
    show_ads = st.checkbox("Tampilkan Iklan", value=False)
    if show_ads:
        st.subheader("Iklan Sponsor")
        components.html(
            """
            <div style="background:#eef;padding:20px;border-radius:10px;text-align:center">
                <script async src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
                <p style="color:#888">Iklan akan tampil di sini...</p>
            </div>
            """,
            height=300
        )

    # Upload video (besar & durasi panjang)
    st.subheader("🎬 Upload Video")
    uploaded_file = st.file_uploader(
        "Upload video (MP4/FLV, max 5GB, durasi panjang diperbolehkan)",
        type=['mp4', 'flv'],
        accept_multiple_files=False
    )

    video_path = None
    if uploaded_file is not None:
        # Simpan file besar dengan metode streaming sementara
        temp_dir = tempfile.gettempdir()
        video_path = os.path.join(temp_dir, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ Video '{uploaded_file.name}' berhasil diupload ke {video_path}")
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        st.info(f"Ukuran file: {file_size:.2f} MB")

    # Pilih video dari folder lokal
    local_videos = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv'))]
    if local_videos:
        selected_video = st.selectbox("Atau pilih video dari folder ini:", ["(Pilih)"] + local_videos)
        if selected_video != "(Pilih)":
            video_path = selected_video

    # Input stream key
    stream_key = st.text_input("Masukkan Stream Key YouTube", type="password")
    is_shorts = st.checkbox("Mode Shorts (vertikal 720x1280)", value=False)

    # Tempat log
    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        try:
            log_placeholder.text("\n".join(logs[-25:]))
        except:
            pass

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    # Tombol kontrol
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Mulai Streaming", use_container_width=True):
            if not video_path or not stream_key:
                st.error("❌ Harap upload/pilih video dan isi Stream Key!")
            else:
                st.session_state['ffmpeg_thread'] = threading.Thread(
                    target=run_ffmpeg,
                    args=(video_path, stream_key, is_shorts, log_callback),
                    daemon=True
                )
                st.session_state['ffmpeg_thread'].start()
                st.success("🎬 Streaming dimulai ke YouTube!")

    with col2:
        if st.button("🛑 Hentikan Streaming", use_container_width=True):
            os.system("pkill ffmpeg")
            log_callback("⚠️ Streaming dihentikan oleh pengguna.")

    st.divider()
    st.write("📜 Log Aktivitas:")
    log_placeholder.text("\n".join(logs[-25:]))


if __name__ == "__main__":
    main()
