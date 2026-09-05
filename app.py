import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st


# =========================================================
# CLIPFLOW AI — CREATIVE VIDEO STUDIO
# =========================================================

st.set_page_config(
    page_title="ClipFlow AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PATHS / SETTINGS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = 200


# =========================================================
# PREMIUM UI
# =========================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(124, 58, 237, 0.18), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(37, 99, 235, 0.15), transparent 30%),
        linear-gradient(135deg, #070711 0%, #0b0b16 48%, #080914 100%);
    color: #f8fafc;
}

/* Main content */
.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #0b0b16 0%,
            #080811 55%,
            #06060d 100%
        );
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

.sidebar-brand {
    padding: 0.5rem 0 1.8rem 0;
}

.sidebar-logo {
    font-size: 2.2rem;
    margin-bottom: 0.35rem;
}

.sidebar-title {
    font-size: 1.35rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.04em;
}

.sidebar-subtitle {
    color: #8f91a6;
    font-size: 0.78rem;
    margin-top: 0.25rem;
}

.sidebar-section {
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 800;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
}

/* Sidebar labels */
section[data-testid="stSidebar"] label {
    color: #d9dbe7 !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #c5c7d5;
}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 30px;
    padding: 4.4rem 4.5rem;
    min-height: 470px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background:
        radial-gradient(
            circle at 85% 20%,
            rgba(124,58,237,0.30),
            transparent 30%
        ),
        radial-gradient(
            circle at 10% 100%,
            rgba(37,99,235,0.20),
            transparent 34%
        ),
        linear-gradient(
            135deg,
            rgba(22,22,40,0.98),
            rgba(12,12,24,0.97)
        );
    box-shadow:
        0 30px 90px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.05);
}

.hero::before {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    right: -150px;
    top: -180px;
    border-radius: 50%;
    background: rgba(124,58,237,0.15);
    filter: blur(70px);
}

.hero::after {
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    left: -150px;
    bottom: -180px;
    border-radius: 50%;
    background: rgba(59,130,246,0.12);
    filter: blur(70px);
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    width: fit-content;
    padding: 9px 15px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    color: #d8d4ff;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.12em;
}

.hero-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #a78bfa;
    box-shadow: 0 0 15px rgba(167,139,250,0.9);
}

.hero h1 {
    margin: 1.45rem 0 1rem 0;
    font-size: clamp(3.2rem, 7vw, 6.7rem);
    line-height: 0.92;
    letter-spacing: -0.075em;
    font-weight: 900;
    color: #ffffff !important;
    text-shadow: 0 8px 40px rgba(0,0,0,0.5);
}

.hero-gradient {
    background: linear-gradient(
        100deg,
        #c4b5fd 0%,
        #a78bfa 35%,
        #60a5fa 70%,
        #93c5fd 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 5px 25px rgba(124,58,237,0.25));
}

.hero p {
    max-width: 700px;
    margin: 0;
    color: #b9bbca !important;
    font-size: 1.03rem;
    line-height: 1.8;
}

.hero-mini {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 2rem;
}

.hero-chip {
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.09);
    color: #dfe1ec;
    font-size: 0.78rem;
    font-weight: 700;
}

/* Feature section */
.section-kicker {
    margin-top: 3.5rem;
    margin-bottom: 0.4rem;
    color: #9b8cff;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 0.16em;
}

.section-title {
    color: #ffffff;
    font-size: 1.65rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    margin-bottom: 1.4rem;
}

.feature-card {
    position: relative;
    min-height: 250px;
    padding: 1.55rem;
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,0.08);
    background:
        linear-gradient(
            145deg,
            rgba(24,24,43,0.92),
            rgba(13,13,25,0.92)
        );
    box-shadow: 0 18px 45px rgba(0,0,0,0.20);
    transition: all 0.25s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
    border-color: rgba(167,139,250,0.30);
    box-shadow: 0 24px 55px rgba(0,0,0,0.35);
}

.feature-number {
    color: #65677a;
    font-size: 0.7rem;
    font-weight: 900;
    letter-spacing: 0.1em;
}

.feature-icon {
    font-size: 2rem;
    margin-top: 1.5rem;
}

