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
        radial-gradient(circle at 15% 10%, rgba(91, 55, 160, 0.20), transparent 28%),
        radial-gradient(circle at 85% 20%, rgba(38, 94, 180, 0.16), transparent 25%),
        linear-gradient(135deg, #070910 0%, #0b0e18 45%, #090b12 100%);
    color: #ffffff;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #090b13 0%, #0c101b 100%);
    border-right: 1px solid rgba(255,255,255,0.07);
}

section[data-testid="stSidebar"] * {
    color: #f4f5f7;
}

.hero {
    padding: 42px 36px;
    border-radius: 28px;
    margin-bottom: 26px;
    background:
        radial-gradient(circle at 80% 20%, rgba(115, 76, 255, 0.25), transparent 30%),
        radial-gradient(circle at 20% 80%, rgba(0, 170, 255, 0.13), transparent 30%),
        linear-gradient(135deg, rgba(20,24,38,0.98), rgba(10,12,21,0.98));
    border: 1px solid rgba(143, 109, 255, 0.22);
    box-shadow: 0 20px 70px rgba(0,0,0,0.35);
}

.hero-title {
    font-size: 44px;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -1.8px;
    margin: 0;
}

.hero-title span {
    background: linear-gradient(90deg, #a98cff, #62b9ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #aeb6c8;
    font-size: 17px;
    line-height: 1.7;
    margin-top: 14px;
    max-width: 720px;
}

.badges {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    margin-top: 22px;
}

.badge {
    display: inline-block;
    padding: 8px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.09);
    color: #dfe4ef;
    font-size: 12px;
    font-weight: 600;
}

.card {
    background: rgba(16, 19, 29, 0.78);
    border: 1px solid rgba(255,255,255,0.075);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.20);
}

.card h3 {
    margin-top: 0;
    margin-bottom: 8px;
}

.muted {
    color: #929bad;
}

.feature {
    min-height: 135px;
}

.feature-icon {
    font-size: 28px;
    margin-bottom: 10px;
}

.status-card {
    padding: 18px;
    border-radius: 16px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    margin: 8px 0;
}

.success-box {
    padding: 18px;
    border-radius: 16px;
    background: rgba(38, 190, 125, 0.08);
    border: 1px solid rgba(38, 190, 125, 0.25);
}

.warning-box {
    padding: 18px;
    border-radius: 16px;
    background: rgba(245, 180, 60, 0.08);
    border: 1px solid rgba(245, 180, 60, 0.22);
}

div.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 46px;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(135deg, #714cff, #4b79ff);
    color: white;
}

div.stButton > button:hover {
    border-color: rgba(255,255,255,0.25);
    transform: translateY(-1px);
}

.stDownloadButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 46px;
    font-weight: 700;
}

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.025);
    border: 1px dashed rgba(150,130,255,0.35);
    border-radius: 18px;
    padding: 8px;
}

div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
}

.stSlider {
    padding-top: 4px;
}

.small-note {
    color: #7f899d;
    font-size: 12px;
    line-height: 1.5;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# FFmpeg
# ============================================================

def get_ffmpeg():
    """
    Returns an FFmpeg executable.
    Uses imageio-ffmpeg when available.
    Falls back to system ffmpeg.
    """
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    return "ffmpeg"


FFMPEG = get_ffmpeg()


def run_ffmpeg(args, timeout=900):
    """
    Execute FFmpeg safely.
    """
    command = [FFMPEG, "-y"] + [str(x) for x in args]

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )

    if process.returncode != 0:
        error_text = process.stderr[-5000:] if process.stderr else "Unknown FFmpeg error."
        raise RuntimeError(error_text)

    return process


# ============================================================
# MEDIA HELPERS
# ============================================================

def get_media_duration(video_path):
    """
    Get media duration using FFmpeg output.
    """
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

    return hours * 3600 + minutes * 60 + seconds


def has_audio(video_path):
    """
    Robust audio detection.
    """
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
# VIDEO FILTERS
# ============================================================

