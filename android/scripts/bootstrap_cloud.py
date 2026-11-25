"""Install owner-authorized, isolated official build tools on the temporary CPU host.
SDK stays in the task prefix; an Ubuntu JDK may be reused from the dedicated
owner-rented disposable container. No Gradle, IDE, GMS or license auto-accept command.
Downloads are checked against publisher hashes; observed SHA256/version is recorded.
"""
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('/root/autodl-tmp/ebook_android_20261125')
TOOLS = ROOT / 'toolchain'
TOOLS.mkdir(parents=True, exist_ok=True)
manifest = []


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ebook-android-build/1.0'}), timeout=90)


def download(url, filename, expected, algorithm, size):
    target = TOOLS / filename
    if not (target.exists() and hashlib.new(algorithm, target.read_bytes()).hexdigest().lower() == expected.lower()):
        # Preserve valid prefixes from an interrupted transfer; range responses
        # must identify the exact requested offset and publisher-declared total.
        chunk_size = 8 * 1024 * 1024
        parts = []
        for start in range(0, size, chunk_size):
            stop = min(size, start + chunk_size)
            part = TOOLS / (filename + '.part-' + str(start))
            if not part.exists() and target.exists() and target.stat().st_size > start:
                with target.open('rb') as source, part.open('wb') as out:
                    source.seek(start)
                    out.write(source.read(min(stop - start, target.stat().st_size - start)))
            parts.append((start, stop, part))

        def fragment(item):
            start, stop, part = item
            for attempt in range(6):
                have = part.stat().st_size if part.exists() else 0
                if have == stop - start:
                    return
                if have > stop - start:
                    raise ValueError('Oversized download fragment')
                more, headers = Path(str(part) + '.next'), Path(str(part) + '.headers')
                subprocess.run(['curl', '--fail', '--location', '--range', str(start + have) + '-' + str(stop - 1),
                                '--connect-timeout', '30', '--max-time', '240', '--silent', '--show-error',
                                '--dump-header', str(headers), '--output', str(more), url], check=False)
                ranges = re.findall(r'(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)', headers.read_text(errors='replace') if headers.exists() else '')
                if more.exists() and ranges and int(ranges[-1][0]) == start + have and int(ranges[-1][2]) == size and more.stat().st_size <= stop - start - have:
                    with part.open('ab') as out, more.open('rb') as source:
                        shutil.copyfileobj(source, out)
                more.unlink(missing_ok=True)
                headers.unlink(missing_ok=True)
            raise ValueError('Range download did not complete: ' + filename + ':' + str(start))

        print('Verified-range transfer', filename, size, 'bytes', flush=True)
        with ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(fragment, parts))
        with target.open('wb') as out:
            for _, _, part in parts:
                with part.open('rb') as source:
                    shutil.copyfileobj(source, out)
        if hashlib.new(algorithm, target.read_bytes()).hexdigest().lower() != expected.lower():
            raise ValueError('Official final hash mismatch: ' + filename)
        for _, _, part in parts:
            part.unlink(missing_ok=True)
    manifest.append(dict(file=filename, url=url, bytes=target.stat().st_size,
                         official_hash_algorithm=algorithm, official_hash=expected,
                         sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    return target


# Official GitHub Release API metadata, read with the existing authenticated gh CLI.
# Pin the release; don't depend on the API edge accepting a cloud datacenter request.
package = dict(name='OpenJDK17U-jdk_x64_linux_hotspot_17.0.21.1_2.tar.gz',
               link='https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21.1%2B2/OpenJDK17U-jdk_x64_linux_hotspot_17.0.21.1_2.tar.gz',
               checksum='0b0ac5eab6db6abaec68c9913bcddb31321e5da411c45073d520d9c125e6f7b4', size=193630735)
system_jdk = Path('/usr/lib/jvm/java-17-openjdk-amd64')
if (system_jdk / 'bin/javac').exists():
    # Owner-authorized new disposable CPU container only. Ubuntu APT validates
    # signed repository metadata/package digests, using its existing Huawei mirror.
    if not (TOOLS / 'jdk').exists():
        (TOOLS / 'jdk').symlink_to(system_jdk, target_is_directory=True)
    manifest.append(dict(jdk_source='Ubuntu signed APT repository / preconfigured Huawei mirror',
                         package_version=subprocess.check_output(['dpkg-query','-W','-f=${Version}','openjdk-17-jdk-headless'],text=True),
                         javac_sha256=hashlib.sha256((system_jdk / 'bin/javac').read_bytes()).hexdigest()))
else:
    jdk = download(package['link'], package['name'], package['checksum'], 'sha256', package['size'])
    if not (TOOLS / 'jdk' / 'bin' / 'javac').exists():
        with tarfile.open(jdk) as archive:
            members = archive.getmembers()
            if any(m.name.startswith('/') or '..' in Path(m.name).parts for m in members):
                raise ValueError('Unsafe JDK archive')
            archive.extractall(TOOLS / 'java')
        (TOOLS / 'jdk').symlink_to(next((TOOLS / 'java').iterdir()), target_is_directory=True)

with fetch('https://dl.google.com/android/repository/repository2-3.xml') as response:
    repository = ET.fromstring(response.read())


def local_tag(element):
    return element.tag.split('}')[-1]


def descendants(element, tag):
    return [e for e in element.iter() if local_tag(e) == tag]


for identifier in ('platforms;android-35', 'build-tools;35.0.0', 'platform-tools'):
    item = next(e for e in repository if e.attrib.get('path') == identifier)
    candidates = descendants(item, 'archive')
    arc = next(a for a in candidates if not descendants(a, 'host-os')
               or descendants(a, 'host-os')[0].text == 'linux')
    complete = descendants(arc, 'complete')[0]
    filename = descendants(complete, 'url')[0].text
    checksum = descendants(complete, 'checksum')[0]
    artifact = download('https://dl.google.com/android/repository/' + filename,
                        filename, checksum.text, checksum.attrib.get('type', 'sha1'), int(descendants(complete, 'size')[0].text))
    dest = TOOLS / 'sdk'
    if identifier == 'build-tools;35.0.0':
        dest = dest / 'build-tools'
    elif identifier.startswith('platforms;'):
        dest = dest / 'platforms'
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact) as archive:
        if any(n.startswith('/') or '..' in Path(n).parts for n in archive.namelist()):
            raise ValueError('Unsafe SDK archive')
        archive.extractall(dest)
    if identifier == 'build-tools;35.0.0':
        original = dest / 'android-15'
        if original.exists() and not (dest / '35.0.0').exists():
            original.rename(dest / '35.0.0')
    if identifier == 'platforms;android-35':
        original = dest / 'android-35'
        # Archive currently uses android-35; preserve official directory.
        if not original.exists():
            found = next(p for p in dest.iterdir() if (p / 'android.jar').exists())
            found.rename(original)

for path in (TOOLS / 'sdk').rglob('*'):
    if path.is_file() and (path.suffix in ('', '.sh') or path.name in ('aapt2', 'd8', 'apksigner', 'zipalign', 'adb')):
        path.chmod(path.stat().st_mode | 0o111)
manifest.append(dict(jdk=str((TOOLS / 'jdk').resolve()), sdk_platform=35, build_tools='35.0.0',
                     android_sdk_license='https://developer.android.com/studio/terms',
                     scope='temporary isolated owner-authorized AutoDL CPU build only'))
(TOOLS / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Official tools verified in isolated cloud prefix', flush=True)