.feature-title {
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 800;
    margin-top: 0.9rem;
}

.feature-text {
    color: #9295a8;
    font-size: 0.83rem;
    line-height: 1.65;
    margin-top: 0.45rem;
}

/* Upload */
.upload-card {
    padding: 1.6rem;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    background:
        linear-gradient(
            145deg,
            rgba(25,25,45,0.88),
            rgba(12,12,23,0.92)
        );
    text-align: center;
    margin-bottom: 1.2rem;
}

.upload-icon {
    font-size: 2.3rem;
}

.upload-title {
    margin-top: 0.65rem;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 800;
}

.upload-text {
    margin-top: 0.4rem;
    color: #85889b;
    font-size: 0.76rem;
}

/* Streamlit uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.025);
    border: 1px dashed rgba(167,139,250,0.30);
    border-radius: 20px;
    padding: 0.5rem;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,0.015) !important;
}

[data-testid="stFileUploaderDropzone"] * {
    color: #c9cad6 !important;
}

/* Inputs */
.stSelectbox > div > div,
.stSlider,
.stCheckbox {
    color: #ffffff !important;
}

div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.045) !important;
    border-color: rgba(255,255,255,0.10) !important;
}

div[data-baseweb="select"] span {
    color: #eeeeF5 !important;
}

input {
    color: #ffffff !important;
}

/* Buttons */
.stButton > button {
    width: 100%;
    min-height: 54px;
    border: 0 !important;
    border-radius: 15px !important;
    color: #ffffff !important;
    font-weight: 900 !important;
    font-size: 0.9rem !important;
    background:
        linear-gradient(
            100deg,
            #7c3aed,
            #6366f1,
            #3b82f6
        ) !important;
    box-shadow:
        0 14px 35px rgba(99,102,241,0.28);
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 18px 45px rgba(99,102,241,0.38);
}

/* Download */
.stDownloadButton > button {
    width: 100%;
    min-height: 52px;
    border-radius: 15px !important;
    border: 1px solid rgba(167,139,250,0.25) !important;
    background: rgba(124,58,237,0.14) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Cards */
.glass-card {
    padding: 1.4rem;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.035);
}

.result-card {
    padding: 1.7rem;
    border-radius: 24px;
    border: 1px solid rgba(167,139,250,0.18);
    background:
        radial-gradient(
            circle at 90% 0%,
            rgba(124,58,237,0.12),
            transparent 35%
        ),
        rgba(255,255,255,0.035);
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 17px;
    padding: 1rem;
}

[data-testid="stMetricLabel"] {
    color: #8f91a4 !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

/* Video */
video {
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.025);
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 15px;
}

/* Empty state */
.empty-state {
    margin-top: 1rem;
    min-height: 230px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    border: 1px dashed rgba(255,255,255,0.10);
    border-radius: 24px;
    background: rgba(255,255,255,0.025);
}

.empty-icon {
    font-size: 2.5rem;
}

.empty-title {
    color: #ffffff;
    font-size: 1rem;
    font-weight: 800;
    margin-top: 0.8rem;
}

.empty-text {
    color: #777b8f;
    font-size: 0.82rem;
    margin-top: 0.4rem;
}

/* Small helper text */
.helper-text {
    color: #777b8f;
    font-size: 0.76rem;
    line-height: 1.6;
}

.success-title {
    color: #ffffff;
    font-size: 1.35rem;
    font-weight: 900;
}

.moment-item {
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    border-radius: 13px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.06);
    color: #c9cad5;
    font-size: 0.82rem;
}

