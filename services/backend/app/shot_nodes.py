"""本地分镜选择及全参考视频提示词规范；不发起网络请求。"""
import copy
import io
from pathlib import Path
import re
import sys
from PIL import Image


SECTIONS = ('subject_definitions', 'summary', 'retention_analysis', 'detailed_description',
            'overall_soundscape', 'non_diegetic_music')

EXPANSION_VERSION = 'performance-8-visual-only'

PERFORMANCE_DIRECTION = '''
Performance direction (apply within the six sections, not as an extra section):
- Plan executable timing before prose. A 4–15 second clip normally contains one
  dramatic beat, not an entire encounter. Do not add cuts, prop interactions or
  dramatic events just to illustrate an aesthetic. Slow pacing needs fewer events.
- Within detailed_description, start each [Shot N] with its start timestamp in
  MM:SS.mmm, starting at 00:00.000. Keep timestamps increasing and below the target
  duration. The last shot ends at the target duration. Budget speech, pauses and
  prerequisite actions within each interval, not merely within the whole clip.
- Estimate translated dialogue after translation, not from the source language.
  For planning use approximately 4 Chinese characters/second, 5 Japanese written
  characters/second or 2.5 English words/second; slow emotional delivery needs more
  time. Reserve time for reaction and physical actions. Never speed through a long
  line, omit requested dialogue, or silently extend the target duration.
- Track initial positions, paths, contact and final object states. For an accident,
  establish the obstacle in the rider's visible path before avoidance; specify
  deceleration, contact and landing in physical order. A fall does not automatically
  propel someone into a bystander. Do not invent extra collisions or injury details.
  After impact, establish balance and support before picking up props or speaking.
  If an accident plus its aftermath cannot fit, it belongs in separate source shots;
  do not hide missing physical transitions through cuts or simultaneous wording.
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
- Ground object motion in visible contact and a plausible force. For a manually
  operated door, specify which free hand reaches the handle or push plate, makes
  contact, operates it if needed, and pushes or pulls before the door moves.
  Track closed/open state and hinge or sliding direction consistently; the body
  crosses the threshold only after sufficient clearance. Keep the crucial contact
  visible with framing compatible with the requested shot; avoid adding arbitrary
  close-ups or cuts. Do not invent an automatic door to skip the hand action.
- When the scene actually contains a double door, treat its two leaves as separate
  objects with independent contact, hinges and open/closed states. Identify the
  operated leaf by a stable spatial description and the specific operating hand.
  One hand moves only the leaf it contacts; the untouched leaf remains in its
  established state. For a person carrying a bag, prefer opening just one leaf
  with the free hand when that provides adequate clearance, then passing through
  that opening with the bag. Do not silently move both leaves symmetrically.
  If both leaves must open, describe two available hands contacting separate leaves
  or explicit sequential contact with each leaf; account for the first leaf's
  support/closer and clearance before releasing it. Respect an automatic or linked
  mechanism only when established by the user or reference; never invent one to
  justify unsupported motion. Preserve the reference door type and do not add
  a double door to a scene that does not specify or show one.
- Account for occupied hands and supported objects. If a character carries a bag,
  establish which hand or shoulder supports it and which hand operates the door.
  Transfers or putting an object down must occur before using the newly freed hand.
  Do not teleport props, fuse hands with handles, or assign one hand simultaneous
  incompatible actions. Apply the same contact-before-motion principle to cups,
  chairs, phones and other objects only when they are actually manipulated.
- A reaction requires a perceptible cue before recognition. Establish what the
  character can see given their head direction, occlusion and position, or what
  they can hear. A door chime can cause an orienting glance, but does not establish
  the entrant's identity. Use cue -> orient eyes/head -> acquire line of sight ->
  recognize -> react or speak. Preserve explicitly established prior knowledge,
  voice recognition, anticipation or fantasy; do not invent these to bridge a gap.
- Keep concurrent events separate from sequential prerequisites. Avoid writing
  entering, noticing, identifying and speaking as simultaneous actions. Make room
  for essential contact and perception beats before optional camera or prop motion.
  For crowded dialogue, keep exact words and speaker order, simplify optional
  staging, and do not hide missing causal steps with a cut or an abrupt time jump.
- Attach (S1), (S2), etc. to the person producing the voice, never to the person
  being looked at or addressed. Bind each spoken line to that speaker's own action
  clause and mouth movement. The listener reacts after the relevant cue or words.
  Speaker IDs follow actual speaking order, not picture numbering.
- Before output, silently check gaze targets, screen directions, speaker order,
  speech/action timing, hand availability, contact-before-motion, object states,
  perception-before-recognition and conflicting motion instructions. Repair conflicts in
  your own added directions without overriding explicit user intent. This is an
  internal self-check, not a seventh section or a claim of guaranteed video quality.
'''


