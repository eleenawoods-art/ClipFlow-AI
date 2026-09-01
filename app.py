import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st


# =========================================================
# CLIPFLOW AI — CREATIVE STUDIO
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
# CREATIVE STUDIO THEME
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(circle at 10% 5%, rgba(124,58,237,.10), transparent 28%),
            radial-gradient(circle at 90% 10%, rgba(59,130,246,.08), transparent 25%),
            #fafafa;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e9e9ef;
    }

    .hero {
        padding: 42px 44px;
        border-radius: 28px;
        margin-bottom: 28px;
        background:
            linear-gradient(135deg, #f5f0ff 0%, #eef5ff 100%);
        border: 1px solid #e7e0f7;
    }

    .hero h1 {
        font-size: 48px;
        line-height: 1.05;
        margin: 0;
        font-weight: 800;
        letter-spacing: -1.5px;
    }

    .hero p {
        color: #5f6270;
        font-size: 17px;
        margin-top: 14px;
        max-width: 700px;
    }

    .badge {
        display: inline-block;
        padding: 7px 13px;
        border-radius: 999px;
        background: #ffffff;
        border: 1px solid #e4ddf5;
        color: #6d28d9;
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 18px;
    }

    .feature-card {
        background: white;
        border: 1px solid #e9e9ef;
        border-radius: 18px;
        padding: 18px;
        min-height: 115px;
    }

    .feature-icon {
        font-size: 25px;
    }

    .feature-title {
        font-weight: 750;
        margin-top: 8px;
    }

    .feature-text {
        color: #737784;
        font-size: 13px;
        margin-top: 4px;
    }

    .upload-card {
        border: 2px dashed #d8d0eb;
        background: #ffffff;
        border-radius: 22px;
        padding: 25px;
        margin: 15px 0;
    }

    .section-title {
        font-size: 23px;
        font-weight: 800;
        margin-top: 30px;
        margin-bottom: 12px;
    }

    .result-card {
        background: white;
        border: 1px solid #e8e8ee;
        border-radius: 20px;
        padding: 20px;
    }

    .metric-card {
        background: white;
        border: 1px solid #e8e8ee;
        border-radius: 16px;
        padding: 16px;
        text-align: center;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 800;
    }

    .metric-label {
        color: #777985;
        font-size: 13px;
        margin-top: 4px;
    }

    div.stButton > button {
        border-radius: 14px;
        min-height: 48px;
        font-weight: 750;
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
        <div class="badge">✨ AI VIDEO EDITOR</div>
        <h1>Turn raw footage into<br>your next great Short.</h1>
        <p>
            ClipFlow AI finds engaging moments, creates smart vertical
            framing, adds captions and optional music — all in one workflow.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FEATURE CARDS
# =========================================================

f1, f2, f3, f4 = st.columns(4)

features = [
    ("🎯", "Smart Moments", "Finds active sections automatically."),
    ("📱", "Smart Framing", "Creates a clean 9:16 composition."),
    ("🎙️", "Auto Captions", "Generates subtitles from speech."),
    ("🎵", "Music Ready", "Mixes your licensed music safely."),
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
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# SIDEBAR SETTINGS
# =========================================================

with st.sidebar:

    st.markdown("## ⚙️ Edit Settings")

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
        "⏸️ Remove long silences",
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
# UPLOAD
# =========================================================

st.markdown(
    '<div class="section-title">📁 Upload your video</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="upload-card">
        <strong>Drop your footage into ClipFlow</strong><br>
        <span style="color:#777985;">
        MP4, MOV, M4V or AVI • Maximum 200MB
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

video_file = st.file_uploader(
    "Choose video",
    type=["mp4", "mov", "m4v", "avi"],
    label_visibility="collapsed",
)


# =========================================================
# MUSIC UPLOAD
# =========================================================

music_file = None

if add_music:

    music_file = st.file_uploader(
        "🎵 Upload licensed music",
        type=["mp3", "wav", "m4a"],
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

        error = result.stderr or "FFmpeg failed."

        if len(error) > 7000:
            error = error[-7000:]

        raise RuntimeError(error)

    return result


# =========================================================
# VIDEO INFO
# =========================================================

def get_video_info(path):

    cap = cv2.VideoCapture(str(path))

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
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

    return width, height, fps, duration


# =========================================================
# VIDEO ANALYSIS
# =========================================================

def analyze_video(path):

    cap = cv2.VideoCapture(str(path))

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
                (160, 90)
            )

            gray = cv2.cvtColor(
                small,
                cv2.COLOR_BGR2GRAY
            )

            if previous is not None:

                diff = cv2.absdiff(
                    gray,
                    previous
                )

                timestamps.append(
                    frame_number / fps
                )

                scores.append(
                    float(diff.mean())
                )

            previous = gray

        frame_number += 1

    cap.release()

    return duration, timestamps, scores


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

        segment = duration / count

        return [
            (
                i * segment,
                min(
                    duration,
                    (i + 1) * segment
                ),
            )
            for i in range(count)
        ]

    values = np.asarray(
        scores,
        dtype=float
    )

    if len(values) >= 5:

        kernel = np.ones(5) / 5

        values = np.convolve(
            values,
            kernel,
            mode="same"
        )

    threshold = np.percentile(
        values,
        60
    )

    windows = []

    for timestamp, score in zip(
        timestamps,
        values,
    ):

        if score >= threshold:

            start = max(
                0,
                timestamp - 2
            )

            end = min(
                duration,
                timestamp + 4
            )

            if not windows:

                windows.append(
                    [start, end]
                )

            elif start <= windows[-1][1] + 2:

                windows[-1][1] = max(
                    windows[-1][1],
                    end
                )

            else:

                windows.append(
                    [start, end]
                )

    if len(windows) < count:

        windows = []

        segment = duration / count

        for i in range(count):

            start = i * segment

            end = min(
                duration,
                start + segment
            )

            windows.append(
                [start, end]
            )

    ranked = sorted(
        windows,
        key=lambda x: x[1] - x[0],
        reverse=True,
    )

    selected = []

    per_clip = max(
        2,
        target / count
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
        zip(starts, ends)
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
        end - start
    )

    video_filter = get_vertical_filter(
        width,
        height
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

    if "[bg]" in video_filter:

        command += [
            "-filter_complex",
            video_filter,
            "-map",
            "[bg]",
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
            .replace("'", "'\\''")
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

        from faster_whisper import WhisperModel

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
# CREATE SRT
# =========================================================

def seconds_to_srt(seconds):

    seconds = max(
        0,
        float(seconds)
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
                clip_start
            )

            overlap_end = min(
                seg_end,
                clip_end
            )

            if overlap_end <= overlap_start:
                continue

            text = segment.text.strip()

            if not text:
                continue

            relative_start = (
                overlap_start - clip_start
            )

            relative_end = (
                overlap_end - clip_start
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

        lines.append(
            text
        )

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
        "/"
    )

    value = value.replace(
        ":",
        r"\:"
    )

    value = value.replace(
        "'",
        r"\'"
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

    analyzed_duration, timestamps, scores = (
        analyze_video(
            video_path
        )
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
        # SILENCE ANALYSIS
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
                work /
                f"clip_{i:02d}.mp4"
            )

            create_clip(
                video_path,
                start,
                end,
                clip,
                width,
                height,
            )

            clip_paths.append(
                clip
            )

        if progress_callback:
            progress_callback(50)

        # -------------------------------------------------
        # JOIN
        # -------------------------------------------------

        joined = (
            work /
            "joined.mp4"
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
                work /
                "music.mp4"
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
                work /
                "captions.srt"
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
                    work /
                    "captioned.mp4"
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
            OUTPUT_DIR /
            "clipflow_ai_result.mp4"
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
            "captions_created": captions_created,
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

    st.success(
        f"✅ {video_file.name}"
    )

    with st.expander(
        "🎥 Original video preview",
        expanded=True,
    ):

        st.video(
            video_file
        )

    if add_music and not music_file:

        st.warning(
            "🎵 Add a licensed music file to enable background music."
        )

    can_process = (
        not add_music
        or music_file is not None
    )

    st.markdown(
        '<div class="section-title">✨ Create your Short</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "✨ CREATE MY SHORT",
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
                "⬇️ DOWNLOAD MY SHORT",
                data=result["file"].read_bytes(),
                file_name="clipflow_ai_short.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

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
                    str(len(result["selected"])),
                    "Clips selected",
                ),
                (
                    c3,
                    "1080 × 1920",
                    "Output",
                ),
                (
                    c4,
                    (
                        "ON"
                        if result["captions_created"]
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

                st.write(
                    f"**Clip {i}** · "
                    f"{start:.1f}s → {end:.1f}s"
                )

            st.markdown(
                '<div class="section-title">✨ Processing details</div>',
                unsafe_allow_html=True,
            )

            details = []

            details.append(
                "🎯 Smart moment detection"
            )

            details.append(
                "📱 9:16 vertical framing"
            )

            if remove_silence:

                details.append(
                    "⏸️ Silence analysis"
                )

            if result["captions_created"]:

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

    st.info(
        "👆 Upload your video above to start editing."
    )
