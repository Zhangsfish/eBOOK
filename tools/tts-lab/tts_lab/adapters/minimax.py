"""MiniMax sync T2A v2: official speech-t2a-http.md, checked 2026-11-23."""
import json
from .base import Adapter
from ..core import AuthBinding, HTTPPlan, LabError, canonical_json, checked_response, validate_wav


class MiniMaxAdapter(Adapter):
    name = 'minimax'
    models = ('speech-2.8-hd', 'speech-2.8-turbo')

    def supports_style(self, model, voice, style):
        return style in ('neutral', 'gentle')

    def prepare(self, request):
        self.validate(request)
        voice = {'voice_id': request.voice, 'speed': request.rate, 'vol': 1.0, 'pitch': 0}
        if request.style == 'gentle':
            voice['emotion'] = 'calm'  # Closest documented control, not an equivalence claim.
        body = {'model': request.model, 'text': request.text, 'stream': False,
                'language_boost': 'Chinese', 'output_format': 'hex', 'voice_setting': voice,
                'audio_setting': {'sample_rate': 24000, 'format': 'wav', 'channel': 1}}
        return HTTPPlan(self.name, 'https://api.minimax.io/v1/t2a_v2',
                        {'Content-Type': 'application/json'}, canonical_json(body).encode(),
                        AuthBinding('MINIMAX_API_KEY', 'Authorization', 'Bearer '), 'minimax_hex_wav')

    def parse(self, response, request):
        checked_response(response)
        try:
            value = json.loads(response.body)
            if not isinstance(value, dict):
                raise ValueError()
            code = value.get('base_resp', {}).get('status_code')
            if type(code) is not int or code != 0:
                category = {1001: 'timeout', 1002: 'rate_limit', 1004: 'authentication',
                            1039: 'rate_limit', 2013: 'invalid_request'}.get(code, 'provider_failure')
                raise LabError(f'MiniMax response: {category}; no retry performed.')
            data = value.get('data')
            if not isinstance(data, dict) or data.get('status') != 2 or not isinstance(data.get('audio'), str):
                raise ValueError()
            # URL mode and unfinished/streaming frames are deliberately rejected.
            audio = bytes.fromhex(data['audio'])
        except (ValueError, TypeError, AttributeError):
            raise LabError('Malformed MiniMax completed hex-audio response.') from None
        validate_wav(audio, request.audio)
        return audio
