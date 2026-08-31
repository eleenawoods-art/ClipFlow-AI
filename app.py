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
# UI
# =========================================================

st.title("🎬 ClipFlow AI")

st.write(
    "Upload a video and ClipFlow AI automatically "
    "creates a short vertical edit."
)

st.divider()


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


# =========================================================
# FILE UPLOAD
# =========================================================

video_file = st.file_uploader(
    "📁 Upload your video",
    type=[
        "mp4",
        "mov",
        "m4v",
        "avi",
    ],
)


music_file = None

if add_music:

    music_file = st.file_uploader(
        "🎵 Upload royalty-safe music",
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

        return shutil.which("ffmpeg") or "ffmpeg"


def run_ffmpeg(arguments):

    ffmpeg = get_ffmpeg()

    result = subprocess.run(
        [ffmpeg] + arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr[-3000:]
        )

    return result


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

    return duration, timestamps, scores


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

    if not scores:

        return [
            (
                0,
                min(
                    duration,
                    target_length,
                )
            )
        ]

    scores_array = np.asarray(
        scores,
        dtype=float,
    )

    # Smooth scene-change values

    if len(scores_array) >= 5:

        kernel = np.ones(5) / 5

        smoothed = np.convolve(
            scores_array,
            kernel,
            mode="same",
        )

    else:

        smoothed = scores_array

    # Select high-activity moments

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

    # Fallback

    if len(windows) < number_of_clips:

        windows = []

        segment_length = (
            duration / number_of_clips
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

    # Rank sections

    ranked = []

    for window in windows:

        start, end = window

        length = end - start

        score = length

        ranked.append(
            (
                score,
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

    for score, start, end in ranked:

        if len(selected) >= number_of_clips:

            break

        clip_length = min(
            end - start,
            target_length /
            number_of_clips,
        )

        end = start + clip_length

        if (
            total_duration + clip_length
            <= max_duration
        ):

            selected.append(
                (start, end)
            )

            total_duration += (
                clip_length
            )

    selected.sort(
        key=lambda x: x[0]
    )

    return selected


# =========================================================
# CREATE VERTICAL CLIPS
# =========================================================

def create_clip(
    source,
    start,
    end,
    output,
):

    duration = end - start

    video_filter = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "setsar=1"
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
            f"file '{clip.as_posix()}'"
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
# ADD MUSIC
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

            "[1:a]volume=0.18[music];"
            "[0:a][music]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2[a]",

            "-map",
            "0:v:0",

            "-map",
            "[a]",

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-shortest",

            str(output),
        ]
    )


# =========================================================
# AUTO EDIT
# =========================================================

def auto_edit(
    video_path,
    music_path,
    number_of_clips,
    target_length,
):

    duration, timestamps, scores = (
        analyze_video(
            video_path
        )
    )

    selected = find_best_sections(
        duration,
        timestamps,
        scores,
        number_of_clips,
        target_length,
    )

    if not selected:

        raise RuntimeError(
            "Could not find usable video sections."
        )

    working_dir = Path(
        tempfile.mkdtemp(
            prefix="clipflow_"
        )
    )

    try:

        clip_paths = []

        for index, (start, end) in enumerate(
            selected
        ):

            clip_path = (
                working_dir /
                f"clip_{index}.mp4"
            )

            create_clip(
                video_path,
                start,
                end,
                clip_path,
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
        )

    finally:

        shutil.rmtree(
            working_dir,
            ignore_errors=True,
        )


# =========================================================
# MAIN BUTTON
# =========================================================

if video_file:

    st.video(video_file)

    st.divider()

    if st.button(
        "✨ AUTO EDIT VIDEO",
        type="primary",
        use_container_width=True,
    ):

        input_suffix = (
            Path(
                video_file.name
            ).suffix
            or ".mp4"
        )

        input_path = Path(
            tempfile.mktemp(
                suffix=input_suffix
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

            with st.status(
                "🎬 ClipFlow AI is editing...",
                expanded=True,
            ):

                st.write(
                    "🔎 Analyzing video..."
                )

                st.write(
                    "✂️ Finding active sections..."
                )

                st.write(
                    "📱 Creating vertical format..."
                )

                if music_path:

                    st.write(
                        f"🎵 Adding {music_mood.lower()} music..."
                    )

                result, selected = auto_edit(
                    input_path,
                    music_path,
                    number_of_clips,
                    target_length,
                )

                st.write(
                    "✅ Rendering finished video..."
                )

            st.success(
                "🎉 Your video is ready!"
            )

            st.video(
                str(result)
            )

            st.download_button(
                "⬇️ Download Edited Video",
                data=result.read_bytes(),
                file_name="clipflow_ai_result.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

            with st.expander(
                "🔍 See what ClipFlow selected"
            ):

                for i, (
                    start,
                    end,
                ) in enumerate(
                    selected,
                    1,
                ):

                    st.write(
                        f"Clip {i}: "
                        f"{start:.1f}s → "
                        f"{end:.1f}s"
                    )

        except Exception as error:

            st.error(
                f"Editing failed: {error}"
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
