```python
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

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# PREMIUM DARK CINEMATIC THEME
# =========================================================

st.markdown(
    """
    <style>

    /* ==============================
       GLOBAL
       ============================== */

    .stApp {
        background:
            radial-gradient(
                circle at 15% 0%,
                rgba(124, 58, 237, 0.18),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 5%,
                rgba(37, 99, 235, 0.16),
                transparent 28%
            ),
            linear-gradient(
                180deg,
                #080812 0%,
                #0b0b15 45%,
                #090910 100%
            );

        color: #f8fafc;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* ==============================
       SIDEBAR
       ============================== */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #0c0c16 0%,
                #090910 100%
            );

        border-right: 1px solid rgba(255,255,255,.08);
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] h2 {
        color: #ffffff;
        font-weight: 800;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,.08);
    }

    /* ==============================
       HERO
       ============================== */

    .hero {
        position: relative;
        overflow: hidden;

        padding: 52px 52px 48px;
        margin-bottom: 28px;

        border-radius: 30px;

        background:
            radial-gradient(
                circle at 80% 25%,
                rgba(124,58,237,.30),
                transparent 28%
            ),
            radial-gradient(
                circle at 65% 85%,
                rgba(37,99,235,.20),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #11111d 0%,
                #10101b 50%,
                #0d1020 100%
            );

        border: 1px solid rgba(255,255,255,.10);

        box-shadow:
            0 25px 80px rgba(0,0,0,.38);
    }

    .hero::before {
        content: "";
        position: absolute;

        width: 240px;
        height: 240px;

        right: -80px;
        top: -90px;

        border-radius: 50%;

        background:
            linear-gradient(
                135deg,
                rgba(168,85,247,.35),
                rgba(59,130,246,.05)
            );

        filter: blur(8px);
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;

        padding: 8px 14px;

        border-radius: 999px;

        background: rgba(139,92,246,.12);

        border: 1px solid rgba(139,92,246,.32);

        color: #c4b5fd;

        font-size: 12px;
        font-weight: 800;

        letter-spacing: 1.2px;

        margin-bottom: 20px;
    }

    .hero h1 {
        position: relative;

        margin: 0;

        color: #ffffff;

        font-size: clamp(42px, 5vw, 68px);

        line-height: .98;

        font-weight: 900;

        letter-spacing: -3px;

        max-width: 850px;
    }

    .hero-gradient {
        background:
            linear-gradient(
                90deg,
                #ffffff 0%,
                #c4b5fd 42%,
                #60a5fa 100%
            );

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero p {
        position: relative;

        max-width: 720px;

        margin-top: 20px;
        margin-bottom: 0;

        color: #a7a8b5;

        font-size: 17px;

        line-height: 1.65;
    }

    .hero-mini {
        position: relative;

        margin-top: 30px;

        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    .hero-chip {
        padding: 8px 13px;

        border-radius: 10px;

        background: rgba(255,255,255,.055);

        border: 1px solid rgba(255,255,255,.08);

        color: #cbd5e1;

        font-size: 12px;
        font-weight: 650;
    }

    /* ==============================
       FEATURE CARDS
       ============================== */

    .feature-card {
        min-height: 145px;

        padding: 20px;

        border-radius: 20px;

        background:
            linear-gradient(
                145deg,
                rgba(255,255,255,.065),
                rgba(255,255,255,.025)
            );

        border: 1px solid rgba(255,255,255,.085);

        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.035);

        transition:
            transform .2s ease,
            border-color .2s ease;
    }

    .feature-card:hover {
        transform: translateY(-3px);

        border-color:
            rgba(139,92,246,.35);
    }

    .feature-icon {
        font-size: 26px;
        margin-bottom: 10px;
    }

    .feature-title {
        color: #f8fafc;

        font-size: 15px;

        font-weight: 800;
    }

    .feature-text {
        margin-top: 5px;

        color: #858796;

        font-size: 12px;

        line-height: 1.5;
    }

    /* ==============================
       SECTION TITLES
       ============================== */

    .section-title {
        margin-top: 34px;
        margin-bottom: 14px;

        color: #f8fafc;

        font-size: 23px;

        font-weight: 850;

        letter-spacing: -.5px;
    }

    .section-kicker {
        color: #7c7e8d;

        font-size: 12px;

        font-weight: 700;

        text-transform: uppercase;

        letter-spacing: 1.3px;

        margin-bottom: 5px;
    }

    /* ==============================
       UPLOAD
       ============================== */

    .upload-card {
        padding: 34px 28px;

        text-align: center;

        border-radius: 24px;

        background:
            radial-gradient(
                circle at 50% 0%,
                rgba(124,58,237,.10),
                transparent 45%
            ),
            rgba(255,255,255,.025);

        border: 2px dashed rgba(139,92,246,.35);

        box-shadow:
            0 20px 60px rgba(0,0,0,.18);
    }

    .upload-icon {
        font-size: 38px;
        margin-bottom: 8px;
    }

    .upload-title {
        color: #ffffff;

        font-size: 18px;

        font-weight: 800;
    }

    .upload-text {
        color: #858796;

        font-size: 13px;

        margin-top: 7px;
    }

    /* ==============================
       GLASS CARDS
       ============================== */

    .glass-card {
        background:
            rgba(255,255,255,.035);

        border:
            1px solid rgba(255,255,255,.085);

        border-radius: 20px;

        padding: 20px;

        box-shadow:
            0 15px 45px rgba(0,0,0,.18);
    }

    /* ==============================
       METRICS
       ============================== */

    .metric-card {
        min-height: 105px;

        padding: 18px;

        border-radius: 18px;

        background:
            linear-gradient(
                145deg,
                rgba(255,255,255,.065),
                rgba(255,255,255,.025)
            );

        border: 1px solid rgba(255,255,255,.08);

        text-align: center;
    }

    .metric-value {
        color: #ffffff;

        font-size: 24px;

        font-weight: 850;
    }

    .metric-label {
        margin-top: 5px;

        color: #858796;

        font-size: 12px;
    }

    /* ==============================
       STREAMLIT BUTTONS
       ============================== */

    div.stButton > button {
        min-height: 50px;

        border-radius: 15px;

        border: 1px solid rgba(139,92,246,.35);

        background:
            linear-gradient(
                135deg,
                #7c3aed,
                #2563eb
            );

        color: #ffffff;

        font-weight: 850;

        letter-spacing: .2px;

        box-shadow:
            0 10px 30px rgba(79,70,229,.20);

        transition:
            transform .15s ease,
            box-shadow .15s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);

        box-shadow:
            0 15px 38px rgba(79,70,229,.32);
    }

    div.stButton > button:disabled {
        opacity: .45;
    }

    /* ==============================
       DOWNLOAD BUTTON
       ============================== */

    .stDownloadButton > button {
        min-height: 50px;

        border-radius: 15px !important;

        background:
            linear-gradient(
                135deg,
                #2563eb,
                #7c3aed
            ) !important;

        color: white !important;

        font-weight: 850 !important;

        border: 0 !important;
    }

    /* ==============================
       INPUTS
       ============================== */

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: rgba(255,255,255,.045);

        border-color: rgba(255,255,255,.10);
    }

    input {
        color: #ffffff !important;
    }

    /* ==============================
       FILE UPLOADER
       ============================== */

    [data-testid="stFileUploader"] section {
        background: rgba(255,255,255,.025);

        border:
            1px solid rgba(255,255,255,.08);

        border-radius: 16px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: transparent;
    }

    /* ==============================
       EXPANDER
       ============================== */

    [data-testid="stExpander"] {
        background: rgba(255,255,255,.025);

        border:
            1px solid rgba(255,255,255,.08);

        border-radius: 18px;
    }

    /* ==============================
       TEXT
       ============================== */

    .stMarkdown,
    .stText,
    label {
        color: #d1d5db;
    }

    /* ==============================
       STATUS BOXES
       ============================== */

    [data-testid="stAlert"] {
        border-radius: 14px;
    }

    /* ==============================
       VIDEO
       ============================== */

    video {
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,.08);

        box-shadow:
            0 20px 60px rgba(0,0,0,.28);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-badge">
            ✦ CLIPFLOW AI · CREATIVE VIDEO STUDIO
        </div>

        <h1>
            YOUR FOOTAGE.<br>
            <span class="hero-gradient">
                YOUR NEXT SHORT.
            </span>
        </h1>

        <p>
            Turn raw footage into polished vertical content with
            AI-powered moment detection, smart framing, synchronized
            captions and optional background music.
        </p>

        <div class="hero-mini">
            <div class="hero-chip">🎯 Smart Moments</div>
            <div class="hero-chip">📱 9:16 Studio</div>
            <div class="hero-chip">🎙️ AI Captions</div>
            <div class="hero-chip">🎵 Music Mix</div>
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FEATURE CARDS
# =========================================================

f1, f2, f3, f4 = st.columns(4)

features = [
    (
        "🎯",
        "Smart Moments",
        "Detects high-activity sections and turns them into usable clips.",
    ),
    (
        "📱",
        "Smart Framing",
        "Transforms landscape footage into a polished 9:16 composition.",
    ),
    (
        "🎙️",
        "Auto Captions",
        "Creates synchronized subtitles from your original speech.",
    ),
    (
        "🎵",
        "Music Ready",
        "Mixes your own licensed background music at a balanced level.",
    ),
]

for col, data in zip(
    [f1, f2, f3, f4],
    features,
):
    icon, title, text = data

    with col:

        st.markdown(
            f"""
            <div class="feature-card">

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
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🎬 ClipFlow AI")

    st.caption(
        "Creative Video Studio"
    )

    st.divider()

    st.markdown("### ⚙️ Edit Settings")

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
        10,
        90,
        30,
    )

    number_of_clips = st.slider(
        "Number of clips",
        2,
        8,
        5,
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
        False,
    )

    remove_silence = st.checkbox(
        "⏸️ Analyze long silences",
        True,
    )

    add_captions = st.checkbox(
        "🎙️ Generate auto captions",
        True,
    )

    st.divider()

    st.caption(
        "🎵 Use only music you have permission to use."
    )


# =========================================================
# UPLOAD SECTION
# =========================================================

st.markdown(
    '<div class="section-kicker">START CREATING</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">📁 Upload your footage</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="upload-card">

        <div class="upload-icon">
            🎬
        </div>

        <div class="upload-title">
            Drop your footage into ClipFlow
        </div>

        <div class="upload-text">
            MP4 · MOV · M4V · AVI &nbsp;•&nbsp; Maximum 200MB
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)

video_file = st.file_uploader(
    "Choose video",
    type=[
        "mp4",
        "mov",
        "m4v",
        "avi",
    ],
    label_visibility="collapsed",
)


# =========================================================
# MUSIC UPLOAD
# =========================================================

music_file = None

if add_music:

    st.markdown(
        '<div class="section-title">🎵 Background music</div>',
        unsafe_allow_html=True,
    )

    music_file = st.file_uploader(
        "Upload licensed music",
        type=[
            "mp3",
            "wav",
            "m4a",
        ],
    )


# =========================================================
# FFMPEG
# =========================================================

def get_ffmpeg():

    try:

        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()

    except Exception:

        found = shutil.which("ffmpeg")

        if found:
            return found

        return "ffmpeg"


def run_ffmpeg(args):

    result = subprocess.run(
        [get_ffmpeg()] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        error = (
            result.stderr
            or "FFmpeg failed."
        )

        if len(error) > 7000:
            error = error[-7000:]

        raise RuntimeError(error)

    return result


# =========================================================
# VIDEO INFO
# =========================================================

def get_video_info(path):

    cap = cv2.VideoCapture(
        str(path)
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

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    frames = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    cap.release()

    if fps <= 0:
        fps = 25

    duration = (
        frames / fps
        if frames > 0
        else 0
    )

    return (
        width,
        height,
        fps,
        duration,
    )


# =========================================================
# VIDEO ANALYSIS
# =========================================================

def analyze_video(path):

    cap = cv2.VideoCapture(
        str(path)
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 25

    frames = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = (
        frames / fps
        if frames > 0
        else 0
    )

    previous = None

    timestamps = []
    scores = []

    frame_number = 0

    step = max(
        1,
        int(fps * 0.5)
    )

    while True:

        ok, frame = cap.read()

        if not ok:
            break

        if frame_number % step == 0:

            small = cv2.resize(
                frame,
                (160, 90),
            )

            gray = cv2.cvtColor(
                small,
                cv2.COLOR_BGR2GRAY,
            )

            if previous is not None:

                diff = cv2.absdiff(
                    gray,
                    previous,
                )

                timestamps.append(
                    frame_number / fps
                )

                scores.append(
                    float(
                        diff.mean()
                    )
                )

            previous = gray

        frame_number += 1

    cap.release()

    return (
        duration,
        timestamps,
        scores,
    )


# =========================================================
# SELECT CLIPS
# =========================================================

def select_clips(
    duration,
    timestamps,
    scores,
    count,
    target,
):

    if duration <= 0:
        return []

    if not scores:

        segment = (
            duration / count
        )

        return [
            (
                i * segment,
                min(
                    duration,
                    (i + 1) * segment,
                ),
            )
            for i in range(count)
        ]

    values = np.asarray(
        scores,
        dtype=float,
    )

    if len(values) >= 5:

        kernel = (
            np.ones(5) / 5
        )

        values = np.convolve(
            values,
            kernel,
            mode="same",
        )

    threshold = np.percentile(
        values,
        60,
    )

    windows = []

    for timestamp, score in zip(
        timestamps,
        values,
    ):

        if score >= threshold:

            start = max(
                0,
                timestamp - 2,
            )

            end = min(
                duration,
                timestamp + 4,
            )

            if not windows:

                windows.append(
                    [start, end]
                )

            elif (
                start
                <= windows[-1][1] + 2
            ):

                windows[-1][1] = max(
                    windows[-1][1],
                    end,
                )

            else:

                windows.append(
                    [start, end]
                )

    if len(windows) < count:

        windows = []

        segment = (
            duration / count
        )

        for i in range(count):

            start = (
                i * segment
            )

            end = min(
                duration,
                start + segment,
            )

            windows.append(
                [start, end]
            )

    ranked = sorted(
        windows,
        key=lambda x: (
            x[1] - x[0]
        ),
        reverse=True,
    )

    selected = []

    per_clip = max(
        2,
        target / count,
    )

    total = 0

    for start, end in ranked:

        if len(selected) >= count:
            break

        clip_length = min(
            end - start,
            per_clip,
        )

        if clip_length < 1:
            continue

        if (
            total + clip_length
            <= target * 1.10
        ):

            selected.append(
                (
                    start,
                    start + clip_length,
                )
            )

            total += clip_length

    selected.sort(
        key=lambda x: x[0]
    )

    return selected


# =========================================================
# SILENCE DETECTION
# =========================================================

def detect_silence(
    source,
    noise="-35dB",
    min_duration=0.8,
):

    try:

        result = run_ffmpeg(
            [
                "-i",
                str(source),
                "-af",
                (
                    "silencedetect="
                    f"noise={noise}:"
                    f"d={min_duration}"
                ),
                "-f",
                "null",
                "-",
            ]
        )

    except Exception:

        return []

    text = result.stderr

    starts = [
        float(x)
        for x in re.findall(
            r"silence_start:\s*([\d.]+)",
            text,
        )
    ]

    ends = [
        float(x)
        for x in re.findall(
            r"silence_end:\s*([\d.]+)",
            text,
        )
    ]

    return list(
        zip(
            starts,
            ends,
        )
    )


# =========================================================
# SMART VERTICAL FRAME
# =========================================================

def get_vertical_filter(
    width,
    height,
):

    ratio = (
        width / height
        if height
        else 1
    )

    # Portrait
    if ratio <= 0.72:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=decrease,"
            "pad=1080:1920:"
            "(ow-iw)/2:"
            "(oh-ih)/2:"
            "black,"
            "setsar=1"
        )

    # Landscape / screen recording
    #
    # FIX:
    # Previously the background stream [bg]
    # was mapped instead of the final overlay.
    #
    return (
        "[0:v]"
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=18:2"
        "[bg];"

        "[0:v]"
        "scale=1080:1920:"
        "force_original_aspect_ratio=decrease"
        "[fg];"

        "[bg][fg]"
        "overlay="
        "(W-w)/2:"
        "(H-h)/2,"
        "setsar=1"
        "[vout]"
    )


# =========================================================
# CREATE CLIP
# =========================================================

def create_clip(
    source,
    start,
    end,
    output,
    width,
    height,
):

    duration = max(
        0.5,
        end - start,
    )

    video_filter = get_vertical_filter(
        width,
        height,
    )

    command = [
        "-y",
        "-ss",
        str(start),
        "-i",
        str(source),
        "-t",
        str(duration),
    ]

    if "[vout]" in video_filter:

        command += [
            "-filter_complex",
            video_filter,
            "-map",
            "[vout]",
        ]

    else:

        command += [
            "-vf",
            video_filter,
            "-map",
            "0:v:0",
        ]

    command += [
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        str(output),
    ]

    run_ffmpeg(command)


# =========================================================
# JOIN CLIPS
# =========================================================

def join_clips(
    clips,
    output,
):

    concat = Path(
        tempfile.mktemp(
            suffix=".txt"
        )
    )

    lines = []

    for clip in clips:

        safe_path = (
            clip
            .resolve()
            .as_posix()
            .replace(
                "'",
                "'\\''",
            )
        )

        lines.append(
            f"file '{safe_path}'"
        )

    concat.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    try:

        run_ffmpeg(
            [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
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
                str(output),
            ]
        )

    finally:

        concat.unlink(
            missing_ok=True
        )


# =========================================================
# MUSIC MIX
# =========================================================

def mix_music(
    video,
    music,
    output,
):

    run_ffmpeg(
        [
            "-y",

            "-i",
            str(video),

            "-stream_loop",
            "-1",

            "-i",
            str(music),

            "-filter_complex",

            "[1:a]"
            "volume=0.14,"
            "afade=t=in:st=0:d=1,"
            "afade=t=out:st=28:d=2"
            "[music];"

            "[0:a]"
            "volume=1.0"
            "[voice];"

            "[voice][music]"
            "amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[audio]",

            "-map",
            "0:v:0",

            "-map",
            "[audio]",

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-b:a",
            "160k",

            "-shortest",

            str(output),
        ]
    )


# =========================================================
# WHISPER
# =========================================================

@st.cache_resource(
    show_spinner=False
)
def load_whisper():

    try:

        from faster_whisper import (
            WhisperModel
        )

        return WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
        )

    except Exception as error:

        raise RuntimeError(
            "Automatic captions could not start. "
            "Make sure faster-whisper is installed. "
            + str(error)
        )


# =========================================================
# SRT TIMESTAMP
# =========================================================

def seconds_to_srt(seconds):

    seconds = max(
        0,
        float(seconds),
    )

    hours = int(
        seconds // 3600
    )

    minutes = int(
        (seconds % 3600) // 60
    )

    secs = int(
        seconds % 60
    )

    millis = int(
        round(
            (
                seconds
                - int(seconds)
            )
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


# =========================================================
# CREATE SRT FOR SELECTED CLIPS
# =========================================================

def create_srt_for_selected_clips(
    source,
    selected_clips,
    output,
):

    model = load_whisper()

    segments, info = model.transcribe(
        str(source),
        vad_filter=True,
        beam_size=1,
    )

    segments = list(segments)

    entries = []

    output_position = 0.0
    index = 1

    for clip_start, clip_end in selected_clips:

        for segment in segments:

            seg_start = float(
                segment.start
            )

            seg_end = float(
                segment.end
            )

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

            relative_start = (
                overlap_start
                - clip_start
            )

            relative_end = (
                overlap_end
                - clip_start
            )

            final_start = (
                output_position
                + relative_start
            )

            final_end = (
                output_position
                + relative_end
            )

            entries.append(
                (
                    index,
                    final_start,
                    final_end,
                    text,
                )
            )

            index += 1

        output_position += (
            clip_end - clip_start
        )

    if not entries:
        return False

    lines = []

    for (
        index,
        start,
        end,
        text,
    ) in entries:

        lines.append(
            str(index)
        )

        lines.append(
            f"{seconds_to_srt(start)} --> "
            f"{seconds_to_srt(end)}"
        )

        lines.append(text)

        lines.append("")

    output.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return True


# =========================================================
# SAFE SUBTITLE PATH
# =========================================================

def ffmpeg_subtitle_path(path):

    value = str(
        Path(path).resolve()
    )

    value = value.replace(
        "\\",
        "/",
    )

    value = value.replace(
        ":",
        r"\:",
    )

    value = value.replace(
        "'",
        r"\'",
    )

    return value


# =========================================================
# BURN CAPTIONS
# =========================================================

def burn_captions(
    video,
    srt,
    output,
):

    if not srt.exists():

        raise RuntimeError(
            "Caption file was not created."
        )

    if srt.stat().st_size == 0:

        raise RuntimeError(
            "Caption file is empty."
        )

    subtitle_path = (
        ffmpeg_subtitle_path(srt)
    )

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'FontName=Arial,"
        "FontSize=20,"
        "Bold=1,"
        "Alignment=2,"
        "MarginV=110,"
        "Outline=2,"
        "Shadow=1'"
    )

    run_ffmpeg(
        [
            "-y",

            "-i",
            str(video),

            "-vf",
            subtitle_filter,

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "128k",

            str(output),
        ]
    )


# =========================================================
# PROCESS VIDEO
# =========================================================

def process_video(
    video_path,
    music_path,
    target_length,
    clip_count,
    silence_enabled,
    captions_enabled,
    progress_callback=None,
):

    width, height, fps, duration = (
        get_video_info(
            video_path
        )
    )

    (
        analyzed_duration,
        timestamps,
        scores,
    ) = analyze_video(
        video_path
    )

    if progress_callback:
        progress_callback(15)

    selected = select_clips(
        analyzed_duration,
        timestamps,
        scores,
        clip_count,
        target_length,
    )

    if not selected:

        raise RuntimeError(
            "No usable video sections were found."
        )

    work = Path(
        tempfile.mkdtemp(
            prefix="clipflow_ai_"
        )
    )

    try:

        # -------------------------------------------------
        # SILENCE
        # -------------------------------------------------

        silence_info = []

        if silence_enabled:

            silence_info = detect_silence(
                video_path
            )

        if progress_callback:
            progress_callback(25)

        # -------------------------------------------------
        # CREATE CLIPS
        # -------------------------------------------------

        clip_paths = []

        for i, (
            start,
            end,
        ) in enumerate(selected):

            clip = (
                work
                / f"clip_{i:02d}.mp4"
            )

            create_clip(
                video_path,
                start,
                end,
                clip,
                width,
                height,
            )

            clip_paths.append(clip)

        if progress_callback:
            progress_callback(50)

        # -------------------------------------------------
        # JOIN
        # -------------------------------------------------

        joined = (
            work / "joined.mp4"
        )

        join_clips(
            clip_paths,
            joined,
        )

        current = joined

        if progress_callback:
            progress_callback(65)

        # -------------------------------------------------
        # MUSIC
        # -------------------------------------------------

        if music_path:

            music_output = (
                work / "music.mp4"
            )

            mix_music(
                current,
                music_path,
                music_output,
            )

            current = music_output

        if progress_callback:
            progress_callback(75)

        # -------------------------------------------------
        # CAPTIONS
        # -------------------------------------------------

        captions_created = False

        if captions_enabled:

            srt = (
                work / "captions.srt"
            )

            captions_created = (
                create_srt_for_selected_clips(
                    video_path,
                    selected,
                    srt,
                )
            )

            if captions_created:

                captioned = (
                    work
                    / "captioned.mp4"
                )

                burn_captions(
                    current,
                    srt,
                    captioned,
                )

                current = captioned

        if progress_callback:
            progress_callback(92)

        # -------------------------------------------------
        # FINAL OUTPUT
        # -------------------------------------------------

        final = (
            OUTPUT_DIR
            / "clipflow_ai_result.mp4"
        )

        shutil.copy2(
            current,
            final,
        )

        if progress_callback:
            progress_callback(100)

        return {
            "file": final,
            "selected": selected,
            "width": width,
            "height": height,
            "duration": duration,
            "silence_count": len(
                silence_info
            ),
            "captions_created": (
                captions_created
            ),
        }

    finally:

        shutil.rmtree(
            work,
            ignore_errors=True,
        )


# =========================================================
# RUN APP
# =========================================================

if video_file:

    st.markdown(
        '<div class="section-title">🎥 Your source footage</div>',
        unsafe_allow_html=True,
    )

    st.success(
        f"✓ {video_file.name}"
    )

    with st.expander(
        "Preview original footage",
        expanded=True,
    ):

        st.video(video_file)

    if add_music and not music_file:

        st.warning(
            "🎵 Upload a licensed music file to enable "
            "background music."
        )

    can_process = (
        not add_music
        or music_file is not None
    )

    st.markdown(
        '<div class="section-title">✨ Create your Short</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        f"{platform} · {target_length}s target · "
        f"{number_of_clips} clips"
    )

    if st.button(
        "✨  CREATE MY SHORT",
        type="primary",
        use_container_width=True,
        disabled=not can_process,
    ):

        suffix = (
            Path(
                video_file.name
            ).suffix
            or ".mp4"
        )

        input_path = Path(
            tempfile.mktemp(
                suffix=suffix
            )
        )

        input_path.write_bytes(
            video_file.getbuffer()
        )

        music_path = None

        if music_file:

            music_suffix = (
                Path(
                    music_file.name
                ).suffix
                or ".mp3"
            )

            music_path = Path(
                tempfile.mktemp(
                    suffix=music_suffix
                )
            )

            music_path.write_bytes(
                music_file.getbuffer()
            )

        progress = st.progress(0)

        status = st.empty()

        try:

            status.info(
                "🔎 Analyzing your footage..."
            )

            def update_progress(value):

                progress.progress(
                    int(value)
                )

                if value < 25:

                    status.info(
                        "🎯 Finding engaging moments..."
                    )

                elif value < 55:

                    status.info(
                        "✂️ Creating smart clips..."
                    )

                elif value < 75:

                    status.info(
                        "📱 Building your vertical edit..."
                    )

                elif value < 93:

                    if add_captions:

                        status.info(
                            "🎙️ Creating synchronized captions..."
                        )

                    elif music_file:

                        status.info(
                            "🎵 Mixing background music..."
                        )

                    else:

                        status.info(
                            "🎬 Rendering final video..."
                        )

                else:

                    status.info(
                        "✨ Finalizing your Short..."
                    )

            result = process_video(
                input_path,
                music_path,
                target_length,
                number_of_clips,
                remove_silence,
                add_captions,
                update_progress,
            )

            progress.progress(100)

            status.success(
                "🎉 Your Short is ready!"
            )

            st.balloons()

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            st.markdown(
                '<div class="section-title">🎬 Your finished Short</div>',
                unsafe_allow_html=True,
            )

            st.video(
                str(result["file"])
            )

            st.download_button(
                "⬇️  DOWNLOAD MY SHORT",
                data=result["file"].read_bytes(),
                file_name="clipflow_ai_short.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            st.markdown(
                '<div class="section-title">📊 Edit Summary</div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)

            metrics = [
                (
                    c1,
                    f"{result['duration']:.1f}s",
                    "Original duration",
                ),
                (
                    c2,
                    str(
                        len(
                            result["selected"]
                        )
                    ),
                    "Clips selected",
                ),
                (
                    c3,
                    "1080 × 1920",
                    "Output format",
                ),
                (
                    c4,
                    (
                        "ON"
                        if result[
                            "captions_created"
                        ]
                        else "OFF"
                    ),
                    "Captions",
                ),
            ]

            for col, value, label in metrics:

                with col:

                    st.markdown(
                        f"""
                        <div class="metric-card">

                            <div class="metric-value">
                                {value}
                            </div>

                            <div class="metric-label">
                                {label}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # -------------------------------------------------
            # SELECTED MOMENTS
            # -------------------------------------------------

            st.markdown(
                '<div class="section-title">🔍 Selected moments</div>',
                unsafe_allow_html=True,
            )

            for i, (
                start,
                end,
            ) in enumerate(
                result["selected"],
                1,
            ):

                st.markdown(
                    f"""
                    <div class="glass-card"
                         style="margin-bottom:10px;">

                        <strong>
                            Clip {i}
                        </strong>

                        <span style="
                            color:#858796;
                            margin-left:10px;
                        ">
                            {start:.1f}s → {end:.1f}s
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # -------------------------------------------------
            # PROCESSING DETAILS
            # -------------------------------------------------

            st.markdown(
                '<div class="section-title">✨ Processing details</div>',
                unsafe_allow_html=True,
            )

            details = [
                "🎯 Smart moment detection",
                "📱 9:16 vertical framing",
            ]

            if remove_silence:

                details.append(
                    "⏸️ Silence analysis"
                )

            if result[
                "captions_created"
            ]:

                details.append(
                    "🎙️ Synchronized auto captions"
                )

            if music_file:

                details.append(
                    f"🎵 {music_mood} music"
                )

            for detail in details:

                st.write(
                    f"✓ {detail}"
                )

        except Exception as error:

            progress.empty()

            status.empty()

            st.error(
                "❌ ClipFlow couldn't finish this edit."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(error)
                )

            st.info(
                "Tip: If captions are enabled, try the same "
                "video once with Auto Captions turned off. "
                "If that works, the issue is isolated to the "
                "caption engine."
            )

        finally:

            input_path.unlink(
                missing_ok=True
            )

            if music_path:

                music_path.unlink(
                    missing_ok=True
                )

else:

    st.markdown(
        """
        <div class="glass-card"
             style="
                margin-top:25px;
                text-align:center;
                padding:28px;
             ">

            <div style="
                font-size:28px;
                margin-bottom:8px;
            ">
                🎬
            </div>

            <div style="
                color:#ffffff;
                font-size:16px;
                font-weight:800;
            ">
                Your editing studio is ready.
            </div>

            <div style="
                color:#858796;
                font-size:13px;
                margin-top:6px;
            ">
                Upload footage above to create your first Short.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
```
