"""Seal CI binary artifacts to the owner's local transport key; no public APK.

CI pack uses existing OpenSSL + stdlib. Local unpack reuses existing Paramiko's
cryptography and Windows DPAPI; no packages are installed by this script.
"""
import argparse
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'android/build'


def pack():
    sealed = BUILD / 'sealed'
    sealed.mkdir(exist_ok=True)
    archive = BUILD / 'evidence-private.tar.gz'
    with tarfile.open(archive, 'w:gz') as out:
        for pattern in ('ebook-unsigned.apk', 'build-info.json', 'core-evidence/core-results.json',
                        'emulator/**/*', 'tools/apksigner.jar'):
            for path in BUILD.glob(pattern):
                if path.is_file():
                    out.add(path, arcname=str(path.relative_to(BUILD)), recursive=False)
    material = secrets.token_bytes(48)
    plain_key = BUILD / 'transport-key.tmp'
    plain_key.write_bytes(material)
    plain_key.chmod(0o600)
    try:
        subprocess.run(['openssl', 'enc', '-aes-256-ctr', '-K', material[:32].hex(), '-iv', material[32:].hex(),
                        '-in', str(archive), '-out', str(sealed / 'evidence.enc')], check=True)
        subprocess.run(['openssl', 'pkeyutl', '-encrypt', '-pubin', '-inkey', str(ROOT / 'android/ci/transport-public.pem'),
                        '-pkeyopt', 'rsa_padding_mode:oaep', '-pkeyopt', 'rsa_oaep_md:sha256',
                        '-in', str(plain_key), '-out', str(sealed / 'sealed-key.bin')], check=True)
    finally:
        plain_key.unlink(missing_ok=True)
        archive.unlink(missing_ok=True)
    metadata = dict(source_sha=os.environ.get('GITHUB_SHA'), api=os.environ.get('EMULATOR_API'),
                    encryption='RSA3072-OAEP-SHA256 + AES256-CTR + HMAC-SHA256',
                    bytes=(sealed / 'evidence.enc').stat().st_size,
                    ciphertext_sha256=hashlib.sha256((sealed / 'evidence.enc').read_bytes()).hexdigest())
    encoded = json.dumps(metadata, sort_keys=True).encode('utf-8')
    (sealed / 'manifest.json').write_bytes(encoded)
    mac = hmac.new(hashlib.sha256(material + b'eBOOK archive authentication').digest(), digestmod='sha256')
    mac.update(encoded)
    mac.update((sealed / 'evidence.enc').read_bytes())
    (sealed / 'mac.sha256').write_text(mac.hexdigest(), encoding='ascii')
    print('Encrypted evidence bundle ready:', metadata['bytes'], 'bytes; no public APK')


def unpack(source, destination, include_tools=False):
    import win32crypt
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    key_bytes = win32crypt.CryptUnprotectData((ROOT / '.local-test-data/private/ci-transport.dpapi').read_bytes(), None, None, None, 0)[1]
    key = serialization.load_pem_private_key(key_bytes, password=None)
    material = key.decrypt((source / 'sealed-key.bin').read_bytes(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    ciphertext = (source / 'evidence.enc').read_bytes()
    encoded = (source / 'manifest.json').read_bytes()
    metadata = json.loads(encoded)
    if hashlib.sha256(ciphertext).hexdigest() != metadata['ciphertext_sha256']:
        raise ValueError('Ciphertext digest mismatch')
    mac = hmac.new(hashlib.sha256(material + b'eBOOK archive authentication').digest(), digestmod='sha256')
    mac.update(encoded)
    mac.update(ciphertext)
    if not hmac.compare_digest(mac.hexdigest(), (source / 'mac.sha256').read_text('ascii').strip()):
        raise ValueError('Artifact authentication failed')
    decryptor = Cipher(algorithms.AES(material[:32]), modes.CTR(material[32:])).decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(plaintext), mode='r:gz') as archive:
        if any(m.issym() or m.islnk() or m.name.startswith('/') or '..' in Path(m.name).parts for m in archive.getmembers()):
            raise ValueError('Unsafe archive')
        for member in archive.getmembers():
            if not include_tools and Path(member.name).parts[0] == 'tools':
                continue  # Local tool confirmation is separate from reading test evidence.
            archive.extract(member, destination)
    print('Authenticated evidence unpacked:', metadata.get('source_sha'), metadata.get('api'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['pack', 'unpack'])
    parser.add_argument('source', nargs='?', type=Path)
    parser.add_argument('destination', nargs='?', type=Path)
    parser.add_argument('--include-tools', action='store_true')
    args = parser.parse_args()
    pack() if args.operation == 'pack' else unpack(args.source, args.destination, args.include_tools)
