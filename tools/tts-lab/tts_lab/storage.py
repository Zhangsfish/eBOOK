"""Ignored local output paths and corruption-aware, provenance-separated cache."""
from hashlib import sha256
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
from .core import LabError, canonical_json, validate_wav

REPOSITORY = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPOSITORY / '.local-test-data' / 'tts-auditions'


def safe_output_directory(value=None):
    allowed = OUTPUT_ROOT.absolute()
    candidate = Path(value).absolute() if value else allowed
    try:
        relative = candidate.resolve().relative_to(allowed)
    except ValueError:
        raise LabError('All audition output must stay under ignored .local-test-data/tts-auditions/.') from None
    for path in (allowed.parent, allowed, *[allowed.joinpath(*relative.parts[:i + 1]) for i in range(len(relative.parts))]):
        if path.is_symlink():
            raise LabError('Symlinked audition output directories are not allowed.')
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate.resolve()


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, data):
    atomic_bytes(path, (canonical_json(data) + '\n').encode('utf-8'))


class AudioCache:
    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink():
            raise LabError('Symlinked audio cache is not allowed.')
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, request, kind):
        directory = self.root / kind / request.cache_key(kind)
        if directory.is_symlink() or directory.parent.is_symlink():
            raise LabError('Symlinked audio cache is not allowed.')
        return directory

    def load(self, request, kind):
        directory = self._directory(request, kind)
        if not directory.exists():
            return None
        try:
            metadata_path, audio_path = directory / 'record.json', directory / 'audio.wav'
            if metadata_path.is_symlink() or audio_path.is_symlink():
                raise ValueError()
            if metadata_path.stat().st_size > 65536:
                raise ValueError()
            record = json.loads(metadata_path.read_text(encoding='utf-8'))
            if record['state'] != 'complete' or record['key'] != request.cache_key(kind) or record['kind'] != kind:
                raise ValueError()
            if audio_path.stat().st_size > 12 * 1024 * 1024:
                raise ValueError()
            audio = audio_path.read_bytes()
            if sha256(audio).hexdigest() != record['audio_sha256']:
                raise ValueError()
            validate_wav(audio, request.audio)
            return audio
        except (OSError, ValueError, KeyError, TypeError, LabError):
            raise LabError('Cache is incomplete, failed or corrupt. No automatic request/rebilling; inspect the local record first.') from None

    def get_or_synthesize(self, adapter, request, transport):
        kind = transport.kind
        existing = self.load(request, kind)
        if existing is not None:
            return existing, True
        adapter.prepare(request)  # Validate before claiming/billing anything.
        directory = self._directory(request, kind)
        directory.parent.mkdir(parents=True, exist_ok=True)
        try:
            directory.mkdir()  # Atomic claim also prevents concurrent duplicate requests.
        except FileExistsError:
            raise LabError('Another request owns this cache key; no duplicate request sent.') from None
        record = {'state': 'pending', 'key': request.cache_key(kind), 'kind': kind,
                  'text_sha256': sha256(request.text.encode()).hexdigest(),
                  'created_at_utc': datetime.now(timezone.utc).isoformat(),
                  'request': {key: value for key, value in asdict(request).items() if key != 'text'}}
        atomic_json(directory / 'record.json', record)
        try:
            audio = adapter.synthesize(request, transport)
            validate_wav(audio, request.audio)
            atomic_bytes(directory / 'audio.wav', audio)
            record.update(state='complete', audio_sha256=sha256(audio).hexdigest())
            atomic_json(directory / 'record.json', record)
            return audio, False
        except Exception:
            record['state'] = 'failed_or_ambiguous'
            atomic_json(directory / 'record.json', record)
            raise LabError('Synthesis failed or timed out. No retry; inspect the local cache state before any later attempt.') from None
