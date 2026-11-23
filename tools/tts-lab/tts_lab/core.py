"""Shared text, request and audio contracts. No networking or credentials here."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from io import BytesIO
import json
import math
import unicodedata
import wave

MAX_CHUNK_SCALARS = 120
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
CONTRACT_VERSION = 's01-2026-11-24-v1'


class LabError(Exception):
    """Public, sanitized error: never include raw service bodies or credentials."""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def normalize_text(text):
    if not isinstance(text, str) or not text.strip():
        raise LabError('Text must be nonempty.')
    if any(0xD800 <= ord(c) <= 0xDFFF or (ord(c) < 32 and c not in '\n\t\r') for c in text):
        raise LabError('Text contains invalid Unicode/control characters.')
    return unicodedata.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n'))


def text_counts(text):
    return {'unicode_scalars': len(text), 'utf8_bytes': len(text.encode('utf-8')),
            'utf16_units': len(text.encode('utf-16-le')) // 2}


def chunks(text, maximum=MAX_CHUNK_SCALARS):
    """Lossless scalar boundaries; prefer punctuation/paragraphs near the limit."""
    if not isinstance(maximum, int) or not 8 <= maximum <= MAX_CHUNK_SCALARS:
        raise LabError('Chunk limit must be between 8 and 120 scalars.')
    text = normalize_text(text)
    result, start = [], 0
    while start < len(text):
        end = min(start + maximum, len(text))
        if end < len(text):
            candidates = [i + 1 for i in range(start + maximum // 2, end)
                          if text[i] in '。！？；，、\n.!?;']
            if candidates:
                end = candidates[-1]
                if end < start + maximum and text[end] in '”’」』':
                    end += 1
        part = text[start:end]
        if part.strip():
            result.append(part)
        elif result and len(result[-1]) + len(part) <= maximum:
            result[-1] += part
        else:
            raise LabError('A whitespace-only chunk cannot be synthesized.')
        start = end
    assert ''.join(result) == text
    return result


@dataclass(frozen=True)
class AudioSpec:
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2
    container: str = 'wav'

    def validate(self):
        if self != AudioSpec():
            raise LabError('S01 comparison format is 24 kHz / 16-bit / mono WAV only.')


@dataclass(frozen=True)
class SynthesisRequest:
    provider: str
    model: str
    voice: str
    text: str
    style: str = 'neutral'
    rate: float = 1.0
    region: str | None = None
    audio: AudioSpec = field(default_factory=AudioSpec)

    def validate(self):
        self.audio.validate()
        if not self.voice or len(self.voice) > 160 or any(ord(c) < 32 for c in self.voice):
            raise LabError('A valid voice identifier is required.')
        if self.text != normalize_text(self.text) or len(self.text) > MAX_CHUNK_SCALARS:
            raise LabError('Text must be normalized and chunked before preparation.')
        if self.style not in ('neutral', 'gentle'):
            raise LabError('Unknown audition style.')
        if isinstance(self.rate, bool) or not math.isfinite(self.rate) or not 0.8 <= self.rate <= 1.2:
            raise LabError('Comparison rate must be between 0.8 and 1.2.')

    def cache_key(self, generation_kind):
        if generation_kind not in ('mock', 'live'):
            raise LabError('Unknown cache provenance.')
        value = asdict(self)
        value.pop('text')
        value.update(text_sha256=sha256(self.text.encode()).hexdigest(),
                     generation_kind=generation_kind, contract_version=CONTRACT_VERSION)
        return sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class AuthBinding:
    environment: str
    header: str
    prefix: str = ''


@dataclass(frozen=True)
class HTTPPlan:
    provider: str
    url: str
    headers: dict
    body: bytes = field(repr=False)
    auth: AuthBinding
    response_kind: str = 'wav'

    def public_summary(self):
        return {'provider': self.provider, 'method': 'POST', 'url': self.url,
                'header_names': sorted([*self.headers, self.auth.header]),
                'credential_environment_name': self.auth.environment,
                'body_sha256': sha256(self.body).hexdigest(), 'body_bytes': len(self.body)}


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    body: bytes = field(repr=False)
    headers: dict = field(default_factory=dict)


def checked_response(response):
    if response.status != 200:
        category = {400: 'invalid_request', 401: 'authentication', 402: 'quota',
                    403: 'permission', 404: 'unavailable', 415: 'format', 429: 'rate_limit'}.get(response.status, 'provider_failure')
        raise LabError(f'Provider response: {category} (HTTP {response.status}); no retry performed.')
    if not response.body or len(response.body) > MAX_RESPONSE_BYTES:
        raise LabError('Empty or oversized provider response.')


def validate_wav(data, spec=AudioSpec()):
    spec.validate()
    if not data or len(data) > MAX_RESPONSE_BYTES:
        raise LabError('Empty or oversized WAV.')
    try:
        with wave.open(BytesIO(data), 'rb') as stream:
            if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getcomptype()) != (
                    spec.sample_rate, spec.channels, spec.sample_width, 'NONE'):
                raise LabError('Audio differs from the comparison format; no resampling performed.')
            frames = stream.getnframes()
            if not 0 < frames <= spec.sample_rate * 120:
                raise LabError('Invalid or excessive audio duration.')
            pcm = stream.readframes(frames)
            if len(pcm) != frames * spec.channels * spec.sample_width:
                raise LabError('Truncated WAV frames.')
            return pcm
    except (wave.Error, EOFError, ValueError):
        raise LabError('Malformed WAV response.') from None


def wav_from_pcm(pcm):
    if not pcm or len(pcm) % 2:
        raise LabError('Invalid PCM byte count.')
    result = BytesIO()
    with wave.open(result, 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(24000)
        stream.writeframes(pcm)
    data = result.getvalue()
    validate_wav(data)
    return data


def join_wavs(parts):
    return wav_from_pcm(b''.join(validate_wav(part) for part in parts))
