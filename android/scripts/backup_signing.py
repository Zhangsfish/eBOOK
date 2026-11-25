"""Back up the owner-authorized cloud signing key in local DPAPI, then remove it.
Only already-installed Paramiko, pywin32 and Python stdlib are used locally.
Never writes the plaintext keystore/password to the local filesystem or output.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import win32crypt
from cloud import connect, ROOT

PRIVATE = ROOT / '.local-test-data/private'
CLOUD = '/root/autodl-tmp/ebook_android_20261125/private-signing'
BACKUP = PRIVATE / 'ebook-upgrade-signing.dpapi'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['backup', 'restore', 'remove-cloud'])
    args = parser.parse_args()
    with connect() as client:
        with client.open_sftp() as sftp:
            if args.operation == 'backup':
                with sftp.open(CLOUD + '/upgrade.p12', 'rb') as f:
                    key = f.read()
                with sftp.open(CLOUD + '/signing-password.txt', 'rb') as f:
                    password = f.read().decode('ascii').strip()
                with sftp.open(CLOUD + '/certificate.expected', 'rb') as f:
                    certificate = f.read().decode('ascii').strip()
                payload = json.dumps(dict(alias='ebook-internal', key_pkcs12_base64=base64.b64encode(key).decode('ascii'),
                                          password=password, key_sha256=hashlib.sha256(key).hexdigest(), certificate_sha256=certificate)).encode('utf-8')
                if BACKUP.exists():
                    old = json.loads(win32crypt.CryptUnprotectData(BACKUP.read_bytes(), None, None, None, 0)[1])
                    if old['certificate_sha256'] != certificate:
                        raise RuntimeError('Existing upgrade certificate differs; refusing to overwrite')
                encrypted = win32crypt.CryptProtectData(payload, 'eBOOK Android upgrade signing', None, None, None, 0)
                if win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1] != payload:
                    raise RuntimeError('DPAPI round-trip verification failed')
                BACKUP.write_bytes(encrypted)
                print('Upgrade key DPAPI CurrentUser backup verified; certificate SHA256', certificate)
            elif args.operation == 'restore':
                saved = json.loads(win32crypt.CryptUnprotectData(BACKUP.read_bytes(), None, None, None, 0)[1])
                key = base64.b64decode(saved['key_pkcs12_base64'])
                if hashlib.sha256(key).hexdigest() != saved['key_sha256']:
                    raise RuntimeError('Protected key digest mismatch')
                try:
                    sftp.mkdir(CLOUD, mode=0o700)
                except IOError:
                    pass
                for name, data in [('upgrade.p12', key), ('signing-password.txt', saved['password'].encode('ascii')), ('certificate.expected', saved['certificate_sha256'].encode('ascii'))]:
                    with sftp.open(CLOUD + '/' + name, 'wb') as f:
                        f.write(data)
                    sftp.chmod(CLOUD + '/' + name, 0o600)
                print('Original upgrade key restored to authorized temporary cloud folder')
            else:
                saved = json.loads(win32crypt.CryptUnprotectData(BACKUP.read_bytes(), None, None, None, 0)[1])
                with sftp.open(CLOUD + '/certificate.expected', 'rb') as f:
                    if f.read().decode('ascii').strip() != saved['certificate_sha256']:
                        raise RuntimeError('Cloud certificate does not match verified backup')
                # Exact known task-only paths, no recursive or computed-root deletion.
                for name in ('upgrade.p12', 'signing-password.txt', 'certificate.expected'):
                    sftp.remove(CLOUD + '/' + name)
                sftp.rmdir(CLOUD)
                print('Cloud temporary signing key/password removed after verified local backup')


if __name__ == '__main__':
    main()
