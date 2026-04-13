import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


logger = logging.getLogger(__name__)


# Speech recognition for audio file transcription
try:
    import speech_recognition as sr  # type: ignore

    SPEECH_RECOGNITION_AVAILABLE = True
except Exception:
    sr = None  # type: ignore
    SPEECH_RECOGNITION_AVAILABLE = False


# Pydub for audio format conversion (requires ffmpeg)
try:
    from pydub import AudioSegment  # type: ignore

    PYDUB_AVAILABLE = True
except Exception:
    AudioSegment = None  # type: ignore
    PYDUB_AVAILABLE = False


# imageio-ffmpeg can provide a bundled ffmpeg binary if system ffmpeg is missing.
try:
    import imageio_ffmpeg  # type: ignore

    IMAGEIO_FFMPEG_AVAILABLE = True
except Exception:
    imageio_ffmpeg = None  # type: ignore
    IMAGEIO_FFMPEG_AVAILABLE = False


FFMPEG_BINARY_PATH: str | None = None
_FFMPEG_CONFIGURED = False


def configure_ffmpeg_binary() -> str | None:
    """
    Best-effort ffmpeg discovery for audio conversion.
    Returns selected ffmpeg path or None.
    """
    global FFMPEG_BINARY_PATH, _FFMPEG_CONFIGURED
    if _FFMPEG_CONFIGURED:
        return FFMPEG_BINARY_PATH

    candidates: list[Path] = []

    env_path = os.getenv("FFMPEG_BINARY")
    if env_path:
        candidates.append(Path(env_path))

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        candidates.append(Path(system_ffmpeg))

    if IMAGEIO_FFMPEG_AVAILABLE and imageio_ffmpeg is not None:
        try:
            bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            if bundled_ffmpeg:
                candidates.append(Path(bundled_ffmpeg))
        except Exception as exc:
            logger.debug("imageio-ffmpeg lookup failed: %s", exc)

    selected = next((p for p in candidates if p and p.exists()), None)
    FFMPEG_BINARY_PATH = str(selected) if selected else None

    if selected and PYDUB_AVAILABLE and AudioSegment is not None:
        AudioSegment.converter = str(selected)
        ffprobe_candidate = selected.with_name(
            "ffprobe.exe" if selected.suffix.lower() == ".exe" else "ffprobe"
        )
        if ffprobe_candidate.exists():
            AudioSegment.ffprobe = str(ffprobe_candidate)

    if selected:
        logger.info("Configured ffmpeg binary: %s", selected)
    else:
        logger.warning(
            "ffmpeg binary not found. Non-WAV audio transcription may fail. "
            "Install ffmpeg or set FFMPEG_BINARY."
        )

    _FFMPEG_CONFIGURED = True
    return FFMPEG_BINARY_PATH


def transcribe_uploaded_audio(audio_file) -> tuple[str, str, str | None]:
    """
    Returns: (transcript, transcription_status, transcription_error)
    """
    if not audio_file:
        return "", "not_requested", None

    if not SPEECH_RECOGNITION_AVAILABLE or sr is None:
        return "", "speech_recognition_unavailable", (
            "SpeechRecognition is not available on the backend."
        )

    ffmpeg_path = configure_ffmpeg_binary()

    tmp_original_path: str | None = None
    wav_path: str | None = None
    created_paths: set[str] = set()

    try:
        original_filename = audio_file.filename or "audio.wav"
        file_ext = os.path.splitext(original_filename)[1].lower() or ".wav"

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_original:
            audio_file.save(tmp_original.name)
            tmp_original_path = tmp_original.name
            created_paths.add(tmp_original_path)

        wav_path = tmp_original_path
        if file_ext not in [".wav", ".wave"]:
            if not ffmpeg_path and not (PYDUB_AVAILABLE and AudioSegment is not None):
                return "", "unsupported_format", (
                    f"Unsupported audio format '{file_ext}'. Upload a WAV file or enable ffmpeg conversion."
                )

            try:
                logger.info("Converting %s audio to WAV", file_ext)
                wav_path = tmp_original_path.rsplit(".", 1)[0] + ".wav"
                if ffmpeg_path:
                    # Use ffmpeg directly so conversion works even when ffprobe is unavailable.
                    cmd = [
                        ffmpeg_path,
                        "-y",
                        "-i",
                        tmp_original_path,
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        wav_path,
                    ]
                    proc = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if proc.returncode != 0:
                        err_text = (proc.stderr or "").strip()
                        raise RuntimeError(err_text or "ffmpeg conversion failed")
                else:
                    audio = AudioSegment.from_file(tmp_original_path)
                    audio.export(wav_path, format="wav")
                created_paths.add(wav_path)
            except Exception as conv_err:
                return "", "conversion_failed", (
                    f"Failed to convert {file_ext} audio: {conv_err}"
                )

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        transcript = recognizer.recognize_google(audio_data, language="en-US").strip()
        if transcript:
            return transcript, "transcribed", None
        return "", "empty_transcript", "No words were detected in the audio."

    except sr.UnknownValueError:
        return "", "not_understood", (
            "Could not understand the voice note. Please speak clearly or try another recording."
        )
    except sr.RequestError as exc:
        return "", "service_error", f"Speech recognition service error: {exc}"
    except Exception as exc:
        return "", "transcription_error", f"Audio transcription failed: {exc}"
    finally:
        for path in created_paths:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except Exception as cleanup_exc:
                logger.debug("Temp file cleanup warning (%s): %s", path, cleanup_exc)