def get_vertical_filter():
    """
    Convert video to 9:16 vertical format.
    Output: 1080x1920.
    """
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
    """
    Create one vertical clip.
    """
    video_filter = get_vertical_filter()

    args = [
        "-ss",
        str(max(0, start_time)),
        "-i",
        str(input_path),
        "-t",
        str(max(1, duration)),
        "-vf",
        video_filter,
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

def detect_moments(video_path, number_of_clips, target_clip_length):
    """
    Simple computer-vision based moment detection.

    Uses frame-to-frame visual differences to identify
    active sections of a video.
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError("Could not open the uploaded video.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        fps = 25.0

    total_duration = frame_count / fps if frame_count > 0 else 0

    if total_duration <= 0:
        cap.release()
        raise RuntimeError("Could not determine video duration.")

    sample_interval = max(1, int(fps * 2))

    scores = []
    previous_frame = None
    frame_index = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_index % sample_interval == 0:
            small = cv2.resize(frame, (160, 90))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            if previous_frame is not None:
                difference = cv2.absdiff(gray, previous_frame)
                score = float(np.mean(difference))
                scores.append(
                    (
                        frame_index / fps,
                        score,
                    )
                )

            previous_frame = gray

        frame_index += 1

    cap.release()

    if not scores:
        starts = np.linspace(
            0,
            max(0, total_duration - target_clip_length),
            number_of_clips,
        )

        return [
            (
                float(start),
                min(target_clip_length, total_duration - start),
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
        if timestamp + target_clip_length > total_duration:
            timestamp = max(
                0,
                total_duration - target_clip_length,
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
            max(0, total_duration - target_clip_length),
            number_of_clips,
        )

        for start in fallback_starts:
            if all(
                abs(float(start) - existing) >= min_gap
                for existing in selected
            ):
                selected.append(float(start))

            if len(selected) >= number_of_clips:
                break

    selected = sorted(selected[:number_of_clips])

    clips = []

    for start in selected:
        duration = min(
            target_clip_length,
            max(1, total_duration - start),
        )

        clips.append(
            (
                float(start),
                float(duration),
            )
        )

    return clips


# ============================================================
# SILENCE DETECTION
# ============================================================

def detect_silence(video_path):
    """
    Detect long silence sections.
    """
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
                max(0, end_value - start_value),
            )
        )

    return silence_sections


# ============================================================
# JOIN CLIPS
# ============================================================

def join_clips(clip_paths, output_path):
    """
    Join multiple MP4 clips.
    """
    if not clip_paths:
        raise RuntimeError("No clips were created.")

    if len(clip_paths) == 1:
        shutil.copy2(
            clip_paths[0],
            output_path,
        )
        return

    concat_file = output_path.parent / "concat.txt"

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as file:
        for clip in clip_paths:
            safe_path = (
                str(Path(clip).resolve())
                .replace("\\", "/")
                .replace("'", "'\\''")
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
# MUSIC MIXING
# ============================================================

def mix_music(
    video_path,
    music_path,
    output_path,
):
    """
    Mix uploaded licensed/user-owned music with video audio.
    """
    video_has_audio = has_audio(video_path)

    if video_has_audio:
        filter_complex = (
            "[0:a]volume=0.85[a0];"
            "[1:a]volume=0.18,"
            "aloop=loop=-1:size=2e+09,"
            "atrim=0:"
            "999999[a1];"
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
            "atrim=0:"
            "999999[aout]"
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

def create_srt(video_path, subtitle_path):
    """
    Generate captions using faster-whisper.
    """
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
            round((seconds - int(seconds)) * 1000)
        )

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
                .replace("-->", "→")
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
    """
    Burn SRT captions into the video.
    """
    subtitle_file = (
        str(Path(subtitle_path).resolve())
        .replace("\\", "/")
        .replace(":", "\\:")
        .replace("'", "\\'")
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

    audio_exists = has_audio(video_path)

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
    """
    Main ClipFlow AI processing pipeline.
    """
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

        status.info("🔎 Reading video...")
        progress.progress(5)

        total_duration = get_media_duration(
            input_path
        )

        if total_duration <= 0:
            raise RuntimeError(
                "Unable to read video duration."
            )

        # ----------------------------------------------------
        # Silence analysis
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
        # Detect moments
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

        for index, (start, duration) in enumerate(
            clip_specs,
            start=1,
        ):
            status.info(
                f"🎬 Creating clip {index}/{len(clip_specs)}..."
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

            clip_paths.append(clip_path)

            percentage = 30 + int(
                (index / max(1, len(clip_specs))) * 40
            )

            progress.progress(
                min(70, percentage)
            )

        # ----------------------------------------------------
        # Join
        # ----------------------------------------------------

        status.info(
            "✨ Combining clips..."
        )

        joined_path = (
            work_dir
            / "joined.mp4"
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
                work_dir
                / "music_mix.mp4"
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
                work_dir
                / "captions.srt"
            )

            caption_video = (
                work_dir
                / "captioned.mp4"
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
        # Save final result
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
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            padding: 12px 4px 24px 4px;
        ">
            <div style="
                font-size: 25px;
                font-weight: 800;
            ">
                🎬 ClipFlow <span style="color:#8d6cff;">AI</span>
            </div>

            <div style="
                color:#8993a8;
                font-size:12px;
                margin-top:5px;
            ">
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
        "🎵 Add my own licensed music",
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
    <div class="hero">
        <div class="hero-title">
            Turn long videos into
            <span>short-form content.</span>
        </div>

        <div class="hero-subtitle">
            ClipFlow AI finds engaging moments, creates
            vertical 9:16 clips, optionally adds your own
            licensed music, and generates captions.
        </div>

        <div class="badges">
            <div class="badge">⚡ Smart Moments</div>
            <div class="badge">📱 9:16 Vertical</div>
            <div class="badge">💬 Auto Captions</div>
            <div class="badge">🎵 Custom Music</div>
            <div class="badge">🔒 Your Content</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURES
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="card feature">
            <div class="feature-icon">🧠</div>
            <h3>Smart Detection</h3>
            <div class="muted">
                Detect visually active moments and turn them
                into short clips.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="card feature">
            <div class="feature-icon">📱</div>
            <h3>Vertical Ready</h3>
            <div class="muted">
                Automatically format your content for Shorts,
                Reels and TikTok.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="card feature">
            <div class="feature-icon">💬</div>
            <h3>Auto Captions</h3>
            <div class="muted">
                Generate readable captions locally with
                faster-whisper.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UPLOAD SECTION
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
# SESSION STATE
# ============================================================

if "clipflow_result" not in st.session_state:
    st.session_state.clipflow_result = None


# ============================================================
# MAIN PROCESSING
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
            # Save uploaded video
            # ------------------------------------------------

            temp_input = Path(
                tempfile.mktemp(
                    suffix=Path(
                        uploaded_video.name
                    ).suffix
                    or ".mp4"
                )
            )

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

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                "### 👀 Source Preview"
            )

            st.video(
                uploaded_video
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

            # ------------------------------------------------
            # Upload music
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

                temp_music = Path(
                    tempfile.mktemp(
                        suffix=music_suffix
                    )
                )

                with open(
                    temp_music,
                    "wb",
                ) as file:
                    file.write(
                        music_file.getbuffer()
                    )

            # ------------------------------------------------
            # Configuration summary
            # ------------------------------------------------

            st.markdown(
                "### 🎛️ Your Settings"
            )

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
                    "On" if (
                        add_music
                        and music_file
                    ) else "Off",
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

    st.markdown(
        """
        <div class="success-box">
            <h2 style="margin-top:0;">
                🎉 Your video is ready!
            </h2>
            <div style="color:#a9b4c7;">
                ClipFlow AI successfully created your
                short-form video.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    result_path = Path(
        result["path"]
    )

    if result_path.exists():

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
                "Yes" if result["captions"] else "No",
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

            st.markdown(
                f"""
                <div class="status-card">
                    🔇 Silence analysis detected
                    <strong>{silence_count}</strong>
                    silence section(s).
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.warning(
            "The result file is no longer available. "
            "Please process the video again."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#687286;
        font-size:12px;
        padding-top:40px;
        padding-bottom:10px;
    ">
        ClipFlow AI · Creative Video Studio
        <br>
        Built for short-form creators.
    </div>
    """,
    unsafe_allow_html=True,
)
