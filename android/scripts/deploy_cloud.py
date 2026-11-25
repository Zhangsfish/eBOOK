"""Deploy a verified committed snapshot, never the other iOS checkout/worktrees."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from cloud import connect, ROOT

CLOUD = '/root/autodl-tmp/ebook_android_20261125'


def main():
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output = ROOT / '.local-test-data/cloud-source'
    output.mkdir(parents=True, exist_ok=True)
    archive = output / (sha + '.zip')
    paths = ['android', 'Tests/Fixtures', 'scripts/generate_long_gb18030_fixture.py']
    # Git archive otherwise applies this Windows checkout's autocrlf to text.
    # Compile the exact committed LF blobs, matching Linux CI and manifest hashes.
    subprocess.run(['git', '-c', 'core.autocrlf=false', 'archive', '--format=zip', '-o', str(archive), sha, *paths], cwd=ROOT, check=True)
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', sha, '--', *paths], cwd=ROOT, text=True).splitlines()
    files = {name: hashlib.sha256(subprocess.check_output(['git', 'show', sha + ':' + name], cwd=ROOT)).hexdigest() for name in names}
    manifest = output / (sha + '.json')
    manifest.write_text(json.dumps(dict(source_sha=sha, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), files=files), indent=2), encoding='utf-8')
    with connect() as client:
        with client.open_sftp() as sftp:
            sftp.put(str(archive), CLOUD + '/source.zip')
            sftp.put(str(manifest), CLOUD + '/SOURCE.json')
        script = '''import hashlib,json,pathlib,shutil,zipfile
base=pathlib.Path('/root/autodl-tmp/ebook_android_20261125')
source=base/'src'
manifest=json.loads((base/'SOURCE.json').read_text())
assert hashlib.sha256((base/'source.zip').read_bytes()).hexdigest()==manifest['archive_sha256']
assert source.resolve()==pathlib.Path('/root/autodl-tmp/ebook_android_20261125/src')
if source.exists(): shutil.rmtree(source)
source.mkdir()
with zipfile.ZipFile(base/'source.zip') as z:
 assert z.testzip() is None and z.comment.decode()==manifest['source_sha']
 assert not any(p.startswith('/') or '..' in pathlib.Path(p).parts or chr(92) in p for p in z.namelist())
 z.extractall(source)
for name,digest in manifest['files'].items():
 assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest,name
shutil.copy2(base/'SOURCE.json',source/'SOURCE.json')
print('Deployed verified committed source',manifest['source_sha'],len(manifest['files']),'files')
'''
        # Exact script over stdin, no shell interpolation of file content.
        stdin, stdout, stderr = client.exec_command('/root/miniconda3/bin/python -')
        stdin.write(script)
        stdin.channel.shutdown_write()
        print(stdout.read().decode(), end='')
        error = stderr.read().decode()
        if error:
            print(error, file=sys.stderr, end='')
        if stdout.channel.recv_exit_status() != 0:
            raise RuntimeError('Cloud source verification failed')


if __name__ == '__main__':
    main()