/* Mobile */
@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 2.5rem 1.5rem;
        min-height: 420px;
        border-radius: 23px;
    }

    .hero h1 {
        font-size: 3.3rem;
    }

    .hero p {
        font-size: 0.9rem;
    }

    .feature-card {
        min-height: 210px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">🎬</div>
            <div class="sidebar-title">ClipFlow AI</div>
            <div class="sidebar-subtitle">Creative Video Studio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section">⚙️ Edit Settings</div>',
        unsafe_allow_html=True,
    )

    platform = st.selectbox(
        "Platform",
        [
            "YouTube Shorts",
            "Instagram Reels",
            "TikTok",
        ],
    )

    target_length = st.slider(
        "Target video length",
        min_value=10,
        max_value=90,
        value=30,
        step=5,
    )

    num_clips = st.slider(
        "Number of clips",
        min_value=2,
        max_value=8,
        value=5,
        step=1,
    )

    music_mood = st.selectbox(
        "Music mood",
        [
            "Auto",
            "Energetic",
            "Cinematic",
            "Calm",
            "Funny",
            "Professional",
        ],
    )

    add_music = st.checkbox(
        "🎵 Add background music",
        value=False,
    )

    analyze_silence = st.checkbox(
        "⏸️ Analyze long silences",
        value=False,
    )

    generate_captions = st.checkbox(
        "🎙️ Generate auto captions",
        value=False,
    )

    st.markdown(
        """
        <div class="helper-text" style="margin-top:1rem;">
            🎵 Only upload music you own or have permission to use.
            ClipFlow does not provide copyrighted music.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-content">

            <div class="hero-badge">
                <span class="hero-dot"></span>
                CLIPFLOW AI · CREATIVE VIDEO STUDIO
            </div>

            <h1>
                YOUR FOOTAGE.<br>
                <span class="hero-gradient">
                    YOUR NEXT SHORT.
                </span>
            </h1>

            <p>
                Turn raw footage into polished vertical content
                with smart moment detection, intelligent framing,
                synchronized captions and optional music mixing.
            </p>

            <div class="hero-mini">
                <div class="hero-chip">🎯 Smart Moments</div>
                <div class="hero-chip">📱 9:16 Studio</div>
                <div class="hero-chip">🎙️ AI Captions</div>
                <div class="hero-chip">🎵 Music Mix</div>
            </div>

        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FEATURES
# =========================================================

st.markdown(
    """
    <div class="section-kicker">WHY CLIPFLOW</div>
    <div class="section-title">Everything you need to create a Short.</div>
    """,
    unsafe_allow_html=True,
)

feature_data = [
    (
        "01",
        "🎯",
        "Smart Moments",
        "Detects visually active sections and turns them into usable clips.",
    ),
    (
        "02",
        "📱",
        "Smart Framing",
        "Transforms landscape footage into polished vertical 9:16 content.",
    ),
    (
        "03",
        "🎙️",
        "Auto Captions",
        "Creates synchronized subtitles from your original speech.",
    ),
    (
        "04",
        "🎵",
        "Music Ready",
        "Mixes your own licensed background music at a balanced level.",
    ),
]

cols = st.columns(4)

for col, item in zip(cols, feature_data):

    number, icon, title, text = item

    with col:

        st.markdown(
            f"""
            <div class="feature-card">

                <div class="feature-number">
                    {number}
                </div>

                <div class="feature-icon">
                    {icon}
                </div>

                <div class="feature-title">
                    {title}
                </div>

                <div class="feature-text">
                    {text}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# UPLOAD SECTION
# =========================================================

st.markdown(
    """
    <div class="section-kicker">START CREATING</div>
    <div class="section-title">📁 Upload your footage</div>

    <div class="upload-card">

        <div class="upload-icon">
            🎬
        </div>

        <div class="upload-title">
            Drop your footage into ClipFlow
        </div>

        <div class="upload-text">
            MP4 · MOV · M4V · AVI
            &nbsp;•&nbsp;
            Maximum 200MB
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


uploaded_video = st.file_uploader(
    "Upload video",
    type=["mp4", "mov", "m4v", "avi"],
    label_visibility="collapsed",
)


# =========================================================
# OPTIONAL MUSIC
# =========================================================

uploaded_music = None

if add_music:

    st.markdown(
        """
        <div class="section-kicker" style="margin-top:1.7rem;">
            OPTIONAL
        </div>
        <div class="section-title">
            🎵 Add your music
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_music = st.file_uploader(
        "Upload licensed music",
        type=["mp3", "wav", "m4a"],
        label_visibility="collapsed",
    )


# =========================================================
# FFMPEG HELPERS
# =========================================================

def get_ffmpeg():

    try:

        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()

    except Exception:
        pass

    system_ffmpeg = shutil.which("ffmpeg")

    if system_ffmpeg:
        return system_ffmpeg

    return "ffmpeg"


FFMPEG = get_ffmpeg()


def run_ffmpeg(args, check=True):

    command = [
        FFMPEG,
        "-y",
        *[str(x) for x in args],
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and result.returncode != 0:

        raise RuntimeError(
            result.stderr[-5000:]
        )

    return result


# =========================================================
# MEDIA DURATION
# =========================================================

def get_media_duration(path):

    try:

        cap = cv2.VideoCapture(str(path))

        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        cap.release()

        if fps and fps > 0 and frames > 0:

            return frames / fps

    except Exception:
        pass

    try:

        result = run_ffmpeg(
            ["-i", str(path)],
            check=False,
        )

        text = result.stderr

        match = re.search(
            r"Duration:\s*(\d+):(\d+):([\d.]+)",
            text,
        )

        if match:

            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))

            return (
                hours * 3600
                + minutes * 60
                + seconds
            )

    except Exception:
        pass

    return 0.0


# =========================================================
# VIDEO ANALYSIS
# =========================================================

def analyze_video(path):

    cap = cv2.VideoCapture(str(path))

    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_count = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = (
        frame_count / fps
        if fps and fps > 0
        else 0
    )

    samples = []

    interval = 0.5

    current_time = 0.0
    previous = None

    while current_time < duration:

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            current_time * 1000,
        )

        ok, frame = cap.read()

        if not ok:
            current_time += interval
            continue

        small = cv2.resize(
            frame,
            (160, 90),
        )

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2GRAY,
        )

        gray = gray.astype(
            np.float32
        )

        if previous is not None:

            diff = np.mean(
                np.abs(gray - previous)
            )

            samples.append(
                (current_time, float(diff))
            )

        previous = gray

        current_time += interval

    cap.release()

    return {
        "duration": duration,
        "samples": samples,
    }


