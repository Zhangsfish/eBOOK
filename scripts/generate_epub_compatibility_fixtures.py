#!/usr/bin/env python3
"""Original EPUB regressions; reproduces markup forms, never an owner's text."""
from pathlib import Path
from zipfile import ZipFile
import io
from generate_small_fixtures import epub

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'Tests/Fixtures'
BODY = '''<h1 id="start">晨光</h1><div><p>换行前<br>换行后。<br/>原有闭合换行。</p>
<p id="dialogue">她说：这段内容是我们自己写的。😀</p>
<img src="../Images/dot.png" alt="原创测试像素"><hr><p>最后一段仍然保留。</p></div>''' + ''.join(
    f'<p>原创阅读段落{i}。清晨的光落在桌面上，她把书签轻轻夹好，准备继续读下去。</p>' for i in range(16))


def document(body=BODY, encoding='utf-8', bom=b''):
    declaration = 'UTF-8' if encoding == 'utf-8' else ('UTF-16LE' if encoding.endswith('le') else 'UTF-16BE')
    text = f'''<?xml version="1.0" encoding="{declaration}"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>原创章节</title>
<meta name="test" content="original"><link href="../unused.css" rel="stylesheet"></head>
<body>{body}</body></html>'''
    return bom + text.encode(encoding)


def package(first, *, metadata=None):
    out = io.BytesIO()
    with ZipFile(io.BytesIO(epub(version=2))) as source, ZipFile(out, 'w') as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == 'OPS/Text/one.xhtml': data = first
            if item.filename == 'OPS/Text/two.xhtml':
                # Leave enough real text after the target for a live chapter
                # anchor; a one-screen book cannot scroll its last row to top.
                tail = ''.join(f'<p>原创尾段{i}。窗外的树影慢慢移动，书页上的故事仍在继续。</p>' for i in range(16))
                data = data.replace(b'</body>', tail.encode('utf-8') + b'</body>')
            if metadata is not None and item.filename == 'OPS/book.opf': data = metadata
            target.writestr(item, data)
    return out.getvalue()


def main():
    cases = {'compat_void.epub': document()}
    for name, encoding, bom in [('le', 'utf-16-le', b'\xff\xfe'), ('be', 'utf-16-be', b'\xfe\xff'),
                                 ('le_nobom', 'utf-16-le', b''), ('be_nobom', 'utf-16-be', b'')]:
        cases[f'compat_void_{name}.epub'] = document(encoding=encoding, bom=bom)
    cases['compat_literals.epub'] = document('''<h1 id="start">晨光</h1>
<!-- <br> is a comment, not a tag -->
<p><![CDATA[字面 <br> 不应被改写。]]></p>
<p><span title="符号 > / &quot;">引号属性后的正文。</span><br>成对内容保留。</br></p>
<div><br><p id="dialogue">未闭合换行之后的原创句子。</p>
<img src="../Images/dot.png" alt="原创测试像素"></div>''')
    cases['compat_bad_nesting.epub'] = document('<div><p>不可恢复的原创建议测试。</div></p>')
    cases['compat_bad_attribute.epub'] = document('<p title="literal <br>">属性仍非法。</p><br>')
    cases['compat_truncated.epub'] = document().rsplit(b'</body>', 1)[0]
    declarations = {
        'file': "<!DOCTYPE html [<!ENTITY forbidden SYSTEM 'file:///not-a-book-secret'>]>",
        'remote': "<!DOCTYPE html [<!ENTITY forbidden SYSTEM 'https://example.invalid/forbidden'>]>",
        'internal': "<!DOCTYPE html [<!ENTITY forbidden 'expanded'>]>",
    }
    for name, declaration in declarations.items():
        value = document('<p>原创实体拒绝测试。</p><br>&forbidden;').decode('utf-8')
        value = value.replace('?>', '?>' + declaration, 1)
        cases[f'compat_entity_{name}.epub'] = value.encode('utf-8')
        if name == 'internal':
            for order in ['le', 'be']:
                cases[f'compat_entity_{order}.epub'] = value.replace('UTF-8', 'UTF-16' + order.upper()).encode('utf-16-' + order)
    for name, content in cases.items(): (DEST / name).write_bytes(package(content))
    print(f'Generated {len(cases)} tiny original EPUB compatibility fixtures.')


if __name__ == '__main__': main()
