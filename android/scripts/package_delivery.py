"""Build the local friend-facing ZIP from verified cloud release + actual evidence.
No tools, keys, private books, models, test APKs or CI credentials enter delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ANDROID = ROOT / 'android'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    version = json.loads((args.release / 'version-and-source.json').read_text('utf-8'))
    results = json.loads(args.results.read_text('utf-8'))
    if not version['signed'] or results['status'] != 'READY_FOR_AUDIT':
        raise ValueError('Signed APK and completed audit handoff evidence required')
    apk = args.release / version['apk_file']
    if hashlib.sha256(apk.read_bytes()).hexdigest() != version['apk_sha256']:
        raise ValueError('Signed APK digest changed')
    destination = ANDROID / 'delivery'
    destination.mkdir(exist_ok=True)
    files = {
        apk.name: apk.read_bytes(),
        '安装与使用说明.txt': (ANDROID / 'reports/INSTALL_GUIDE.zh-CN.md').read_text('utf-8').encode('utf-8-sig'),
        '真实测试报告.txt': args.report.read_text('utf-8').encode('utf-8-sig'),
        '版本与源码.json': json.dumps(version, ensure_ascii=False, indent=2).encode('utf-8'),
        'TEST_RESULTS.json': args.results.read_bytes(),
        '签名验证.txt': (args.release / 'signature-verification.txt').read_bytes(),
        '包信息.txt': (args.release / 'package-verification.txt').read_bytes(),
    }
    forbidden = ('.jks', '.p12', '.keystore', '.dpapi', '.jar', '.aab', '.wav', '.onnx', '.bin')
    if any(name.lower().endswith(forbidden) for name in files):
        raise ValueError('Forbidden private/tool artifact in delivery')
    sums = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in files.items())
    files['SHA256SUMS.txt'] = sums.encode('utf-8')
    archive = destination / 'HUAWEI_Mate_X3_eBOOK_Android_0.1.0_20261126.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for name, data in files.items():
            out.writestr(name, data)
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None or set(check.namelist()) != set(files):
            raise ValueError('Delivery ZIP structure/CRC mismatch')
        for name, data in files.items():
            if hashlib.sha256(check.read(name)).digest() != hashlib.sha256(data).digest():
                raise ValueError('Delivery member digest mismatch')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n', encoding='utf-8')
    print('Verified local delivery ZIP:', archive)
    print('Bytes:', archive.stat().st_size, 'SHA256:', digest)


if __name__ == '__main__':
    main()
