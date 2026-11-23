"""Audition planning and mock-only rendering. Never selects a winning provider."""
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import json
import random
import re
import subprocess
import tempfile
import uuid
from .adapters import ADAPTERS
from .billing import PRICE_SOURCES, estimate
from .core import AudioSpec, LabError, SynthesisRequest, join_wavs, text_counts
from .corpus import CORPUS_PATH, load_samples
from .player import write_player
from .storage import AudioCache, OUTPUT_ROOT, REPOSITORY, atomic_bytes, atomic_json, safe_output_directory
from .transport import MockTransport

DEFAULT_AZURE_VOICES = {
    ('neural', 'female'): 'zh-CN-XiaoxiaoNeural',
    ('neural', 'male'): 'zh-CN-YunxiNeural',
    ('dragon-hd-flash', 'female'): 'zh-CN-Xiaoyi:DragonHDFlashLatestNeural',
    ('dragon-hd-flash', 'male'): 'zh-CN-Yunxia:DragonHDFlashLatestNeural',
}


@dataclass(frozen=True)
class Condition:
    provider: str
    model: str
    slot: str
    style: str
    voice: str | None
    voice_source: str

    @property
    def configuration_key(self):
        return f'{self.provider}/{self.model}/{self.slot}'


def read_voice_configuration(path):
    if path is None:
        return {}
    source = Path(path).resolve()
    try:
        source.relative_to(OUTPUT_ROOT.resolve())
        if source.stat().st_size > 16384:
            raise ValueError()
        value = json.loads(source.read_text(encoding='utf-8'))
        allowed = {f'{provider}/{model}/{slot}' for provider, adapter in ADAPTERS.items()
                   for model in adapter.models for slot in ('female', 'male')}
        if not isinstance(value, dict) or not set(value).issubset(allowed):
            raise ValueError()
        if any(not isinstance(voice, str) or not voice or len(voice) > 160 or any(ord(c) < 32 for c in voice)
               for voice in value.values()):
            raise ValueError()
        return value
    except (ValueError, OSError, TypeError):
        raise LabError('Voice configuration must be a small local ID-only JSON object under ignored tts-auditions/.') from None


def conditions(provider, voices):
    selected = ADAPTERS if provider == 'all' else {provider: ADAPTERS[provider]}
    result = []
    for name, adapter in selected.items():
        for model in adapter.models:
            for slot in ('female', 'male'):
                key = f'{name}/{model}/{slot}'
                voice = voices.get(key)
                source = 'local_configuration_unverified' if voice else 'voice_selection_required'
                if voice is None and name == 'azure':
                    voice = DEFAULT_AZURE_VOICES[(model, slot)]
                    source = 'official_static_example_region_access_unverified'
                for style in ('neutral', 'gentle'):
                    result.append(Condition(name, model, slot, style, voice, source))
    return result


def anonymous_label(index):
    result = ''
    while index >= 0:
        result = chr(65 + index % 26) + result
        index = index // 26 - 1
    return result


def _synthetic_voice(condition):
    # Valid field shapes for MOCK / planning only, never claimed as vendor IDs.
    if condition.provider == 'fish':
        return sha256(condition.configuration_key.encode()).hexdigest()[:32]
    return 'MOCK_UNCONFIGURED_' + condition.slot.upper()


def _source_revision():
    try:
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPOSITORY, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPOSITORY, text=True))
        return {'head': head, 'working_tree_dirty': dirty}
    except (OSError, subprocess.CalledProcessError):
        return {'head': None, 'working_tree_dirty': None}


