"""Owner-selected AutoDL signing; never called in public CI or on local computer.
The key is temporary on the disposable cloud container and must be backed up with
backup_signing.py, verified, and removed from the cloud before final shutdown.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CLOUD = Path('/root/autodl-tmp/ebook_android_20261125')
TOOLS = CLOUD / 'toolchain'
BUILD = ROOT / 'android/build'
RELEASE = BUILD / 'release'


def run(args, **kwargs):
    print('+', ' '.join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def main():
    if not str(ROOT.resolve()).startswith(str(CLOUD) + '/'):
        raise RuntimeError('Signing is authorized only in the task-specific AutoDL prefix')
    os.umask(0o077)
    private = CLOUD / 'private-signing'
    private.mkdir(mode=0o700, exist_ok=True)
    private.chmod(0o700)
    keystore = private / 'upgrade.p12'
    password_file = private / 'signing-password.txt'
    if not keystore.exists():
        password_file.write_text(secrets.token_urlsafe(40), encoding='ascii')
    if not password_file.exists():
        raise RuntimeError('Signing password missing; restore the original key, do not replace it')
    os.environ['EBOOK_SIGN_PASS'] = password_file.read_text('ascii').strip()
    os.environ['JAVA_HOME'] = str(TOOLS / 'jdk')
    os.environ['PATH'] = str(TOOLS / 'jdk/bin') + os.pathsep + os.environ['PATH']
    if not keystore.exists():
        run([TOOLS / 'jdk/bin/keytool', '-genkeypair', '-keystore', keystore, '-storetype', 'PKCS12',
             '-storepass:env', 'EBOOK_SIGN_PASS', '-keypass:env', 'EBOOK_SIGN_PASS', '-alias', 'ebook-internal',
             '-dname', 'CN=eBOOK Internal Test,O=Private Development,C=CN', '-keyalg', 'RSA', '-keysize', '3072',
             '-sigalg', 'SHA256withRSA', '-validity', '10950', '-noprompt'])
    RELEASE.mkdir(exist_ok=True)
    apk = RELEASE / 'eBOOK-0.1.0-android.1.apk'
    signer = TOOLS / 'sdk/build-tools/35.0.0/apksigner'
    run([signer, 'sign', '--ks', keystore, '--ks-pass', 'env:EBOOK_SIGN_PASS', '--ks-key-alias', 'ebook-internal',
         '--min-sdk-version', '26', '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true',
         '--v3-signing-enabled', 'true', '--v4-signing-enabled', 'false', '--out', apk, BUILD / 'ebook-unsigned.apk'])
    verified = subprocess.check_output([str(signer), 'verify', '--verbose', '--print-certs', str(apk)], text=True)
    if 'Verified using v2 scheme (APK Signature Scheme v2): true' not in verified or 'Verified using v3 scheme (APK Signature Scheme v3): true' not in verified:
        raise RuntimeError('Required v2/v3 signature verification did not pass')
    (RELEASE / 'signature-verification.txt').write_text(verified, encoding='utf-8')
    fingerprint = re.search(r'certificate SHA-256 digest: ([a-f0-9]+)', verified).group(1)
    if (private / 'certificate.expected').exists() and (private / 'certificate.expected').read_text().strip() != fingerprint:
        raise RuntimeError('Upgrade certificate changed')
    (private / 'certificate.expected').write_text(fingerprint, encoding='ascii')
    badging = subprocess.check_output([str(TOOLS / 'sdk/build-tools/35.0.0/aapt2'), 'dump', 'badging', str(apk)], text=True)
    (RELEASE / 'package-verification.txt').write_text(badging, encoding='utf-8')
    if "package: name='cn.zhangsfish.ebook'" not in badging or "targetSdkVersion:'35'" not in badging or not any(label in badging for label in ("minSdkVersion:'26'","sdkVersion:'26'")):
        raise RuntimeError('Unexpected package metadata')
    if 'android.permission.INTERNET' in badging or 'cn.zhangsfish.ebook.tests' in badging:
        raise RuntimeError('Unexpected network permission or test package')
    with zipfile.ZipFile(apk) as archive:
        if archive.testzip() is not None or any(n.startswith('assets/') for n in archive.namelist()):
            raise RuntimeError('APK CRC error or unexpected bundled test books')
        entries = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if not n.startswith('META-INF/')}
    metadata = json.loads((BUILD / 'build-info.json').read_text('utf-8'))
    metadata.update(signed=True, signing='internal-test RSA3072 / SHA256; official verification v2+v3 PASS',
                    apk_file=apk.name, apk_bytes=apk.stat().st_size,
                    apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(), certificate_sha256=fingerprint,
                    apk_payload_sha256=entries, physical_Huawei='NOT_RUN')
    (RELEASE / 'version-and-source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Signed and officially verified', apk.name, metadata['apk_bytes'], 'bytes', metadata['source_sha'])


if __name__ == '__main__':
    main()
