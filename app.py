import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st

try:
    import imageio_ffmpeg
except Exception:
    imageio_ffmpeg = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ClipFlow AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 10% 5%,
            rgba(112, 72, 255, 0.16),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 15%,
            rgba(40, 120, 255, 0.12),
            transparent 25%
        ),
        linear-gradient(
            135deg,
            #06070c 0%,
            #0a0d15 48%,
            #080a10 100%
        );
    color: #ffffff;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}


/* ================= SIDEBAR ================= */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #080a11 0%,
            #0c101a 100%
        );
    border-right: 1px solid rgba(255,255,255,0.07);
}

section[data-testid="stSidebar"] * {
    color: #f4f5f8;
}

.sidebar-brand {
    padding-bottom: 18px;
}

.sidebar-brand-title {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.7px;
}

.sidebar-brand-subtitle {
    color: #8993a8;
    font-size: 12px;
    margin-top: 4px;
}


/* ================= HERO ================= */

.hero-box {
    background:
        radial-gradient(
            circle at 82% 20%,
            rgba(118, 74, 255, 0.22),
            transparent 32%
        ),
        radial-gradient(
            circle at 18% 80%,
            rgba(0, 164, 255, 0.10),
            transparent 32%
        ),
        linear-gradient(
            135deg,
            rgba(19,23,36,0.98),
            rgba(9,11,19,0.98)
        );
    border: 1px solid rgba(143,109,255,0.22);
    border-radius: 26px;
    padding: 38px;
    margin-bottom: 25px;
    box-shadow: 0 20px 70px rgba(0,0,0,0.32);
}

.hero-title {
    font-size: 43px;
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -1.8px;
    margin-bottom: 13px;
}

.hero-gradient {
    background: linear-gradient(
        90deg,
        #a98cff,
        #62b9ff
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-description {
    color: #aeb6c8;
    font-size: 16px;
    line-height: 1.7;
    max-width: 720px;
}


/* ================= NATIVE STREAMLIT ELEMENTS ================= */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15,18,28,0.72);
    border-color: rgba(255,255,255,0.07) !important;
    border-radius: 18px !important;
}

div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.025);
    border: 1px dashed rgba(140,120,255,0.38);
    border-radius: 18px;
    padding: 8px;
}

div.stButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(
        135deg,
        #714cff,
        #4b79ff
    );
    color: white;
}

div.stButton > button:hover {
    border-color: rgba(255,255,255,0.28);
}

.stDownloadButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    font-weight: 700;
}

div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.045);
    border-radius: 10px;
}

.stSlider {
    padding-top: 4px;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 12px;
}


/* ================= FEATURE CARDS ================= */

.feature-title {
    font-weight: 700;
    font-size: 18px;
}

.feature-text {
    color: #929bad;
    font-size: 14px;
    line-height: 1.6;
}

.feature-icon {
    font-size: 27px;
}


/* ================= INFO ================= */

.small-note {
    color: #7f899d;
    font-size: 12px;
    line-height: 1.55;
}


/* ================= MOBILE ================= */

