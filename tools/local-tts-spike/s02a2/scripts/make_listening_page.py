"""Private offline A/B materials made only from verified real original-text WAVs."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import shutil
import uuid
import wave
import zipfile
from model_assets import SPIKE, REPO, LOCAL, sha256

DIMENSIONS = ['自然度', '柔和程度', '情绪表现', '停顿', '发音', '长时间耐听程度']


def copy_audio(source, destination, row):
    if sha256(source) != row['wav_sha256']:
        raise ValueError('Source waveform differs from measured real output')
    with wave.open(str(source), 'rb') as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getframerate() != row['sample_rate'] or audio.getnframes() != row['frames']:
            raise ValueError('Waveform format/frame mismatch')
        if len(audio.readframes(audio.getnframes())) != row['frames'] * 2:
            raise ValueError('Truncated waveform')
    shutil.copy2(source, destination)
    return {'file': destination.name, 'sha256': sha256(destination), 'bytes': destination.stat().st_size,
            'duration_seconds': row['duration_seconds'], 'sample_rate': row['sample_rate']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--matcha-metrics', type=Path, required=True)
    parser.add_argument('--suxin-metrics', type=Path)
    args = parser.parse_args()
    corpus_path = SPIKE / 'fixtures/corpus.json'
    corpus = json.loads(corpus_path.read_text(encoding='utf-8'))['cases']
    baseline = json.loads((SPIKE / 'evidence/desktop-metrics.json').read_text(encoding='utf-8'))
    old = [r for r in baseline['records'] if r['voice'] == 'zf_001']
    baseline_dirs = [p for p in (REPO / '.local-test-data/s02a').glob('desktop-*') if p.is_dir()]
    candidates = []
    for p in baseline_dirs:
        if all((p / r['wav_local_name']).is_file() and sha256(p / r['wav_local_name']) == r['wav_sha256'] for r in old):
            candidates.append(p)
    if len(candidates) != 1: raise ValueError('A unique verified original Kokoro output set is required')
    matcha = json.loads(args.matcha_metrics.read_text(encoding='utf-8'))
    if matcha['status'] != 'PASS_DESKTOP_ONLY_REAL_WAV' or matcha['genuine_ios_inference']:
        raise ValueError('Expected actual desktop Matcha evidence')
    models = [('A', 'Kokoro zf_001', baseline, old, candidates[0]),
              ('B', 'Matcha zh-baker 单中文女声', matcha, matcha['records'], args.matcha_metrics.parent)]
    if args.suxin_metrics:
        suxin = json.loads(args.suxin_metrics.read_text(encoding='utf-8'))
        if suxin['status'] != 'PASS_DESKTOP_ONLY_REAL_WAV' or suxin['genuine_ios_inference']:
            raise ValueError('Expected actual desktop Suxin evidence')
        models.append(('C', 'Suxin-Light', suxin, suxin['records'], args.suxin_metrics.parent))
    destination = LOCAL / 'comparison' / ('listening-' + uuid.uuid4().hex)
    destination.mkdir(parents=True, exist_ok=False)
    audio_dir = destination / 'audio'; audio_dir.mkdir()
    manifest = {'status': 'REAL_DESKTOP_AUDIO_OWNER_QUALITY_PENDING', 'corpus_sha256': sha256(corpus_path),
        'environment': 'WINDOWS_DESKTOP_CPU', 'genuine_ios_inference': False,
        'audio_edited': False, 'models': [], 'cloud_api_calls': 0,
        'm5': 'REFERENCE_ONLY_OFFICIAL_PRERECORDED_DIFFERENT_TEXT_NO_MODEL_RUN'}
    for label, name, metrics, rows, source in models:
        if [r['fixture_id'] for r in rows] != [c['id'] for c in corpus]: raise ValueError('Original corpus mismatch')
        item = {'label': label, 'model': name, 'source_sha': metrics['source_sha'],
            'source_file_sha256': metrics.get('source_file_sha256', {}),
            'execution_worktree_dirty': metrics.get('execution_worktree_dirty', False), 'records': []}
        for case, row in zip(corpus, rows):
            if row['text_sha256'] != hashlib.sha256(case['text'].encode('utf-8')).hexdigest():
                raise ValueError('Cannot compare different text')
            filename = label + '-' + case['id'] + '.wav'
            saved = copy_audio(source / row['wav_local_name'], audio_dir / filename, row)
            item['records'].append(dict(saved, fixture_id=case['id'], text_sha256=row['text_sha256']))
        manifest['models'].append(item)
    cards = []
    for case in corpus:
        players = ''.join('<div><b>声音 ' + label + '</b><audio controls preload="metadata" src="audio/' + label + '-' + case['id'] + '.wav"></audio></div>' for label, *_ in models)
        cards.append('<section><h2>' + html.escape(case['id']) + '</h2><p>' + html.escape(case['text']) + '</p><div class="players">' + players + '</div></section>')
    scores = []
    for label, *_ in models:
        cells = ''.join('<label>' + title + '<select data-label="' + label + '" data-dimension="' + title + '"><option value="">待评 / 暂无法判断</option>' + ''.join('<option>' + str(n) + '</option>' for n in range(1, 6)) + '</select></label>' for title in DIMENSIONS)
        scores.append('<fieldset><legend>声音 ' + label + '</legend><div class="scores">' + cells + '</div><textarea data-label="' + label + '" placeholder="记录具体句子、刺耳/含糊音、停顿或听久后的感受"></textarea></fieldset>')
    mapping = '<br>'.join(html.escape(label + ' = ' + name + '，桌面实际合成 SHA ' + metrics['source_sha']) for label, name, metrics, *_ in models)
    pending = '' if args.suxin_metrics else '<p class="notice">Suxin-Light：NOT_RUN，前端依赖安装确认待答复；没有用其他声音代替。</p>'
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>中文本地 TTS · 私有同文试听</title><style>
:root{color-scheme:light dark;font-family:system-ui,"Microsoft YaHei",sans-serif;background:#f3f0e8;color:#292d29}body{max-width:1080px;margin:auto;padding:28px}h1{font-size:28px}p{line-height:1.8}section,fieldset,details{border:1px solid #d5d7cf;border-radius:14px;padding:20px;margin:20px 0;background:#fffdf7}h2{font-size:17px;color:#606760}.players{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}audio{display:block;width:100%;margin-top:10px}.notice{padding:15px;background:#f6ead2;border-radius:10px}.scores{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}label{display:grid;gap:6px}select,textarea,button{font:inherit;padding:9px;border:1px solid #aeb5aa;border-radius:8px;background:#fff;color:#222}textarea{box-sizing:border-box;width:100%;min-height:75px;margin-top:14px}button{cursor:pointer;margin-right:10px}a{color:#426852}small{color:#606760}@media(prefers-color-scheme:dark){:root{background:#1f2421;color:#e1e5df}section,fieldset,details{background:#2c332d;border-color:#556052}.notice{background:#493c27}h2,small{color:#b6c4b5}a{color:#afd3a9}}
</style><h1>中文本地 TTS · 私有同文试听</h1>
<p>下面全部是<strong>同一份原创中文</strong>经模型实际生成的 Windows WAV。没有 Mock、测试音或商业小说；不代表 iPhone 结果。先用原速听同一段，再看模型名称。只试听和评分，不上传任何内容。</p>
<p class="notice">B 是单中文模型，mixed 测试中的 Reader、Wi-Fi、Play、Pause 会被跳过。录音保持各模型原始输出，未做音量归一化。短样本不足以证明十分钟耐听度，无法判断时保留“待评”。</p>
''' + pending + ''.join(cards) + '''<details><summary>显示模型及精确来源</summary><p>''' + mapping + '''</p></details>
<h2>你的评分（1 低 / 5 高）</h2><p>请依据实际听感填写；程序不会从速度或 ASR 编造自然度评分。</p>''' + ''.join(scores) + '''
<p><button id="export">导出本机评分 JSON</button><span id="saved" role="status"></span></p>
<section><h2>M5-TTS：仅官方参考试听</h2><p>未运行本模型，未生成同文样本，不纳入上述 A/B 评分。<a href="https://aslp-lab.github.io/M5-TTS-Demo-Page/" target="_blank" rel="noopener">打开官方预录演示</a>会联网加载官方样本，但不发送这里的测试文本。50M LM 不含独立 codec；服务器数据不代表手机。</p></section>
<script>
const fields=[...document.querySelectorAll('select[data-label],textarea[data-label]')];
const key='ebook-s02a2-private-listening-v1';
function collect(){return {status:'OWNER_ENTERED_PRIVATE_SCORES',created:new Date().toISOString(),scores:fields.map(e=>({label:e.dataset.label,dimension:e.dataset.dimension||'notes',value:e.value}))};}
try{const old=JSON.parse(localStorage.getItem(key)||'null');if(old)for(const e of fields){const row=old.scores.find(r=>r.label===e.dataset.label&&r.dimension===(e.dataset.dimension||'notes'));if(row)e.value=row.value;}}catch{}
for(const e of fields)e.addEventListener('change',()=>{try{localStorage.setItem(key,JSON.stringify(collect()));document.querySelector('#saved').textContent='已保存在当前浏览器本机';}catch{document.querySelector('#saved').textContent='无法自动保存，请导出评分';}});
for(const a of document.querySelectorAll('audio'))a.addEventListener('play',()=>{for(const b of document.querySelectorAll('audio'))if(a!==b)b.pause();});
document.querySelector('#export').addEventListener('click',()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='私人试听评分.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
</script></html>'''
    (destination / 'index.html').write_text(page, encoding='utf-8')
    (destination / 'listening-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / '原创测试文本.txt').write_text('\n\n'.join(c['id'] + '\n' + c['text'] for c in corpus), encoding='utf-8')
    archive = destination.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as target:
        for path in sorted(destination.rglob('*')):
            if path.is_file(): target.write(path, path.relative_to(destination).as_posix())
    print('PRIVATE_LISTENING_PAGE', destination / 'index.html')
    print('PRIVATE_LISTENING_ZIP', archive)


if __name__ == '__main__': main()
