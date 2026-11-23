#!/usr/bin/env python3
"""Original tiny fixtures only. Python stdlib; no network or dependencies."""
from pathlib import Path
import io
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "Tests" / "Fixtures"
TEXT = "001晨光\r\n\r\n她说：‘今天读一段自己写的故事。’\r\n\r\n002小路\r\n\r\n雨停了，风吹过树梢。\r\n\r\n003归来\r\n\r\n他把书放回桌上，轻声说：‘明天再读。’\r\n\r\n4.第4章后记\r\n\r\n本测试文字为原创合成内容。\r\n"
EXTRA = "补充字符：𠀀与😀。"


def png():
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0\x60\x80\x90\xff')) + chunk(b'IEND', b'')


def epub(version=3, *, traversal=False, entity=False, bad_spine=False):
    metadata = '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>合成的清晨</dc:title><dc:creator>测试作者</dc:creator><dc:identifier id="id">urn:synthetic:s00</dc:identifier><dc:language>zh-CN</dc:language></metadata>'
    nav_item = '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>' if version == 3 else '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    spine = '<spine' + (' toc="ncx"' if version == 2 else '') + '><itemref idref="' + ('missing' if bad_spine else 'c1') + '"/><itemref idref="c2"/></spine>'
    package = f'<package xmlns="http://www.idpf.org/2007/opf" version="{version}.0" unique-identifier="id">{metadata}<manifest>{nav_item}<item id="c1" href="Text/one.xhtml" media-type="application/xhtml+xml"/><item id="c2" href="Text/two.xhtml" media-type="application/xhtml+xml"/><item id="img" href="Images/dot.png" media-type="image/png"/></manifest>{spine}</package>'
    first = '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>第一章</title><style>body{color:red}</style></head><body><h1 id="start">第一章 晨光</h1><p>这是原创合成的第一段。<em>斜体中的文字也要保留。</em></p><p id="dialogue">她说：“请慢慢读。”</p><img src="../Images/dot.png" alt="原创测试像素"/><script>不应显示的脚本</script></body></html>'
    if entity:
        first = '<!DOCTYPE html [<!ENTITY secret SYSTEM "file:///etc/passwd">]>' + first.replace('这是原创', '&secret;这是原创')
    second = '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1 id="end">第二章 回声</h1><p>风从窗边经过。测试结束。</p></body></html>'
    nav = '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body><nav epub:type="toc"><ol><li><a href="Text/one.xhtml#start">晨光</a><ol><li><a href="Text/one.xhtml#dialogue">对话</a></li></ol></li><li><a href="Text/two.xhtml#end">回声</a></li></ol></nav></body></html>'
    ncx = '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap><navPoint id="a" playOrder="1"><navLabel><text>晨光</text></navLabel><content src="Text/one.xhtml#start"/></navPoint><navPoint id="b" playOrder="2"><navLabel><text>回声</text></navLabel><content src="Text/two.xhtml#end"/></navPoint></navMap></ncx>'
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        info = zipfile.ZipInfo('mimetype', date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        archive.writestr(info, 'application/epub+zip')
        resources = {
            'META-INF/container.xml': '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OPS/book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
            'OPS/book.opf': package, 'OPS/Text/one.xhtml': first, 'OPS/Text/two.xhtml': second,
            'OPS/nav.xhtml' if version == 3 else 'OPS/toc.ncx': nav if version == 3 else ncx,
            'OPS/Images/dot.png': png(),
        }
        for name, content in resources.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
        if traversal:
            info = zipfile.ZipInfo('../outside.txt', date_time=(2020, 1, 1, 0, 0, 0))
            archive.writestr(info, 'unsafe path')
    return out.getvalue()


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, encoding in [('utf8', 'utf-8'), ('utf8_bom', 'utf-8-sig'), ('utf16le', 'utf-16-le'), ('utf16be', 'utf-16-be'), ('gbk', 'gbk')]:
        data = TEXT.encode(encoding)
        if name == 'utf16le': data = b'\xff\xfe' + data
        if name == 'utf16be': data = b'\xfe\xff' + data
        (FIXTURES / f'sample_{name}.txt').write_bytes(data)
    (FIXTURES / 'sample_gb18030.txt').write_bytes((TEXT + EXTRA).encode('gb18030'))
    for name, options in [('synthetic', {}), ('synthetic_ncx', {'version': 2}), ('unsafe_path', {'traversal': True}), ('unsafe_entity', {'entity': True}), ('bad_spine', {'bad_spine': True})]:
        (FIXTURES / f'{name}.epub').write_bytes(epub(**options))
    print('Generated 6 tiny original TXT and 5 EPUB fixtures.')


if __name__ == '__main__': main()
