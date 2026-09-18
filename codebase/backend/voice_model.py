import os
import io
import wave
from pathlib import Path
from typing import Union, BinaryIO, Optional

try:
    import audioop
except ImportError:
    try:
        import aup_audioop as audioop
    except ImportError:
        audioop = None

try:
    import riva.client
except ImportError:
    riva = None

from config.config import settings

VI_ASR_FUNCTION_ID = "f3dff2bb-99f9-403d-a5f1-f574a757deb0"
NVCF_SERVER = "grpc.nvcf.nvidia.com:443"

_cached_asr_service = None
_cached_api_key: Optional[str] = None


def _get_asr_service():
    global _cached_asr_service, _cached_api_key
    if not riva or not settings.NVIDIA_API_KEY:
        return None
    if _cached_asr_service is None or _cached_api_key != settings.NVIDIA_API_KEY:
        try:
            auth = riva.client.Auth(
                uri=NVCF_SERVER,
                use_ssl=True,
                metadata_args=[
                    ["function-id", VI_ASR_FUNCTION_ID],
                    ["authorization", f"Bearer {settings.NVIDIA_API_KEY}"],
                ],
            )
            _cached_asr_service = riva.client.ASRService(auth)
            _cached_api_key = settings.NVIDIA_API_KEY
        except Exception as auth_err:
            print(f"⚠️ Riva Auth error: {auth_err}")
            _cached_asr_service = None
    return _cached_asr_service


def transcribe_audio(
    audio_data: Union[str, Path, bytes, BinaryIO],
    language_code: str = "vi-VN"
) -> str:
    """
    Fast Vietnamese Speech-to-Text with NVIDIA Riva ASR (Parakeet 0.6B).
    Blazing fast: in-memory streaming for WAV, with multi-engine fallback.
    """
    file_path = None
    raw_bytes: bytes = b""

    if isinstance(audio_data, (str, Path)):
        file_path = str(audio_data)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
    elif isinstance(audio_data, (bytes, bytearray)):
        raw_bytes = bytes(audio_data)
    elif hasattr(audio_data, "read"):
        raw_bytes = audio_data.read()

    if not raw_bytes:
        return ""

    asr_service = _get_asr_service()
    if not asr_service:
        return _transcribe_with_fallback(raw_bytes)

    pcm_bytes = None

    # In-memory WAV processing (mono + 16kHz resampling)
    if raw_bytes[:4] == b"RIFF":
        try:
            with wave.open(io.BytesIO(raw_bytes), "rb") as w:
                nchannels = w.getnchannels()
                sampwidth = w.getsampwidth()
                framerate = w.getframerate()
                frames = w.readframes(w.getnframes())

            if audioop is not None:
                if sampwidth != 2:
                    frames = audioop.lin2lin(frames, sampwidth, 2)
                    sampwidth = 2
                if nchannels == 2:
                    frames = audioop.tomono(frames, 2, 0.5, 0.5)
                elif nchannels > 2:
                    frames = audioop.tomono(frames[:len(frames) // nchannels * 2], 2, 1.0, 0.0)
                if framerate != 16000:
                    frames, _ = audioop.ratecv(frames, 2, 1, framerate, 16000, None)

            pcm_bytes = frames
        except Exception as wav_err:
            print(f"⚠️ In-memory WAV processing error: {wav_err}")
            return _transcribe_with_fallback(raw_bytes)
    else:
        pcm_bytes = raw_bytes

    if not pcm_bytes:
        return _transcribe_with_fallback(raw_bytes)

    try:
        config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=16000,
                audio_channel_count=1,
                language_code=language_code,
                max_alternatives=1,
                enable_automatic_punctuation=True,
                verbatim_transcripts=True,
            ),
            interim_results=False,
        )

        def chunk_iter():
            chunk_size = 3200
            for i in range(0, len(pcm_bytes), chunk_size):
                yield pcm_bytes[i:i + chunk_size]

        responses = asr_service.streaming_response_generator(
            audio_chunks=chunk_iter(),
            streaming_config=config,
        )
        transcripts = []
        for resp in responses:
            for res in resp.results:
                if res.is_final:
                    transcripts.append(res.alternatives[0].transcript)

        result_text = " ".join(transcripts).strip()
        if result_text:
            return result_text
        return _transcribe_with_fallback(raw_bytes)
    except Exception as e:
        print(f"⚠️ Riva ASR error: {e}, falling back to alternative engine...")
        return _transcribe_with_fallback(raw_bytes)


def _transcribe_with_fallback(raw_bytes: bytes) -> str:
    """Fallback audio transcription using Gemini Flash or Groq Whisper."""
    if not raw_bytes:
        return ""

    # 1. Thử Groq Whisper nếu có GROQ_API_KEY (siêu nhanh)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            groq_client = Groq(api_key=groq_key)
            ext = "wav" if raw_bytes[:4] == b"RIFF" else "webm"
            audio_file = ("input_audio." + ext, raw_bytes, f"audio/{ext}")
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language="vi",
                response_format="text"
            )
            text = str(transcription).strip()
            if text:
                return text
        except Exception as groq_err:
            print(f"[ASR] Groq fallback error: {groq_err}")

    # 2. Thử Gemini Flash qua google-genai
    try:
        from google import genai
        from google.genai import types
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            client = genai.Client(api_key=gemini_key)
            mime = "audio/wav" if raw_bytes[:4] == b"RIFF" else "audio/webm"
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Part.from_bytes(data=raw_bytes, mime_type=mime),
                    "Hãy chuyển đoạn âm thanh tiếng Việt này thành văn bản chữ viết một cách chính xác. Chỉ trả về duy nhất nội dung văn bản nói tiếng Việt, không kèm giải thích hay thêm dấu ngoặc kép."
                ]
            )
            result = (response.text or "").strip()
            if result:
                return result
    except Exception as gemini_err:
        print(f"[ASR] Gemini fallback error: {gemini_err}")

    # 3. Thử OpenAI Whisper nếu có OPENAI_API_KEY
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            ext = "wav" if raw_bytes[:4] == b"RIFF" else "webm"
            audio_file = ("input_audio." + ext, raw_bytes, f"audio/{ext}")
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language="vi",
            )
            text = (transcription.text or "").strip()
            if text:
                return text
        except Exception as oai_err:
            print(f"⚠️ OpenAI ASR fallback error: {oai_err}")

    return ""

