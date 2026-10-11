"""本地分镜选择及全参考视频提示词规范；不发起网络请求。"""
import copy
import io
from pathlib import Path
import re
import sys
from PIL import Image


SECTIONS = ('subject_definitions', 'summary', 'retention_analysis', 'detailed_description',
            'overall_soundscape', 'non_diegetic_music')

EXPANSION_VERSION = 'performance-1'

PERFORMANCE_DIRECTION = '''
Performance direction (apply within the six sections, not as an extra section):
- Respect explicit staging and acting choices first, including avoided eye contact,
  monologues, direct address, stylized stillness, and off-screen speakers. Do not
  invent a partner, dialogue, emotional conflict, or reference asset.
- For each visible interaction, establish screen-left/right positions, torso and
  head orientation, and the specific gaze target using stable subject labels.
  Keep these spatial relationships coherent across the shot. A speaker addressing
  a partner normally looks toward that partner's eyes, not vaguely forward.
  For an off-screen partner, specify the off-screen eyeline. Looking into the lens
  is reserved for requested direct address. Preserve intentional gaze avoidance.
- Describe a small causal sequence when useful: attention shifts to the partner,
  a slight head turn follows if needed, then speech begins. Do not force a turn if
  the characters are already facing each other. Use observable behavior instead
  of abstract commands such as 'act naturally' or 'less AI-looking'.
- Give the listener a restrained response to the meaning of the line: a pause,
  softened expression, brief glance, or small posture adjustment when motivated.
  Distinguish who speaks and who listens using stable speaker IDs. Avoid assigning
  every gesture to every person, synchronized nodding, or perpetual eye contact.
- Allow natural breathing, occasional blinks and subtle weight shifts without
  prescribing repetitive cycles. A locked camera does not freeze the actors.
  Keep necessary prop/contact continuity without immobilizing the entire body.
  Use understated facial changes and plausible skin and lighting, not a stack of
  beauty, glossy-skin, or exaggerated cinematic adjectives.
- Character turnaround sheets supply identity, hair and wardrobe, not their
  neutral standing pose, multiple copies, panel borders or camera-facing gaze.
  Scene sheets supply layout and materials, not four simultaneous panels.
  Preserve a picture's exact pose/composition only when requested as a frame anchor.
- Budget the supplied duration for any attention shift, the exact supplied speech,
  natural pauses and a listener response. Favor one clear dramatic beat per shot.
  If speech is dense, remove optional gestures and extra cuts first; never rewrite,
  omit or add dialogue, silently extend duration, or demand unnaturally rushed speech.
- Before output, silently check gaze targets, screen directions, speaker order,
  speech/action timing and conflicting motion instructions. Repair conflicts in
  your own added directions without overriding explicit user intent. This is an
  internal self-check, not a seventh section or a claim of guaranteed video quality.
'''


def validate_expansion_inputs(seconds, images):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 4 <= seconds <= 15:
        raise ValueError('视频提示词扩写时长必须为 4–15 秒')
    if len(images) > 9:
        raise ValueError('视频提示词扩写最多支持 9 张参考图片')
    try:
        for data in images:
            with Image.open(io.BytesIO(data)) as image:
                image.load()
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError('参考图片无法解码，请更换有效图片') from exc


def select_shot(shots, config):
    index = config.get('shotIndex')
    if (not isinstance(shots, list) or type(index) is not int or not 0 <= index < len(shots)
            or not isinstance(shots[index], dict) or shots[index] != config.get('selectedShot')):
        raise ValueError('请连接提取分镜节点并选择分镜；原分镜变化后需要重新选择')
    shot = shots[index]
    duration = shot.get('durationMs')
    if type(duration) is not int or not 4000 <= duration <= 15000:
        raise ValueError('所选分镜时长必须为 4–15 秒，请重新提取或编辑分镜')
    if not isinstance(shot.get('visualPrompt'), str) or not shot['visualPrompt'].strip():
        raise ValueError('所选分镜缺少画面描述，请重新选择')
    text = '\n'.join(f'{label}：{shot[field]}' for field, label in
                     [('title', '分镜'), ('visualPrompt', '画面'), ('dialogue', '对白'),
                      ('shotSize', '景别'), ('cameraMove', '镜头运动')] if shot.get(field))
    seconds = duration / 1000
    return {'text': text + f'\n时长：{seconds:g} 秒', 'shot': copy.deepcopy(shot), 'seconds': seconds}


def expansion_instruction():
    root = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[3]
    guide = (root / 'ref-en.txt').read_text(encoding='utf-8-sig')
    return ('Rewrite the user input as a complete video generation prompt using the following guide. '
            'The target duration must be 4–15 seconds and match the supplied duration exactly. '
            'Keep the supplied plot, identities, dialogue and reference numbering. Do not copy the example plot. '
            'Use all supplied reference images in their numbered order when the user requests them. '
            'Only describe reference appearance visible in supplied images or explicitly provided in the text; '
            'do not invent reference assets, sources or reference characteristics. '
            'If there are no reference assets, use N/A in subject_definitions and retention_analysis and '
            'describe the intended scene without invented reference labels. '
            'Output only the six named sections in order, each as section_name: followed by its content, '
            'without markdown fences or explanations.\n\n' + guide + '\n\n' + PERFORMANCE_DIRECTION)


def validate_expansion(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    matches = list(re.finditer(r'^\s*(' + '|'.join(SECTIONS) + r'):\s*', text, re.MULTILINE))
    if tuple(match.group(1) for match in matches) != SECTIONS or text[:matches[0].start()].strip():
        raise ValueError('扩写结果必须包含规范的六段内容')
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if not text[match.end():end].strip():
            raise ValueError('扩写结果包含空段落')
    return text
