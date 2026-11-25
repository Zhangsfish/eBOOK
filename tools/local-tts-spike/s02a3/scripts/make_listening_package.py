"""Private, offline same-text Matcha/Suxin audition; no publication or audio edits."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import sys
import uuid
import zipfile

REPO = Path(__file__).resolve().parents[4]
SPIKE = REPO / 'tools/local-tts-spike'
sys.path.insert(0, str(SPIKE / 's02a2/scripts'))
from make_listening_page import copy_audio, DIMENSIONS
from model_assets import sha256


def validated_model(label, title, metrics_path, corpus, output):
    metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
    if metrics.get('status') != 'PASS_DESKTOP_ONLY_REAL_WAV' or metrics.get('genuine_ios_inference') is not False:
        raise ValueError('Only genuine explicitly desktop evidence is accepted')
    if metrics.get('corpus_sha256') != sha256(SPIKE / 'fixtures/corpus.json'):
        raise ValueError('Different original corpus')
    rows = metrics['records']
    if [row['fixture_id'] for row in rows] != [case['id'] for case in corpus]:
        raise ValueError('Incomplete original speech set')
    item = {'label': label, 'model': title, 'source_sha': metrics['source_sha'],
            'source_metrics_sha256': sha256(metrics_path),
            'execution_worktree_dirty': metrics.get('execution_worktree_dirty', False),
            'source_file_sha256': metrics.get('source_file_sha256', {}), 'records': []}
    for case, row in zip(corpus, rows):
        expected = hashlib.sha256(case['text'].encode('utf-8')).hexdigest()
        if row['text_sha256'] != expected:
            raise ValueError('Cannot compare different text')
        saved = copy_audio(metrics_path.parent / row['wav_local_name'],
                           output / 'audio' / (label + '-' + case['id'] + '.wav'), row)
        item['records'].append(dict(saved, fixture_id=case['id'], text_sha256=expected,
                                   frontend_missing_phonemes=row.get('frontend_missing_phonemes')))
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--matcha-metrics', type=Path, required=True)
    parser.add_argument('--suxin-metrics', type=Path, required=True)
    args = parser.parse_args()
    corpus = json.loads((SPIKE / 'fixtures/corpus.json').read_text(encoding='utf-8'))['cases']
    output = REPO / '.local-test-data/s02a2/s02a3/listening' / ('matcha-suxin-' + uuid.uuid4().hex)
    (output / 'audio').mkdir(parents=True, exist_ok=False)
    models = [validated_model('A', 'Matcha zh-baker（当前优先候选）', args.matcha_metrics, corpus, output),
              validated_model('B', 'Suxin-Light（等待你试听判断）', args.suxin_metrics, corpus, output)]
    cards = []
    for case in corpus:
        players = ''.join('<div><h3>' + html.escape(model['model']) + '</h3><audio controls preload="metadata" src="audio/' + model['label'] + '-' + case['id'] + '.wav"></audio></div>' for model in models)
        cards.append('<section><h2>' + html.escape(case['id']) + '</h2><p>' + html.escape(case['text']) + '</p><div class="players">' + players + '</div></section>')
    scores = []
    for model in models:
        fields = ''.join('<label>' + dimension + '<select data-model="' + model['label'] + '" data-dimension="' + dimension + '"><option value="">待评 / 暂无法判断</option>' + ''.join('<option>' + str(n) + '</option>' for n in range(1, 6)) + '</select></label>' for dimension in DIMENSIONS)
        scores.append('<fieldset><legend>' + html.escape(model['model']) + '</legend><div class="scores">' + fields + '</div><textarea data-model="' + model['label'] + '" data-dimension="备注" aria-label="' + model['label'] + '备注" placeholder="记录具体读错的词、停顿和听感；短样本无法判断耐听度时留空"></textarea></fieldset>')
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Matcha / Suxin · 真实同文试听</title><style>
:root{font-family:system-ui,"Microsoft YaHei",sans-serif;color:#27302b;background:#f1f1e9}body{max-width:1000px;margin:auto;padding:24px}h1{font-size:27px}h2{font-size:18px}h3{font-size:16px}p{line-height:1.8}section,fieldset,details{background:#fffef8;border:1px solid #d4dacf;border-radius:14px;padding:20px;margin:22px 0}.players{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}audio{width:100%}.notice{padding:16px;background:#e6eddf;border-radius:10px}.scores{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}label{display:grid;gap:6px}select,textarea,button{font:inherit;padding:10px;border:1px solid #a6b3a1;border-radius:7px;background:#fff;color:#27302b}textarea{box-sizing:border-box;width:100%;min-height:90px;margin-top:16px}button{cursor:pointer}code{word-break:break-all}@media(max-width:650px){body{padding:15px}.players{grid-template-columns:1fr}.scores{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(prefers-color-scheme:dark){:root{color:#e7ece4;background:#202620}section,fieldset,details{background:#2b342b;border-color:#55604e}.notice{background:#354432}}
</style><h1>Matcha / Suxin · 真实同文试听</h1>
<p>先听同一段的两种声音，再决定更喜欢谁。全部来自本机 Windows CPU 实际模型合成，未调音量、未变速；没有 Mock、测试音或小说片段。网页完全离线，声音和评分都不上传。</p>
<p class="notice">Matcha 暂为首选，Suxin 由你试听后决定。Matcha 是中文单语模型，mixed 段落里的 Reader、Wi-Fi、Play、Pause 可能被跳过，输入原文没有删改。Suxin 使用作者原装中文/英文前端。短样本不能证明十分钟耐听，无法判断的项目请留空。</p>
''' + ''.join(cards) + '<h2>你的评分（1低 / 5高，可留空）</h2>' + ''.join(scores) + '''
<p><button id="export">导出本机评分 JSON</button> <span id="saved" role="status"></span></p>
<details><summary>音频来源</summary><p>这是桌面试听，不代表 iPhone 或完整原生前端通过。精确源码、文本和 WAV 哈希见同目录 listening-manifest.json。</p></details>
<script>
const fields=[...document.querySelectorAll('[data-model]')];
const key='ebook-s02a3-''' + output.name + '''';
function collect(){return {status:'OWNER_ENTERED_PRIVATE_SCORES',created:new Date().toISOString(),scores:fields.map(e=>({model:e.dataset.model,dimension:e.dataset.dimension,value:e.value}))};}
try{const old=JSON.parse(localStorage.getItem(key)||'null');if(old)for(const e of fields){const r=old.scores.find(x=>x.model===e.dataset.model&&x.dimension===e.dataset.dimension);if(r)e.value=r.value;}}catch{}
for(const e of fields)e.addEventListener('change',()=>{try{localStorage.setItem(key,JSON.stringify(collect()));document.querySelector('#saved').textContent='已保存在此浏览器本机';}catch{document.querySelector('#saved').textContent='请用按钮导出评分';}});
for(const a of document.querySelectorAll('audio'))a.addEventListener('play',()=>{for(const b of document.querySelectorAll('audio'))if(a!==b)b.pause();});
document.querySelector('#export').addEventListener('click',()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='Matcha-Suxin-私人试听评分.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
</script></html>'''
    (output / 'index.html').write_text(page, encoding='utf-8')
    provenance = {'state': 'OWNER_LISTENING_PENDING', 'genuine_ios_inference': False,
        'environment': 'WINDOWS_DESKTOP_CPU', 'audio_edited': False, 'cloud_tts_calls': 0,
        'corpus_sha256': sha256(SPIKE / 'fixtures/corpus.json'), 'models': models}
    (output / 'listening-manifest.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / '原创测试文本.txt').write_text('\n\n'.join(case['id'] + '\n' + case['text'] for case in corpus), encoding='utf-8')
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as target:
        for path in sorted(output.rglob('*')):
            if path.is_file():
                target.write(path, path.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        assert len([name for name in check.namelist() if name.endswith('.wav')]) == 10
        for model in models:
            for row in model['records']:
                assert hashlib.sha256(check.read('audio/' + row['file'])).hexdigest() == row['sha256']
    print('PRIVATE_LISTENING_PAGE', output / 'index.html')
    print('PRIVATE_LISTENING_ZIP', archive)
    print('ZIP_WAV_HASH_AND_CRC_PASS', sha256(archive))


if __name__ == '__main__':
    main()
