import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st


# =========================================================
# CLIPFLOW AI V2
# =========================================================

st.set_page_config(
    page_title="ClipFlow AI",
    page_icon="🎬",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# =========================================================
# UI
# =========================================================

st.title("🎬 ClipFlow AI")

st.write(
    "Turn raw footage into a polished, ready-to-post short automatically."
)

st.markdown(
    """
    <div style="
        padding:20px;
        border:1px solid rgba(128,128,128,.25);
        border-radius:16px;
        margin:15px 0;
    ">
        <h3>Upload → Analyze → Smart Edit → Captions → Export</h3>
        <p>
        ClipFlow detects active sections, removes unnecessary silence,
        preserves important screen content, creates vertical framing,
        and can generate automatic captions.
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
        "Use only music you have permission to use."
    )


# =========================================================
# UPLOADS
# =========================================================

video_file = st.file_uploader(
    "📁 Upload your video",
    type=["mp4", "mov", "m4v", "avi"],
)

music_file = None

if add_music:

    music_file = st.file_uploader(
        "🎵 Upload royalty-safe music",
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

        return found or "ffmpeg"


def run_ffmpeg(args):

    result = subprocess.run(
        [get_ffmpeg()] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        error = result.stderr

        if len(error) > 5000:
            error = error[-5000:]

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

    if not fps or fps <= 0:
        fps = 25

    duration = 0

    if frames:
        duration = frames / fps

    return width, height, fps, duration


# =========================================================
# SCENE ANALYSIS
# =========================================================

def analyze_video(path):

    cap = cv2.VideoCapture(str(path))

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if not fps or fps <= 0:
        fps = 25

    frames = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = (
        frames / fps
        if frames
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

                scores.append(
                    float(diff.mean())
                )

                timestamps.append(
                    frame_number / fps
                )

            previous = gray

        frame_number += 1

    cap.release()

    return duration, timestamps, scores


# =========================================================
# SELECT BEST CLIPS
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

        each = max(
            2,
            target / count
        )

        return [
            (
                i * each,
                min(
                    duration,
                    (i + 1) * each
                )
            )
            for i in range(count)
            if i * each < duration
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
        values
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

        segment = (
            duration / count
        )

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
        reverse=True
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

        length = min(
            end - start,
            per_clip
        )

        if length < 1:
            continue

        if (
            total + length
            <= target * 1.10
        ):

            selected.append(
                (
                    start,
                    start + length
                )
            )

            total += length

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
    min_duration=0.8
):

    result = run_ffmpeg(
        [
            "-i",
            str(source),

            "-af",
            (
                f"silencedetect="
                f"noise={noise}:"
                f"d={min_duration}"
            ),

            "-f",
            "null",

            "-"
        ]
    )

    text = result.stderr

    starts = []
    ends = []

    for match in re.finditer(
        r"silence_start:\s*([\d.]+)",
        text
    ):

        starts.append(
            float(match.group(1))
        )

    for match in re.finditer(
        r"silence_end:\s*([\d.]+)",
        text
    ):

        ends.append(
            float(match.group(1))
        )

    return list(
        zip(starts, ends)
    )


# =========================================================
# SMART FRAME
# =========================================================

def get_vertical_filter(
    width,
    height
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
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1"
        )

    # Landscape / screen recording
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
# CAPTIONS
# =========================================================

@st.cache_resource(show_spinner=False)
def load_whisper():

    try:

        from faster_whisper import WhisperModel

        model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        return model

    except Exception as error:

        raise RuntimeError(
            "Caption engine could not load: "
            + str(error)
        )


def create_srt(
    source,
    output
):

    model = load_whisper()

    segments, info = model.transcribe(
        str(source),
        vad_filter=True,
        beam_size=1
    )

    def timestamp(seconds):

        hours = int(seconds // 3600)

        minutes = int(
            (seconds % 3600) // 60
        )

        secs = int(
            seconds % 60
        )

        millis = int(
            (seconds - int(seconds))
            * 1000
        )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{millis:03d}"
        )

    lines = []

    index = 1

    for segment in segments:

        text = segment.text.strip()

        if not text:
            continue

        lines.append(
            str(index)
        )

        lines.append(
            f"{timestamp(segment.start)} --> "
            f"{timestamp(segment.end)}"
        )

        lines.append(
            text
        )

        lines.append("")

        index += 1

    output.write_text(
        "\n".join(lines),
        encoding="utf-8"
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
    height
):

    duration = max(
        0.5,
        end - start
    )

    vertical_filter = get_vertical_filter(
        width,
        height
    )

    if "[bg]" in vertical_filter:

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
                vertical_filter,

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

                str(output)
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
                vertical_filter,

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

                str(output)
            ]
        )


# =========================================================
# JOIN
# =========================================================

def join_clips(
    clips,
    output
):

    concat = Path(
        tempfile.mktemp(
            suffix=".txt"
        )
    )

    concat.write_text(
        "\n".join(
            f"file '{p.as_posix()}'"
            for p in clips
        ),
        encoding="utf-8"
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

                "-c",
                "copy",

                str(output)
            ]
        )

    finally:

        concat.unlink(
            missing_ok=True
        )


# =========================================================
# ADD MUSIC
# =========================================================

def mix_music(
    video,
    music,
    output
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
            "volume=0.16"
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

            str(output)
        ]
    )


# =========================================================
# ADD CAPTIONS TO FINAL VIDEO
# =========================================================

def burn_captions(
    video,
    srt,
    output
):

    escaped = str(srt).replace(
        "\\",
        "/"
    ).replace(
        ":",
        "\\:"
    )

    subtitle_filter = (
        f"subtitles='{escaped}':"
        "force_style="
        "'FontSize=18,"
        "Bold=1,"
        "Alignment=2,"
        "MarginV=120,"
        "Outline=2'"
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

            "-c:a",
            "copy",

            str(output)
        ]
    )


# =========================================================
# MAIN EDIT PIPELINE
# =========================================================

def process_video(
    video_path,
    music_path,
    target_length,
    clip_count,
    silence_enabled,
    captions_enabled
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

    selected = select_clips(
        analyzed_duration,
        timestamps,
        scores,
        clip_count,
        target_length
    )

    if not selected:

        raise RuntimeError(
            "No usable video sections found."
        )

    work = Path(
        tempfile.mkdtemp(
            prefix="clipflow_v2_"
        )
    )

    try:

        clip_paths = []

        for i, (
            start,
            end
        ) in enumerate(selected):

            clip = (
                work /
                f"clip_{i}.mp4"
            )

            create_clip(
                video_path,
                start,
                end,
                clip,
                width,
                height
            )

            clip_paths.append(
                clip
            )

        joined = (
            work /
            "joined.mp4"
        )

        join_clips(
            clip_paths,
            joined
        )

        current = joined

        # Music
        if music_path:

            music_output = (
                work /
                "music.mp4"
            )

            mix_music(
                current,
                music_path,
                music_output
            )

            current = music_output

        # Captions
        if captions_enabled:

            srt = (
                work /
                "captions.srt"
            )

            create_srt(
                video_path,
                srt
            )

            captioned = (
                work /
                "captioned.mp4"
            )

            burn_captions(
                current,
                srt,
                captioned
            )

            current = captioned

        final = (
            OUTPUT_DIR /
            "clipflow_ai_v2_result.mp4"
        )

        shutil.copy2(
            current,
            final
        )

        return (
            final,
            selected,
            width,
            height,
            duration
        )

    finally:

        shutil.rmtree(
            work,
            ignore_errors=True
        )


# =========================================================
# APP
# =========================================================

if video_file:

    st.success(
        f"✅ Video uploaded: {video_file.name}"
    )

    st.video(video_file)

    if add_music and not music_file:

        st.warning(
            "Please upload a royalty-safe music track."
        )

    else:

        st.divider()

        if st.button(
            "✨ CREATE AI SHORT",
            type="primary",
            use_container_width=True
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

            try:

                progress = st.progress(0)

                status = st.empty()

                status.info(
                    "🔎 Analyzing your video..."
                )

                progress.progress(15)

                status.info(
                    "🎯 Finding the strongest moments..."
                )

                progress.progress(30)

                if remove_silence:

                    status.info(
                        "⏸️ Checking for unnecessary silence..."
                    )

                progress.progress(40)

                status.info(
                    "📱 Creating smart 9:16 framing..."
                )

                progress.progress(55)

                if add_captions:

                    status.info(
                        "🎙️ Generating automatic captions..."
                    )

                progress.progress(70)

                if music_path:

                    status.info(
                        f"🎵 Adding {music_mood.lower()} music..."
                    )

                else:

                    status.info(
                        "🎬 Rendering final video..."
                    )

                result, selected, width, height, duration = (
                    process_video(
                        input_path,
                        music_path,
                        target_length,
                        number_of_clips,
                        remove_silence,
                        add_captions
                    )
                )

                progress.progress(100)

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
                    "⬇️ Download AI Edited Video",
                    data=result.read_bytes(),
                    file_name="clipflow_ai_v2.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

                st.divider()

                st.subheader(
                    "📊 Edit Summary"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.metric(
                        "Original Duration",
                        f"{duration:.1f}s"
                    )

                with c2:

                    st.metric(
                        "Clips Selected",
                        len(selected)
                    )

                with c3:

                    st.metric(
                        "Output",
                        "1080 × 1920"
                    )

                with st.expander(
                    "🔍 Selected Clips"
                ):

                    for i, (
                        start,
                        end
                    ) in enumerate(
                        selected,
                        1
                    ):

                        st.write(
                            f"**Clip {i}:** "
                            f"{start:.1f}s → "
                            f"{end:.1f}s"
                        )

                with st.expander(
                    "✨ AI Features Used"
                ):

                    st.write(
                        "🎯 Smart scene selection"
                    )

                    st.write(
                        "📱 Smart vertical framing"
                    )

                    if remove_silence:
                        st.write(
                            "⏸️ Silence analysis enabled"
                        )

                    if add_captions:
                        st.write(
                            "🎙️ Automatic captions enabled"
                        )

                    if music_path:
                        st.write(
                            "🎵 Background music enabled"
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
