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
# PATHS
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
        radial-gradient(circle at 10% 0%, rgba(124,58,237,.18), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(37,99,235,.15), transparent 25%),
        linear-gradient(135deg, #070812 0%, #0b0d18 48%, #080a12 100%);
    color: #f8fafc;
}

.main .block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* =====================================================
   SIDEBAR
===================================================== */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #0a0b14 0%, #080910 100%);
    border-right: 1px solid rgba(255,255,255,.07);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.6rem;
}

.sidebar-brand {
    padding: 10px 4px 28px 4px;
}

.sidebar-logo {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 15px;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    box-shadow: 0 12px 30px rgba(124,58,237,.3);
    font-size: 24px;
    margin-bottom: 13px;
}

.sidebar-title {
    font-size: 22px;
    font-weight: 900;
    color: #ffffff;
}

.sidebar-subtitle {
    margin-top: 4px;
    color: #8d93a7;
    font-size: 12px;
}

.sidebar-section {
    margin: 12px 0 16px;
    color: #c7cad7;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: .03em;
}


/* =====================================================
   HERO
===================================================== */

.hero {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 56px 58px;
    margin-bottom: 34px;
    border: 1px solid rgba(255,255,255,.09);

    background:
        radial-gradient(circle at 82% 20%, rgba(59,130,246,.28), transparent 30%),
        radial-gradient(circle at 25% 0%, rgba(139,92,246,.30), transparent 36%),
        linear-gradient(135deg, #121326 0%, #0c1020 55%, #101326 100%);

    box-shadow:
        0 30px 80px rgba(0,0,0,.35),
        inset 0 1px 0 rgba(255,255,255,.05);
}

.hero::after {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    right: -160px;
    bottom: -230px;
    border-radius: 50%;
    background: rgba(124,58,237,.18);
    filter: blur(30px);
}

.hero-content {
    position: relative;
    z-index: 2;
    max-width: 850px;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 8px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.10);
    color: #d6d9e5;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .12em;
}

.hero-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #8b5cf6;
    box-shadow: 0 0 14px #8b5cf6;
}

.hero h1 {
    margin: 24px 0 18px;
    color: #ffffff !important;
    font-size: clamp(42px, 6vw, 78px);
    line-height: .98;
    letter-spacing: -.055em;
    font-weight: 900;
    text-shadow: 0 3px 24px rgba(0,0,0,.5);
}

.hero-gradient {
    color: #a78bfa !important;
    background: linear-gradient(
        90deg,
        #ffffff 0%,
        #c4b5fd 35%,
        #60a5fa 75%,
        #93c5fd 100%
    );
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    max-width: 760px;
    color: #b8bdce !important;
    font-size: 16px;
    line-height: 1.75;
    margin-bottom: 25px;
}

.hero-mini {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.hero-chip {
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.08);
    color: #d7d9e5;
    font-size: 12px;
    font-weight: 700;
}


/* =====================================================
   SECTION TITLES
===================================================== */

.section-kicker {
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: .16em;
    margin-bottom: 7px;
}

.section-title {
    color: #ffffff;
    font-size: 29px;
    font-weight: 850;
    letter-spacing: -.035em;
    margin-bottom: 22px;
}


/* =====================================================
   FEATURE CARDS
===================================================== */

.feature-card {
    min-height: 205px;
    padding: 25px;
    border-radius: 22px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.025)
        );

    border: 1px solid rgba(255,255,255,.075);

    box-shadow:
        0 15px 45px rgba(0,0,0,.18),
        inset 0 1px 0 rgba(255,255,255,.025);

    transition: transform .2s ease, border-color .2s ease;
}

.feature-card:hover {
    transform: translateY(-3px);
    border-color: rgba(139,92,246,.35);
}

.feature-number {
    color: #6f7487;
    font-size: 11px;
    font-weight: 800;
    margin-bottom: 22px;
}

.feature-icon {
    font-size: 26px;
    margin-bottom: 15px;
}

.feature-card h3 {
    color: #ffffff;
    font-size: 17px;
    margin: 0 0 8px;
    font-weight: 800;
}

.feature-card p {
    color: #9298aa;
    font-size: 12px;
    line-height: 1.65;
    margin: 0;
}


/* =====================================================
   UPLOAD AREA
===================================================== */

.upload-section {
    margin-top: 42px;
}