def run_lab(provider='all', mode='dry_run', output=None, seed=None, voice_configuration=None, region=None):
    if provider not in (*ADAPTERS, 'all') or mode not in ('dry_run', 'mock'):
        raise LabError('S01 supports offline dry_run/mock modes only.')
    if region is not None and not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', region):
        raise LabError('Invalid Azure public-cloud region.')
    base = safe_output_directory(output)
    samples = load_samples()
    configurations = conditions(provider, read_voice_configuration(voice_configuration))
    rng = random.SystemRandom() if seed is None else random.Random(seed)
    rng.shuffle(configurations)
    aliases = [anonymous_label(i) for i in range(len(configurations))]
    timestamp = datetime.now(timezone(timedelta(hours=8), 'Asia/Shanghai'))
    session = Path(tempfile.mkdtemp(prefix=timestamp.strftime('%Y%m%d-%H%M%S-') + mode + '-', dir=base))
    cache = AudioCache(base / 'cache')
    transport = MockTransport()
    mapping, tracks, estimates_by_model = [], [], {}
    cache_hits = 0
    planned_requests = 0
    for alias, condition in zip(aliases, configurations):
        adapter = ADAPTERS[condition.provider]
        voice = condition.voice or _synthetic_voice(condition)
        supported = adapter.supports_style(condition.model, voice, condition.style)
        row = {'alias': alias, **asdict(condition), 'style_supported': supported, 'samples': []}
        for sample in samples:
            item = {'sample_id': sample.id, 'status': 'not_run', 'audio': None, 'chunk_plans': []}
            if not supported:
                item['status'] = 'unsupported_style'
                item['reason'] = 'No documented equivalent gentle control without adding provider-specific text tags.'
            else:
                audio_parts = []
                for text in sample.pieces:
                    request = SynthesisRequest(condition.provider, condition.model, voice, text,
                                               condition.style, 1.0,
                                               (region or 'eastus') if condition.provider == 'azure' else None)
                    plan = adapter.prepare(request)
                    cost = estimate(request, plan)
                    estimates_by_model.setdefault((condition.provider, condition.model), []).append(cost)
                    planned_requests += 1
                    item['chunk_plans'].append({**text_counts(text), 'text_sha256': sha256(text.encode()).hexdigest(),
                                                'request': plan.public_summary(), 'cost': cost.public()})
                    if mode == 'mock':
                        audio, hit = cache.get_or_synthesize(adapter, request, transport)
                        cache_hits += int(hit); audio_parts.append(audio)
                if mode == 'mock':
                    relative = 'audio/' + uuid.uuid4().hex + '.wav'
                    atomic_bytes(session / relative, join_wavs(audio_parts))
                    item.update(status='mock_signal_not_vendor_speech', audio=relative)
                else:
                    item['status'] = 'dry_run_voice_selection_required' if condition.voice is None else 'dry_run_not_synthesized'
            row['samples'].append(item)
            tracks.append({'sample_id': sample.id, 'alias': alias, 'audio': item['audio'], 'status': item['status']})
        mapping.append(row)
    totals = []
    for (name, model), estimates in sorted(estimates_by_model.items()):
        known = all(item.usd is not None for item in estimates)
        totals.append({'provider': name, 'model': model, 'hypothetical_chunk_requests': len(estimates),
                       'billable_units_estimate': sum(item.units for item in estimates),
                       'billing_unit': estimates[0].unit_name,
                       'estimated_usd_if_all_configured_and_executed': str(sum((item.usd for item in estimates), Decimal(0))) if known else None,
                       'price_source': PRICE_SOURCES[name]})
    metadata = {'mode': mode, 'created_at': timestamp.isoformat(), 'timezone': 'Asia/Shanghai',
                'source_revision': _source_revision(), 'original_corpus_sha256': sha256(CORPUS_PATH.read_bytes()).hexdigest(),
                'audio_format': asdict(AudioSpec()), 'actual_vendor_requests': 0, 'incurred_cost_usd': '0',
                'real_audio_generated': False, 'human_listening': 'NOT_RUN', 'provider_selected': None,
                'condition_count': len(configurations), 'sample_count': len(samples),
                'planned_chunk_requests': planned_requests, 'mock_transport_calls': len(transport.calls),
                'mock_cache_hits': cache_hits, 'cost_estimates': totals,
                'azure_region': region, 'azure_region_note': 'Unconfigured plans use eastus only as a syntax placeholder; no resource voice list was queried.',
                'warning': 'No provider voice/audio/latency/quality evidence. Mock signals are identical test tones. Prices are dated estimates, not a live quote.'}
    atomic_json(session / 'session.json', metadata)
    atomic_json(session / 'private-mapping.json', {'mode': mode, 'seed': seed, 'conditions': mapping})
    atomic_json(session / 'original-samples.json', {'samples': [sample.public() for sample in samples]})
    write_player(session, samples, tracks, aliases, mode)
    return session, metadata, mapping