# =========================================================
# SMART CLIP SELECTION
# =========================================================

def select_clips(
    samples,
    duration,
    target_length,
    num_clips,
):

    if duration <= 0:
        return []

    if duration <= target_length:

        return [
            {
                "start": 0,
                "end": duration,
            }
        ]

    if not samples:

        segment = duration / num_clips

        return [
            {
                "start": i * segment,
                "end": min(
                    duration,
                    (i + 1) * segment,
                ),
            }
            for i in range(num_clips)
        ]

    scores = np.array(
        [score for _, score in samples],
        dtype=np.float32,
    )

    if len(scores) >= 5:

        kernel = np.ones(5) / 5

        smooth = np.convolve(
            scores,
            kernel,
            mode="same",
        )

    else:

        smooth = scores

    threshold = np.percentile(
        smooth,
        55,
    )

    active_times = [
        t
        for (t, _), score in zip(
            samples,
            smooth,
        )
        if score >= threshold
    ]

    windows = []

    if active_times:

        start = active_times[0]
        previous = active_times[0]

        for t in active_times[1:]:

            if t - previous > 1.5:

                windows.append(
                    (start, previous + 0.5)
                )

                start = t

            previous = t

        windows.append(
            (start, previous + 0.5)
        )

    min_clip = max(
        4.0,
        min(
            12.0,
            target_length / max(num_clips, 1),
        ),
    )

    usable = [
        (s, e)
        for s, e in windows
        if e - s >= min_clip
    ]

    if not usable:

        segment = duration / num_clips

        usable = [
            (
                i * segment,
                min(
                    duration,
                    (i + 1) * segment,
                ),
            )
            for i in range(num_clips)
        ]

    usable = sorted(
        usable,
        key=lambda x: x[1] - x[0],
        reverse=True,
    )

    selected = []

    for start, end in usable:

        if len(selected) >= num_clips:
            break

        clip_length = min(
            end - start,
            max(
                5,
                target_length / max(num_clips, 1),
            ),
        )

        center = (
            start + end
        ) / 2

        clip_start = max(
            0,
            center - clip_length / 2,
        )

        clip_end = min(
            duration,
            clip_start + clip_length,
        )

        if clip_end - clip_start >= 2:

            selected.append(
                {
                    "start": clip_start,
                    "end": clip_end,
                }
            )

    if not selected:

        segment = duration / num_clips

        selected = [
            {
                "start": i * segment,
                "end": min(
                    duration,
                    (i + 1) * segment,
                ),
            }
            for i in range(num_clips)
        ]

    selected = sorted(
        selected,
        key=lambda x: x["start"],
    )

    return selected


