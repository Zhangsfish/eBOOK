"""Azure regional REST SSML. Model labels select a voice family, not a JSON field."""
import re
import xml.etree.ElementTree as ET
from .base import Adapter
from ..core import AuthBinding, HTTPPlan, LabError

SSML = 'http://www.w3.org/2001/10/synthesis'
MSTTS = 'https://www.w3.org/2001/mstts'
XML = 'http://www.w3.org/XML/1998/namespace'
ET.register_namespace('', SSML)
ET.register_namespace('mstts', MSTTS)

# Static documentation examples, not proof of access in any configured region.
GENTLE_STYLES = {
    'zh-CN-XiaoxiaoNeural': 'gentle',
    'zh-CN-YunxiNeural': 'narration-relaxed',
    'zh-CN-Xiaoyi:DragonHDFlashLatestNeural': 'gentle',
    'zh-CN-Yunxia:DragonHDFlashLatestNeural': 'comforting',
}


class AzureAdapter(Adapter):
    name = 'azure'
    models = ('neural', 'dragon-hd-flash')

    def supports_style(self, model, voice, style):
        return style == 'neutral' or (style == 'gentle' and voice in GENTLE_STYLES)

    def prepare(self, request):
        self.validate(request)
        if not request.region or not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', request.region):
            raise LabError('A valid Azure public-cloud region is required.')
        if not re.fullmatch(r'zh-CN-[A-Za-z0-9:-]+Neural', request.voice):
            raise LabError('Select a documented Mandarin voice ID.')
        is_hd = ':DragonHD' in request.voice
        if is_hd != (request.model == 'dragon-hd-flash'):
            raise LabError('Azure voice does not match the requested model family.')
        if is_hd and ':DragonHDFlash' not in request.voice:
            raise LabError('This S01 HD profile uses documented Chinese DragonHD Flash voices.')
        if is_hd and request.rate != 1.0:
            raise LabError('HD prosody-rate controls are not supported; no ignored setting is sent.')
        root = ET.Element(f'{{{SSML}}}speak', {'version': '1.0', f'{{{XML}}}lang': 'zh-CN'})
        voice = ET.SubElement(root, f'{{{SSML}}}voice', {'name': request.voice})
        content = voice
        if request.style == 'gentle':
            content = ET.SubElement(content, f'{{{MSTTS}}}express-as', {'style': GENTLE_STYLES[request.voice]})
        if request.rate != 1.0:
            content = ET.SubElement(content, f'{{{SSML}}}prosody', {'rate': f'{(request.rate - 1) * 100:+.4f}%'})
        content.text = request.text  # ElementTree escapes text; imported markup is never executable SSML.
        body = ET.tostring(root, encoding='utf-8', short_empty_elements=False)
        return HTTPPlan(self.name, f'https://{request.region}.tts.speech.microsoft.com/cognitiveservices/v1',
                        {'Content-Type': 'application/ssml+xml',
                         'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
                         'User-Agent': 'eBOOK-S01-VoiceLab'}, body,
                        AuthBinding('AZURE_SPEECH_KEY', 'Ocp-Apim-Subscription-Key'))
