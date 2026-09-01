import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st


# =========================================================
# CLIPFLOW AI
# =========================================================

st.set_page_config(
    page_title="ClipFlow AI",
    page_icon="🎬",
    layout="wide",
)


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================================
# PAGE STYLE
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.4rem;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 18px;
        margin-bottom: 1.2rem;
    }

    .status-box {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.title("🎬 ClipFlow AI")

st.write(
    "Upload a video and ClipFlow AI automatically "
    "creates a polished short vertical edit."
)


st.markdown(
    """
    <div class="hero">
        <h3>Upload → Analyze → Smart Frame → Edit → Export</h3>
        <p>
        ClipFlow analyzes your footage, selects active sections,
        converts them to vertical format without unnecessarily
        cutting important content, and creates a ready-to-post video.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Edit Settings")

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
    )

    number_of_clips = st.slider(
        "Number of clips",
        min_value=2,
        max_value=8,
        value=5,
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
        "Add background music",
        value=False,
    )

    st.divider()

    st.caption(
        "🎵 Use only music you have permission to use."
    )


# =========================================================
# VIDEO UPLOAD
# =========================================================

video_file = st.file_uploader(
    "📁 Upload your video",
    type=[
        "mp4",
        "mov",
        "m4v",
        "avi",
    ],
    help="Maximum upload size depends on your Streamlit configuration.",
)


# =========================================================
# MUSIC UPLOAD
# =========================================================

music_file = None

if add_music:

    music_file = st.file_uploader(
        "🎵 Upload royalty-safe music",
        type=[
            "mp3",
            "wav",
            "m4a",
        ],
        help=(
            "Upload music that you are legally allowed to use."
        ),
    )


# =========================================================
# FFMPEG
# =========================================================

def get_ffmpeg():

    try:

        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()

    except Exception:

        system_ffmpeg = shutil.which("ffmpeg")

        if system_ffmpeg:
            return system_ffmpeg

        return "ffmpeg"


def run_ffmpeg(arguments):

    ffmpeg = get_ffmpeg()

    result = subprocess.run(
        [ffmpeg] + arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        error_text = result.stderr

        if len(error_text) > 4000:
            error_text = error_text[-4000:]

        raise RuntimeError(error_text)

    return result


# =========================================================
# VIDEO INFORMATION
# =========================================================

def get_video_info(video_path):

    cap = cv2.VideoCapture(
        str(video_path)
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

    frame_count = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    cap.release()

    if not fps or fps <= 0:
        fps = 25

    duration = 0

    if frame_count and frame_count > 0:
        duration = frame_count / fps

    return width, height, fps, duration


# =========================================================
# VIDEO ANALYSIS
# =========================================================

def analyze_video(video_path):

    cap = cv2.VideoCapture(
        str(video_path)
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if not fps or fps <= 0:
        fps = 25

    frame_count = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = 0

    if frame_count:
        duration = frame_count / fps

    previous_frame = None

    timestamps = []
    scores = []

    frame_number = 0

    sample_every = max(
        1,
        int(fps * 0.5),
    )

    while True:

        success, frame = cap.read()

        if not success:
            break

        if frame_number % sample_every == 0:

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
                    difference.mean()
                )

                timestamps.append(
                    frame_number / fps
                )

                scores.append(score)

            previous_frame = gray

        frame_number += 1

    cap.release()

    return (
        duration,
        timestamps,
        scores,
    )


# =========================================================
# FIND BEST SECTIONS
# =========================================================

def find_best_sections(
    duration,
    timestamps,
    scores,
    number_of_clips,
    target_length,
):

    if duration <= 0:
        return []

    # No scene-change data
    if not scores:

        clip_length = min(
            duration,
            max(
                3,
                target_length / number_of_clips,
            ),
        )

        return [
            (
                i * clip_length,
                min(
                    duration,
                    (i * clip_length)
                    + clip_length,
                ),
            )
            for i in range(number_of_clips)
            if i * clip_length < duration
        ]

    scores_array = np.asarray(
        scores,
        dtype=float,
    )

    # Smooth noisy changes
    if len(scores_array) >= 5:

        kernel = np.ones(5) / 5

        smoothed = np.convolve(
            scores_array,
            kernel,
            mode="same",
        )

    else:

        smoothed = scores_array

    threshold = np.percentile(
        smoothed,
        60,
    )

    candidates = []

    for timestamp, score in zip(
        timestamps,
        smoothed,
    ):

        if score >= threshold:

            candidates.append(
                timestamp
            )

    windows = []

    for timestamp in candidates:

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

        elif start <= windows[-1][1] + 2:

            windows[-1][1] = max(
                windows[-1][1],
                end,
            )

        else:

            windows.append(
                [start, end]
            )

    # Fallback if scene analysis is weak
    if len(windows) < number_of_clips:

        windows = []

        segment_length = (
            duration /
            number_of_clips
        )

        for i in range(
            number_of_clips
        ):

            start = (
                i *
                segment_length
            )

            end = min(
                duration,
                start + segment_length,
            )

            windows.append(
                [start, end]
            )

    # Rank windows
    ranked = []

    for start, end in windows:

        length = end - start

        ranked.append(
            (
                length,
                start,
                end,
            )
        )

    ranked.sort(
        reverse=True
    )

    selected = []

    total_duration = 0

    max_duration = (
        target_length * 1.10
    )

    per_clip_target = max(
        2,
        target_length /
        number_of_clips,
    )

    for score, start, end in ranked:

        if len(selected) >= number_of_clips:
            break

        clip_length = min(
            end - start,
            per_clip_target,
        )

        if clip_length < 1:
            continue

        new_end = start + clip_length

        if (
            total_duration
            + clip_length
            <= max_duration
        ):

            selected.append(
                (
                    start,
                    new_end,
                )
            )

            total_duration += (
                clip_length
            )

    # Final fallback
    if not selected:

        clip_length = min(
            duration,
            per_clip_target,
        )

        selected.append(
            (
                0,
                clip_length,
            )
        )

    selected.sort(
        key=lambda item: item[0]
    )

    return selected


# =========================================================
# SMART VERTICAL FILTER
# =========================================================

def get_smart_vertical_filter(
    width,
    height,
):

    if width <= 0 or height <= 0:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=decrease,"
            "pad=1080:1920:"
            "(ow-iw)/2:(oh-ih)/2,"
            "setsar=1"
        )

    aspect_ratio = width / height

    # -----------------------------------------------------
    # PORTRAIT
    # -----------------------------------------------------

    if aspect_ratio <= 0.72:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1"
        )

    # -----------------------------------------------------
    # NEAR VERTICAL
    # -----------------------------------------------------

    if aspect_ratio <= 0.85:

        return (
            "scale=1080:1920:"
            "force_original_aspect_ratio=decrease,"
            "pad=1080:1920:"
            "(ow-iw)/2:(oh-ih)/2,"
            "setsar=1"
        )

    # -----------------------------------------------------
    # LANDSCAPE / SCREEN RECORDING
    #
    # IMPORTANT:
    # Do NOT center-crop.
    #
    # Instead:
    # 1. Create a blurred 9:16 background.
    # 2. Scale the original video to fit.
    # 3. Put the complete original frame in the center.
    #
    # This prevents text, websites and screen recordings
    # from being cut off.
    # -----------------------------------------------------

    return (
        "[0:v]"
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "boxblur=18:2,"
        "setsar=1"
        "[bg];"

        "[0:v]"
        "scale=1080:1920:"
        "force_original_aspect_ratio=decrease,"
        "setsar=1"
        "[fg];"

        "[bg][fg]"
        "overlay="
        "(W-w)/2:"
        "(H-h)/2"
    )


# =========================================================
# CREATE SMART CLIP
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

    video_filter = (
        get_smart_vertical_filter(
            width,
            height,
        )
    )

    # Complex filters need -filter_complex
    if "[bg]" in video_filter:

        filter_graph = (
            f"[0:v]"
            f"scale=1080:1920:"
            f"force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"boxblur=18:2,"
            f"setsar=1"
            f"[bg];"

            f"[0:v]"
            f"scale=1080:1920:"
            f"force_original_aspect_ratio=decrease,"
            f"setsar=1"
            f"[fg];"

            f"[bg][fg]"
            f"overlay="
            f"(W-w)/2:"
            f"(H-h)/2"
        )

        run_ffmpeg(
            [
                "-y",

                "-ss",
                str(start),

                "-i",
                str(source),

                "-t",
                str(duration),

                "-filter_complex",
                filter_graph,

                "-map",
                "0:v:0",

                "-map",
                "0:a?",

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

                "-shortest",

                str(output),
            ]
        )

    else:

        run_ffmpeg(
            [
                "-y",

                "-ss",
                str(start),

                "-i",
                str(source),

                "-t",
                str(duration),

                "-vf",
                video_filter,

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


# =========================================================
# JOIN CLIPS
# =========================================================

def join_clips(
    clip_paths,
    output,
):

    concat_file = Path(
        tempfile.mktemp(
            suffix=".txt"
        )
    )

    lines = []

    for clip in clip_paths:

        lines.append(
            "file '"
            + clip.as_posix()
            + "'"
        )

    concat_file.write_text(
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
                str(concat_file),

                "-c",
                "copy",

                str(output),
            ]
        )

    finally:

        concat_file.unlink(
            missing_ok=True
        )


# =========================================================
# ADD BACKGROUND MUSIC
# =========================================================

def add_background_music(
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
            "volume=0.18"
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

            "-shortest",

            str(output),
        ]
    )


# =========================================================
# COMPLETE AUTO EDIT
# =========================================================

def auto_edit(
    video_path,
    music_path,
    number_of_clips,
    target_length,
):

    width, height, fps, duration = (
        get_video_info(
            video_path
        )
    )

    if duration <= 0:

        raise RuntimeError(
            "Could not read the uploaded video."
        )

    (
        analyzed_duration,
        timestamps,
        scores,
    ) = analyze_video(
        video_path
    )

    selected = find_best_sections(
        analyzed_duration,
        timestamps,
        scores,
        number_of_clips,
        target_length,
    )

    if not selected:

        raise RuntimeError(
            "No usable video sections were detected."
        )

    working_dir = Path(
        tempfile.mkdtemp(
            prefix="clipflow_"
        )
    )

    try:

        clip_paths = []

        for index, (
            start,
            end,
        ) in enumerate(selected):

            clip_path = (
                working_dir /
                f"clip_{index}.mp4"
            )

            create_clip(
                video_path,
                start,
                end,
                clip_path,
                width,
                height,
            )

            clip_paths.append(
                clip_path
            )

        joined = (
            working_dir /
            "joined.mp4"
        )

        join_clips(
            clip_paths,
            joined,
        )

        final_output = (
            OUTPUT_DIR /
            "clipflow_result.mp4"
        )

        if music_path:

            add_background_music(
                joined,
                music_path,
                final_output,
            )

        else:

            shutil.copy2(
                joined,
                final_output,
            )

        return (
            final_output,
            selected,
            width,
            height,
            duration,
        )

    finally:

        shutil.rmtree(
            working_dir,
            ignore_errors=True,
        )


# =========================================================
# MAIN APP
# =========================================================

if video_file:

    st.success(
        f"✅ Video uploaded: {video_file.name}"
    )

    st.caption(
        f"File size: "
        f"{video_file.size / (1024 * 1024):.1f} MB"
    )

    st.video(
        video_file
    )

    st.divider()

    if add_music and not music_file:

        st.warning(
            "🎵 Background music is enabled. "
            "Please upload a music file."
        )

    else:

        if st.button(
            "✨ AUTO EDIT VIDEO",
            type="primary",
            use_container_width=True,
        ):

            video_suffix = (
                Path(
                    video_file.name
                ).suffix
                or ".mp4"
            )

            input_path = Path(
                tempfile.mktemp(
                    suffix=video_suffix
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

            try:

                progress = st.progress(
                    0
                )

                status = st.empty()

                status.info(
                    "🔎 Reading video information..."
                )

                progress.progress(
                    10
                )

                width, height, fps, duration = (
                    get_video_info(
                        input_path
                    )
                )

                st.write(
                    f"📐 Original video: "
                    f"{width} × {height}"
                )

                st.write(
                    f"⏱️ Duration: "
                    f"{duration:.1f} seconds"
                )

                status.info(
                    "🔍 Analyzing scene changes..."
                )

                progress.progress(
                    25
                )

                status.info(
                    "✂️ Selecting the strongest sections..."
                )

                progress.progress(
                    40
                )

                status.info(
                    "📱 Creating smart 9:16 framing..."
                )

                if width > height:

                    st.caption(
                        "🖥️ Landscape/screen recording detected — "
                        "full frame will be preserved."
                    )

                else:

                    st.caption(
                        "📱 Portrait video detected — "
                        "optimized vertical framing will be used."
                    )

                progress.progress(
                    55
                )

                if music_path:

                    status.info(
                        "🎵 Mixing background music..."
                    )

                else:

                    status.info(
                        "🎬 Rendering final video..."
                    )

                result, selected, final_width, final_height, final_duration = (
                    auto_edit(
                        input_path,
                        music_path,
                        number_of_clips,
                        target_length,
                    )
                )

                progress.progress(
                    100
                )

                status.success(
                    "🎉 ClipFlow AI finished your video!"
                )

                st.success(
                    f"Ready for {platform}!"
                )

                st.video(
                    str(result)
                )

                st.download_button(
                    "⬇️ Download Edited Video",
                    data=result.read_bytes(),
                    file_name=(
                        "clipflow_ai_result.mp4"
                    ),
                    mime="video/mp4",
                    use_container_width=True,
                )

                st.divider()

                st.subheader(
                    "📊 Edit Summary"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Original Duration",
                        f"{final_duration:.1f}s",
                    )

                with col2:

                    st.metric(
                        "Clips Selected",
                        len(selected),
                    )

                with col3:

                    st.metric(
                        "Output",
                        "1080 × 1920",
                    )

                with st.expander(
                    "🔍 Selected Sections"
                ):

                    for index, (
                        start,
                        end,
                    ) in enumerate(
                        selected,
                        1,
                    ):

                        st.write(
                            f"**Clip {index}:** "
                            f"{start:.1f}s → "
                            f"{end:.1f}s "
                            f"({end - start:.1f}s)"
                        )

                with st.expander(
                    "🎵 Music Information"
                ):

                    if music_path:

                        st.write(
                            "Background music was added "
                            "from the uploaded music file."
                        )

                        st.caption(
                            f"Selected mood: {music_mood}"
                        )

                    else:

                        st.write(
                            "No background music was added."
                        )

            except Exception as error:

                st.error(
                    "❌ ClipFlow could not finish the edit."
                )

                st.code(
                    str(error)
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
        "👆 Upload a video above to begin."
    )