.upload-card {
    padding: 30px;
    border-radius: 24px;
    background:
        linear-gradient(
            145deg,
            rgba(124,58,237,.10),
            rgba(37,99,235,.06)
        );
    border: 1px solid rgba(139,92,246,.20);
}

.upload-icon {
    font-size: 36px;
    margin-bottom: 10px;
}

.upload-title {
    color: #ffffff;
    font-size: 21px;
    font-weight: 850;
}

.upload-subtitle {
    color: #8f95a8;
    font-size: 13px;
    margin-top: 5px;
}


/* =====================================================
   STREAMLIT FILE UPLOADER
===================================================== */

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,.025);
    border-radius: 18px;
    border: 1px dashed rgba(255,255,255,.15);
    padding: 7px;
}

[data-testid="stFileUploader"] section {
    background: transparent !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,.025) !important;
    border: 1px dashed rgba(139,92,246,.30) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #a7adbf !important;
}


/* =====================================================
   INPUTS
===================================================== */

.stSelectbox label,
.stSlider label,
.stCheckbox label {
    color: #cbd0dd !important;
    font-weight: 600 !important;
    font-size: 12px !important;
}

.stSelectbox > div > div {
    background: #11131e !important;
    border-color: rgba(255,255,255,.10) !important;
    color: #ffffff !important;
}

.stSlider [data-baseweb="slider"] {
    padding-top: 7px;
}


/* =====================================================
   BUTTONS
===================================================== */

.stButton > button {
    width: 100%;
    min-height: 48px;
    border: 0;
    border-radius: 14px;

    background:
        linear-gradient(
            100deg,
            #7c3aed,
            #6366f1,
            #2563eb
        );

    color: #ffffff !important;
    font-weight: 850 !important;
    font-size: 13px !important;

    box-shadow:
        0 12px 30px rgba(99,102,241,.24);

    transition: all .2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 18px 38px rgba(99,102,241,.34);
}

.stDownloadButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 14px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.10);
    color: #ffffff !important;
    font-weight: 800;
}


/* =====================================================
   METRICS
===================================================== */

.metric-card {
    padding: 19px;
    border-radius: 18px;
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.07);
}

.metric-label {
    color: #7e8497;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.metric-value {
    color: #ffffff;
    font-size: 22px;
    font-weight: 850;
    margin-top: 5px;
}


/* =====================================================
   RESULT CARD
===================================================== */

.result-card {
    padding: 26px;
    margin-top: 28px;
    border-radius: 24px;
    background:
        linear-gradient(
            145deg,
            rgba(34,197,94,.07),
            rgba(255,255,255,.025)
        );
    border: 1px solid rgba(34,197,94,.18);
}

.result-title {
    color: #ffffff;
    font-size: 22px;
    font-weight: 850;
}

.result-subtitle {
    color: #8e95a8;
    font-size: 12px;
    margin-top: 5px;
}


/* =====================================================
   MOMENT ROW
===================================================== */

.moment-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 15px;
    margin-bottom: 8px;
    border-radius: 13px;
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.05);
}

.moment-left {
    color: #dfe2eb;
    font-size: 12px;
    font-weight: 700;
}

.moment-right {
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 800;
}


/* =====================================================
   EMPTY STATE
===================================================== */

.empty-state {
    margin-top: 35px;
    padding: 58px 25px;
    text-align: center;
    border-radius: 24px;
    border: 1px dashed rgba(255,255,255,.10);
    background: rgba(255,255,255,.018);
}

.empty-icon {
    font-size: 42px;
    margin-bottom: 14px;
}

.empty-title {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
}

.empty-text {
    color: #7f8699;
    font-size: 13px;
    margin-top: 7px;
}


/* =====================================================
   FOOTER
===================================================== */

.footer {
    margin-top: 55px;
    padding-top: 22px;
    border-top: 1px solid rgba(255,255,255,.07);
    color: #666c7d;
    font-size: 11px;
    text-align: center;
}

.footer strong {
    color: #a1a6b5;
}


/* =====================================================
   MOBILE
===================================================== */

