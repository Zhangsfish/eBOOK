"""Fish S2.1 JSON REST contract; no reference-audio/cloning fields are accepted."""
from .base import Adapter
from ..core import AuthBinding, HTTPPlan, canonical_json


class FishAdapter(Adapter):
    name = 'fish'
    models = ('s2.1-pro', 's2.1-pro-free')

    def prepare(self, request):
        self.validate(request)
        # OpenAPI specifies a string, not a fixed-length hex constraint. The lab
        # requires an explicit ID to keep voice identity comparable across runs.
        body = {'text': request.text, 'reference_id': request.voice,
                'format': 'wav', 'sample_rate': 24000, 'normalize': True,
                'prosody': {'speed': request.rate, 'volume': 0, 'normalize_loudness': False},
                'latency': 'normal'}
        # The official schema recommends leaving normalization language unset
        # for mixed-language text. The corpus includes Chinese/English cases.
        # Explicit header is important: unknown/omitted models fall back to paid s2.1-pro.
        return HTTPPlan(self.name, 'https://api.fish.audio/v1/tts',
                        {'Content-Type': 'application/json', 'model': request.model},
                        canonical_json(body).encode(), AuthBinding('FISH_API_KEY', 'Authorization', 'Bearer '))
