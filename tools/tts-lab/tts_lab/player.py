"""Generate a self-contained, blind, local A/B player. No server or CDN."""
import csv
from html import escape
from io import StringIO
import json
from pathlib import Path
from .core import LabError
from .ratings import CRITERIA
from .storage import atomic_bytes


def write_player(directory, samples, tracks, aliases, mode):
    directory = Path(directory)
    # This is the entire browser-visible model. No provider/model/voice mapping.
    visible = []
    for track in tracks:
        audio = track.get('audio')
        if audio and (not audio.startswith('audio/') or '..' in audio or ':' in audio or '\\' in audio):
            raise LabError('Player audio references must be opaque local relative paths.')
        visible.append({'case': track['sample_id'], 'alias': track['alias'],
                        'audio': audio, 'status': 'mock' if audio else 'not_run'})
    data = {'samples': [sample.public() for sample in samples], 'tracks': visible, 'aliases': aliases, 'mode': mode}
    encoded = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    criteria = ''.join(f'<li><span>{escape(title)}</span><b>{weight}%</b></li>' for _, title, weight in CRITERIA)
    html = TEMPLATE.replace('__DATA__', encoded).replace('__CRITERIA__', criteria)
    atomic_bytes(directory / 'index.html', html.encode('utf-8'))
    sheet = StringIO(newline='')
    writer = csv.writer(sheet)
    writer.writerow(['blind_label', *[name for name, _, _ in CRITERIA], 'weighted_score_1_to_5', 'notes'])
    for alias in aliases:
        writer.writerow([alias, *[''] * (len(CRITERIA) + 2)])
    atomic_bytes(directory / 'ratings.csv', ('\ufeff' + sheet.getvalue()).encode('utf-8'))
    guide = ('# 本地盲听评分\n\n当前 S01 没有真实供应商音频。Dry Run 无音频；Mock 只有相同测试音，不能评分。\n'
             '真实听感、延迟与可靠性全部 NOT_RUN，不得据此选供应商。\n\n'
             '后续取得授权和真实音频后，先听同一匿名候选的全部六类片段，再在同目录 ratings.csv 填 1–5 分。\n'
             '七项全填后，加权分为 sum(分数 × 权重 / 100)；留空代表未评估，不能记成零分。\n'
             '以疲劳、齿音、气声、机械节奏、过度咬字、多音字、数字读法和分段衔接为笔记重点。\n'
             '先完成评分，再查看 private-mapping.json；音色库可用性、条款和地区尚未核验。\n'
             '表格按匿名声线整体评分，切换片段不会更换其匿名标签。所有输出与填写后的评分留在当前本地目录。\n\n')
    guide += '\n'.join(f'- {title}：{weight}%' for _, title, weight in CRITERIA) + '\n'
    atomic_bytes(directory / 'LISTENING_GUIDE.md', guide.encode('utf-8'))