def validate_timing_budget(text, seconds):
    """Heuristic speech guard, not measured TTS duration or a physics evaluator."""
    body = text.split('detailed_description:', 1)[-1].split('overall_soundscape:', 1)[0]
    stamp = re.compile(r'(?<!\d)(?:(\d{1,2}):)?(\d{1,2}):(\d{2}(?:\.\d+)?)(?!\d)')

    def moment(match):
        return int(match[1] or 0) * 3600 + int(match[2]) * 60 + float(match[3])

    # Only interpret timestamps in shot headings, not quoted dialogue or sound cues.
    shots = list(re.finditer(r'\[Shot\s+\d+\]', body, re.IGNORECASE))
    intervals = []
    starts = []
    for index, marker in enumerate(shots):
        end = shots[index + 1].start() if index + 1 < len(shots) else len(body)
        section = body[marker.end():end]
        match = stamp.search(section[:80].split('<d>', 1)[0])
        if not match and index == 0:
            starts.append((0.0, section))
        if match:
            start = moment(match)
            if start >= seconds or (starts and start <= starts[-1][0]):
                raise ValueError('分镜时间安排超出目标时长或顺序错误，请重新扩写或拆分分镜')
            starts.append((start, section))
    if shots and len(starts) == len(shots):
        intervals = [(section, (starts[i + 1][0] if i + 1 < len(starts) else seconds) - start)
                     for i, (start, section) in enumerate(starts)]
    else:
        intervals = [(body, seconds)]
    for index, (section, available) in enumerate(intervals):
        lines = re.findall(r'<d>(.*?)</d>', section, flags=re.DOTALL | re.IGNORECASE)
        required = 0.0
        for line in lines:
            japanese = bool(re.search(r'Japanese|日语|日本語|[\u3040-\u30ff]', line, re.IGNORECASE))
            clean = re.sub(r'\[[^\]]*\]|<[^>]*>', '', line)
            cjk = len(re.findall(r'[\u3040-\u30ff\u3400-\u9fff]', clean))
            words = len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", clean))
            required += cjk / (6 if japanese else 4.5) + words / 2.5 + 0.35
        if lines and required + 0.5 > available:
            raise ValueError(f'第{index + 1}段对白估算至少需要{required + 0.5:.1f}秒，但仅分配{available:g}秒；请拆分分镜或精简对白后重新扩写，不应强行加速')


def validate_expansion_inputs(seconds, images, audios=None, videos=None):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 4 <= seconds <= 15:
        raise ValueError('视频提示词扩写时长必须为 4–15 秒')
    if len(images) > 9:
        raise ValueError('视频提示词扩写最多支持 9 张参考图片')
    for label, items in [('音频', audios or []), ('视频', videos or [])]:
        if len(items) > 3:
            raise ValueError(f'视频提示词扩写最多支持 3 段参考{label}')
        if any(not isinstance(data, bytes) or not data or len(data) > 20 * 1024 * 1024 for data in items):
            raise ValueError(f'参考{label}为空或超过 20 MiB，请先裁剪或压缩')
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
            'Use supplied images and silent <Video N> references in their numbered order. No audio is supplied to this rewriting stage. '
            'Analyze visible action causality, eye lines and camera movement only; never claim to hear reference audio or video sound. '
            'Adapt reference timing to the target duration instead of copying a longer sequence. Use all supplied reference images in their numbered order when the user requests them. '
            'Only describe reference appearance visible in supplied images or explicitly provided in the text; '
            'do not invent reference assets, sources or reference characteristics. '
            'An audio reference for voice timbre does not specify spoken words. Preserve exact user dialogue and speaker assignments; do not add speech. '
            'When audio is not supplied, only retain an Audio binding explicitly requested by the user for later video generation; never claim to have heard it or invent its pitch, gender, accent or transcript. '
            'When a model cannot hear video sound, do not infer a transcript from video frames. '
            'If there are no reference assets or explicit future bindings, use N/A in subject_definitions and retention_analysis and '
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
