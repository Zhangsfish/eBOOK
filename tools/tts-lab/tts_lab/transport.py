"""Mock I/O and a fail-closed future HTTP boundary. Nothing auto-retries."""
from dataclasses import dataclass
import json
import math
import os
import re
import struct
from urllib.parse import urlsplit
from urllib import request as urllib_request
from urllib.error import HTTPError
from .billing import check_spend_cap
from .core import HTTPResponse, LabError, MAX_RESPONSE_BYTES, canonical_json, wav_from_pcm


def mock_wav():
    """Identical 0.16 s test tone for every candidate: never a synthetic voice."""
    pcm = b''.join(struct.pack('<h', round(800 * math.sin(2 * math.pi * 440 * i / 24000)))
                   for i in range(3840))
    return wav_from_pcm(pcm)


class MockTransport:
    kind = 'mock'

    def __init__(self, responses=None):
        self.calls = []
        self.responses = None if responses is None else list(responses)

    def send(self, plan):
        self.calls.append(plan)
        if self.responses is not None:
            if not self.responses:
                raise LabError('Mock response queue exhausted; no retry performed.')
            value = self.responses.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        audio = mock_wav()
        if plan.response_kind == 'minimax_hex_wav':
            value = {'base_resp': {'status_code': 0}, 'data': {'status': 2, 'audio': audio.hex()}}
            return HTTPResponse(200, canonical_json(value).encode(), {'Content-Type': 'application/json'})
        return HTTPResponse(200, audio, {'Content-Type': 'audio/wav'})


@dataclass(frozen=True)
class LivePolicy:
    execute_live: bool = False
    maximum_spend_usd: str | None = None
    phase_authorized: bool = False

    def authorize(self, estimates):
        if not self.execute_live:
            raise LabError('Live transport requires explicit --execute-live.')
        check_spend_cap(self.maximum_spend_usd, estimates)
        if not self.phase_authorized:
            raise LabError('S01 forbids live provider requests, even with a spend cap. No credentials were read and no request was sent.')


class NoRedirect(urllib_request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GuardedHTTPTransport:
    """Future extension only. S01 CLI never supplies an authorized phase policy.

    Credentials enter only an ephemeral wire request after policy/host checks;
    plans, errors and persisted cache metadata contain no credential values.
    """
    kind = 'live'

    def __init__(self, policy, plan_quotes, opener=None):
        self.policy, self.plan_quotes, self.opener = policy, tuple(plan_quotes), opener
        self._used = False

    def send(self, plan):
        self.policy.authorize([quote for _, quote in self.plan_quotes])
        if not self.plan_quotes or not any(plan == approved for approved, _ in self.plan_quotes):
            raise LabError('Live I/O requires a nonempty reviewed batch quote bound to this exact request plan.')
        if self._used:
            raise LabError('A live transport permit is single-use; no automatic retry.')
        parsed = urlsplit(plan.url)
        allowed = {
            'minimax': parsed.hostname == 'api.minimax.io' and parsed.path == '/v1/t2a_v2',
            'fish': parsed.hostname == 'api.fish.audio' and parsed.path == '/v1/tts',
            'elevenlabs': parsed.hostname == 'api.elevenlabs.io' and parsed.path.startswith('/v1/text-to-speech/'),
            'azure': bool(re.fullmatch(r'[a-z][a-z0-9-]{1,40}\.tts\.speech\.microsoft\.com', parsed.hostname or ''))
                     and parsed.path == '/cognitiveservices/v1',
        }
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.fragment or parsed.port not in (None, 443) or not allowed.get(plan.provider):
            raise LabError('Unreviewed provider endpoint is not allowed.')
        if any(name.lower() in ('authorization', 'xi-api-key', 'ocp-apim-subscription-key') for name in plan.headers):
            raise LabError('Credentials must be bound at the transport boundary.')
        secret = os.environ.get(plan.auth.environment)
        if not secret or '\r' in secret or '\n' in secret:
            raise LabError('Required provider credential is absent or invalid.')
        headers = {**plan.headers, plan.auth.header: plan.auth.prefix + secret}
        wire = urllib_request.Request(plan.url, data=plan.body, headers=headers, method='POST')
        self._used = True  # Mark before attempting I/O, including timeouts.
        opener = self.opener or urllib_request.build_opener(NoRedirect())
        try:
            with opener.open(wire, timeout=30) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise LabError('Provider response exceeded the byte limit; no retry.')
                return HTTPResponse(response.status, body)
        except HTTPError as error:
            # Never propagate a remote body/message, which can reflect secrets.
            return HTTPResponse(error.code, b'')
        except LabError:
            raise
        except Exception:
            raise LabError('Ambiguous transport failure; billing may have occurred. No retry performed.') from None
