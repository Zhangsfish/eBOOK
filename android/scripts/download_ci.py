"""Read existing authenticated gh; verify GitHub artifact digest/ZIP CRC before use."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from envelope import unpack

ROOT = Path(__file__).resolve().parents[2]
GH = Path('E:/odd_jobs/GPT_to_Codex_B001_20261115/tools/gh-2.104.0/bin/gh.exe')


def api(path):
    return subprocess.check_output([str(GH), 'api', path])


def main():
    run = sys.argv[1]
    if not run.isdigit():
        raise ValueError('Numeric run ID required')
    result = json.loads(api('/repos/Zhangsfish/eBOOK/actions/runs/' + run + '/artifacts'))
    base = ROOT / '.local-test-data/ci' / run
    base.mkdir(parents=True, exist_ok=True)
    (base / 'github-artifacts.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    for artifact in result['artifacts']:
        name = artifact['name']
        if name not in ('android-api30-encrypted', 'android-api35-encrypted'):
            continue
        archive = base / (name + '.zip')
        raw = archive.read_bytes() if archive.exists() else api('/repos/Zhangsfish/eBOOK/actions/artifacts/' + str(artifact['id']) + '/zip')
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if digest != artifact['digest']:
            raise ValueError('GitHub artifact SHA256 mismatch')
        archive.write_bytes(raw)
        sealed = base / (name + '-sealed')
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None or any(p.startswith('/') or '\\' in p or '..' in Path(p).parts for p in z.namelist()):
                raise ValueError('Unsafe or corrupt CI ZIP')
            z.extractall(sealed)
        unpack(sealed, base / name)
        print('Verified GitHub artifact', name, digest)


if __name__ == '__main__':
    main()
