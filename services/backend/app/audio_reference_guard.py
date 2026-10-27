"""Validate H3 audio references without requiring an audio-capable expansion model."""
import re


def validate_audio_labels(text, count):
    for number in re.findall(r'<Audio\s+(\d+)>', text, flags=re.IGNORECASE):
        if not 1 <= int(number) <= count:
            raise ValueError(f'提示词引用音频 {number}，实际只有 {count} 段音频；请检查接线和编号')


def video_audio_indices(links, dependencies):
    videos, audio_slots = {}, []
    counts = {'video': 0, 'video_audio': 0}
    video_count = 0
    for link in links:
        port = link['port']
        if port not in counts:
            continue
        counts[port] += 1
        handle = link.get('targetHandle', '')
        digits = ''.join(c for c in handle if c.isdigit())
        slot = int(digits or '1') if handle else counts[port]
        assets = dependencies[link['source']]['output'].get('assets', [])
        if port == 'video':
            videos[slot] = (video_count, len(assets))
            video_count += len(assets)
        elif assets:
            if len(assets) != 1:
                raise ValueError('配套视频音频端口只能输入一段音频')
            audio_slots.append(slot)
    # Preserve actual video pairing first; unpaired inputs still get an upload slot.
    reserved = {videos[slot][0] for slot in audio_slots if slot in videos and videos[slot][1] == 1}
    indices = []
    for slot in audio_slots:
        if slot in videos and videos[slot][1] == 1:
            index = videos[slot][0]
        else:
            available = [i for i in range(3) if i not in reserved and i not in indices]
            index = slot - 1 if slot - 1 in available else available[0]
        indices.append(index)
    return indices