@media (max-width: 768px) {

    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 35px 25px;
        border-radius: 23px;
    }

    .hero h1 {
        font-size: 43px;
    }

    .hero p {
        font-size: 14px;
    }

    .feature-card {
        margin-bottom: 12px;
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
        "🎵 Add background music"
    )

    analyze_silence = st.checkbox(
        "⏸️ Analyze long silences"
    )

    generate_captions = st.checkbox(
        "🎙️ Generate auto captions"
    )

    st.markdown("---")

    st.caption(
        "🎵 Only upload music you own or have permission to use. "
        "ClipFlow does not provide copyrighted music."
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
                <span class="hero-gradient">YOUR NEXT SHORT.</span>
            </h1>

            <p>
                Turn raw footage into polished vertical content with
                smart moment detection, intelligent framing,
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
# WHY CLIPFLOW
# =========================================================

st.markdown(
    """
    <div class="section-kicker">WHY CLIPFLOW</div>
    <div class="section-title">Everything you need to create a Short.</div>
    """,
    unsafe_allow_html=True,
)

features = [
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

for col, feature in zip(cols, features):

    number, icon, title, description = feature

    with col:

        st.markdown(
            f"""
            <div class="feature-card">

                <div class="feature-number">{number}</div>

                <div class="feature-icon">{icon}</div>

                <h3>{title}</h3>

                <p>{description}</p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# UPLOAD SECTION
# =========================================================

st.markdown(
    """
    <div class="upload-section">

        <div class="section-kicker">START CREATING</div>

        <div class="section-title">
            📁 Upload your footage
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="upload-card">

        <div class="upload-icon">🎬</div>

        <div class="upload-title">
            Drop your footage into ClipFlow
        </div>

        <div class="upload-subtitle">
            MP4 · MOV · M4V · AVI • Maximum 200MB
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


uploaded_video = st.file_uploader(
    "Upload video",
    type=[
        "mp4",
        "mov",
        "m4v",
        "avi",
    ],
    label_visibility="collapsed",
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


FFMPEG = get_ffmpeg()


def run_ffmpeg(args, check=True):

    command = [FFMPEG, "-y"]

    command.extend(
        [str(x) for x in args]
    )

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and result.returncode != 0:

        raise RuntimeError(
            result.stderr[-7000:]
        )

    return result


# =========================================================
# MEDIA DURATION
# =========================================================

def get_media_duration(path):

    try:

        cap = cv2.VideoCapture(
            str(path)
        )

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        frames = cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )

        cap.release()

        if (
            fps
            and fps > 0
            and frames
            and frames > 0
        ):

            return frames / fps

    except Exception:
        pass

    try:

        result = run_ffmpeg(
            ["-i", path],
            check=False,
        )

        match = re.search(
            r"Duration:\s*(\d+):(\d+):([\d.]+)",
            result.stderr,
        )

        if match:

            hours = int(
                match.group(1)
            )

            minutes = int(
                match.group(2)
            )

            seconds = float(
                match.group(3)
            )

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

    cap = cv2.VideoCapture(
        str(path)
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    frames = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = (
        frames / fps
        if fps and fps > 0
        else 0
    )

    samples = []

    previous = None

    current = 0.0

    interval = 0.5

    while current < duration:

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            current * 1000,
        )

        ok, frame = cap.read()

        if not ok:

            current += interval
            continue

        small = cv2.resize(
            frame,
            (160, 90),
        )

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2GRAY,
        ).astype(
            np.float32
        )

        if previous is not None:

            difference = float(
                np.mean(
                    np.abs(
                        gray - previous
                    )
                )
            )

            samples.append(
                (
                    current,
                    difference,
                )
            )

        previous = gray

        current += interval

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
                "start": 0.0,
                "end": duration,
            }
        ]

    if not samples:

        segment = (
            duration / num_clips
        )

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
        [item[1] for item in samples],
        dtype=np.float32,
    )

    if len(scores) >= 5:

        smooth = np.convolve(
            scores,
            np.ones(5) / 5,
            mode="same",
        )

    else:

        smooth = scores

    threshold = np.percentile(
        smooth,
        55,
    )

    active = []

    for item, score in zip(
        samples,
        smooth,
    ):

        if score >= threshold:

            active.append(
                item[0]
            )

    windows = []

    if active:

        start = active[0]

        previous = active[0]

        for timestamp in active[1:]:

            if timestamp - previous > 1.5:

                windows.append(
                    (
                        start,
                        previous + 0.5,
                    )
                )

                start = timestamp

            previous = timestamp

        windows.append(
            (
                start,
                previous + 0.5,
            )
        )

    min_clip = max(
        4.0,
        min(
            12.0,
            target_length
            / max(num_clips, 1),
        ),
    )

    usable = [
        (start, end)
        for start, end in windows
        if end - start >= min_clip
    ]

    if not usable:

        segment = (
            duration / num_clips
        )

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

    usable.sort(
        key=lambda item: item[1] - item[0],
        reverse=True,
    )

    selected = []

    desired_clip_length = max(
        5.0,
        target_length
        / max(num_clips, 1),
    )

    for start, end in usable:

        if len(selected) >= num_clips:
            break

        clip_length = min(
            end - start,
            desired_clip_length,
        )

        center = (
            start + end
        ) / 2

        clip_start = max(
            0.0,
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

    return sorted(
        selected,
        key=lambda item: item["start"],
    )


# =========================================================
# SILENCE DETECTION
# =========================================================

def detect_silence(path):

    result = run_ffmpeg(
        [
            "-i",
            path,
            "-af",
            "silencedetect=noise=-35dB:d=0.8",
            "-f",
            "null",
            "-",
        ],
        check=False,
    )

    starts = re.findall(
        r"silence_start:\s*([\d.]+)",
        result.stderr,
    )

    ends = re.findall(
        r"silence_end:\s*([\d.]+)",
        result.stderr,
    )

    return [
        {
            "start": float(start),
            "end": float(end),
        }
        for start, end in zip(
            starts,
            ends,
        )
    ]


# =========================================================
# VERTICAL VIDEO FILTER
# =========================================================

def get_vertical_filter(
    width,
    height,
):

    if width <= 0 or height <= 0:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=decrease,"
            "pad=1080:1920:"
            "(ow-iw)/2:(oh-ih)/2:black"
        )

    ratio = width / height

    if ratio < 0.9:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=decrease,"
            "pad=1080:1920:"
            "(ow-iw)/2:(oh-ih)/2:black"
        )

    return (
        "split=2[bg][fg];"
        "[bg]"
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=25:10[blur];"
        "[fg]"
        "scale=980:1740:"
        "force_original_aspect_ratio=decrease,"
        "pad=980:1740:"
        "(ow-iw)/2:(oh-ih)/2:"
        "0x11111b[foreground];"
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

    run_ffmpeg(
        [
            "-ss",
            start,
            "-i",
            source,
            "-t",
            duration,
            "-vf",
            get_vertical_filter(
                width,
                height,
            ),
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

def join_clips(
    clips,
    output,
    work_dir,
):

    concat_file = (
        work_dir / "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as file:

        for clip in clips:

            clip_path = (
                Path(clip)
                .resolve()
                .as_posix()
            )

            file.write(
                f"file '{clip_path}'\n"
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

    duration = max(
        get_media_duration(
            video_path
        ),
        1,
    )

    fade_start = max(
        0.0,
        duration - 1.5,
    )

    filter_complex = (
        "[1:a]"
        "volume=0.14,"
        "afade=t=in:st=0:d=1,"
        f"afade=t=out:st={fade_start}:d=1.5"
        "[music];"
        "[0:a][music]"
        "amix=inputs=2:"
        "duration=first:"
        "dropout_transition=2"
        "[aout]"
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
# SRT TIMESTAMP
# =========================================================

def seconds_to_srt(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours, milliseconds = divmod(
        milliseconds,
        3600000,
    )

    minutes, milliseconds = divmod(
        milliseconds,
        60000,
    )

    seconds_value, milliseconds = divmod(
        milliseconds,
        1000,
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d},"
        f"{milliseconds:03d}"
    )


# =========================================================
# CREATE SRT
# =========================================================

def create_srt(
    source,
    selected_clips,
    output_srt,
):

    model = load_whisper()

    segments, _ = model.transcribe(
        str(source),
        beam_size=1,
        vad_filter=True,
    )

    transcript = []

    for segment in segments:

        transcript.append(
            {
                "start": float(
                    segment.start
                ),
                "end": float(
                    segment.end
                ),
                "text": segment.text.strip(),
            }
        )

    subtitles = []

    output_cursor = 0.0

    for clip in selected_clips:

        clip_start = clip["start"]
        clip_end = clip["end"]

        for segment in transcript:

            overlap_start = max(
                segment["start"],
                clip_start,
            )

            overlap_end = min(
                segment["end"],
                clip_end,
            )

            if overlap_end <= overlap_start:
                continue

            local_start = (
                output_cursor
                + overlap_start
                - clip_start
            )

            local_end = (
                output_cursor
                + overlap_end
                - clip_start
            )

            subtitles.append(
                (
                    local_start,
                    local_end,
                    segment["text"],
                )
            )

        output_cursor += (
            clip_end - clip_start
        )

    with open(
        output_srt,
        "w",
        encoding="utf-8",
    ) as file:

        for index, item in enumerate(
            subtitles,
            start=1,
        ):

            start, end, text = item

            file.write(
                f"{index}\n"
            )

            file.write(
                f"{seconds_to_srt(start)} --> "
                f"{seconds_to_srt(end)}\n"
            )

            file.write(
                f"{text}\n\n"
            )

    return len(subtitles) > 0


# =========================================================
# BURN CAPTIONS
# =========================================================

def burn_captions(
    video_path,
    subtitle_path,
    output_path,
):

    subtitle_escaped = (
        str(
            Path(subtitle_path)
            .resolve()
        )
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )

    filter_value = (
        f"subtitles='{subtitle_escaped}':"
        "force_style='"
        "FontName=Arial,"
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
            filter_value,
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
    target_length,
    num_clips,
    add_music,
    music_path,
    analyze_silence_enabled,
    generate_captions_enabled,
    progress_callback=None,
):

    work_dir = Path(
        tempfile.mkdtemp(
            prefix="clipflow_"
        )
    )

    try:

        # -------------------------------------------------
        # ANALYZE
        # -------------------------------------------------

        if progress_callback:
            progress_callback(
                0.08,
                "Analyzing your footage..."
            )

        analysis = analyze_video(
            source
        )

        duration = analysis[
            "duration"
        ]

        if duration <= 0:

            duration = get_media_duration(
                source
            )

        if duration <= 0:

            raise RuntimeError(
                "Could not determine video duration."
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

        # -------------------------------------------------
        # SMART MOMENTS
        # -------------------------------------------------

        if progress_callback:
            progress_callback(
                0.18,
                "Finding your best moments..."
            )

        selected = select_clips(
            analysis["samples"],
            duration,
            target_length,
            num_clips,
        )

        if not selected:

            raise RuntimeError(
                "No usable moments were detected."
            )

        # -------------------------------------------------
        # SILENCE
        # -------------------------------------------------

        silence = []

        if analyze_silence_enabled:

            if progress_callback:
                progress_callback(
                    0.24,
                    "Analyzing long silences..."
                )

            silence = detect_silence(
                source
            )

        # -------------------------------------------------
        # CREATE CLIPS
        # -------------------------------------------------

        clip_paths = []

        total_clips = len(
            selected
        )

        for index, clip in enumerate(
            selected
        ):

            progress = (
                0.28
                + (
                    index
                    / max(total_clips, 1)
                )
                * 0.35
            )

            if progress_callback:
                progress_callback(
                    progress,
                    f"Creating Short {index + 1} of {total_clips}..."
                )

            clip_path = (
                work_dir
                / f"clip_{index + 1}.mp4"
            )

            create_clip(
                source,
                clip_path,
                clip["start"],
                clip["end"],
                width,
                height,
            )

            clip_paths.append(
                clip_path
            )

        # -------------------------------------------------
        # JOIN
        # -------------------------------------------------

        if progress_callback:
            progress_callback(
                0.68,
                "Combining your clips..."
            )

        joined_path = (
            work_dir
            / "joined.mp4"
        )

        join_clips(
            clip_paths,
            joined_path,
            work_dir,
        )

        current_video = (
            joined_path
        )

        # -------------------------------------------------
        # MUSIC
        # -------------------------------------------------

        music_added = False

        if (
            add_music
            and music_path
        ):

            if progress_callback:
                progress_callback(
                    0.76,
                    "Mixing your background music..."
                )

            music_output = (
                work_dir
                / "music_mix.mp4"
            )

            mix_music(
                current_video,
                music_path,
                music_output,
            )

            current_video = (
                music_output
            )

            music_added = True

        # -------------------------------------------------
        # CAPTIONS
        # -------------------------------------------------

        captions_created = False

        if generate_captions_enabled:

            if progress_callback:
                progress_callback(
                    0.82,
                    "Generating AI captions..."
                )

            subtitle_path = (
                work_dir
                / "captions.srt"
            )

            has_subtitles = create_srt(
                source,
                selected,
                subtitle_path,
            )

            if has_subtitles:

                caption_output = (
                    work_dir
                    / "captions.mp4"
                )

                burn_captions(
                    current_video,
                    subtitle_path,
                    caption_output,
                )

                current_video = (
                    caption_output
                )

                captions_created = True

        # -------------------------------------------------
        # FINAL OUTPUT
        # -------------------------------------------------

        if progress_callback:
            progress_callback(
                0.95,
                "Finishing your Short..."
            )

        final_path = (
            OUTPUT_DIR
            / "clipflow_ai_result.mp4"
        )

        shutil.copy2(
            current_video,
            final_path,
        )

        if progress_callback:
            progress_callback(
                1.0,
                "Your Short is ready!"
            )

        return {
            "file": final_path,
            "selected": selected,
            "width": width,
            "height": height,
            "duration": duration,
            "silence_count": len(silence),
            "captions": captions_created,
            "music": music_added,
        }

    finally:

        shutil.rmtree(
            work_dir,
            ignore_errors=True,
        )


# =========================================================
# MAIN APPLICATION
# =========================================================

if uploaded_video:

    file_size_mb = (
        len(uploaded_video.getvalue())
        / (1024 * 1024)
    )

    if file_size_mb > MAX_UPLOAD_MB:

        st.error(
            f"❌ This file is {file_size_mb:.1f}MB. "
            f"Maximum allowed size is {MAX_UPLOAD_MB}MB."
        )

        st.stop()

    # -----------------------------------------------------
    # SAVE INPUT VIDEO
    # -----------------------------------------------------

    suffix = Path(
        uploaded_video.name
    ).suffix.lower()

    temp_input = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    temp_input.write(
        uploaded_video.getbuffer()
    )

    temp_input.close()

    input_path = Path(
        temp_input.name
    )

    # -----------------------------------------------------
    # PREVIEW
    # -----------------------------------------------------

    st.markdown(
        """
        <div style="
            margin-top:28px;
            color:#8b5cf6;
            font-size:11px;
            font-weight:900;
            letter-spacing:.16em;
        ">
            SOURCE FOOTAGE
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.video(
        str(input_path)
    )

    source_duration = (
        get_media_duration(
            input_path
        )
    )

    metric_cols = st.columns(4)

    metrics = [
        (
            "FILE SIZE",
            f"{file_size_mb:.1f} MB",
        ),
        (
            "DURATION",
            f"{source_duration:.1f}s"
            if source_duration
            else "Unknown",
        ),
        (
            "TARGET",
            f"{target_length}s",
        ),
        (
            "CLIPS",
            str(num_clips),
        ),
    ]

    for col, (label, value) in zip(
        metric_cols,
        metrics,
    ):

        with col:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div class="metric-label">
                        {label}
                    </div>

                    <div class="metric-value">
                        {value}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------
    # MUSIC
    # -----------------------------------------------------

    music_path = None

    if add_music:

        st.markdown(
            "<br>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="section-kicker">
                MUSIC
            </div>

            <div class="section-title">
                🎵 Add your own licensed music
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_music = st.file_uploader(
            "Upload music",
            type=[
                "mp3",
                "wav",
                "m4a",
            ],
            label_visibility="collapsed",
        )

        if uploaded_music:

            music_suffix = Path(
                uploaded_music.name
            ).suffix.lower()

            temp_music = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=music_suffix,
            )

            temp_music.write(
                uploaded_music.getbuffer()
            )

            temp_music.close()

            music_path = Path(
                temp_music.name
            )

            st.success(
                f"🎵 Music ready: "
                f"{uploaded_music.name}"
            )

        else:

            st.info(
                "Upload an MP3, WAV or M4A file "
                "to enable music mixing."
            )

    # -----------------------------------------------------
    # CREATE BUTTON
    # -----------------------------------------------------

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    create_button = st.button(
        "✨ CREATE MY SHORT",
        use_container_width=True,
    )

    if create_button:

        if add_music and music_path is None:

            st.error(
                "Please upload your music file first."
            )

            st.stop()

        progress = st.progress(
            0
        )

        status = st.empty()

        def update_progress(
            value,
            message,
        ):

            progress.progress(
                min(
                    max(value, 0.0),
                    1.0,
                )
            )

            status.markdown(
                f"""
                <div style="
                    padding:12px 16px;
                    border-radius:12px;
                    background:rgba(255,255,255,.04);
                    border:1px solid rgba(255,255,255,.07);
                    color:#b9bfd0;
                    font-size:12px;
                ">
                    ⚡ {message}
                </div>
                """,
                unsafe_allow_html=True,
            )

        try:

            result = process_video(
                source=input_path,
                target_length=target_length,
                num_clips=num_clips,
                add_music=add_music,
                music_path=music_path,
                analyze_silence_enabled=analyze_silence,
                generate_captions_enabled=generate_captions,
                progress_callback=update_progress,
            )

            progress.progress(
                1.0
            )

            status.success(
                "🎉 Your Short is ready!"
            )

            st.balloons()

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            st.markdown(
                """
                <div class="result-card">

                    <div class="result-title">
                        🎬 Your Short is ready
                    </div>

                    <div class="result-subtitle">
                        Your footage has been transformed
                        into vertical short-form content.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            st.video(
                str(result["file"])
            )

            download_col, empty_col = st.columns(
                [1, 2]
            )

            with download_col:

                with open(
                    result["file"],
                    "rb",
                ) as video_file:

                    st.download_button(
                        "⬇️ DOWNLOAD MY SHORT",
                        data=video_file,
                        file_name="clipflow_ai_short.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                    )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            st.markdown(
                "<br>",
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="section-kicker">
                    CREATION SUMMARY
                </div>

                <div class="section-title">
                    What ClipFlow created
                </div>
                """,
                unsafe_allow_html=True,
            )

            summary_cols = st.columns(4)

            summary = [
                (
                    "ORIGINAL",
                    f"{result['duration']:.1f}s",
                ),
                (
                    "CLIPS SELECTED",
                    str(
                        len(
                            result["selected"]
                        )
                    ),
                ),
                (
                    "OUTPUT",
                    "1080 × 1920",
                ),
                (
                    "CAPTIONS",
                    "ON"
                    if result["captions"]
                    else "OFF",
                ),
            ]

            for col, (label, value) in zip(
                summary_cols,
                summary,
            ):

                with col:

                    st.markdown(
                        f"""
                        <div class="metric-card">

                            <div class="metric-label">
                                {label}
                            </div>

                            <div class="metric-value">
                                {value}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # -------------------------------------------------
            # SMART MOMENTS
            # -------------------------------------------------

            st.markdown(
                "<br>",
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="section-kicker">
                    SMART MOMENTS
                </div>

                <div class="section-title">
                    Selected moments
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
                    <div class="moment-row">

                        <div class="moment-left">
                            🎬 Short {index}
                        </div>

                        <div class="moment-right">
                            {start:.1f}s → {end:.1f}s
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # -------------------------------------------------
            # DETAILS
            # -------------------------------------------------

            with st.expander(
                "⚙️ Processing details"
            ):

                st.write(
                    f"**Platform:** {platform}"
                )

                st.write(
                    f"**Music mood:** {music_mood}"
                )

                st.write(
                    f"**Background music:** "
                    f"{'Added' if result['music'] else 'Not added'}"
                )

                st.write(
                    f"**Long silence analysis:** "
                    f"{result['silence_count']} silence regions found"
                )

                st.write(
                    f"**Auto captions:** "
                    f"{'Created' if result['captions'] else 'Not created'}"
                )

                st.write(
                    "**Output format:** 1080 × 1920 vertical"
                )

        except Exception as error:

            st.error(
                "❌ ClipFlow could not finish processing "
                "this video."
            )

            with st.expander(
                "Show technical details"
            ):

                st.code(
                    str(error)
                )

                st.caption(
                    "If captions are enabled, the issue may "
                    "be related to Whisper or FFmpeg subtitle support."
                )

        finally:

            try:
                input_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

            if music_path:

                try:
                    music_path.unlink(
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

            <div class="empty-icon">🎬</div>

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
    <div class="footer">

        <strong>🎬 ClipFlow AI · Creative Video Studio</strong>
        <br>
        Turn footage into your next Short.

    </div>
    """,
    unsafe_allow_html=True,
)
