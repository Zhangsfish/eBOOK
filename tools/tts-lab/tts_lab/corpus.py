"""Only the checked-in original short sample suite is accepted by the CLI."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import re
from .core import LabError, chunks, normalize_text, text_counts

CORPUS_PATH = Path(__file__).resolve().parents[1] / 'samples' / 'corpus.json'


@dataclass(frozen=True)
class Sample:
    id: str
    title: str
    purpose: str
    text: str
    pronunciation_notes: str = ''

    @property
    def pieces(self):
        return chunks(self.text)

    def public(self):
        return {'id': self.id, 'title': self.title, 'purpose': self.purpose,
                'text': self.text, 'pronunciation_notes': self.pronunciation_notes,
                'counts': text_counts(self.text), 'text_sha256': sha256(self.text.encode()).hexdigest(),
                'chunks': [{'index': i, 'text_sha256': sha256(text.encode()).hexdigest(),
                            **text_counts(text)} for i, text in enumerate(self.pieces)]}


def load_samples():
    value = json.loads(CORPUS_PATH.read_text(encoding='utf-8'))
    if value['version'] != 's01-original-mandarin-v1' or len(value['samples']) != 6:
        raise LabError('Unexpected original corpus version or sample count.')
    result = []
    for item in value['samples']:
        sample = Sample(item['id'], item['title'], item['purpose'], normalize_text(item['text']),
                        item.get('pronunciation_notes', ''))
        if not re.fullmatch(r'[a-z_]+', sample.id) or len(sample.text) > 1000:
            raise LabError('Invalid original sample ID/length.')
        result.append(sample)
    if len({sample.id for sample in result}) != len(result):
        raise LabError('Duplicate sample IDs.')
    return result
