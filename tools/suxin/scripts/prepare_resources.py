"""Prepare deterministic, verified Suxin resources; no package installation.

Only model/config/LICENSE and two JSON dictionaries from a hash-pinned wheel
are consumed. No wheel code or setup script executes. Outputs are Git-ignored.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / '.local-test-data/s02b'
REVISION = '5ee2da546f3635da263602842d238d8624cb7a81'
ASSETS = [
    ('zh_en-suxin-light.int8-excldec.onnx', 'model.onnx', 67260202, '5dbe3500e7d36835e073dad4f3502a579ae497f62c0a6574c736345237e1e7aa'),
    ('zh_en-suxin-light.int8-excldec.onnx.json', 'config.json', 5981, '7228b4619a4eb38c8f297fab80b63051e0c059c196696e186b38b9d8a0fb29dd'),
    ('LICENSE', 'author-LICENSE.txt', 1353, 'c00757a3751a61e3cf5229887e183d6aa11f6ce9a1aecb6a10e20505f5a4cb6d'),
]
WHEEL = 'pypinyin-0.55.0-py2.py3-none-any.whl'
WHEEL_SHA = 'd53b1e8ad2cdb815fb2cb604ed3123372f5a28c6f447571244aca36fc62a286f'


def sha(path):
    with path.open('rb') as source:
        value = hashlib.sha256()
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def download(url, path, expected, size):
    if path.exists():
        if sha(path) != expected or path.stat().st_size != size:
            raise ValueError('Existing source mismatch; preserve and inspect ' + path.name)
        return path
    temporary = path.with_suffix(path.suffix + '.partial')
    if temporary.exists():
        raise FileExistsError('Preserve prior interrupted download: ' + str(temporary))
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open('xb') as target:
        shutil.copyfileobj(response, target, 1024 * 1024)
    if sha(temporary) != expected or temporary.stat().st_size != size:
        raise ValueError('Source download failed integrity validation')
    temporary.rename(path)
    return path


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path)
    parser.add_argument('--pypinyin-wheel', type=Path)
    args = parser.parse_args()
    downloads = LOCAL / 'downloads'; downloads.mkdir(parents=True, exist_ok=True)
    output = LOCAL / 'bundle/Suxin'; output.mkdir(parents=True, exist_ok=True)
    for source_name, name, size, digest in ASSETS:
        if args.source_dir:
            source = args.source_dir / source_name
            if sha(source) != digest or source.stat().st_size != size:
                raise ValueError('Local author source integrity failure')
        else:
            url = f'https://huggingface.co/TEQUILA123/suxin-light/resolve/{REVISION}/{source_name}'
            source = download(url, downloads / source_name, digest, size)
        shutil.copyfile(source, output / name)
    if args.pypinyin_wheel:
        wheel = args.pypinyin_wheel
        if sha(wheel) != WHEEL_SHA or wheel.stat().st_size != 840203:
            raise ValueError('Local wheel integrity failure')
    else:
        with urllib.request.urlopen('https://pypi.org/pypi/pypinyin/0.55.0/json', timeout=30) as response:
            metadata = json.load(response)
        row = next(item for item in metadata['urls'] if item['filename'] == WHEEL)
        if row['digests']['sha256'] != WHEEL_SHA or row['size'] != 840203:
            raise ValueError('Official wheel metadata mismatch')
        if not row['url'].startswith('https://files.pythonhosted.org/'):
            raise ValueError('Unexpected official wheel host')
        wheel = download(row['url'], downloads / WHEEL, WHEEL_SHA, 840203)
    with zipfile.ZipFile(wheel) as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupt dictionary archive')
        chars_raw = archive.read('pypinyin/pinyin_dict.json')
        phrases_raw = archive.read('pypinyin/phrases_dict.json')
        pins = json.loads((ROOT / 'tools/suxin/manifests/syllables.json').read_text(encoding='utf-8'))
        if hashlib.sha256(chars_raw).hexdigest() != pins['pinyin_dict_sha256'] or hashlib.sha256(phrases_raw).hexdigest() != pins['phrases_dict_sha256']:
            raise ValueError('Dictionary differs from the author-oracle source')
        chars = {chr(int(key)): value.split(',')[0] for key, value in json.loads(chars_raw).items()}
        phrases = {key: [item[0] for item in value] for key, value in json.loads(phrases_raw).items()}
        write_json(output / 'lexicon.json', {'characters': chars, 'phrases': phrases})
        shutil.copyfile(ROOT / 'tools/suxin/manifests/syllables.json', output / 'syllables.json')
        licenses = [name for name in archive.namelist() if '.dist-info/' in name and Path(name).name.lower() in ['license', 'license.txt']]
        if len(licenses) != 1:
            raise ValueError('Pinned dictionary license missing or ambiguous')
        (output / 'pypinyin-LICENSE.txt').write_bytes(archive.read(licenses[0]))
    names = ['model.onnx', 'config.json', 'lexicon.json', 'syllables.json', 'author-LICENSE.txt', 'pypinyin-LICENSE.txt']
    manifest = {'schema': 1, 'modelRevision': REVISION, 'frontendVersion': pins['version'],
                'sampleRate': 22050, 'scope': 'Native Mandarin; explicit Apple fallback for mixed English/unsupported text',
                'licenseState': 'ROOT_DECLARATIONS_PRESENT_TRANSITIVE_DISTRIBUTION_REVIEW_INCOMPLETE',
                'files': [{'path': name, 'bytes': (output / name).stat().st_size, 'sha256': sha(output / name)} for name in names]}
    write_json(output / 'manifest.json', manifest)
    print('SUXIN_RESOURCES_VERIFIED', output, 'bytes', sum(item['bytes'] for item in manifest['files']))
    print('RESOURCE_MANIFEST_SHA256', sha(output / 'manifest.json'))


if __name__ == '__main__':
    main()
