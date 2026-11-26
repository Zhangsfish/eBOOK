"""Export generic syllable data and original-text oracle using existing approved tools.

No package installation, neural inference, private books or network request.
Run with the previously approved Suxin venv; author files remain read-only.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--author-dir', type=Path, required=True)
    parser.add_argument('--production-boundaries', action='store_true')
    args = parser.parse_args()
    author = args.author_dir.resolve()
    expected = {'mixed_frontend.py': '6bbf508c0e7fb6a887da787631d23a09d8e712d5d231e08b8d3a33325cbd333e',
                'synthesizer.py': '3231440ceaf809465373235d9526b7437906c0b18d8892e74822d6684603b769'}
    for name, sha in expected.items():
        assert digest(author / 'suxin_tts' / name) == sha
    assert importlib.metadata.version('pypinyin') == '0.55.0'
    sys.path.insert(0, str(author))
    from suxin_tts.mixed_frontend import MixedFrontend
    from pypinyin import Style
    from pypinyin.style import convert
    import pypinyin
    frontend = MixedFrontend(author, 'zh_en-suxin-light.int8-excldec')
    if args.production_boundaries:
        texts = []
        for prefix in [17, 53, 239]:
            for suffix in ['不是这样，一个人慢慢走过石桥。', '重庆银行的行长重新整理行李。', '一个人看着一杯温水，不是没有办法。']:
                texts.append('甲' * prefix + suffix + '窗边的风吹动书页。' * 4)
        for prefix in [15, 51, 237]:
            texts.append('甲' * prefix + '12:05。今天是2026年，桌上有1234张纸，温度12.05摄氏度。')
        cases = []
        for i, text in enumerate(texts):
            ids, symbols = frontend.prepare(text)
            assert not frontend.missing_phonemes
            cases.append({'id': f'production-{i:02d}', 'text': text, 'ids': ids, 'phonemes': symbols})
        value = {'mode': 'ACTUAL_PINNED_AUTHOR_FRONTEND_ORACLE_NOT_NEURAL_AUDIO',
                 'author_revision': '5ee2da546f3635da263602842d238d8624cb7a81',
                 'author_frontend_sha256': expected['mixed_frontend.py'],
                 'pypinyin': '0.55.0', 'original_text_only': True, 'cases': cases}
        target = ROOT / 'Tests/Fixtures/suxin-production-oracle.json'
        target.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8', newline='\n')
        print('PRODUCTION_AUTHOR_CASES', len(cases), 'BYTES', target.stat().st_size, 'SHA256', digest(target))
        return
    site = Path(pypinyin.__file__).parent
    chars = json.loads((site / 'pinyin_dict.json').read_text(encoding='utf-8'))
    phrases = json.loads((site / 'phrases_dict.json').read_text(encoding='utf-8'))
    syllables = {item for raw in chars.values() for item in raw.split(',')}
    syllables.update(item for values in phrases.values() for variants in values for item in variants)
    table = {}
    for item in sorted(syllables):
        initial = convert(item, Style.INITIALS, strict=False)
        final = convert(item, Style.FINALS_TONE3, strict=False)
        table[item] = frontend._zh_syllable('', initial, final)
    output = ROOT / 'tools/suxin/manifests'
    output.mkdir(parents=True, exist_ok=True)
    value = {'version': 'pypinyin-0.55.0-author-5ee2da5-zh1',
             'provenance': 'Generic dictionary-syllable conversion; not per-book or per-test IDs',
             'author_frontend_sha256': expected['mixed_frontend.py'],
             'pinyin_dict_sha256': digest(site / 'pinyin_dict.json'),
             'phrases_dict_sha256': digest(site / 'phrases_dict.json'),
             'syllables': table}
    (output / 'syllables.json').write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8', newline='\n')
    originals = [
        '清晨的河岸很安静，薄雾沿着石阶慢慢散开。小宁合上笔记，听见远处传来第一声鸟鸣。',
        '“你今天还去图书馆吗？”小宁问。“去，不过我们慢一点走。”朋友笑着回答。',
        '银行旁边的行人道正在施工。小宁重新整理行李，认真比较两种重量不同的乐器。',
        '桌上还有一杯温水，小宁停下脚步，认真读完这一页。',
        '一行人走过银行，重新称量行李。一点也不着急，不要重复。',
        '请到3号窗口，等待12:05的通知。血液检查已经结束。',
        '《原创短篇》：灯还亮着……“不要急！”她说。',
        '山风吹过窗边\n\n小宁认真地整理笔记。',
    ]
    for year in [2001, 2026, 1999, 2030]:
        for number in [0, 1, 10, 11, 20, 101, 1005, 1024, 9999]:
            originals.append(f'今天是{year}年11月24日，书架上有{number}本书，气温18.5摄氏度。')
    for clock in ['00:00', '08:05', '12:30', '23:59']:
        for number in ['1.25', '10.01', '0.5', '999.9']:
            originals.append(f'请在{clock}打开窗户，桌上的标记是{number}。')
    for first in ['重庆', '银行', '重新', '音乐', '长大', '行李', '快乐', '重量']:
        for second in ['一杯温水', '不是这样', '一段故事', '一个人']:
            originals.append(f'小宁读到{first}这个词，又轻声说了{second}。')
    cases = []
    for index, text in enumerate(originals):
        ids, symbols = frontend.prepare(text)
        assert not any(ch.isascii() and ch.isalpha() for ch in text)
        assert not frontend.missing_phonemes
        cases.append({'id': f'author-{index:03d}', 'text': text,
                      'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                      'ids': ids, 'phonemes': symbols})
    fixture = {'mode': 'ACTUAL_PINNED_AUTHOR_FRONTEND_ORACLE_NOT_NEURAL_AUDIO',
               'author_revision': '5ee2da546f3635da263602842d238d8624cb7a81',
               'pypinyin': '0.55.0', 'original_text_only': True, 'cases': cases}
    target = ROOT / 'Tests/Fixtures/suxin-frontend-oracle.json'
    target.write_text(json.dumps(fixture, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8', newline='\n')
    print('EXPORTED_GENERIC_SYLLABLES', len(table), 'AUTHOR_ORIGINAL_CASES', len(cases))
    print('SYLLABLES_SHA256', digest(output / 'syllables.json'))
    print('ORACLE_SHA256', digest(target))


if __name__ == '__main__':
    main()
