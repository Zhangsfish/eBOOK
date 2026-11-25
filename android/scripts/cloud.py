"""Task-local SSH runner; private connection details are outside Git.

Requires only the already-installed F:/anaconda3 Python/Paramiko on Windows.
Never prints credentials. SSH host keys are pinned on first connection in the
ignored task-private directory and must match on subsequent connections.
"""
import argparse
import os
from pathlib import Path
import shlex
import sys
import warnings

warnings.filterwarnings('ignore', category=Warning, module='paramiko')
import paramiko
import win32crypt

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local-test-data' / 'private'


def connect():
    parts = shlex.split((PRIVATE / 'ssh-command.txt').read_text('utf-8'))
    dest = next(x for x in parts if '@' in x)
    user, host = dest.split('@', 1)
    port = int(parts[parts.index('-p') + 1]) if '-p' in parts else 22
    password = win32crypt.CryptUnprotectData(
        (PRIVATE / 'autodl-password.dpapi').read_bytes(), None, None, None, 0)[1].decode('utf-8')
    client = paramiko.SSHClient()
    known = PRIVATE / 'known_hosts'
    if known.exists():
        client.load_host_keys(str(known))
    # Task-specific TOFU: only this directly owner-rented instance, never global.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password,
                   allow_agent=False, look_for_keys=False, timeout=30)
    client.save_host_keys(str(known))
    return client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['exec', 'put', 'get'])
    parser.add_argument('value')
    parser.add_argument('destination', nargs='?')
    args = parser.parse_args()
    with connect() as client:
        if args.operation == 'exec':
            _, stdout, stderr = client.exec_command(args.value, timeout=1800)
            # Reports are restricted to task commands, never secret environment dumps.
            for line in stdout:
                print(line, end='', flush=True)
            error = stderr.read().decode('utf-8', errors='replace')
            if error:
                print(error, file=sys.stderr, end='')
            return stdout.channel.recv_exit_status()
        with client.open_sftp() as sftp:
            if args.operation == 'put':
                sftp.put(args.value, args.destination)
            else:
                Path(args.destination).parent.mkdir(parents=True, exist_ok=True)
                sftp.get(args.value, args.destination)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
