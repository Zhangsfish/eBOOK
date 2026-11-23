"""Dated list-price estimates, not invoices. Unknown prices remain unknown."""
from dataclasses import dataclass
from decimal import Decimal
import re
import unicodedata
from .core import LabError, text_counts

PRICE_DATE = '2026-11-23'
PRICE_SOURCES = {
    'minimax': 'https://platform.minimax.io/docs/pricing/overview.md',
    'fish': 'https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits.md',
    'elevenlabs': 'https://elevenlabs.io/pricing/api',
    'azure': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech',
}
USD_PER_MILLION = {
    ('minimax', 'speech-2.8-hd'): Decimal('100'),
    ('minimax', 'speech-2.8-turbo'): Decimal('60'),
    ('fish', 's2.1-pro'): Decimal('15'),
    ('fish', 's2.1-pro-free'): Decimal('0'),
    ('elevenlabs', 'eleven_v4'): Decimal('80'),
    ('elevenlabs', 'eleven_multilingual_v2'): Decimal('80'),
    ('azure', 'neural'): None,
    ('azure', 'dragon-hd-flash'): None,
}


def is_han(character):
    name = unicodedata.name(character, '')
    return (name.startswith(('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-'))
            or character == '〇' or 0x20000 <= ord(character) <= 0x323AF)


def azure_billable_units(plan):
    # Microsoft includes SSML markup except speak/voice tags. Count the exact
    # escaped inner serialization conservatively, including style/prosody tags.
    inner = re.sub(r'</?(?:speak|voice)\b[^>]*>', '', plan.body.decode('utf-8'))
    return len(inner) + sum(is_han(c) for c in inner)


@dataclass(frozen=True)
class CostEstimate:
    units: int
    unit_name: str
    usd_per_million: Decimal | None
    notes: str

    def __post_init__(self):
        if type(self.units) is not int or self.units < 0:
            raise LabError('Billable-unit estimates must be nonnegative integers.')
        if self.usd_per_million is not None and (not isinstance(self.usd_per_million, Decimal)
                or not self.usd_per_million.is_finite() or self.usd_per_million < 0):
            raise LabError('A price must be a finite nonnegative Decimal, or unknown.')

    @property
    def usd(self):
        return None if self.usd_per_million is None else self.usd_per_million * self.units / Decimal(1_000_000)

    def public(self):
        return {'billable_units_estimate': self.units, 'billing_unit': self.unit_name,
                'usd_per_million_units': None if self.usd_per_million is None else str(self.usd_per_million),
                'estimated_usd_if_executed': None if self.usd is None else str(self.usd),
                'price_checked_on': PRICE_DATE, 'notes': self.notes}


def estimate(request, plan):
    pair = (request.provider, request.model)
    if pair not in USD_PER_MILLION:
        raise LabError('No reviewed billing rule for this provider/model.')
    if request.provider == 'fish':
        units, unit = text_counts(request.text)['utf8_bytes'], 'UTF-8 bytes'
        notes = 'Exact submitted text bytes; no dictionary expansion or inline direction tags.'
        if request.model.endswith('-free'):
            notes += ' Published free developer tier; access/limits/terms remain unverified.'
    elif request.provider == 'azure':
        units, unit = azure_billable_units(plan), 'Azure billable characters (Han doubled + inner SSML)'
        notes = 'Regional/SKU price unknown. Han ideographs/〇 doubled; inner serialized markup counted, speak/voice excluded; entity escaping is a conservative estimate.'
    else:
        units, unit = text_counts(request.text)['unicode_scalars'], 'Unicode characters (scalar estimate)'
        notes = 'List-price text estimate only; vendor reported usage, normalization, plan/taxes and any voice fees can differ.'
    return CostEstimate(units, unit, USD_PER_MILLION[pair], notes)


def check_spend_cap(cap, estimates):
    try:
        limit = Decimal(str(cap))
    except Exception:
        raise LabError('An explicit finite positive USD spend cap is required.') from None
    if not limit.is_finite() or limit <= 0:
        raise LabError('An explicit finite positive USD spend cap is required.')
    if any(item.usd is None for item in estimates):
        raise LabError('Unknown regional/model price prevents a bounded live batch.')
    total = sum((item.usd for item in estimates), Decimal(0))
    if total > limit:
        raise LabError('Estimated batch cost exceeds the explicit spend cap.')
    return total
