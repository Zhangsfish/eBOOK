"""ElevenLabs convert endpoint; explicit v4/v2 models and WAV output."""
import re
from urllib.parse import quote
from .base import Adapter
from ..core import AuthBinding, HTTPPlan, LabError, canonical_json


class ElevenLabsAdapter(Adapter):
    name = 'elevenlabs'
    models = ('eleven_v4', 'eleven_multilingual_v2')

    def prepare(self, request):
        self.validate(request)
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', request.voice):
            raise LabError('Invalid ElevenLabs voice ID.')
        body = {'text': request.text, 'model_id': request.model,
                'voice_settings': {'speed': request.rate}}
        # language_code is explicitly unsupported by multilingual_v2.
        if request.model == 'eleven_v4':
            body['language_code'] = 'zh'
        # Do not promise Enterprise-only zero retention via enable_logging=false.
        url = 'https://api.elevenlabs.io/v1/text-to-speech/' + quote(request.voice, safe='') + '?output_format=wav_24000'
        return HTTPPlan(self.name, url, {'Content-Type': 'application/json'},
                        canonical_json(body).encode(), AuthBinding('ELEVENLABS_API_KEY', 'xi-api-key'))