TEMPLATE = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; media-src 'self' file:; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'">
<title>中文声线 · 本地盲听台</title>
<style>
:root{color-scheme:light;--paper:#f4f0e6;--card:#fffdf8;--ink:#24382e;--muted:#607267;--line:#d6ddcf;--accent:#3e614d}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:auto;padding:40px 28px 60px}header{display:flex;justify-content:space-between;gap:24px;align-items:start;border-bottom:1px solid var(--line);padding-bottom:28px}
.eyebrow{font-size:12px;letter-spacing:.18em;color:var(--muted)}h1{font-size:clamp(28px,4vw,46px);font-weight:600;letter-spacing:.03em;margin:10px 0}p{margin:8px 0}.small{font-size:13px;color:var(--muted)}
.pill{border:1px solid var(--line);border-radius:24px;padding:6px 14px;white-space:nowrap;font-size:13px}.notice{background:#f3e4bd;border:1px solid #d3b875;border-radius:12px;padding:16px 20px;margin:24px 0}
.toolbar{display:flex;align-items:end;justify-content:space-between;gap:20px;margin:28px 0 18px}label{display:block;font-size:14px;color:var(--muted)}select,button{font:inherit;border:1px solid var(--line);border-radius:8px;padding:9px 12px;background:var(--card);color:var(--ink)}select{max-width:100%;min-height:44px}button{cursor:pointer;min-height:44px}button:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #aa783e;outline-offset:3px}
.text{border-left:3px solid #a1b29a;padding:10px 20px;background:#edf0e5;white-space:pre-wrap;margin-bottom:28px}.compare{display:grid;grid-template-columns:1fr 1fr;gap:20px}.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px}.panel h2{font-size:23px;margin:0 0 16px}.panel select{width:100%;margin:7px 0 18px}audio{width:100%;margin-top:16px;min-height:54px}.state{min-height:48px;color:var(--muted);font-size:14px}.rubric{display:grid;grid-template-columns:1.3fr 1fr;gap:32px;margin-top:30px}h2{font-size:21px}ul{list-style:none;padding:0;margin:0}li{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);padding:8px 0;font-size:14px}a{color:var(--accent)}.note{background:#e4eadf;padding:20px;border-radius:12px}footer{border-top:1px solid var(--line);margin-top:32px;padding-top:16px;color:var(--muted);font-size:13px}
@media(max-width:650px){main{padding:24px 16px}.compare,.rubric{grid-template-columns:1fr}header,.toolbar{display:block}.pill{display:inline-block;margin-top:12px}.toolbar button{margin-top:12px}.panel{padding:20px}}
</style></head><body><main>
<header><div><div class="eyebrow">MANDARIN VOICE LAB / S01</div><h1>慢一点，听清楚。</h1><p class="small">同一段原创文字，同一组分段。先听，再揭晓声线来源。</p></div><span class="pill" id="mode">离线试听规划</span></header>
<section class="notice" aria-label="证据状态"><strong id="warning">尚未合成供应商音频。</strong><p class="small">S01 不执行真实 API 调用。这里没有音质评分、实测延迟或供应商排名。</p></section>
<div class="toolbar"><div><label for="sample">选择原创片段</label><select id="sample"></select></div><button id="stop" type="button">暂停全部播放</button></div>
<p id="purpose" class="small"></p><section class="text" id="text" aria-label="试听原文"></section><p id="pronunciation" class="small"></p>
<section class="compare" aria-label="A/B 盲听比较">
<article class="panel"><h2>A / 左侧</h2><label for="candidate-a">匿名候选</label><select id="candidate-a"></select><div class="state" id="state-a" aria-live="polite"></div><audio id="audio-a" controls preload="none" aria-label="左侧候选音频"></audio></article>
<article class="panel"><h2>B / 右侧</h2><label for="candidate-b">匿名候选</label><select id="candidate-b"></select><div class="state" id="state-b" aria-live="polite"></div><audio id="audio-b" controls preload="none" aria-label="右侧候选音频"></audio></article>
</section>
<section class="rubric"><div><h2>听感记录的七个维度</h2><ul>__CRITERIA__</ul></div><div class="note"><h2>听完一套，再评分</h2><p>同一匿名标签贯穿全部片段。先记录疲劳、齿音、过度咬字、数字读法和分段衔接，再查看供应商映射。</p><p>评分模板已生成在本页面同目录：<code>ratings.csv</code>。填写后的文件也请保存在当前本地目录。</p><p class="small">每项 1–5 分，七项完整后按权重计算；未评估请留空。当前 Dry Run / Mock 无真实声线可评分。</p></div></section>
<footer>仅本地文件 · 不加载第三方资源 · 不上传文字、音频或评分 · 供应商选择仍待真实试听与独立审查</footer>
<script id="audition-data" type="application/json">__DATA__</script>
<script>
'use strict';
const lab=JSON.parse(document.getElementById('audition-data').textContent);
const byId=id=>document.getElementById(id), players=[byId('audio-a'),byId('audio-b')];
function options(element,rows){element.replaceChildren(...rows.map(([value,text])=>{const option=document.createElement('option');option.value=value;option.textContent=text;return option;}));}
options(byId('sample'),lab.samples.map(s=>[s.id,s.title]));
for(const side of ['a','b'])options(byId('candidate-'+side),lab.aliases.map(a=>[a,'候选 '+a]));
byId('candidate-b').selectedIndex=Math.min(1,lab.aliases.length-1);
if(lab.mode==='mock'){byId('mode').textContent='Mock 流程演示';byId('warning').textContent='这些是相同的 0.16 秒测试音，不含语音，不能用来评价供应商。';}
function update(){const sample=lab.samples.find(s=>s.id===byId('sample').value);byId('text').textContent=sample.text;byId('purpose').textContent=sample.purpose;byId('pronunciation').textContent=sample.pronunciation_notes||'';
for(const side of ['a','b']){const audio=byId('audio-'+side);audio.pause();const track=lab.tracks.find(t=>t.case===sample.id&&t.alias===byId('candidate-'+side).value);if(track&&track.audio){audio.src=track.audio;byId('state-'+side).textContent='Mock 测试音；不是供应商朗读。';}else{audio.removeAttribute('src');audio.load();byId('state-'+side).textContent='NOT_RUN · 尚未生成真实供应商音频。';}}}
byId('sample').addEventListener('change',update);for(const side of ['a','b'])byId('candidate-'+side).addEventListener('change',()=>{if(byId('candidate-a').value===byId('candidate-b').value&&lab.aliases.length>1){const other=side==='a'?'b':'a';byId('candidate-'+other).value=lab.aliases.find(a=>a!==byId('candidate-'+side).value);}update();});
byId('stop').addEventListener('click',()=>players.forEach(p=>p.pause()));for(const player of players){player.addEventListener('play',()=>players.filter(p=>p!==player).forEach(p=>p.pause()));player.addEventListener('error',()=>{byId(player.id==='audio-a'?'state-a':'state-b').textContent='本地音频不可用；未发起任何网络合成。';});}update();
</script></main></body></html>'''