# =========================================================
# SILENCE DETECTION
# =========================================================

def detect_silence(path):

    result = run_ffmpeg(
        [
            "-i",
            str(path),
            "-af",
            "silencedetect=noise=-35dB:d=0.8",
            "-f",
            "null",
            "-",
        ],
        check=False,
    )

    output = result.stderr

    starts = re.findall(
        r"silence_start:\s*([\d.]+)",
        output,
    )

    ends = re.findall(
        r"silence_end:\s*([\d.]+)",
        output,
    )

    return [
        {
            "start": float(s),
            "end": float(e),
        }
        for s, e in zip(starts, ends)
    ]


# =========================================================
# VERTICAL VIDEO FILTER
# =========================================================

def get_vertical_filter(width, height):

    if width <= 0 or height <= 0:

        return (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
        )

    ratio = width / height

    if ratio < 0.9:

        return (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
        )

    return (
        "split=2[bg][fg];"
        "[bg]"
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=25:10,"
        "[blur];"
        "[fg]"
        "scale=980:1740:force_original_aspect_ratio=decrease,"
        "pad=980:1740:(ow-iw)/2:(oh-ih)/2:0x11111b,"
        "[foreground];"
        "[blur][foreground]"
        "overlay=(W-w)/2:(H-h)/2"
    )


# =========================================================
# CREATE CLIP
# =========================================================

def create_clip(
    source,
    output,
    start,
    end,
    width,
    height,
):

    duration = max(
        0.1,
        end - start,
    )

    vf = get_vertical_filter(
        width,
        height,
    )

    run_ffmpeg(
        [
            "-ss",
            start,
            "-i",
            source,
            "-t",
            duration,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output,
        ]
    )


# =========================================================
# JOIN CLIPS
# =========================================================

def join_clips(clips, output, work_dir):

    concat_file = work_dir / "concat.txt"

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as f:

        for clip in clips:

            safe_path = str(
                Path(clip).resolve()
            ).replace(
                "'",
                "'\\''",
            )

            f.write(
                f"file '{safe_path}'\n"
            )

    run_ffmpeg(
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output,
        ]
    )


# =========================================================
# MUSIC MIXING
# =========================================================

def mix_music(
    video_path,
    music_path,
    output_path,
):

    duration = get_media_duration(
        video_path
    )

    if duration <= 0:
        duration = 30

    fade_out_start = max(
        0,
        duration - 1.5,
    )

    filter_complex = (
        f"[1:a]"
        f"volume=0.14,"
        f"afade=t=in:st=0:d=1,"
        f"afade=t=out:st={fade_out_start}:d=1.5"
        f"[music];"
        f"[0:a][music]"
        f"amix=inputs=2:"
        f"duration=first:"
        f"dropout_transition=2"
        f"[aout]"
    )

    run_ffmpeg(
        [
            "-i",
            video_path,
            "-stream_loop",
            "-1",
            "-i",
            music_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            "-movflags",
            "+faststart",
            output_path,
        ]
    )


# =========================================================
# WHISPER
# =========================================================

@st.cache_resource
def load_whisper():

    from faster_whisper import WhisperModel

    return WhisperModel(
        "tiny",
        device="cpu",
        compute_type="int8",
    )


# =========================================================
# SRT
# =========================================================

def seconds_to_srt(seconds):

    hours = int(seconds // 3600)

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = int(
        seconds % 60
    )

    millis = int(
        round(
            (seconds - int(seconds))
            * 1000
        )
    )

    if millis >= 1000:

        millis = 0
        secs += 1

    if secs >= 60:

        secs = 0
        minutes += 1

    if minutes >= 60:

        minutes = 0
        hours += 1

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{millis:03d}"
    )