@media (max-width: 768px) {

    .hero-box {
        padding: 26px 22px;
    }

    .hero-title {
        font-size: 32px;
    }

    .hero-description {
        font-size: 14px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# FFMPEG
# ============================================================

def get_ffmpeg():
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    return "ffmpeg"


FFMPEG = get_ffmpeg()


def run_ffmpeg(args, timeout=900):
    command = [FFMPEG, "-y"] + [str(item) for item in args]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )

    if process.returncode != 0:
        error_text = (
            process.stderr[-5000:]
            if process.stderr
            else "Unknown FFmpeg error."
        )
        raise RuntimeError(error_text)

    return process


# ============================================================
# MEDIA HELPERS
# ============================================================

def get_media_duration(video_path):
    command = [
        FFMPEG,
        "-i",
        str(video_path),
    ]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    match = re.search(
        r"Duration:\s*(\d+):(\d+):([\d.]+)",
        process.stderr,
    )

    if not match:
        return 0.0

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


def has_audio(video_path):
    command = [
        FFMPEG,
        "-v",
        "error",
        "-i",
        str(video_path),
        "-map",
        "0:a:0",
        "-f",
        "null",
        "-",
    ]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return process.returncode == 0


# ============================================================
# VIDEO
# ============================================================

def get_vertical_filter():
    return (
        "scale=1080:1920:"
        "force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
        "setsar=1"
    )


def create_vertical_clip(
    input_path,
    output_path,
    start_time,
    duration,
):
    args = [
        "-ss",
        str(max(0, start_time)),
        "-i",
        str(input_path),
        "-t",
        str(max(1, duration)),
        "-vf",
        get_vertical_filter(),
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
        "160k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    run_ffmpeg(args)


# ============================================================
# SMART MOMENT DETECTION
# ============================================================

def detect_moments(
    video_path,
    number_of_clips,
    target_clip_length,
):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open the uploaded video."
        )

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        fps = 25.0

    total_duration = (
        frame_count / fps
        if frame_count > 0
        else 0
    )

    if total_duration <= 0:
        cap.release()
        raise RuntimeError(
            "Could not determine video duration."
        )

    sample_interval = max(
        1,
        int(fps * 2),
    )

    scores = []
    previous_frame = None
    frame_index = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_index % sample_interval == 0:

            small = cv2.resize(
                frame,
                (160, 90),
            )

            gray = cv2.cvtColor(
                small,
                cv2.COLOR_BGR2GRAY,
            )

            if previous_frame is not None:

                difference = cv2.absdiff(
                    gray,
                    previous_frame,
                )

                score = float(
                    np.mean(difference)
                )

                scores.append(
                    (
                        frame_index / fps,
                        score,
                    )
                )

            previous_frame = gray

        frame_index += 1

    cap.release()

    max_start = max(
        0,
        total_duration - target_clip_length,
    )

    if not scores:

        starts = np.linspace(
            0,
            max_start,
            number_of_clips,
        )

        return [
            (
                float(start),
                min(
                    target_clip_length,
                    max(
                        1,
                        total_duration - start,
                    ),
                ),
            )
            for start in starts
        ]

    scores_sorted = sorted(
        scores,
        key=lambda x: x[1],
        reverse=True,
    )

    selected = []

    min_gap = max(
        4.0,
        target_clip_length * 0.65,
    )

    for timestamp, _score in scores_sorted:

        timestamp = min(
            max(0, timestamp),
            max_start,
        )

        if all(
            abs(timestamp - existing) >= min_gap
            for existing in selected
        ):
            selected.append(timestamp)

        if len(selected) >= number_of_clips:
            break

    if len(selected) < number_of_clips:

        fallback_starts = np.linspace(
            0,
            max_start,
            number_of_clips,
        )

        for start in fallback_starts:

            start = float(start)

            if all(
                abs(start - existing) >= min_gap
                for existing in selected
            ):
                selected.append(start)

            if len(selected) >= number_of_clips:
                break

    selected = sorted(
        selected[:number_of_clips]
    )

    clips = []

    for start in selected:

        duration = min(
            target_clip_length,
            max(
                1,
                total_duration - start,
            ),
        )

        clips.append(
            (
                float(start),
                float(duration),
            )
        )

    return clips


# ============================================================
# SILENCE
# ============================================================

def detect_silence(video_path):
    command = [
        FFMPEG,
        "-i",
        str(video_path),
        "-af",
        "silencedetect=noise=-35dB:d=0.8",
        "-f",
        "null",
        "-",
    ]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    output = process.stderr

    starts = re.findall(
        r"silence_start:\s*([\d.]+)",
        output,
    )

    ends = re.findall(
        r"silence_end:\s*([\d.]+)",
        output,
    )

    silence_sections = []

    for index, start in enumerate(starts):

        start_value = float(start)

        if index < len(ends):
            end_value = float(ends[index])
        else:
            end_value = start_value

        silence_sections.append(
            (
                start_value,
                end_value,
                max(
                    0,
                    end_value - start_value,
                ),
            )
        )

    return silence_sections


# ============================================================
# JOIN CLIPS
# ============================================================

def join_clips(
    clip_paths,
    output_path,
):
    if not clip_paths:
        raise RuntimeError(
            "No clips were created."
        )

    if len(clip_paths) == 1:
        shutil.copy2(
            clip_paths[0],
            output_path,
        )
        return

    concat_file = (
        output_path.parent / "concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as file:

        for clip in clip_paths:

            safe_path = (
                str(
                    Path(clip).resolve()
                )
                .replace("\\", "/")
                .replace(
                    "'",
                    "'\\''",
                )
            )

            file.write(
                f"file '{safe_path}'\n"
            )

    args = [
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
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
        "160k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    try:
        run_ffmpeg(args)

    finally:
        try:
            concat_file.unlink()
        except Exception:
            pass


# ============================================================
# MUSIC
# ============================================================

def mix_music(
    video_path,
    music_path,
    output_path,
):
    video_has_audio = has_audio(video_path)

    if video_has_audio:

        filter_complex = (
            "[0:a]volume=0.85[a0];"
            "[1:a]volume=0.18,"
            "aloop=loop=-1:size=2e+09,"
            "atrim=0:999999[a1];"
            "[a0][a1]amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2[aout]"
        )

        args = [
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",
            "-i",
            str(music_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
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
            str(output_path),
        ]

    else:

        filter_complex = (
            "[1:a]volume=0.20,"
            "aloop=loop=-1:size=2e+09,"
            "atrim=0:999999[aout]"
        )

        args = [
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",
            "-i",
            str(music_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
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
            str(output_path),
        ]

    run_ffmpeg(args)


# ============================================================
# CAPTIONS
# ============================================================

def create_srt(
    video_path,
    subtitle_path,
):
    from faster_whisper import WhisperModel

    model = WhisperModel(
        "tiny",
        device="cpu",
        compute_type="int8",
    )

    segments, _info = model.transcribe(
        str(video_path),
        beam_size=1,
        vad_filter=True,
    )

    segments = list(segments)

    if not segments:
        return False

    def format_time(seconds):

        milliseconds = int(
            round(
                (
                    seconds
                    - int(seconds)
                )
                * 1000
            )
        )

        if milliseconds >= 1000:
            milliseconds = 0
            seconds += 1

        total_seconds = int(seconds)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{milliseconds:03d}"
        )

    with open(
        subtitle_path,
        "w",
        encoding="utf-8",
    ) as file:

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            start = format_time(
                float(segment.start)
            )

            end = format_time(
                float(segment.end)
            )

            text = (
                segment.text
                .strip()
                .replace(
                    "-->",
                    "→",
                )
            )

            file.write(
                f"{index}\n"
                f"{start} --> {end}\n"
                f"{text}\n\n"
            )

    return True


def burn_captions(
    video_path,
    subtitle_path,
    output_path,
):
    subtitle_file = (
        str(
            Path(
                subtitle_path
            ).resolve()
        )
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace(
            "'",
            "\\'",
        )
    )

    subtitle_filter = (
        f"subtitles='{subtitle_file}':"
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

    audio_exists = has_audio(
        video_path
    )

    args = [
        "-i",
        str(video_path),
        "-vf",
        subtitle_filter,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
    ]

    if audio_exists:

        args += [
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ]

    else:

        args += [
            "-an",
        ]

    args += [
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    run_ffmpeg(args)


# ============================================================
# PROCESS VIDEO
# ============================================================

def process_video(
    input_path,
    target_length,
    number_of_clips,
    add_music=False,
    music_path=None,
    add_captions=False,
    analyze_silence=False,
):
    work_dir = Path(
        tempfile.mkdtemp(
            prefix="clipflow_"
        )
    )

    try:

        progress = st.progress(0)
        status = st.empty()

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        status.info(
            "🔎 Reading video..."
        )

        progress.progress(5)

        total_duration = get_media_duration(
            input_path
        )

        if total_duration <= 0:
            raise RuntimeError(
                "Unable to read video duration."
            )

        # ----------------------------------------------------
        # Silence
        # ----------------------------------------------------

        silence_sections = []

        if analyze_silence:

            status.info(
                "🔇 Analyzing silence..."
            )

            try:
                silence_sections = detect_silence(
                    input_path
                )
            except Exception:
                silence_sections = []

        progress.progress(15)

        # ----------------------------------------------------
        # Smart moments
        # ----------------------------------------------------

        status.info(
            "🧠 Finding the best moments..."
        )

        clip_specs = detect_moments(
            input_path,
            number_of_clips,
            target_length,
        )

        progress.progress(30)

        # ----------------------------------------------------
        # Create clips
        # ----------------------------------------------------

        clip_paths = []

        for index, (
            start,
            duration,
        ) in enumerate(
            clip_specs,
            start=1,
        ):

            status.info(
                f"🎬 Creating clip "
                f"{index}/{len(clip_specs)}..."
            )

            clip_path = (
                work_dir
                / f"clip_{index}.mp4"
            )

            create_vertical_clip(
                input_path,
                clip_path,
                start,
                duration,
            )

            clip_paths.append(
                clip_path
            )

            percentage = (
                30
                + int(
                    (
                        index
                        / max(
                            1,
                            len(clip_specs),
                        )
                    )
                    * 40
                )
            )

            progress.progress(
                min(
                    70,
                    percentage,
                )
            )

        # ----------------------------------------------------
        # Join
        # ----------------------------------------------------

        status.info(
            "✨ Combining clips..."
        )

        joined_path = (
            work_dir / "joined.mp4"
        )

        join_clips(
            clip_paths,
            joined_path,
        )

        progress.progress(78)

        # ----------------------------------------------------
        # Music
        # ----------------------------------------------------

        current_video = joined_path

        if add_music and music_path:

            status.info(
                "🎵 Adding your music..."
            )

            music_output = (
                work_dir / "music_mix.mp4"
            )

            mix_music(
                current_video,
                music_path,
                music_output,
            )

            current_video = music_output

        progress.progress(86)

        # ----------------------------------------------------
        # Captions
        # ----------------------------------------------------

        captions_created = False

        if add_captions:

            status.info(
                "💬 Generating captions..."
            )

            subtitle_path = (
                work_dir / "captions.srt"
            )

            caption_video = (
                work_dir / "captioned.mp4"
            )

            try:

                captions_created = create_srt(
                    current_video,
                    subtitle_path,
                )

                if captions_created:

                    burn_captions(
                        current_video,
                        subtitle_path,
                        caption_video,
                    )

                    current_video = caption_video

            except Exception:
                captions_created = False

        progress.progress(96)

        # ----------------------------------------------------
        # Final output
        # ----------------------------------------------------

        final_output = (
            OUTPUT_DIR
            / "clipflow_ai_result.mp4"
        )

        shutil.copy2(
            current_video,
            final_output,
        )

        progress.progress(100)

        status.success(
            "✅ Your ClipFlow AI video is ready!"
        )

        return {
            "path": str(final_output),
            "duration": total_duration,
            "clips": len(clip_paths),
            "silence_sections": silence_sections,
            "captions": captions_created,
        }

    finally:

        shutil.rmtree(
            work_dir,
            ignore_errors=True,
        )


# ============================================================
# SESSION STATE
# ============================================================

if "clipflow_result" not in st.session_state:
    st.session_state.clipflow_result = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">
                🎬 ClipFlow <span style="color:#8d6cff;">AI</span>
            </div>
            <div class="sidebar-brand-subtitle">
                Creative Video Studio
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⚙️ Project Settings")

    platform = st.selectbox(
        "Platform",
        [
            "YouTube Shorts",
            "Instagram Reels",
            "TikTok",
        ],
    )

    target_length = st.slider(
        "Target clip length",
        min_value=10,
        max_value=90,
        value=30,
        step=5,
    )

    number_of_clips = st.slider(
        "Number of clips",
        min_value=2,
        max_value=8,
        value=5,
        step=1,
    )

    st.markdown("---")

    music_mood = st.selectbox(
        "🎵 Music mood",
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
        "Add my own licensed music",
        value=False,
    )

    music_file = None

    if add_music:

        music_file = st.file_uploader(
            "Upload music",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
            ],
        )

    analyze_silence = st.checkbox(
        "🔇 Analyze long silence",
        value=False,
    )

    add_captions = st.checkbox(
        "💬 Auto captions",
        value=False,
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="small-note">
            Your uploaded media is processed for the current
            session. Use only content and music you have rights
            to use.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">
            Turn long videos into
            <span class="hero-gradient">
                short-form content.
            </span>
        </div>

        <div class="hero-description">
            ClipFlow AI finds engaging moments, creates
            vertical 9:16 clips, optionally adds your own
            licensed music, and generates captions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURE SECTION
# ============================================================

st.markdown("### ✨ Built for Short-Form Creators")

feature1, feature2, feature3 = st.columns(3)

with feature1:

    with st.container(border=True):

        st.markdown("### 🧠 Smart Detection")

        st.markdown(
            """
            <div class="feature-text">
                Detect visually active moments and turn them
                into short clips automatically.
            </div>
            """,
            unsafe_allow_html=True,
        )

with feature2:

    with st.container(border=True):

        st.markdown("### 📱 Vertical Ready")

        st.markdown(
            """
            <div class="feature-text">
                Format your content for YouTube Shorts,
                Instagram Reels and TikTok.
            </div>
            """,
            unsafe_allow_html=True,
        )

with feature3:

    with st.container(border=True):

        st.markdown("### 💬 Auto Captions")

        st.markdown(
            """
            <div class="feature-text">
                Generate readable captions locally using
                faster-whisper.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# UPLOAD
# ============================================================

st.markdown("## 🎥 Upload your video")

uploaded_video = st.file_uploader(
    "Drop your video here",
    type=[
        "mp4",
        "mov",
        "m4v",
        "avi",
    ],
    help="Maximum file size: 200 MB",
)


# ============================================================
# MAIN
# ============================================================

if uploaded_video:

    file_size_mb = (
        uploaded_video.size
        / (1024 * 1024)
    )

    if file_size_mb > 200:

        st.error(
            "❌ Video is larger than 200 MB. "
            "Please upload a smaller file."
        )

    else:

        temp_input = None
        temp_music = None

        try:

            # ------------------------------------------------
            # Save video safely
            # ------------------------------------------------

            suffix = (
                Path(
                    uploaded_video.name
                ).suffix
                or ".mp4"
            )

            input_temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
            )

            temp_input = Path(
                input_temp.name
            )

            input_temp.close()

            with open(
                temp_input,
                "wb",
            ) as file:

                file.write(
                    uploaded_video.getbuffer()
                )

            # ------------------------------------------------
            # Preview
            # ------------------------------------------------

            st.markdown("### 👀 Source Preview")

            st.video(
                uploaded_video
            )

            # ------------------------------------------------
            # Music
            # ------------------------------------------------

            if (
                add_music
                and music_file is not None
            ):

                music_suffix = (
                    Path(
                        music_file.name
                    ).suffix
                    or ".mp3"
                )

                music_temp = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=music_suffix,
                )

                temp_music = Path(
                    music_temp.name
                )

                music_temp.close()

                with open(
                    temp_music,
                    "wb",
                ) as file:

                    file.write(
                        music_file.getbuffer()
                    )

            # ------------------------------------------------
            # Settings
            # ------------------------------------------------

            st.markdown("### 🎛️ Your Settings")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Platform",
                    platform,
                )

            with c2:
                st.metric(
                    "Clip Length",
                    f"{target_length}s",
                )

            with c3:
                st.metric(
                    "Clips",
                    number_of_clips,
                )

            with c4:
                st.metric(
                    "Music",
                    "On"
                    if (
                        add_music
                        and music_file is not None
                    )
                    else "Off",
                )

            if add_music:
                st.caption(
                    f"Music mood: {music_mood}"
                )

            # ------------------------------------------------
            # Process button
            # ------------------------------------------------

            st.markdown("")

            if st.button(
                "🚀 Create My Clips",
                type="primary",
                use_container_width=True,
            ):

                with st.spinner(
                    "ClipFlow AI is processing your video..."
                ):

                    result = process_video(
                        input_path=temp_input,
                        target_length=target_length,
                        number_of_clips=number_of_clips,
                        add_music=(
                            add_music
                            and music_file is not None
                        ),
                        music_path=temp_music,
                        add_captions=add_captions,
                        analyze_silence=analyze_silence,
                    )

                    st.session_state.clipflow_result = result

                st.rerun()

        except Exception as error:

            st.error(
                "❌ Processing failed."
            )

            with st.expander(
                "Technical details"
            ):
                st.code(
                    str(error)
                )

        finally:

            if temp_input:

                try:
                    temp_input.unlink()
                except Exception:
                    pass

            if temp_music:

                try:
                    temp_music.unlink()
                except Exception:
                    pass


# ============================================================
# RESULT
# ============================================================

result = st.session_state.get(
    "clipflow_result"
)

if result:

    st.markdown("---")

    st.success(
        "🎉 Your ClipFlow AI video is ready!"
    )

    result_path = Path(
        result["path"]
    )

    if result_path.exists():

        st.markdown("### 🎬 Final Video")

        st.video(
            str(result_path)
        )

        st.markdown("### 📊 Result Details")

        r1, r2, r3 = st.columns(3)

        with r1:
            st.metric(
                "Source Duration",
                f"{result['duration']:.1f}s",
            )

        with r2:
            st.metric(
                "Clips Created",
                result["clips"],
            )

        with r3:
            st.metric(
                "Captions",
                "Yes"
                if result["captions"]
                else "No",
            )

        st.markdown("")

        with open(
            result_path,
            "rb",
        ) as file:

            st.download_button(
                label="⬇️ Download Final Video",
                data=file.read(),
                file_name="clipflow_ai_result.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

        if analyze_silence:

            silence_count = len(
                result.get(
                    "silence_sections",
                    [],
                )
            )

            st.info(
                f"🔇 Silence analysis detected "
                f"{silence_count} silence section(s)."
            )

    else:

        st.warning(
            "The result file is no longer available. "
            "Please process the video again."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🎬 ClipFlow AI · Creative Video Studio · "
    "Built for short-form creators."
)