def create_srt_for_selected_clips(
    source,
    selected_clips,
    output_srt,
):

    model = load_whisper()

    segments, _ = model.transcribe(
        str(source),
        beam_size=1,
    )

    whisper_segments = list(
        segments
    )

    lines = []

    subtitle_index = 1
    output_offset = 0.0

    for clip in selected_clips:

        clip_start = clip["start"]
        clip_end = clip["end"]

        for segment in whisper_segments:

            seg_start = segment.start
            seg_end = segment.end

            overlap_start = max(
                seg_start,
                clip_start,
            )

            overlap_end = min(
                seg_end,
                clip_end,
            )

            if overlap_end <= overlap_start:
                continue

            text = segment.text.strip()

            if not text:
                continue

            local_start = (
                overlap_start
                - clip_start
                + output_offset
            )

            local_end = (
                overlap_end
                - clip_start
                + output_offset
            )

            lines.append(
                f"{subtitle_index}\n"
                f"{seconds_to_srt(local_start)} --> "
                f"{seconds_to_srt(local_end)}\n"
                f"{text}\n"
            )

            subtitle_index += 1

        output_offset += (
            clip_end - clip_start
        )

    with open(
        output_srt,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("\n".join(lines))

    return len(lines)


# =========================================================
# BURN CAPTIONS
# =========================================================

def burn_captions(
    video_path,
    srt_path,
    output_path,
):

    escaped = str(
        Path(srt_path).resolve()
    )

    escaped = escaped.replace(
        "\\",
        "/",
    )

    escaped = escaped.replace(
        ":",
        "\\:",
    )

    escaped = escaped.replace(
        "'",
        "\\'",
    )

    subtitle_filter = (
        f"subtitles='{escaped}':"
        "force_style="
        "'FontName=Arial,"
        "FontSize=20,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=90'"
    )

    run_ffmpeg(
        [
            "-i",
            video_path,
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            output_path,
        ]
    )


# =========================================================
# COMPLETE PROCESS
# =========================================================

def process_video(
    source,
    music,
    target_length,
    num_clips,
    use_music,
    use_silence,
    use_captions,
    progress,
):

    work_dir = Path(
        tempfile.mkdtemp(
            prefix="clipflow_"
        )
    )

    try:

        progress.progress(
            5,
            text="Analyzing your footage..."
        )

        cap = cv2.VideoCapture(
            str(source)
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        cap.release()

        analysis = analyze_video(
            source
        )

        duration = analysis["duration"]

        if duration <= 0:

            raise RuntimeError(
                "Could not read video duration."
            )

        progress.progress(
            20,
            text="Finding the best moments..."
        )

        selected = select_clips(
            analysis["samples"],
            duration,
            target_length,
            num_clips,
        )

        if not selected:

            raise RuntimeError(
                "No usable video moments were detected."
            )

        silence_data = []

        if use_silence:

            progress.progress(
                28,
                text="Analyzing long silences..."
            )

            silence_data = detect_silence(
                source
            )

        clip_files = []

        total = len(selected)

        for index, clip in enumerate(
            selected,
            start=1,
        ):

            output_clip = (
                work_dir
                / f"clip_{index:02d}.mp4"
            )

            create_clip(
                source,
                output_clip,
                clip["start"],
                clip["end"],
                width,
                height,
            )

            clip_files.append(
                output_clip
            )

            progress.progress(
                30
                + int(
                    (index / total)
                    * 35
                ),
                text=(
                    f"Creating Short "
                    f"{index}/{total}..."
                ),
            )

        joined = (
            work_dir
            / "joined.mp4"
        )

        progress.progress(
            68,
            text="Combining your best moments..."
        )

        join_clips(
            clip_files,
            joined,
            work_dir,
        )

        current_video = joined

        music_added = False

        if use_music and music:

            progress.progress(
                76,
                text="Mixing your background music..."
            )

            music_output = (
                work_dir
                / "music_mix.mp4"
            )

            mix_music(
                current_video,
                music,
                music_output,
            )

            current_video = (
                music_output
            )

            music_added = True

        captions_created = 0

        if use_captions:

            progress.progress(
                84,
                text="Generating AI captions..."
            )

            srt_file = (
                work_dir
                / "captions.srt"
            )

            captions_created = (
                create_srt_for_selected_clips(
                    source,
                    selected,
                    srt_file,
                )
            )

            if captions_created > 0:

                caption_output = (
                    work_dir
                    / "captions.mp4"
                )

                progress.progress(
                    90,
                    text="Burning captions into video..."
                )

                burn_captions(
                    current_video,
                    srt_file,
                    caption_output,
                )

                current_video = (
                    caption_output
                )

        progress.progress(
            96,
            text="Preparing your final Short..."
        )

        final_output = (
            OUTPUT_DIR
            / "clipflow_ai_result.mp4"
        )

        shutil.copy2(
            current_video,
            final_output,
        )

        progress.progress(
            100,
            text="Your Short is ready!"
        )

        return {
            "file": final_output,
            "selected": selected,
            "width": width,
            "height": height,
            "duration": duration,
            "silence_count": len(
                silence_data
            ),
            "captions": captions_created,
            "music": music_added,
        }

    finally:

        shutil.rmtree(
            work_dir,
            ignore_errors=True,
        )


# =========================================================
# MAIN APP
# =========================================================

if uploaded_video is not None:

    file_size_mb = (
        uploaded_video.size
        / (1024 * 1024)
    )

    if file_size_mb > MAX_UPLOAD_MB:

        st.error(
            f"❌ File is {file_size_mb:.1f}MB. "
            f"Maximum allowed size is {MAX_UPLOAD_MB}MB."
        )

        st.stop()

    st.markdown(
        """
        <div class="section-kicker">
            SOURCE FOOTAGE
        </div>
        <div class="section-title">
            Your footage is ready.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_preview, col_info = st.columns(
        [2.2, 1]
    )

    with col_preview:

        st.video(
            uploaded_video
        )

    with col_info:

        temp_preview = (
            Path(
                tempfile.gettempdir()
            )
            / "clipflow_preview.mp4"
        )

        with open(
            temp_preview,
            "wb",
        ) as f:

            f.write(
                uploaded_video.getbuffer()
            )

        preview_duration = (
            get_media_duration(
                temp_preview
            )
        )

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.metric(
            "File size",
            f"{file_size_mb:.1f} MB",
        )

        st.metric(
            "Duration",
            f"{preview_duration:.1f}s",
        )

        st.metric(
            "Target",
            f"{target_length}s",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        try:
            temp_preview.unlink(
                missing_ok=True
            )
        except Exception:
            pass

    # -----------------------------------------------------
    # MUSIC VALIDATION
    # -----------------------------------------------------

    music_path = None
    temp_music = None

    if add_music:

        if uploaded_music is None:

            st.info(
                "🎵 Background music is enabled. "
                "Upload your licensed music below."
            )

        else:

            music_size_mb = (
                uploaded_music.size
                / (1024 * 1024)
            )

            temp_music = (
                Path(
                    tempfile.gettempdir()
                )
                / f"clipflow_music_{uploaded_music.name}"
            )

            with open(
                temp_music,
                "wb",
            ) as f:

                f.write(
                    uploaded_music.getbuffer()
                )

            music_path = temp_music

            st.success(
                f"🎵 Music ready: "
                f"{uploaded_music.name}"
            )

    # -----------------------------------------------------
    # CREATE BUTTON
    # -----------------------------------------------------

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    create_col1, create_col2, create_col3 = (
        st.columns([1, 2, 1])
    )

    with create_col2:

        create_button = st.button(
            "✨ CREATE MY SHORT",
            use_container_width=True,
        )

    if create_button:

        if add_music and music_path is None:

            st.warning(
                "Please upload your licensed music "
                "or turn off background music."
            )

            st.stop()

        temp_video = (
            Path(
                tempfile.gettempdir()
            )
            / f"clipflow_source_{uploaded_video.name}"
        )

        with open(
            temp_video,
            "wb",
        ) as f:

            f.write(
                uploaded_video.getbuffer()
            )

        progress = st.progress(
            0,
            text="Starting ClipFlow AI..."
        )

        try:

            result = process_video(
                temp_video,
                music_path,
                target_length,
                num_clips,
                add_music,
                analyze_silence,
                generate_captions,
                progress,
            )

            st.balloons()

            st.markdown(
                """
                <br>

                <div class="result-card">

                    <div class="success-title">
                        ✨ Your Short is ready.
                    </div>

                    <div class="helper-text" style="margin-top:0.45rem;">
                        ClipFlow found the strongest moments
                        and transformed them into vertical content.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            st.video(
                str(result["file"])
            )

            # ---------------------------------------------
            # DOWNLOAD
            # ---------------------------------------------

            with open(
                result["file"],
                "rb",
            ) as f:

                video_bytes = f.read()

            st.download_button(
                label="⬇️ DOWNLOAD MY SHORT",
                data=video_bytes,
                file_name="clipflow_ai_short.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

            # ---------------------------------------------
            # SUMMARY
            # ---------------------------------------------

            st.markdown(
                """
                <div class="section-kicker">
                    CREATION SUMMARY
                </div>
                """,
                unsafe_allow_html=True,
            )

            metric_cols = st.columns(4)

            with metric_cols[0]:

                st.metric(
                    "Original",
                    f"{result['duration']:.1f}s",
                )

            with metric_cols[1]:

                st.metric(
                    "Clips",
                    len(
                        result["selected"]
                    ),
                )

            with metric_cols[2]:

                st.metric(
                    "Format",
                    "1080 × 1920",
                )

            with metric_cols[3]:

                st.metric(
                    "Captions",
                    (
                        "Yes"
                        if result["captions"] > 0
                        else "Off"
                    ),
                )

            # ---------------------------------------------
            # SELECTED MOMENTS
            # ---------------------------------------------

            st.markdown(
                """
                <div class="section-kicker">
                    SMART MOMENTS
                </div>

                <div class="section-title">
                    Selected sections
                </div>
                """,
                unsafe_allow_html=True,
            )

            for index, clip in enumerate(
                result["selected"],
                start=1,
            ):

                start = clip["start"]
                end = clip["end"]

                st.markdown(
                    f"""
                    <div class="moment-item">
                        <strong>
                            Moment {index}
                        </strong>
                        &nbsp;&nbsp;
                        {start:.1f}s → {end:.1f}s
                        &nbsp;&nbsp;
                        ({end - start:.1f}s)
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ---------------------------------------------
            # DETAILS
            # ---------------------------------------------

            with st.expander(
                "🔧 Processing details"
            ):

                st.write(
                    f"**Platform:** {platform}"
                )

                st.write(
                    f"**Target length:** "
                    f"{target_length} seconds"
                )

                st.write(
                    f"**Music mood:** "
                    f"{music_mood}"
                )

                st.write(
                    f"**Background music:** "
                    f"{'Added' if result['music'] else 'Not added'}"
                )

                st.write(
                    f"**Silence analysis:** "
                    f"{'Enabled' if analyze_silence else 'Disabled'}"
                )

                if analyze_silence:

                    st.write(
                        f"**Long silence sections:** "
                        f"{result['silence_count']}"
                    )

                st.write(
                    f"**Auto captions:** "
                    f"{'Generated' if result['captions'] > 0 else 'Disabled'}"
                )

                st.write(
                    "**Output:** 1080 × 1920 MP4"
                )

        except Exception as e:

            progress.empty()

            st.error(
                "❌ ClipFlow could not finish processing."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(e)
                )

            if generate_captions:

                st.info(
                    "💡 If the error happened while "
                    "creating captions, make sure "
                    "faster-whisper is installed and "
                    "FFmpeg supports the subtitles filter."
                )

        finally:

            try:
                temp_video.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

            if temp_music:

                try:
                    temp_music.unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass


else:

    # =====================================================
    # EMPTY STATE
    # =====================================================

    st.markdown(
        """
        <div class="empty-state">

            <div class="empty-icon">
                🎬
            </div>

            <div class="empty-title">
                Your editing studio is ready.
            </div>

            <div class="empty-text">
                Upload footage above to create your first Short.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:4rem;
        padding-top:1.5rem;
        border-top:1px solid rgba(255,255,255,0.06);
        color:#55586b;
        font-size:0.72rem;
    ">
        🎬 ClipFlow AI · Creative Video Studio
        <br>
        Turn footage into your next Short.
    </div>
    """,
    unsafe_allow_html=True,
)
